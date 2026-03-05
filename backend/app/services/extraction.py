import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.claim import Claim, ClaimStatus, ClaimTile
from app.models.extraction import ExtractedData
from app.llm.provider import QwenLocalProvider

import logging

logger = logging.getLogger(__name__)

class ExtractionService:
    def __init__(self, db: Session):
        self.db = db
        self.provider = QwenLocalProvider()

    async def extract_tile(self, tile_id: uuid.UUID) -> ExtractedData:
        # Get Tile
        tile = self.db.query(ClaimTile).filter(ClaimTile.id == tile_id).first()
        if not tile:
            raise ValueError("Tile not found")

        # Idempotency: Check if extraction already exists
        existing = self.db.query(ExtractedData).filter(ExtractedData.tile_id == tile_id).first()
        if existing:
            logger.info(f"Tile {tile_id} already extracted. Skipping.")
            return existing

        # Call LLM
        # Note: tile.image_path refers to local fs
        logger.info(f"Extracting tile {tile_id} ({tile.type}). Sending to LLM...")
        # Add a placeholder for user visibility in logs if needed, but logging is fine for now.
        result = await self.provider.extract_from_tile(tile.image_path, tile.type)
        logger.info(f"Received LLM response for tile {tile_id}")
        
        # Save Result
        extraction = ExtractedData(
            id=uuid.uuid4(),
            tile_id=tile.id,
            raw_json=result
        )
        self.db.add(extraction)
        self.db.commit()
        return extraction

    async def extract_claim(self, claim_id: uuid.UUID):
        # Transactional Lock: Prevent double processing
        # We assume the caller handles the transaction scope or we commit here.
        # Since we use self.db.commit(), we own the transaction in this scope.
        try:
            claim_record = self.db.query(Claim).with_for_update().filter(Claim.id == claim_id).first()
            
            if not claim_record:
                logger.error(f"Claim {claim_id} not found.")
                return []
            
            # Idempotency Check
            if claim_record.status not in [ClaimStatus.PROCESSING, ClaimStatus.REJECTED]:
                logger.info(f"Claim {claim_id} is in status {claim_record.status}. Skipping extraction.")
                return []

            claim_record.status = ClaimStatus.EXTRACTING
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Database lock failed for claim {claim_id}: {e}")
            self.db.rollback()
            raise e

        logger.info(f"Starting extraction for claim {claim_id}")
        tiles = self.db.query(ClaimTile).join(ClaimTile.page).filter(ClaimTile.page.has(claim_id=claim_id)).all()
        results = []
        if not tiles:
            logger.warning(f"No tiles found for claim {claim_id}")
            return []

        success_count = 0
        for tile in tiles:
            try:
                res = await self.extract_tile(tile.id)
                results.append(res)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to extract tile {tile.id}: {e}")
        
        
        if success_count == 0 and tiles:
            raise Exception(f"Failed to extract any tiles for claim {claim_id}. See logs for details.")

        logger.info(f"Completed extraction for claim {claim_id}. Processed {len(results)} tiles.")
        return results
