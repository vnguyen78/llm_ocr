import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.claim import Claim
from app.config import settings
import uuid

router = APIRouter()

@router.get("/{claim_id}/tiles/{tile_filename}")
async def get_tile(
    claim_id: uuid.UUID,
    tile_filename: str,
    db: Session = Depends(get_db)
):
    # 1. Verify Claim Exists (Basic Security)
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # 2. Construct Path
    # Security: Ensure we are only looking inside the TILES_DIR
    tiles_dir = Path(settings.DATA_DIR) / "tiles"
    tile_path = (tiles_dir / tile_filename).resolve()
    
    # Security: Path Traversal Check
    if not str(tile_path).startswith(str(tiles_dir.resolve())):
        raise HTTPException(status_code=403, detail="Invalid path")
        
    if not tile_path.exists():
        raise HTTPException(status_code=404, detail="Tile not found")
        
    return FileResponse(tile_path)
