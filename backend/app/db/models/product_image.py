"""
Product Image Folder ORM model.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProductImageFolder(Base):
    """ProductImageFolder model for storing user's product image folder metadata."""

    __tablename__ = "product_image_folders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    image_count = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="product_image_folder")
    images = relationship(
        "UploadedImage",
        primaryjoin="and_(UploadedImage.folder_id == ProductImageFolder.id, UploadedImage.folder_type == 'product')",
        foreign_keys="[UploadedImage.folder_id]",
        viewonly=True
    )

