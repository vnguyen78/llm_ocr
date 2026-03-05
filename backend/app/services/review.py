from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.claim import Claim, ClaimStatus
from app.models.extraction import ExtractedData, ReviewCorrection
from app.models.audit import AuditFlag
from app.schemas.review import ReviewPayload
from app.auditor.service import AuditorService
from app.services.settlement import SettlementService
from sqlalchemy.orm.attributes import flag_modified

class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.auditor = AuditorService()
        self.settlement = SettlementService(db)

    def get_queue(self, status: str = ClaimStatus.NEEDS_REVIEW) -> List[Any]:
        """Returns claims filtered by status."""
        print(f"DEBUG: get_queue called for status {status}")
        query = self.db.query(Claim)
        if status == ClaimStatus.PROCESSING:
            query = query.filter(Claim.status.in_([ClaimStatus.PROCESSING, ClaimStatus.EXTRACTING]))
        else:
            query = query.filter(Claim.status == status)
        claims = query.order_by(Claim.created_at.desc()).all()
        
        from app.schemas.claim import ClaimResponse
        return [ClaimResponse.model_validate(c).model_dump(mode='json') for c in claims]

    def reject_claim(self, claim_id: UUID):
        """Moves claim to REJECTED status."""
        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        claim.status = ClaimStatus.REJECTED
        self.db.commit()
        return {"status": "REJECTED"}

    def bulk_reject_claims(self, claim_ids: List[UUID]):
        """Moves multiple claims to REJECTED status."""
        self.db.query(Claim).filter(Claim.id.in_(claim_ids)).update(
            {Claim.status: ClaimStatus.REJECTED}, synchronize_session=False
        )
        self.db.commit()
        return {"status": "BATCH_REJECTED", "count": len(claim_ids)}

    def delete_claim(self, claim_id: UUID):
        """Hard deletes the claim."""
        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        self.db.delete(claim)
        self.db.commit()
        return {"status": "DELETED"}

    def bulk_delete_claims(self, claim_ids: List[UUID]):
        """Hard deletes multiple claims."""
        self.db.query(Claim).filter(Claim.id.in_(claim_ids)).delete(synchronize_session=False)
        self.db.commit()
        return {"status": "BATCH_DELETED", "count": len(claim_ids)}

    def get_claim_details(self, claim_id: UUID) -> Dict[str, Any]:
        """Returns full bundle of claim data for the UI."""
        print(f"DEBUG: get_claim_details called for {claim_id}")
        from sqlalchemy.orm import joinedload
        from app.models.claim import Claim, ClaimPage, ClaimTile
        claim = self.db.query(Claim).options(
            joinedload(Claim.pages).joinedload(ClaimPage.tiles).joinedload(ClaimTile.extraction),
            joinedload(Claim.corrections)
        ).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Sort tiles (Header -> Body -> Footer)
        # Note: We sort the list in place on the ORM object before serialization
        tile_order = {"HEADER": 1, "BODY": 2, "FOOTER": 3}
        for page in claim.pages:
            # Sort tiles in-place. SQLAlchemy collections are list-like.
            page.tiles.sort(key=lambda t: tile_order.get(str(t.type).upper(), 99))

        
        # Determine specific flags
        flags = self.auditor.validate_claim(claim)
        
        # Explicitly convert to schemas and dump to dict to avoid serialization issues
        from app.schemas.claim import ClaimDetailedResponse, ClaimDetailsResponse
        
        details = ClaimDetailsResponse(
            claim=ClaimDetailedResponse.model_validate(claim),
            flags=flags
        )
        return details.model_dump(mode='json')

    def resolve_claim(self, claim_id: UUID, payload: ReviewPayload) -> Dict[str, Any]:
        """
        Applies corrections, re-audits, and settles if clean.
        """
        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")

        # 1. Apply Corrections
        for correction in payload.corrections:
            self._apply_correction(correction)
        
        # Commit corrections so Auditor sees new values
        self.db.commit() 
        self.db.expire_all() # Ensure fresh data for Auditor
        self.db.refresh(claim)

        # 2. Re-Audit
        flags = self.auditor.validate_claim(claim)
        
        # 3. Decision
        should_approve = False
        
        if not flags:
            should_approve = True
        elif payload.confirm_with_issues:
            if not payload.approval_note or not payload.approval_note.strip():
                 raise HTTPException(status_code=400, detail="Approval note is required when confirming with issues")
            
            # Log the User Approval Note
            print(f"Claim {claim_id} approved with issues. Note: {payload.approval_note}")
            should_approve = True

        if should_approve:
            if claim.status == ClaimStatus.AUDITED:
                # Level 2 Approval -> Finalize
                self.settlement.settle_claim(claim)
                status = ClaimStatus.COMPLETED
            else:
                # Level 1 Approval -> Audited
                claim.status = ClaimStatus.AUDITED
                self.db.add(claim)
                self.db.commit()
                status = ClaimStatus.AUDITED
        else:
            # Still issues.
            # Keep as NEEDS_REVIEW and return flags
            if claim.status != ClaimStatus.NEEDS_REVIEW:
                claim.status = ClaimStatus.NEEDS_REVIEW
                self.db.commit()
            status = ClaimStatus.NEEDS_REVIEW

        # Sync Application Status
        from app.services.status_sync import StatusSyncService
        sync_service = StatusSyncService(self.db)
        sync_service.sync_application_status(claim.application_id)

        return {
            "status": status,
            "remaining_flags": flags
        }


    def _apply_correction(self, correction):
        """
        Updates the ExtractedData raw_json with the new value.
        Logs the correction in ReviewCorrection table.
        """
        extraction = self.db.query(ExtractedData).filter(ExtractedData.tile_id == correction.tile_id).first()
        
        if not extraction:
            print(f"WARNING: _apply_correction failed to find extraction for tile_id={correction.tile_id}")
            return

        data = dict(extraction.raw_json) if extraction.raw_json else {}
        
        if "fields" not in data:
            data["fields"] = {}
        
        field_entry = data["fields"].get(correction.field_name, {})
        original_value = field_entry.get("value")
        
        # Log the correction if the value actually changed
        if str(original_value) != str(correction.new_value):
            # We need claim_id, it's available in extraction -> tile -> page -> claim
            # But it's easier to just pass it or get it from tile.
            from app.models.claim import ClaimTile, ClaimPage
            tile = self.db.query(ClaimTile).filter(ClaimTile.id == correction.tile_id).first()
            claim_id = tile.page.claim_id if tile and tile.page else None

            if claim_id:
                audit_log = ReviewCorrection(
                    claim_id=claim_id,
                    tile_id=correction.tile_id,
                    field_name=correction.field_name,
                    original_value=original_value,
                    corrected_value=correction.new_value
                )
                self.db.add(audit_log)

            field_entry["value"] = correction.new_value
            field_entry["confidence"] = 1.0 # Manual override is 100% confident
            field_entry["manual_override"] = True
            
            data["fields"][correction.field_name] = field_entry
            
            extraction.raw_json = data
            flag_modified(extraction, "raw_json")
            self.db.add(extraction)
