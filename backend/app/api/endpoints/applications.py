from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.services.ingestion import IngestionService
from app.schemas.application import ClaimApplicationResponse, ClaimApplicationDetailResponse
from app.models.application import ClaimApplication
from app.models.claim import ClaimStatus

router = APIRouter()

@router.post("/ingest", response_model=ClaimApplicationResponse)
async def ingest_application(
    files: List[UploadFile],
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    service = IngestionService(db)
    return await service.create_application(files)

@router.get("/", response_model=List[ClaimApplicationDetailResponse])
def list_applications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return db.query(ClaimApplication).order_by(ClaimApplication.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=ClaimApplicationDetailResponse)
def get_application(
    id: UUID,
    db: Session = Depends(get_db)
):
    app = db.query(ClaimApplication).filter(ClaimApplication.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app
