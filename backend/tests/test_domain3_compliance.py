import pytest
import logging
import io
from app.auditor.pii import PIIMasker
from app.auditor.service import AuditorService
from app.models.audit import AuditFlag, AuditSeverity
from app.models.claim import Claim, ClaimPage
from uuid import uuid4

def test_pii_masking():
    # Setup
    logger = logging.getLogger("test_pii")
    logger.setLevel(logging.INFO)
    capture = io.StringIO()
    handler = logging.StreamHandler(capture)
    masker = PIIMasker()
    handler.addFilter(masker)
    logger.addHandler(handler)

    # Action
    logger.info("User email is test@example.com and phone is 123-456-7890")
    
    # Assert
    log_output = capture.getvalue()
    assert "test@example.com" not in log_output
    assert "[EMAIL]" in log_output
    assert "123-456-7890" not in log_output
    assert "[PHONE]" in log_output

from app.models.claim import Claim, ClaimPage, ClaimTile, TileType
from app.models.extraction import ExtractedData
import json

# ... (Previous imports)

def test_math_guard_success():
    service = AuditorService()
    
    # Construct Claim
    claim = Claim(id=uuid4())
    page = ClaimPage(id=uuid4(), claim=claim, page_number=1, image_path="test.jpg")
    # claim.pages.append(page) 
    
    # Tile 1: Line Items
    tile1 = ClaimTile(id=uuid4(), page=page, type=TileType.BODY, coordinates={}, image_path="t1.jpg")
    # page.tiles.append(tile1)
    
    data1 = {
        "fields": {
            "line_items": {
                "value": [
                    {"description": "X-Ray", "amount": 100.00},
                    {"description": "Lab Fee", "amount": 50.00}
                ]
            }
        }
    }
    extract1 = ExtractedData(id=uuid4(), tile=tile1, raw_json=data1)
    tile1.extraction = [extract1]

    # Tile 2: Total
    tile2 = ClaimTile(id=uuid4(), page=page, type=TileType.FOOTER, coordinates={}, image_path="t2.jpg")
    # page.tiles.append(tile2)
    
    data2 = {
        "fields": {
            "total_amount": {
                "value": 150.00
            }
        }
    }
    extract2 = ExtractedData(id=uuid4(), tile=tile2, raw_json=data2)
    tile2.extraction = [extract2]

    # Validate
    flags = service.validate_claim(claim)
    assert flags == []

def test_math_guard_failure():
    service = AuditorService()
    
    # Construct Claim with Mismatch
    claim = Claim(id=uuid4())
    page = ClaimPage(id=uuid4(), claim=claim, page_number=1, image_path="test.jpg")
    # claim.pages.append(page)
    
    # Tile 1: Line Items (Sum = 150)
    tile1 = ClaimTile(id=uuid4(), page=page, type=TileType.BODY, coordinates={}, image_path="t1.jpg")
    # page.tiles.append(tile1)
    
    data1 = {
        "fields": {
            "line_items": {
                "value": [
                    {"description": "X-Ray", "amount": 100.00},
                    {"description": "Lab Fee", "amount": 50.00}
                ]
            }
        }
    }
    extract1 = ExtractedData(id=uuid4(), tile=tile1, raw_json=data1)
    tile1.extraction = [extract1]

    # Tile 2: Total (140 != 150)
    tile2 = ClaimTile(id=uuid4(), page=page, type=TileType.FOOTER, coordinates={}, image_path="t2.jpg")
    # page.tiles.append(tile2)
    
    data2 = {
        "fields": {
            "total_amount": {
                "value": 140.00
            }
        }
    }
    extract2 = ExtractedData(id=uuid4(), tile=tile2, raw_json=data2)
    tile2.extraction = [extract2]

    # Validate
    flags = service.validate_claim(claim)
    assert len(flags) > 0
    assert flags[0].code == "MATH_MISMATCH"
