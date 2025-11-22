"""
Brand Style Folder ORM model.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, JSON, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class ExtractionStatus:
    """Extraction status enum values."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class BrandStyleFolder(Base):
    """BrandStyleFolder model for storing user's brand style image folder metadata."""

    __tablename__ = "brand_style_folders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    image_count = Column(Integer, default=0, nullable=False)
    
    # Extraction fields
    extracted_style_json = Column(JSON, nullable=True)  # JSONB for PostgreSQL, TEXT for SQLite
    extraction_status = Column(
        Enum("pending", "completed", "failed", name="extraction_status_enum"),
        default=ExtractionStatus.PENDING,
        nullable=False
    )
    extracted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="brand_style_folder")
    images = relationship(
        "UploadedImage",
        primaryjoin="and_(UploadedImage.folder_id == BrandStyleFolder.id, UploadedImage.folder_type == 'brand_style')",
        foreign_keys="[UploadedImage.folder_id]",
        viewonly=True
    )

