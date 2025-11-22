"""
Pydantic schemas for product image-related requests and responses.
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from app.schemas.brand_style import UploadedImageResponse


class ProductImageUploadResponse(BaseModel):
    """Schema for product image upload response."""

    message: str
    count: int


class ProductImageListResponse(BaseModel):
    """Schema for product image list response."""

    images: List[UploadedImageResponse]

