"""
Pydantic schemas for generation requests and responses.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class GenerationListItem(BaseModel):
    """Schema for a single generation item in list responses."""

    id: str
    prompt: str
    status: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: int
    cost: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerationListResponse(BaseModel):
    """Schema for paginated generation list response."""

    total: int = Field(..., description="Total number of generations matching the query")
    limit: int = Field(..., description="Number of results per page")
    offset: int = Field(..., description="Pagination offset")
    generations: List[GenerationListItem] = Field(
        ..., description="List of generation items"
    )

