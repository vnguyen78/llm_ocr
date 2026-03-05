from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.models.audit import AuditFlag
from app.models.claim import Claim
from app.auditor.service import AuditorService

router = APIRouter()

@router.post("/{claim_id}/audit", response_model=List[AuditFlag])
def trigger_audit(claim_id: UUID, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    service = AuditorService()
    flags = service.validate_claim(claim)
    
    return flags
