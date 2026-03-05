import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from app.models.claim import Base

class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tile_id = Column(UUID(as_uuid=True), ForeignKey("claim_tiles.id"), nullable=False, unique=True)
    
    # Storing the raw JSON result from LLM
    raw_json = Column(JSON, nullable=True)
    
    # We can also store normalized fields if needed, but for now specific fields 
    # might be dynamic. Let's start with a flexible JSON structure + specific tracking columns
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Link back to Tile
    # Link back to Tile
    # Link back to Tile
    # Link back to Tile
    tile = relationship("ClaimTile", back_populates="extraction")

class ReviewCorrection(Base):
    __tablename__ = "review_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    tile_id = Column(UUID(as_uuid=True), ForeignKey("claim_tiles.id"), nullable=False)
    field_name = Column(String, nullable=False)
    original_value = Column(JSON, nullable=True) # JSON to handle strings or complex objects
    corrected_value = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    claim = relationship("Claim", backref=backref("corrections", cascade="all, delete-orphan"))
    tile = relationship("ClaimTile", backref=backref("corrections", cascade="all, delete-orphan"))
