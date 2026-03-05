from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class AuditSeverity(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class AuditFlag(BaseModel):
    claim_id: Optional[UUID] = None
    code: str
    description: str
    severity: AuditSeverity
