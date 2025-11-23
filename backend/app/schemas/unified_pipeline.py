"""
Pydantic schemas for unified pipeline.

These schemas define the request/response contracts and configuration models
for the unified pipeline that consolidates 4 separate pipelines into 1 system.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class BrandAssets(BaseModel):
    """Brand assets provided by user for reference image generation."""
    product_images: List[str] = Field(default_factory=list, description="S3 URLs of product images")
    logo: Optional[str] = Field(None, description="S3 URL of logo image")
    character_images: List[str] = Field(default_factory=list, description="S3 URLs of character/model images")


class ReferenceImageAnalysis(BaseModel):
    """GPT-4 Vision analysis results for a reference image."""
    character_description: Optional[str] = Field(None, description="Character appearance details")
    product_features: Optional[str] = Field(None, description="Product visual characteristics")
    colors: List[str] = Field(default_factory=list, description="Dominant color palette as hex codes")
    style: Optional[str] = Field(None, description="Visual style (photorealistic, illustrated, 3D render, etc.)")
    environment: Optional[str] = Field(None, description="Environmental context (indoor/outdoor, lighting, setting)")


class ReferenceImage(BaseModel):
    """Reference image with Vision analysis for visual consistency."""
    url: str = Field(..., description="S3 URL of reference image")
    type: str = Field(..., description="Image type: product, character, logo, environment")
    analysis: ReferenceImageAnalysis = Field(..., description="GPT-4 Vision analysis results")


class Scene(BaseModel):
    """Scene description for video generation."""
    id: int = Field(..., description="Scene number (1-based)")
    description: str = Field(..., description="Detailed scene description")
    duration: float = Field(..., description="Scene duration in seconds")
    quality_score: Optional[float] = Field(None, description="Scene quality score from Critic agent")


class VideoClip(BaseModel):
    """Video clip generation tracking."""
    scene_id: int = Field(..., description="Corresponding scene ID")
    url: Optional[str] = Field(None, description="S3 URL when generation complete")
    duration: Optional[float] = Field(None, description="Actual duration in seconds")
    status: str = Field(..., description="Status: queued, processing, rendering, complete, failed")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage (0-100)")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class PipelineConfig(BaseModel):
    """Pipeline configuration settings loaded from YAML."""
    pipeline_name: str = Field("default", description="Pipeline configuration name")

    # Story stage settings
    story_max_iterations: int = Field(3, ge=1, le=10, description="Max story refinement iterations")
    story_timeout_seconds: int = Field(120, ge=30, description="Story generation timeout")

    # Reference stage settings
    reference_count: int = Field(3, ge=1, le=5, description="Number of reference images to generate")
    reference_quality_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum quality threshold")

    # Scene stage settings
    scene_max_iterations: int = Field(2, ge=1, le=10, description="Max scene refinement iterations")
    scene_timeout_seconds: int = Field(180, ge=30, description="Scene generation timeout")

    # Video stage settings
    video_parallel: bool = Field(True, description="Enable parallel video generation")
    video_max_concurrent: int = Field(5, ge=1, le=10, description="Max concurrent video generations")
    video_timeout_seconds: int = Field(600, ge=60, description="Video generation timeout per clip")

    # Quality scoring settings
    vbench_enabled: bool = Field(True, description="Enable VBench quality scoring")
    vbench_run_in_background: bool = Field(True, description="Run VBench in background tasks")
    vbench_threshold_good: float = Field(80.0, ge=0.0, le=100.0, description="Good quality threshold")
    vbench_threshold_acceptable: float = Field(60.0, ge=0.0, le=100.0, description="Acceptable quality threshold")


class GenerationRequest(BaseModel):
    """Request schema for unified pipeline generation endpoint."""
    prompt: str = Field(..., min_length=10, max_length=5000, description="User prompt for video generation")
    framework: Optional[str] = Field(None, description="Advertising framework: AIDA, PAS, FAB, custom")
    brand_assets: Optional[BrandAssets] = Field(None, description="Brand assets for reference images")
    config: Optional[Dict[str, Any]] = Field(None, description="Config overrides (quality_threshold, etc.)")
    interactive: bool = Field(True, description="Interactive mode (wait for user feedback) or automated")
    session_id: Optional[str] = Field(None, description="Session ID for resuming existing generation")
    parallel_variants: int = Field(1, ge=1, le=5, description="Number of parallel variants for A/B testing")


class GenerationResponse(BaseModel):
    """Response schema for unified pipeline generation endpoint."""
    generation_id: str = Field(..., description="Unique generation ID")
    session_id: str = Field(..., description="WebSocket session ID")
    websocket_url: str = Field(..., description="WebSocket URL for real-time updates")
    status: str = Field(..., description="Current status: pending, story, references, scenes, videos, completed, failed")
    message: Optional[str] = Field(None, description="Human-readable status message")


class StoryGeneratedMessage(BaseModel):
    """WebSocket message: story generation complete."""
    type: Literal["story_generated"] = "story_generated"
    payload: Dict[str, Any] = Field(..., description="Story text, quality score, awaiting_approval flag")


class ReferenceImagesReadyMessage(BaseModel):
    """WebSocket message: reference images ready."""
    type: Literal["reference_images_ready"] = "reference_images_ready"
    payload: Dict[str, Any] = Field(..., description="Array of reference images with analysis")


class ScenesGeneratedMessage(BaseModel):
    """WebSocket message: scenes generated."""
    type: Literal["scenes_generated"] = "scenes_generated"
    payload: Dict[str, Any] = Field(..., description="Array of scenes, awaiting_approval flag")


class VideoProgressMessage(BaseModel):
    """WebSocket message: video clip progress update."""
    type: Literal["video_progress"] = "video_progress"
    payload: Dict[str, Any] = Field(..., description="clip_id, progress (0-100), status")


class VideoCompleteMessage(BaseModel):
    """WebSocket message: video clip complete."""
    type: Literal["video_complete"] = "video_complete"
    payload: Dict[str, Any] = Field(..., description="clip_id, S3 URL, duration")


class VBenchScoreMessage(BaseModel):
    """WebSocket message: VBench quality score available."""
    type: Literal["vbench_score"] = "vbench_score"
    payload: Dict[str, Any] = Field(..., description="clip_id (or null for overall), overall_score, breakdown")


class GenerationCompleteMessage(BaseModel):
    """WebSocket message: generation complete."""
    type: Literal["generation_complete"] = "generation_complete"
    payload: Dict[str, Any] = Field(..., description="generation_id, final_video_url, overall_quality_score")


class UserFeedbackMessage(BaseModel):
    """WebSocket message: user feedback (client -> server)."""
    type: Literal["user_feedback"] = "user_feedback"
    payload: Dict[str, Any] = Field(..., description="message, stage, optional scene_id")
