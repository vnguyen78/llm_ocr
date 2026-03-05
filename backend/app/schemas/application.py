from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.models.application import ApplicationStatus
from app.schemas.claim import ClaimResponse

class ClaimApplicationResponse(BaseModel):
    id: UUID
    name: Optional[str] = None
    status: ApplicationStatus
    created_at: datetime
    # We might want summary counts here eventually, but for now simple is fine.
    
    model_config = ConfigDict(from_attributes=True)

class ClaimApplicationDetailResponse(ClaimApplicationResponse):
    documents: List[ClaimResponse] = []
