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
    automatic_regeneration: bool = Field(default=False, description="Automatically regenerate clips that fail quality thresholds")
    post_processing_enhancement: bool = Field(default=True, description="Post-processing enhancement")
    color_grading: bool = Field(default=False, description="Apply color grading based on brand style")
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
                "automatic_regeneration": False,
                "post_processing_enhancement": True,
                "color_grading": False,
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
    target_duration: Optional[int] = Field(None, ge=9, le=60, description="Target total video duration in seconds (default: 15). LLM will decide number of scenes and duration per scene (max 7s per scene)")
    use_llm: Optional[bool] = Field(True, description="Whether to use LLM enhancement (default: True)")
    
    # Multi-stage workflow options
    use_multi_stage: Optional[bool] = Field(
        False,
        description="Use new multi-stage story-driven workflow (Stage 0: Template Selection, Stage 1: Story, Stage 2: Scenes, Stage 3: Visual Prompts). Default: False (uses legacy single-stage)"
    )
    use_fill_in_template: Optional[bool] = Field(
        False,
        description="Use fill-in-the-blank template system with ~290 structured fields for maximum control and consistency. Default: False"
    )
    template_override: Optional[str] = Field(
        None,
        description="Manually specify story template (aida, problem-agitate-solve, before-after-bridge, hero-journey, emotional-arc, teaser-reveal, social-proof, sensory-experience). If not provided, AI will select optimal template."
    )
    
    # Advanced image generation options
    use_advanced_image_generation: Optional[bool] = Field(
        False,
        description="Use advanced image generation with 2-agent prompt enhancement and 4-model quality scoring. Generates 4 variations per scene and selects best. Higher quality but 5x cost and 6x time. Default: False"
    )
    advanced_image_quality_threshold: Optional[float] = Field(
        30.0,
        ge=0.0,
        le=100.0,
        description="Minimum quality score threshold for advanced image generation (0-100). Images below this score will log warnings. Default: 30.0"
    )
    advanced_image_num_variations: Optional[int] = Field(
        4,
        ge=2,
        le=8,
        description="Number of image variations to generate per scene in advanced mode. Best variation is selected automatically. Default: 4"
    )
    advanced_image_max_enhancement_iterations: Optional[int] = Field(
        4,
        ge=1,
        le=6,
        description="Maximum number of prompt enhancement iterations in advanced mode. Default: 4"
    )
    
    refinement_instructions: Optional[dict] = Field(
        default=None,
        description="Optional refinement instructions for storyboard. Dict mapping scene_number (int) to refinement instruction (str), or 'all' to refine all scenes. Example: {1: 'make lighting more dramatic', 2: 'add more product details', 'all': 'increase visual detail'}"
    )
    brand_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional brand name to display at the end of the video. If not provided, the system will attempt to extract it from the prompt."
    )
    product_image_id: Optional[str] = Field(
        default=None,
        description="Optional product image ID from user's uploaded product folder. If provided, product style JSON will be extracted and incorporated into scene generation (Story 10.3)."
    )
    top_note: Optional[str] = Field(
        default=None,
        description="Optional top note for fragrance advertising. If provided along with heart_note and/or base_note, will generate a scent profile and incorporate cinematic atmospheric cues into KLING pipeline prompts."
    )
    heart_note: Optional[str] = Field(
        default=None,
        description="Optional heart note for fragrance advertising. If provided along with top_note and/or base_note, will generate a scent profile and incorporate cinematic atmospheric cues into KLING pipeline prompts."
    )
    base_note: Optional[str] = Field(
        default=None,
        description="Optional base note for fragrance advertising. If provided along with top_note and/or heart_note, will generate a scent profile and incorporate cinematic atmospheric cues into KLING pipeline prompts."
    )


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
    storyboard_plan: Optional[dict] = None  # Storyboard plan with scenes and images
    
    # Multi-stage workflow data
    workflow_type: Optional[str] = None  # "multi_stage_story_driven" or "legacy_single_stage"
    template_used: Optional[str] = None  # Story template ID if multi-stage
    story_title: Optional[str] = None  # Story title if multi-stage
    multi_stage_data: Optional[dict] = None  # Complete multi-stage output (stage_0, stage_1, stage_2, stage_3)
    
    # Advanced image generation metadata
    advanced_image_generation_used: Optional[bool] = None  # Whether advanced image generation was used
    image_quality_scores: Optional[dict] = None  # Quality scores for each scene's selected image


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
    model: Optional[str] = Field(None, description="Model used for generation (e.g., 'openai/sora-2')")
    num_clips: Optional[int] = Field(None, description="Number of clips requested")
    use_llm: Optional[bool] = Field(None, description="Whether LLM enhancement was used")
    generation_time_seconds: Optional[int] = Field(None, description="Time taken to generate the video in seconds")

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
    estimated_time_seconds: Optional[int] = Field(None, description="Estimated generation time in seconds")
    estimated_time_formatted: Optional[str] = Field(None, description="Human-readable estimated time (e.g., '2 minutes')")


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
    """
    Scene specification from storyboard.
    
    Each scene includes:
    - Reference image path (from storyboard)
    - Start image path (first frame for Kling 2.5 Turbo)
    - End image path (last frame for Kling 2.5 Turbo)
    - Model-specific optimized prompts (different for each video model)
    - Standard scene metadata
    - Transition to next scene
    """
    model_config = {"protected_namespaces": ()}  # Allow model_prompts field
    
    scene_number: int = Field(..., ge=1)
    scene_type: str = Field(..., description="Framework-specific type (e.g., 'Attention', 'Interest' for AIDA)")
    visual_prompt: str = Field(..., description="Base visual prompt from storyboard")
    # Model-specific prompts (optimized for each video generation model)
    model_prompts: dict[str, str] = Field(default_factory=dict, description="Model-specific optimized prompts: {'openai/sora-2': '...', 'google/veo-3': '...', etc.}")
    final_cinematic_prompt: Optional[str] = Field(None, description="Final enhanced prompt sent to KLING (enhanced with brand/product style and scent profile at video generation time)")
    reference_image_path: Optional[str] = Field(None, description="Path to reference image for this scene (from storyboard)")
    start_image_path: Optional[str] = Field(None, description="Path to start image (first frame) for Kling 2.5 Turbo")
    end_image_path: Optional[str] = Field(None, description="Path to end image (last frame) for Kling 2.5 Turbo")
    text_overlay: Optional[TextOverlay] = None
    duration: int = Field(..., ge=3, le=7, description="Duration in seconds (4 seconds for AIDA framework)")
    sound_design: Optional[str] = Field(None, description="Sound design description for ambient SFX (e.g., 'gentle room tone, faint fabric movement')")
    transition_to_next: Optional[str] = Field(
        default="crossfade",
        description="Transition effect to next scene: crossfade, cut, wipe_left, wipe_right, wipe_up, wipe_down, flash, zoom_blur, whip_pan_left, whip_pan_right, whip_pan_up, whip_pan_down, glitch"
    )


class AdSpec(BaseModel):
    """Ad specifications from LLM response."""
    target_audience: str
    call_to_action: str
    tone: str


class AdSpecification(BaseModel):
    """
    Complete LLM response schema for ad specification.
    
    Note: With the new v2.0 compact format (AIDA framework), exactly 4 scenes
    of 4 seconds each are generated. Each scene uses 3-7 word fragments for
    visual descriptions, assembled into natural Sora-2 prompts.
    """
    product_description: str
    brand_guidelines: BrandGuidelines
    ad_specifications: AdSpec
    framework: str = Field(..., pattern="^(PAS|BAB|AIDA)$", description="Selected framework (AIDA uses 4 scenes of 4s each)")
    scenes: List[Scene] = Field(..., min_length=3, max_length=5, description="3-5 scenes (AIDA: exactly 4 scenes of 4s each)")


class ScenePlan(BaseModel):
    """Scene plan with enriched scenes and metadata."""
    scenes: List[Scene]
    total_duration: int
    framework: str


# Quality Metrics Schemas
class QualityMetricDetail(BaseModel):
    """Quality metric detail for a single clip."""
    scene_number: int
    clip_path: str
    vbench_scores: dict
    overall_quality: float
    passed_threshold: bool
    regeneration_attempts: int
    created_at: datetime

    class Config:
        from_attributes = True


class QualityMetricsResponse(BaseModel):
    """Response schema for GET /api/generations/{id}/quality endpoint."""
    generation_id: str
    clips: List[QualityMetricDetail]
    summary: dict = Field(
        ...,
        description="Summary statistics: average_quality, total_clips, passed_count, failed_count"
    )
