import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

# Assuming we have a get_db dependency. If not, I'll need to create one or mock it for now.
# Since I haven't seen app/dependencies.py, I will add a basic one here or assume main has it.
# Ideally I should check main for db setup.

from app.services.ingestion import IngestionService
from app.models.claim import Claim

# Mock DB Handling for now if not existing, but let's try to import from main or create a local get_db
# I'll create a simple get_db stub if needed, but first let's see where DeclarativeBase is connected.

router = APIRouter()

# Placeholder for DB Dependency
# In a real app, this comes from app.dependencies
# In a real app, this comes from app.dependencies
from app.database import get_db

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from app.config import settings
from app.database import SessionLocal
from app.models.claim import Claim, ClaimStatus
from app.services.extraction import ExtractionService

@router.post("/ingest", status_code=202)
async def ingest_claim(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    service = IngestionService(db)
    
    # Validate
    await service.validate_file(file)
    
    # Create Application Wrapper (Backward Compatibility)
    app_id = uuid.uuid4()
    from app.models.application import ClaimApplication
    application = ClaimApplication(id=app_id)
    db.add(application)
    db.commit()

    # Process
    claim_id = uuid.uuid4()
    await service.process_document(file, claim_id, app_id)
    
    # Immediate Trigger for Testing/Debugging
    if settings.TRIGGER_EXTRACTION_IMMEDIATELY:
        async def run_immediate_extraction(cid: uuid.UUID):
            # Create new session for background task
            bg_db = SessionLocal()
            try:
                ext_service = ExtractionService(bg_db)
                claim = bg_db.query(Claim).get(cid)
                if claim and claim.status == ClaimStatus.PROCESSING:
                    await ext_service.extract_claim(cid)
                    # Refresh claim as status might have been changed to EXTRACTING inside extract_claim
                    bg_db.refresh(claim)
                    claim.status = ClaimStatus.NEEDS_REVIEW
                    bg_db.commit()
                    
                    # Sync Application Status
                    from app.services.status_sync import StatusSyncService
                    sync_service = StatusSyncService(bg_db)
                    sync_service.sync_application_status(claim.application_id)
            except Exception as e:
                print(f"Immediate extraction failed: {e}")
            finally:
                bg_db.close()

        background_tasks.add_task(run_immediate_extraction, claim_id)
    
    return {
        "claim_id": str(claim_id),
        "status": "PROCESSING",
        "message": "Upload accepted. Processing started."
    }

from app.services.extraction import ExtractionService

@router.post("/{claim_id}/extract", status_code=202)
async def extract_claim(
    claim_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service = ExtractionService(db)
    # Warning: Long running process. In prod, push to queue.
    await service.extract_claim(claim_id)
    
    return {"status": "EXTRACTION_STARTED", "claim_id": str(claim_id)}

# Include Tiles Router
from app.api.endpoints.tiles import router as tiles_router
router.include_router(tiles_router)
