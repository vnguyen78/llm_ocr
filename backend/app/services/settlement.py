from sqlalchemy.orm import Session
from app.models.claim import Claim, ClaimStatus
import logging

logger = logging.getLogger(__name__)

class SettlementService:
    def __init__(self, db: Session):
        self.db = db

    def settle_claim(self, claim: Claim):
        """
        Finalizes a claim.
        1. Updates status to COMPLETED.
        2. (Future) Moves files to long-term storage.
        """
        logger.info(f"Settling claim {claim.id}")
        
        # Update Status
        claim.status = ClaimStatus.COMPLETED
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        
        # TODO: Move files to 'settled/' directory
        return claim
