"""
Pydantic schemas for video generation requests, responses, and LLM output validation.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CoherenceSettings(BaseModel):
    """Coherence technique settings for video generation."""
    seed_control: bool = Field(default=True, description="Seed control for visual consistency")
    ip_adapter_reference: bool = Field(default=False, description="IP-Adapter with reference images (same real images for all clips)")
    ip_adapter_sequential: bool = Field(default=False, description="IP-Adapter with sequential images (reference + previous clip images)")
    lora: bool = Field(default=False, description="LoRA training for character/product consistency")
    enhanced_planning: bool = Field(default=True, description="Enhanced LLM planning")
    vbench_quality_control: bool = Field(default=True, description="VBench quality control")
    post_processing_enhancement: bool = Field(default=True, description="Post-processing enhancement")
    controlnet: bool = Field(default=False, description="ControlNet for compositional consistency")
    csfd_detection: bool = Field(default=False, description="CSFD character consistency detection")

    class Config:
        json_schema_extra = {
            "example": {
                "seed_control": True,
                "ip_adapter_reference": False,
                "ip_adapter_sequential": False,
                "lora": False,
                "enhanced_planning": True,
                "vbench_quality_control": True,
                "post_processing_enhancement": True,
                "controlnet": False,
                "csfd_detection": False,
            }
        }


class GenerateRequest(BaseModel):
    """Request schema for POST /api/generate endpoint."""
    prompt: str = Field(..., min_length=10, description="User prompt for video generation")
    title: Optional[str] = Field(default=None, max_length=200, description="Optional title for the video")
    coherence_settings: Optional[CoherenceSettings] = Field(
        default=None,
        description="Optional coherence technique settings. If not provided, defaults will be applied."
    )
    model: Optional[str] = Field(None, description="Specific model to use (optional, uses default fallback chain if not specified)")
    num_clips: Optional[int] = Field(None, ge=1, le=10, description="Number of clips to generate (optional, uses scene plan if not specified)")
    use_llm: Optional[bool] = Field(True, description="Whether to use LLM enhancement (default: True)")


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
    seed_value: Optional[int] = None  # Seed value used for visual consistency across scenes


class GenerateResponse(BaseModel):
    """Response schema for POST /api/generate endpoint."""
    generation_id: str
    status: str
    message: str


class GenerationListItem(BaseModel):
    """Schema for a single generation item in list responses."""

    id: str
    title: Optional[str] = None  # User-defined title for the video
    prompt: str
    status: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: int
    cost: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    generation_group_id: Optional[str] = None  # Group ID if part of parallel generation
    variation_label: Optional[str] = None  # Variation label (A, B, C, etc.) if part of parallel generation
    coherence_settings: Optional[dict] = None  # Coherence technique settings
    parent_generation_id: Optional[str] = Field(None, description="ID of original generation if this is an edited version")

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


# Parallel Generation Schemas
class ParallelGenerateRequest(BaseModel):
    """Request schema for POST /api/generate/parallel endpoint."""
    variations: List[GenerateRequest] = Field(..., min_length=2, max_length=10, description="Array of generation requests (2-10 variations)")
    comparison_type: str = Field(..., pattern="^(settings|prompt)$", description="Comparison type: 'settings' or 'prompt'")


class ParallelGenerateResponse(BaseModel):
    """Response schema for POST /api/generate/parallel endpoint."""
    group_id: str
    generation_ids: List[str]
    status: str
    message: str


class VariationDetail(BaseModel):
    """Schema for a single variation in a comparison group."""
    generation_id: str
    prompt: str
    coherence_settings: Optional[dict] = None
    status: str
    progress: int = Field(..., ge=0, le=100)
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    cost: Optional[float] = None
    generation_time_seconds: Optional[int] = None
    error_message: Optional[str] = None


class ComparisonGroupResponse(BaseModel):
    """Response schema for GET /api/comparison/{group_id} endpoint."""
    group_id: str
    comparison_type: str
    variations: List[VariationDetail]
    total_cost: float
    differences: Optional[dict] = Field(
        default=None,
        description="Object showing which settings/prompts differ between variations"
    )


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
    text_overlay: Optional[TextOverlay] = None
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
