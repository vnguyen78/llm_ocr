import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

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

class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String, nullable=False)
    status = Column(String, default=ClaimStatus.PROCESSING)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    application_id = Column(UUID(as_uuid=True), ForeignKey("claim_applications.id"), nullable=False)
    application = relationship("ClaimApplication", back_populates="documents")

    pages = relationship("ClaimPage", back_populates="claim", cascade="all, delete-orphan")

class ClaimPage(Base):
    __tablename__ = "claim_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String, nullable=False)
    
    claim = relationship("Claim", back_populates="pages")
    tiles = relationship("ClaimTile", back_populates="page", cascade="all, delete-orphan")

class ClaimTile(Base):
    __tablename__ = "claim_tiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey("claim_pages.id"), nullable=False)
    type = Column(String, default=TileType.UNKNOWN)
    coordinates = Column(JSON, nullable=False) # {x, y, w, h}
    image_path = Column(String, nullable=False)
    
    page = relationship("ClaimPage", back_populates="tiles")
    extraction = relationship("ExtractedData", back_populates="tile", uselist=False, cascade="all, delete-orphan")
