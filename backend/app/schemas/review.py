from typing import List, Any, Optional
from uuid import UUID
from pydantic import BaseModel

class ReviewCorrection(BaseModel):
    tile_id: UUID
    field_name: str
    new_value: Any

class ReviewPayload(BaseModel):
    corrections: List[ReviewCorrection]
    confirm_with_issues: bool = False
    approval_note: Optional[str] = None

class BulkActionRequest(BaseModel):
    claim_ids: List[UUID]
import typing
