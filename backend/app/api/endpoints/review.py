from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from app.database import get_db
from app.models.claim import Claim
from app.schemas.review import ReviewPayload, BulkActionRequest
from app.services.review import ReviewService

from app.schemas.claim import ClaimResponse, ClaimDetailsResponse

router = APIRouter()

from fastapi.responses import JSONResponse

@router.get("/queue")
def get_review_queue(status: str = "NEEDS_REVIEW", db: Session = Depends(get_db)):
    service = ReviewService(db)
    return JSONResponse(content=service.get_queue(status))

@router.get("/{claim_id}/details")
def get_claim_details(claim_id: UUID, db: Session = Depends(get_db)):
    service = ReviewService(db)
    return JSONResponse(content=service.get_claim_details(claim_id))

@router.post("/{claim_id}/resolve")
def resolve_claim(claim_id: UUID, payload: ReviewPayload, db: Session = Depends(get_db)):
    service = ReviewService(db)
    return service.resolve_claim(claim_id, payload)

@router.post("/{claim_id}/reject")
def reject_claim(claim_id: UUID, db: Session = Depends(get_db)):
    service = ReviewService(db)
    return service.reject_claim(claim_id)

@router.delete("/{claim_id}")
def delete_claim(claim_id: UUID, db: Session = Depends(get_db)):
    service = ReviewService(db)
    return service.delete_claim(claim_id)

@router.post("/bulk-reject")
def bulk_reject_claims(payload: BulkActionRequest, db: Session = Depends(get_db)):
    service = ReviewService(db)
    return service.bulk_reject_claims(payload.claim_ids)

@router.post("/bulk-delete")
def bulk_delete_claims(payload: BulkActionRequest, db: Session = Depends(get_db)):
    service = ReviewService(db)
    return service.bulk_delete_claims(payload.claim_ids)
