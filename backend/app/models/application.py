import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.claim import Base

class ApplicationStatus(str, Enum):
    PROCESSING = "PROCESSING"     # Still ingesting/extracting
    NEEDS_REVIEW = "NEEDS_REVIEW" # >0 docs need review
    AUDITED = "AUDITED"           # All docs audited/approved
    COMPLETED = "COMPLETED"       # All docs settled

class ClaimApplication(Base):
    __tablename__ = "claim_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    status = Column(String, default=ApplicationStatus.PROCESSING)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to Claims (now acting as Documents)
    documents = relationship("Claim", back_populates="application", cascade="all, delete-orphan")
