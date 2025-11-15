"""
Pydantic schemas for video generation requests, responses, and LLM output validation.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request schema for POST /api/generate endpoint."""
    prompt: str = Field(..., min_length=10, max_length=500, description="User prompt for video generation")


class StatusResponse(BaseModel):
    """Response schema for GET /api/status/{generation_id} endpoint."""
    generation_id: str
    status: str  # pending, processing, completed, failed
    progress: int = Field(..., ge=0, le=100)  # 0-100
    current_step: Optional[str] = None
    video_url: Optional[str] = None
    cost: Optional[float] = None
    error: Optional[str] = None
    num_scenes: Optional[int] = None  # Total number of scenes planned
    available_clips: int = 0  # Number of clips currently available for download


class GenerateResponse(BaseModel):
    """Response schema for POST /api/generate endpoint."""
    generation_id: str
    status: str
    message: str


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


class DeleteResponse(BaseModel):
    """Response schema for DELETE /api/generations/{id} endpoint."""
    message: str
    generation_id: str


# LLM Response Schemas (for validating OpenAI API responses)
class BrandGuidelines(BaseModel):
    """Brand guidelines extracted from LLM response."""
    brand_name: str
    brand_colors: List[str] = Field(..., description="Hex color codes")
    visual_style_keywords: str
    mood: str


class TextOverlay(BaseModel):
    """Text overlay specification for a scene."""
    text: str
    position: str = Field(..., description="top, center, or bottom")
    font_size: int = Field(default=48, ge=24, le=96)
    color: str = Field(..., description="Hex color code")
    animation: str = Field(default="fade_in", description="fade_in, slide_up, or none")


class Scene(BaseModel):
    """Scene specification from LLM response."""
    scene_number: int = Field(..., ge=1)
    scene_type: str = Field(..., description="Framework-specific type (e.g., 'Problem', 'Solution' for PAS)")
    visual_prompt: str
    text_overlay: TextOverlay
    duration: int = Field(..., ge=3, le=7, description="Duration in seconds")


class AdSpec(BaseModel):
    """Ad specifications from LLM response."""
    target_audience: str
    call_to_action: str
    tone: str


class AdSpecification(BaseModel):
    """Complete LLM response schema for ad specification."""
    product_description: str
    brand_guidelines: BrandGuidelines
    ad_specifications: AdSpec
    framework: str = Field(..., pattern="^(PAS|BAB|AIDA)$", description="Selected framework")
    scenes: List[Scene] = Field(..., min_length=3, max_length=5)


class ScenePlan(BaseModel):
    """Scene plan with enriched scenes and metadata."""
    scenes: List[Scene]
    total_duration: int
    framework: str
