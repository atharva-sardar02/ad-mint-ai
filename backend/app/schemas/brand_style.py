"""
Pydantic schemas for brand style-related requests and responses.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict


class UploadedImageResponse(BaseModel):
    """Schema for uploaded image response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    url: str  # URL to access the image (e.g., /api/assets/users/{user_id}/brand_styles/{filename})
    uploaded_at: datetime


class BrandStyleUploadResponse(BaseModel):
    """Schema for brand style upload response."""

    message: str
    count: int


class BrandStyleListResponse(BaseModel):
    """Schema for brand style list response."""

    images: List[UploadedImageResponse]


class BrandStyleExtractResponse(BaseModel):
    """Schema for brand style extraction response."""

    message: str
    extracted_style_json: Optional[Dict[str, Any]] = None
    extraction_status: str
    extracted_at: Optional[datetime] = None

