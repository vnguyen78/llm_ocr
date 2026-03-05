import os
import io
import uuid
import shutil
from typing import List, Tuple
from pathlib import Path
from pdf2image import convert_from_bytes
from PIL import Image
from fastapi import UploadFile, HTTPException

from app.models.claim import Claim, ClaimPage, ClaimTile, TileType
from app.models.application import ClaimApplication, ApplicationStatus

from app.config import settings

DATA_DIR = Path(settings.DATA_DIR)
RAW_DIR = DATA_DIR / "raw"
TILES_DIR = DATA_DIR / "tiles"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
TILES_DIR.mkdir(parents=True, exist_ok=True)

class IngestionService:
    def __init__(self, db_session):
        self.db = db_session

    async def validate_file(self, file: UploadFile) -> None:
        # 1. Size Check (10MB)
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

# Robust Magic Byte Check (No libmagic dependency required)
        # Read header to sniff type
        header = file.file.read(2048)
        file.file.seek(0)
        
        # Magic Signatures
        # PDF: %PDF (25 50 44 46)
        # JPG: FF D8 Basic check
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        
        is_valid = False
        mime = "unknown"
        
        if header.startswith(b"%PDF"):
            is_valid = True
            mime = "application/pdf"
        elif header.startswith(b"\xFF\xD8"):
            is_valid = True
            mime = "image/jpeg"
        elif header.startswith(b"\x89PNG\r\n\x1a\n"):
            is_valid = True
            mime = "image/png"
            
        allowed_mimes = ["application/pdf", "image/jpeg", "image/png"]
        if not is_valid:
             raise HTTPException(status_code=400, detail=f"Unsupported file type. Magic bytes mismatch. Detected: {header[:8].hex()}")

    async def create_application(self, files: List[UploadFile]) -> ClaimApplication:
        app_id = uuid.uuid4()
        # Generate Friendly Name
        # Format: App-YYYYMMDD-HHMM-{ShortUUID}
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        short_id = str(app_id)[:4].upper()
        friendly_name = f"App-{timestamp}-{short_id}"
        
        application = ClaimApplication(id=app_id, name=friendly_name)
        self.db.add(application)
        self.db.commit()

        for file in files:
            await self.validate_file(file)
            claim_id = uuid.uuid4()
            # File pointer reset is handled in validate, but process_document needs it at 0
            file.file.seek(0)
            await self.process_document(file, claim_id, app_id)
        
        return application

    async def process_document(self, file: UploadFile, claim_id: uuid.UUID, application_id: uuid.UUID) -> Claim:
        # Save Original
        ext = file.filename.split(".")[-1]
        original_path = RAW_DIR / f"{claim_id}.{ext}"
        
        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create Claim Record
        claim = Claim(id=claim_id, application_id=application_id, original_filename=file.filename)
        self.db.add(claim)
        self.db.commit()

        # Convert/Process
        images = []
        if file.content_type == "application/pdf":
            # Read from file we just saved to avoid memory issues
            images = convert_from_bytes(open(original_path, "rb").read(), dpi=300)
        else:
            images = [Image.open(original_path)]

        # Process Pages & Tiles
        for i, img in enumerate(images):
            # Ensure RGB for JPEG saving
            if img.mode != "RGB":
                img = img.convert("RGB")

            page_id = uuid.uuid4()
            page_path = RAW_DIR / f"{claim_id}_page_{i+1}.jpg"
            img.save(page_path, "JPEG")

            claim_page = ClaimPage(
                id=page_id,
                claim_id=claim_id,
                page_number=i+1,
                image_path=str(page_path)
            )
            self.db.add(claim_page)

            # Generate Tiles
            tiles = self._generate_tiles(img, page_id, claim_id, i+1)
            self.db.add_all(tiles)
        
        self.db.commit()
        return claim

    def _generate_tiles(self, img: Image.Image, page_id: uuid.UUID, claim_id: uuid.UUID, page_num: int) -> List[ClaimTile]:
        tiles = []
        w, h = img.size
        
        # Simple Logic: Slice into Header (Top 20%), Body (Middle), Footer (Bottom 20%)
        # In a real app, this would be smarter.
        
        header_h = int(h * 0.2)
        footer_h = int(h * 0.2)
        body_h = h - header_h - footer_h

        # Header
        header_img = img.crop((0, 0, w, header_h))
        header_path = TILES_DIR / f"{claim_id}_p{page_num}_header.jpg"
        header_img.save(header_path)
        tiles.append(ClaimTile(
            page_id=page_id,
            type=TileType.HEADER,
            coordinates={"x": 0, "y": 0, "w": w, "h": header_h},
            image_path=str(header_path)
        ))

        # Body
        body_img = img.crop((0, header_h, w, header_h + body_h))
        body_path = TILES_DIR / f"{claim_id}_p{page_num}_body.jpg"
        body_img.save(body_path)
        tiles.append(ClaimTile(
            page_id=page_id,
            type=TileType.BODY,
            coordinates={"x": 0, "y": header_h, "w": w, "h": body_h},
            image_path=str(body_path)
        ))

        # Footer
        footer_img = img.crop((0, header_h + body_h, w, h))
        footer_path = TILES_DIR / f"{claim_id}_p{page_num}_footer.jpg"
        footer_img.save(footer_path)
        tiles.append(ClaimTile(
            page_id=page_id,
            type=TileType.FOOTER,
            coordinates={"x": 0, "y": header_h + body_h, "w": w, "h": footer_h},
            image_path=str(footer_path)
        ))

        return tiles
