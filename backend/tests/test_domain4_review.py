from uuid import uuid4
from unittest.mock import MagicMock
from app.models.claim import Claim, ClaimStatus, ClaimPage, ClaimTile, TileType
from app.models.extraction import ExtractedData
from app.services.review import ReviewService
from app.schemas.review import ReviewPayload, ReviewCorrection

def test_resolve_correction_and_settle():
    # Setup
    db = MagicMock()
    service = ReviewService(db)
    
    # Mock Claim (Needs Review, Math Mismatch)
    claim_id = uuid4()
    claim = Claim(id=claim_id, status=ClaimStatus.NEEDS_REVIEW)
    db.query().filter().first.return_value = claim
    
    # Mock Tile & Extraction (Total = 140, Sum = 150)
    tile_id = uuid4()
    
    # We need to simulate the _apply_correction logic finding the extraction
    extraction = ExtractedData(
        tile_id=tile_id,
        raw_json={
            "fields": {
                "total_amount": {"value": 140.00}
            }
        }
    )
    db.query().filter().first.side_effect = [claim, extraction, claim] 
    # 1. get claim, 2. get extraction, 3. refresh claim logic inside resolve/auditor

    # But we also need the AuditorService to see the *updated* values.
    # Since we are mocking DB, we need to ensure the objects in memory share state or we mock auditor.
    # To test the integration properly without a real DB is hard for the "Shadow Audit" re-run part
    # because Auditor traverses the claim -> pages -> tiles -> extraction relationship.
    
    # Let's mock the AuditorService inside the ReviewService
    service.auditor = MagicMock()
    service.auditor.validate_claim.return_value = [] # Return CLEAN on re-audit
    
    # Action: Correct the Total to 150.00
    payload = ReviewPayload(corrections=[
        ReviewCorrection(tile_id=tile_id, field_name="total_amount", new_value=150.00)
    ])
    
    result = service.resolve_claim(claim_id, payload)
    
    # Assert
    # 1. Correction Applied
    assert extraction.raw_json["fields"]["total_amount"]["value"] == 150.00
    assert extraction.raw_json["fields"]["total_amount"]["manual_override"] is True
    
    # 2. Re-Audit called
    service.auditor.validate_claim.assert_called_with(claim)
    
    # 3. Settle called (implicitly check status)
    assert claim.status == ClaimStatus.COMPLETED
    assert result["status"] == ClaimStatus.COMPLETED

def test_resolve_failure():
    # Setup
    db = MagicMock()
    service = ReviewService(db)
    service.auditor = MagicMock()
    service.auditor.validate_claim.return_value = ["STILL_ERROR"] 
    
    claim = Claim(id=uuid4(), status=ClaimStatus.NEEDS_REVIEW)
    db.query().filter().first.return_value = claim
    
    # Action
    payload = ReviewPayload(corrections=[])
    result = service.resolve_claim(uuid4(), payload)
    
    # Assert
    assert claim.status == ClaimStatus.NEEDS_REVIEW
    assert result["status"] == ClaimStatus.NEEDS_REVIEW
