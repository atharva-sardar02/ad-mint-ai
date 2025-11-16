"""
Pydantic schemas for video editor requests and responses.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class ClipInfo(BaseModel):
    """Schema for individual clip information in editor data."""

    clip_id: str = Field(..., description="Unique identifier for the clip")
    scene_number: int = Field(..., ge=1, description="Scene number (1-based)")
    original_path: str = Field(..., description="Original file path of the clip")
    clip_url: str = Field(..., description="URL to access the clip")
    duration: float = Field(..., ge=0, description="Clip duration in seconds")
    start_time: float = Field(..., ge=0, description="Start time in the original video")
    end_time: float = Field(..., ge=0, description="End time in the original video")
    thumbnail_url: Optional[str] = Field(None, description="URL to clip thumbnail")
    text_overlay: Optional[dict] = Field(None, description="Text overlay metadata for the clip")


class EditorDataResponse(BaseModel):
    """Response schema for GET /api/editor/{generation_id} endpoint."""

    generation_id: str = Field(..., description="Generation ID")
    original_video_url: str = Field(..., description="URL to the original video")
    original_video_path: str = Field(..., description="Path to the original video file")
    clips: List[ClipInfo] = Field(..., description="Array of scene clips")
    total_duration: float = Field(..., ge=0, description="Total duration of all clips in seconds")
    aspect_ratio: str = Field(..., description="Video aspect ratio (e.g., '9:16')")
    framework: Optional[str] = Field(None, description="Ad framework used (PAS, BAB, AIDA)")
    trim_state: Optional[dict] = Field(None, description="Trim state for clips (clipId -> {trimStart, trimEnd})")


class TrimClipRequest(BaseModel):
    """Request schema for POST /api/editor/{generation_id}/trim endpoint."""

    clip_id: str = Field(..., description="ID of the clip to trim")
    trim_start: float = Field(..., ge=0, description="Trim start time (relative to clip start)")
    trim_end: float = Field(..., ge=0, description="Trim end time (relative to clip start)")


class TrimClipResponse(BaseModel):
    """Response schema for POST /api/editor/{generation_id}/trim endpoint."""

    message: str = Field(..., description="Success message")
    clip_id: str = Field(..., description="ID of the trimmed clip")
    new_duration: float = Field(..., ge=0, description="New duration after trimming")
    updated_state: dict = Field(..., description="Updated editing state")


class SplitClipRequest(BaseModel):
    """Request schema for POST /api/editor/{generation_id}/split endpoint."""

    clip_id: str = Field(..., description="ID of the clip to split")
    split_time: float = Field(..., ge=0, description="Time position to split at (relative to clip start)")


class SplitClipResponse(BaseModel):
    """Response schema for POST /api/editor/{generation_id}/split endpoint."""

    message: str = Field(..., description="Success message")
    original_clip_id: str = Field(..., description="ID of the original clip that was split")
    new_clips: List[dict] = Field(..., description="Array of two new clips created from split")
    updated_state: dict = Field(..., description="Updated editing state")


class MergeClipsRequest(BaseModel):
    """Request schema for POST /api/editor/{generation_id}/merge endpoint."""

    clip_ids: List[str] = Field(..., min_items=2, description="Array of clip IDs to merge (must be adjacent)")


class MergeClipsResponse(BaseModel):
    """Response schema for POST /api/editor/{generation_id}/merge endpoint."""

    message: str = Field(..., description="Success message")
    merged_clip_id: str = Field(..., description="ID of the merged clip")
    new_duration: float = Field(..., ge=0, description="New duration after merging")
    updated_state: dict = Field(..., description="Updated editing state")


class SaveSessionRequest(BaseModel):
    """Request schema for POST /api/editor/{generation_id}/save endpoint."""

    editing_state: Optional[dict] = Field(None, description="Current editing state to save (optional, uses session state if not provided)")


class SaveSessionResponse(BaseModel):
    """Response schema for POST /api/editor/{generation_id}/save endpoint."""

    message: str = Field(..., description="Success message")
    session_id: str = Field(..., description="Editing session ID")
    saved_at: str = Field(..., description="Timestamp when session was saved (ISO format)")


class ExportVideoRequest(BaseModel):
    """Request schema for POST /api/editor/{generation_id}/export endpoint."""

    # No required fields - export uses current editing state from session
    pass


class ExportVideoResponse(BaseModel):
    """Response schema for POST /api/editor/{generation_id}/export endpoint."""

    message: str = Field(..., description="Success message")
    export_id: str = Field(..., description="Export job ID for tracking progress")
    status: str = Field(..., description="Export status (processing, completed, failed)")
    estimated_time_seconds: Optional[int] = Field(None, description="Estimated time remaining in seconds")


class ExportStatusResponse(BaseModel):
    """Response schema for GET /api/editor/export/{export_id}/status endpoint."""

    export_id: str = Field(..., description="Export job ID")
    status: str = Field(..., description="Export status (processing, completed, failed)")
    progress: float = Field(..., ge=0, le=100, description="Export progress percentage (0-100)")
    current_step: str = Field(..., description="Current export step description")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated time remaining in seconds")