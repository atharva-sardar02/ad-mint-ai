"""
Uploaded Image ORM model.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, Integer, String, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class UploadedImage(Base):
    """UploadedImage model for storing individual uploaded image metadata."""

    __tablename__ = "uploaded_images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    folder_id = Column(String(36), nullable=False, index=True)  # FK to brand_style_folders.id or product_image_folders.id
    folder_type = Column(
        Enum("brand_style", "product", name="folder_type_enum"),
        nullable=False,
        index=True
    )  # 'brand_style' or 'product'
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Product style extraction (only for product images)
    extracted_product_style_json = Column(JSON, nullable=True)  # JSONB for PostgreSQL, TEXT for SQLite

    # Relationships - Note: folder_id can point to either BrandStyleFolder or ProductImageFolder
    # Since folder_id doesn't have a FK constraint, we use primaryjoin to handle the association
    # Using viewonly=True and removing back_populates to avoid circular dependency issues
    # Cascading deletes will be handled manually in application code
    brand_style_folder = relationship(
        "BrandStyleFolder",
        primaryjoin="and_(UploadedImage.folder_id == BrandStyleFolder.id, UploadedImage.folder_type == 'brand_style')",
        foreign_keys="[UploadedImage.folder_id]",
        viewonly=True
    )
    product_image_folder = relationship(
        "ProductImageFolder",
        primaryjoin="and_(UploadedImage.folder_id == ProductImageFolder.id, UploadedImage.folder_type == 'product')",
        foreign_keys="[UploadedImage.folder_id]",
        viewonly=True
    )

