import asyncio
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.claim import Claim, ClaimStatus
from app.services.extraction import ExtractionService

logger = logging.getLogger(__name__)

async def process_pending_claims():
    """
    Scans for claims with status PROCESSING and triggers extraction.
    """
    logger.info("Scheduler: Checking for pending claims...")
    db: Session = SessionLocal()
    try:
        # Find claims in PROCESSING state
        # Limiting to a reasonable number to avoid holding DB lock for too long if many accumulate
        pending_claims = db.query(Claim).filter(Claim.status == ClaimStatus.PROCESSING).limit(10).all()
        
        if not pending_claims:
            logger.info("Scheduler: No pending claims found.")
            return

        logger.info(f"Scheduler: Found {len(pending_claims)} pending claims. Processing...")

        service = ExtractionService(db)

        for claim in pending_claims:
            try:
                logger.info(f"Scheduler: Starting extraction for claim {claim.id}")
                # Trigger extraction
                # Service is expected to handle tile extraction
                await service.extract_claim(claim.id)
                
                # Update status to NEEDS_REVIEW only if successful
                claim.status = ClaimStatus.NEEDS_REVIEW
                db.commit()
                logger.info(f"Scheduler: Claim {claim.id} extracted and moved to NEEDS_REVIEW.")
                
                # Sync Application Status
                from app.services.status_sync import StatusSyncService
                sync_service = StatusSyncService(db)
                sync_service.sync_application_status(claim.application_id)
                
            except Exception as e:
                logger.error(f"Scheduler: Failed to extract claim {claim.id}: {e}")
                db.rollback() 
                # Leave as PROCESSING to retry later. 

    except Exception as e:
        logger.error(f"Scheduler: Global error in process_pending_claims: {e}")
    finally:
        db.close()
