"""
Pydantic schemas for video generation requests, responses, and LLM output validation.
"""
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


class GenerateResponse(BaseModel):
    """Response schema for POST /api/generate endpoint."""
    generation_id: str
    status: str
    message: str


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

