from pydantic import BaseModel, ConfigDict
from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any

class ClaimStatus(str, Enum):
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    AUDITED = "AUDITED"

class TileType(str, Enum):
    HEADER = "HEADER"
    BODY = "BODY"
    FOOTER = "FOOTER"
    UNKNOWN = "UNKNOWN"

class ExtractedDataResponse(BaseModel):
    id: UUID
    tile_id: UUID
    raw_json: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)

class ReviewCorrectionResponse(BaseModel):
    id: UUID
    field_name: str
    original_value: Optional[Any] = None
    corrected_value: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClaimTileResponse(BaseModel):
    id: UUID
    page_id: UUID
    type: TileType
    coordinates: Any
    image_path: str
    extraction: Optional[ExtractedDataResponse] = None
    
    model_config = ConfigDict(from_attributes=True)

class ClaimPageResponse(BaseModel):
    id: UUID
    claim_id: UUID
    page_number: int
    image_path: str
    tiles: List[ClaimTileResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ClaimResponse(BaseModel):
    """Summary record for queue listing."""
    id: UUID
    original_filename: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ClaimDetailedResponse(ClaimResponse):
    """Detailed record for review view including pages/tiles/extraction."""
    pages: List[ClaimPageResponse] = []
    corrections: List[ReviewCorrectionResponse] = []

from app.models.audit import AuditFlag

class ClaimDetailsResponse(BaseModel):
    claim: ClaimDetailedResponse
    flags: List[Any] = []

    model_config = ConfigDict(from_attributes=True)

