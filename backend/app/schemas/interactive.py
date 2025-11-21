"""
Pydantic schemas for interactive pipeline - WebSocket-based iterative refinement.

This module defines the request/response schemas for the interactive pipeline
that allows users to review and refine AI-generated content (story, images,
storyboard) through conversational feedback before committing API credits.
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Pipeline Session Schemas
# ============================================================================

class PipelineStartRequest(BaseModel):
    """Request to start an interactive pipeline session."""

    prompt: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="User prompt for video generation"
    )
    target_duration: Optional[int] = Field(
        15,
        ge=9,
        le=60,
        description="Target video duration in seconds (default: 15)"
    )
    mode: Literal["interactive", "auto"] = Field(
        "interactive",
        description="Pipeline mode: 'interactive' pauses at each stage, 'auto' runs without pauses"
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional title for the video"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a product showcase video for our new eco-friendly water bottle",
                "target_duration": 15,
                "mode": "interactive",
                "title": "EcoBottle Launch Video"
            }
        }


class PipelineSessionResponse(BaseModel):
    """Response containing session details."""

    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User who owns this session")
    status: Literal["story", "reference_image", "storyboard", "video", "complete", "error"] = Field(
        ...,
        description="Current pipeline stage"
    )
    current_stage: str = Field(..., description="Human-readable current stage name")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stage outputs (story text, image URLs, storyboard data, etc.)"
    )
    conversation_history: List["ChatMessage"] = Field(
        default_factory=list,
        description="Chat conversation history for current stage"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123xyz",
                "user_id": "user_456",
                "status": "story",
                "current_stage": "Story Review",
                "created_at": "2025-11-19T10:30:00Z",
                "updated_at": "2025-11-19T10:30:15Z",
                "outputs": {
                    "story": {
                        "narrative": "A journey of sustainable living...",
                        "script": "Scene 1: Opening shot..."
                    }
                },
                "conversation_history": []
            }
        }


class SessionStatusResponse(BaseModel):
    """Lightweight session status response (no full conversation history)."""

    session_id: str
    status: Literal["story", "reference_image", "storyboard", "video", "complete", "error"]
    current_stage: str
    updated_at: datetime
    has_output: bool = Field(
        ...,
        description="Whether the current stage has generated output"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123xyz",
                "status": "story",
                "current_stage": "Story Review",
                "updated_at": "2025-11-19T10:30:15Z",
                "has_output": True
            }
        }


# ============================================================================
# Chat & Conversation Schemas
# ============================================================================

class ChatMessage(BaseModel):
    """Individual chat message in conversation history."""

    type: Literal["user", "assistant", "system", "stage_update"] = Field(
        ...,
        description="Message type"
    )
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata (intent, modifications, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "user",
                "content": "Make the story more humorous and focus on product benefits",
                "timestamp": "2025-11-19T10:32:00Z",
                "metadata": None
            }
        }


class ChatMessageRequest(BaseModel):
    """Request to send a chat message via REST API (alternative to WebSocket)."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User message content"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Can you make it more upbeat and emphasize sustainability?"
            }
        }


# ============================================================================
# Stage Action Schemas
# ============================================================================

class StageApprovalRequest(BaseModel):
    """Request to approve the current stage and proceed to next."""

    stage: Literal["story", "reference_image", "storyboard"] = Field(
        ...,
        description="Stage being approved"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional approval notes"
    )
    selected_indices: Optional[List[int]] = Field(
        None,
        description="Optional selected outputs (e.g., reference images) to carry forward"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stage": "story",
                "notes": "Story looks great, ready for images"
            }
        }


class StageApprovalResponse(BaseModel):
    """Response after stage approval."""

    session_id: str
    approved_stage: str
    next_stage: str
    message: str = Field(..., description="Human-readable confirmation message")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123xyz",
                "approved_stage": "story",
                "next_stage": "reference_image",
                "message": "Story approved! Generating reference images..."
            }
        }


class RegenerateRequest(BaseModel):
    """Request to regenerate content for current stage with feedback."""

    stage: Literal["story", "reference_image", "storyboard"] = Field(
        ...,
        description="Stage to regenerate"
    )
    feedback: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional feedback to incorporate (if not provided, uses conversation history)"
    )
    modifications: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured modifications extracted from conversation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stage": "story",
                "feedback": "Make it more humorous, focus on product benefits, shorter opening",
                "modifications": {
                    "tone": "humorous",
                    "focus": ["product benefits", "sustainability"],
                    "structure": "shorter_opening"
                }
            }
        }


class RegenerateResponse(BaseModel):
    """Response after regenerating stage content."""

    session_id: str
    stage: str
    message: str = Field(..., description="Status message")
    regenerated: bool = Field(..., description="Whether regeneration was successful")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123xyz",
                "stage": "story",
                "message": "Story regenerated with your feedback",
                "regenerated": True
            }
        }


# ============================================================================
# WebSocket Message Schemas
# ============================================================================

class WSMessageBase(BaseModel):
    """Base WebSocket message schema."""

    type: str = Field(..., description="Message type identifier")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )


class WSFeedbackMessage(WSMessageBase):
    """User feedback message sent via WebSocket."""

    type: Literal["feedback"] = "feedback"
    stage: Literal["story", "reference_image", "storyboard"] = Field(
        ...,
        description="Stage this feedback applies to"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User feedback message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "feedback",
                "stage": "story",
                "message": "Can you make the opening more dramatic?",
                "timestamp": "2025-11-19T10:32:00Z"
            }
        }


class WSResponseMessage(WSMessageBase):
    """LLM response message sent via WebSocket."""

    type: Literal["llm_response"] = "llm_response"
    message: str = Field(..., description="LLM's conversational response")
    intent: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted intent/modifications from user feedback"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "llm_response",
                "message": "I'll make the opening more dramatic by starting with a bold statement about sustainability. I'll also add tension through contrasting scenes.",
                "intent": {
                    "modifications": ["dramatic_opening", "add_tension"],
                    "confidence": 0.95
                },
                "timestamp": "2025-11-19T10:32:05Z"
            }
        }


class WSStageCompleteMessage(WSMessageBase):
    """Stage completion notification sent via WebSocket."""

    type: Literal["stage_complete"] = "stage_complete"
    stage: str = Field(..., description="Completed stage name")
    data: Dict[str, Any] = Field(..., description="Stage output data")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "stage_complete",
                "stage": "story",
                "data": {
                    "narrative": "Story text here...",
                    "script": "Scene 1: ..."
                },
                "timestamp": "2025-11-19T10:30:15Z"
            }
        }


class WSErrorMessage(WSMessageBase):
    """Error message sent via WebSocket."""

    type: Literal["error"] = "error"
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    recoverable: bool = Field(
        True,
        description="Whether the error is recoverable"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "error",
                "error_code": "GENERATION_FAILED",
                "message": "Failed to generate story. Please try again.",
                "recoverable": True,
                "timestamp": "2025-11-19T10:30:20Z"
            }
        }


class WSHeartbeatMessage(WSMessageBase):
    """Heartbeat/ping message for connection health monitoring."""

    type: Literal["heartbeat"] = "heartbeat"

    class Config:
        json_schema_extra = {
            "example": {
                "type": "heartbeat",
                "timestamp": "2025-11-19T10:33:00Z"
            }
        }


# ============================================================================
# Session State Internal Schema (for Redis/DB storage)
# ============================================================================

class PipelineSessionState(BaseModel):
    """
    Internal session state schema for persistence (Redis/PostgreSQL).
    Not exposed via API - used internally by InteractivePipelineOrchestrator.
    """

    session_id: str
    user_id: str
    status: Literal["story", "reference_image", "storyboard", "video", "complete", "error"]
    current_stage: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime = Field(
        ...,
        description="Session expiration timestamp (TTL)"
    )

    # Pipeline configuration
    prompt: str
    target_duration: int
    mode: Literal["interactive", "auto"]
    title: Optional[str] = None

    # Stage outputs
    outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stage outputs keyed by stage name"
    )

    # Conversation tracking
    conversation_history: List[ChatMessage] = Field(
        default_factory=list,
        description="Full conversation history"
    )

    # Stage-specific data
    stage_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Internal stage-specific data (parameters, iterations, etc.)"
    )

    # Error tracking
    error: Optional[str] = None
    error_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123xyz",
                "user_id": "user_456",
                "status": "story",
                "current_stage": "Story Review",
                "created_at": "2025-11-19T10:30:00Z",
                "updated_at": "2025-11-19T10:32:15Z",
                "expires_at": "2025-11-19T11:30:00Z",
                "prompt": "Create product showcase video",
                "target_duration": 15,
                "mode": "interactive",
                "title": "EcoBottle Launch",
                "outputs": {
                    "story": {"narrative": "...", "script": "..."}
                },
                "conversation_history": [],
                "stage_data": {},
                "error": None,
                "error_count": 0
            }
        }


# ============================================================================
# Image Editing Schemas (Story 4: Advanced Image Editing)
# ============================================================================

class InpaintRequest(BaseModel):
    """Request to inpaint/edit a specific region of an image."""

    image_id: int = Field(..., description="Index of image in current stage (0-based)")
    mask_data: str = Field(
        ...,
        description="Base64-encoded mask data (1=replace, 0=preserve)"
    )
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Text prompt describing the replacement content"
    )
    negative_prompt: Optional[str] = Field(
        "blurry, low quality, distorted, deformed",
        max_length=500,
        description="Optional negative prompt for what to avoid"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "image_id": 0,
                "mask_data": "base64_encoded_mask_data_here...",
                "prompt": "red sports car in the foreground",
                "negative_prompt": "blurry, low quality, distorted"
            }
        }


class InpaintResponse(BaseModel):
    """Response after inpainting an image."""

    session_id: str = Field(..., description="Session identifier")
    edited_image_url: str = Field(..., description="URL/path to the edited image")
    original_image_url: str = Field(..., description="URL/path to the original image")
    version: int = Field(..., description="Edit version number (1=first edit, 2=second, etc.)")
    edit_history: List[str] = Field(
        ...,
        description="List of all image versions (original, edit1, edit2, ...)"
    )
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123xyz",
                "edited_image_url": "/outputs/sess_abc123xyz/image_edited_1.png",
                "original_image_url": "/outputs/sess_abc123xyz/image_original.png",
                "version": 1,
                "edit_history": [
                    "/outputs/sess_abc123xyz/image_original.png",
                    "/outputs/sess_abc123xyz/image_edited_1.png"
                ],
                "message": "Image edited successfully"
            }
        }


# Allow forward references for ChatMessage in PipelineSessionResponse
PipelineSessionResponse.model_rebuild()
