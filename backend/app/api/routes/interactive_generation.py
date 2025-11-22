"""
Interactive pipeline API routes.

Provides REST endpoints for managing interactive pipeline sessions:
- Start new session
- Get session status
- Approve stage and proceed
- Regenerate stage with feedback
"""

import logging
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.interactive import (
    PipelineStartRequest,
    PipelineSessionResponse,
    SessionStatusResponse,
    StageApprovalRequest,
    StageApprovalResponse,
    RegenerateRequest,
    RegenerateResponse,
    InpaintRequest,
    InpaintResponse,
    ManualReferenceUploadResponse,
)
from app.services.pipeline.interactive_pipeline import get_orchestrator
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_MANUAL_REFERENCE_IMAGES = 3
MAX_MANUAL_REFERENCE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_REFERENCE_TYPES = {"image/png", "image/jpeg", "image/jpg"}


@router.post("/start", response_model=PipelineSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_interactive_pipeline(
    request: PipelineStartRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start a new interactive pipeline session.

    Creates a session and begins story generation. Frontend will connect
    via WebSocket to receive updates and provide feedback.

    **Parameters:**
    - **prompt**: User's video generation prompt (10-5000 chars)
    - **target_duration**: Target video duration in seconds (9-60, default: 15)
    - **mode**: Pipeline mode - 'interactive' (pause at each stage) or 'auto' (run through)
    - **title**: Optional video title (max 200 chars)

    **Returns:**
    - **session_id**: Unique session identifier (use for WebSocket connection)
    - **status**: Current pipeline stage
    - **current_stage**: Human-readable stage name
    - **outputs**: Stage outputs (initially empty)
    - **conversation_history**: Chat history (initially empty)

    **Example:**
    ```json
    {
        "prompt": "Create a product showcase for our eco-friendly water bottle",
        "target_duration": 15,
        "mode": "interactive",
        "title": "EcoBottle Launch Video"
    }
    ```
    """
    logger.info(f"Starting interactive pipeline for user {current_user.id}")
    logger.info(f"  Prompt: {request.prompt[:100]}...")
    logger.info(f"  Mode: {request.mode}")

    try:
        orchestrator = get_orchestrator()

        session = await orchestrator.start_pipeline(
            user_id=str(current_user.id),
            prompt=request.prompt,
            target_duration=request.target_duration,
            mode=request.mode,
            title=request.title
        )

        response = PipelineSessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            status=session.status,
            current_stage=session.current_stage,
            created_at=session.created_at,
            updated_at=session.updated_at,
            outputs=session.outputs,
            conversation_history=session.conversation_history
        )

        logger.info(f"✅ Pipeline started: session_id={session.session_id}")
        return response

    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start pipeline: {str(e)}"
        )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get current status of a pipeline session.

    Returns lightweight status information without full conversation history.
    Use this for polling session state or checking if output is ready.

    **Parameters:**
    - **session_id**: Session identifier (from start_interactive_pipeline)

    **Returns:**
    - **session_id**: Session identifier
    - **status**: Current stage (story/reference_image/storyboard/video/complete/error)
    - **current_stage**: Human-readable stage name
    - **updated_at**: Last update timestamp
    - **has_output**: Whether current stage has generated output

    **Errors:**
    - **404**: Session not found or expired
    - **403**: Session belongs to different user
    """
    logger.info(f"Getting session status: {session_id}")

    orchestrator = get_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    # Verify user owns this session
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this session"
        )

    return SessionStatusResponse(
        session_id=session.session_id,
        status=session.status,
        current_stage=session.current_stage,
        updated_at=session.updated_at,
        has_output=session.status in session.outputs and bool(session.outputs[session.status])
    )


@router.post("/{session_id}/approve", response_model=StageApprovalResponse)
async def approve_stage(
    session_id: str,
    request: StageApprovalRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Approve current stage and proceed to next stage.

    User has reviewed the output and is satisfied. Pipeline will transition
    to the next stage and begin generation.

    **Parameters:**
    - **session_id**: Session identifier
    - **stage**: Stage being approved (must match current session stage)
    - **notes**: Optional approval notes

    **Returns:**
    - **session_id**: Session identifier
    - **approved_stage**: Stage that was approved
    - **next_stage**: Next stage the pipeline will move to
    - **message**: Human-readable confirmation message

    **Stage Flow:**
    - story → reference_image
    - reference_image → storyboard
    - storyboard → video
    - video → complete

    **Errors:**
    - **404**: Session not found
    - **403**: Session belongs to different user
    - **400**: Stage mismatch (trying to approve wrong stage)
    """
    logger.info(f"Approving stage '{request.stage}' for session {session_id}")

    orchestrator = get_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this session"
        )

    try:
        result = await orchestrator.approve_stage(
            session_id=session_id,
            stage=request.stage,
            notes=request.notes,
            selected_indices=request.selected_indices,
        )

        logger.info(f"✅ Stage approved: {request.stage} → {result['next_stage']}")

        return StageApprovalResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to approve stage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve stage: {str(e)}"
        )


@router.post("/{session_id}/regenerate", response_model=RegenerateResponse)
async def regenerate_stage(
    session_id: str,
    request: RegenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate current stage with user feedback.

    User has reviewed the output and wants changes. Pipeline will regenerate
    the current stage incorporating the feedback/modifications.

    **Parameters:**
    - **session_id**: Session identifier
    - **stage**: Stage to regenerate (must match current session stage)
    - **feedback**: Optional feedback text (if not provided, uses conversation history)
    - **modifications**: Optional structured modifications (extracted from conversation)

    **Returns:**
    - **session_id**: Session identifier
    - **stage**: Stage that was regenerated
    - **message**: Status message
    - **regenerated**: Whether regeneration succeeded

    **Note:** For conversational feedback, use WebSocket instead. This endpoint
    is for explicit regeneration after providing feedback via WebSocket chat.

    **Errors:**
    - **404**: Session not found
    - **403**: Session belongs to different user
    - **400**: Stage mismatch or invalid modifications
    """
    logger.info(f"Regenerating stage '{request.stage}' for session {session_id}")
    if request.feedback:
        logger.info(f"  Feedback: {request.feedback[:100]}...")
    if request.modifications:
        logger.info(f"  Modifications: {request.modifications}")

    orchestrator = get_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this session"
        )

    try:
        result = await orchestrator.regenerate_stage(
            session_id=session_id,
            stage=request.stage,
            feedback=request.feedback,
            modifications=request.modifications
        )

        logger.info(f"✅ Stage regenerated: {request.stage}")

        return RegenerateResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to regenerate stage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate stage: {str(e)}"
        )


@router.post(
    "/{session_id}/reference-images/upload",
    response_model=ManualReferenceUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_manual_reference_images(
    session_id: str,
    images: List[UploadFile] = File(..., description="One to three reference images"),
    current_user: User = Depends(get_current_user),
):
    """
    Upload manual reference images to skip automatic generation.

    Users can provide up to three JPG/PNG files during the story review stage.
    When the story stage is approved, the pipeline will immediately move to
    storyboard generation using the uploaded assets.
    """
    if not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image must be uploaded",
        )
    if len(images) > MAX_MANUAL_REFERENCE_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can upload up to {MAX_MANUAL_REFERENCE_IMAGES} images",
        )

    orchestrator = get_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )
    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this session",
        )
    if session.status != "story":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual reference images can only be uploaded during the story stage before approval",
        )

    output_dir = Path(settings.OUTPUT_BASE_DIR) / "interactive" / session_id / "reference_images"
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_images: List[dict] = []
    for idx, image in enumerate(images, start=1):
        content_type = image.content_type.lower() if image.content_type else ""
        if content_type not in ALLOWED_REFERENCE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type for '{image.filename}'. Use PNG or JPG images.",
            )

        contents = await image.read()
        if len(contents) > MAX_MANUAL_REFERENCE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image '{image.filename}' is too large. Max size is 10MB.",
            )

        ext = ".png" if content_type == "image/png" else ".jpg"
        file_name = f"manual_ref_{idx}_{uuid4().hex[:8]}{ext}"
        file_path = output_dir / file_name
        file_path.write_bytes(contents)

        saved_images.append(
            {
                "index": idx,
                "path": str(file_path),
                "url": f"/api/v1/outputs/interactive/{session_id}/reference_images/{file_name}",
                "prompt": session.prompt,
                "quality_score": None,
                "source": "manual",
            }
        )

    await orchestrator.register_manual_reference_images(session_id, saved_images)

    message = (
        f"Uploaded {len(saved_images)} reference image{'s' if len(saved_images) > 1 else ''}. "
        "Story approval will now skip automated reference generation."
    )

    return ManualReferenceUploadResponse(
        session_id=session_id,
        images=saved_images,
        message=message,
    )


@router.get("/{session_id}", response_model=PipelineSessionResponse)
async def get_full_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get full session details including conversation history.

    Returns complete session state including all outputs and conversation
    history. Use this to restore session state after page refresh.

    **Parameters:**
    - **session_id**: Session identifier

    **Returns:**
    - Complete session state with all outputs and conversation history

    **Errors:**
    - **404**: Session not found or expired
    - **403**: Session belongs to different user
    """
    logger.info(f"Getting full session: {session_id}")

    orchestrator = get_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this session"
        )

    return PipelineSessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        status=session.status,
        current_stage=session.current_stage,
        created_at=session.created_at,
        updated_at=session.updated_at,
        outputs=session.outputs,
        conversation_history=session.conversation_history
    )


@router.post("/{session_id}/inpaint", response_model=InpaintResponse)
async def inpaint_image(
    session_id: str,
    request: InpaintRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Inpaint/edit a specific region of an image using AI.

    Allows users to select specific regions (mask) and replace them with
    AI-generated content based on text prompts. Uses SDXL-inpaint model.

    **Parameters:**
    - **session_id**: Session identifier
    - **image_id**: Index of image to edit (0-based, from current stage outputs)
    - **mask_data**: Base64-encoded mask (1=replace region, 0=preserve)
    - **prompt**: Text describing the replacement content
    - **negative_prompt**: Optional - what to avoid (default: "blurry, low quality...")

    **Returns:**
    - **session_id**: Session identifier
    - **edited_image_url**: Path/URL to the edited image
    - **original_image_url**: Path/URL to the original image
    - **version**: Edit version number
    - **edit_history**: List of all versions (original + edits)
    - **message**: Status message

    **Example:**
    ```json
    {
        "image_id": 0,
        "mask_data": "base64_encoded_mask...",
        "prompt": "red sports car in the foreground",
        "negative_prompt": "blurry, low quality"
    }
    ```

    **Errors:**
    - **404**: Session not found or image_id out of range
    - **403**: Session belongs to different user
    - **400**: Invalid mask data or current stage doesn't have images
    - **500**: Inpainting service failure
    """
    logger.info(f"Inpainting image {request.image_id} in session {session_id}")
    logger.info(f"  Prompt: {request.prompt}")

    orchestrator = get_orchestrator()
    session = await orchestrator.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}"
        )

    if session.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this session"
        )

    try:
        # Get current stage images
        current_stage_output = session.outputs.get(session.status, {})
        images = current_stage_output.get("images", [])

        if not images:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Current stage '{session.status}' has no images to edit"
            )

        if request.image_id < 0 or request.image_id >= len(images):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image index {request.image_id} out of range (0-{len(images)-1})"
            )

        # Get the image to edit
        image_data = images[request.image_id]
        original_image_path = image_data.get("url") or image_data.get("image_path")

        if not original_image_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image {request.image_id} has no valid path"
            )

        # Import inpainting service
        from app.services.pipeline.inpainting_service import inpaint_image as do_inpaint
        from app.core.config import settings

        # Determine output directory (same as session)
        from pathlib import Path
        output_dir = Path(settings.OUTPUT_BASE_DIR) / f"sessions/{session_id}/edited_images"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Perform inpainting
        logger.info(f"Starting inpainting: {original_image_path}")
        edited_image_path = await do_inpaint(
            image_path=original_image_path,
            mask_base64=request.mask_data,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            output_dir=str(output_dir),
            image_id=request.image_id
        )

        # Track edit history in session
        edit_history_key = f"edit_history_{request.image_id}"
        if edit_history_key not in session.stage_data:
            session.stage_data[edit_history_key] = [original_image_path]

        session.stage_data[edit_history_key].append(edited_image_path)
        version = len(session.stage_data[edit_history_key]) - 1  # -1 because first is original

        # Update session
        await orchestrator._save_session(session)

        logger.info(f"✅ Image inpainted successfully: {edited_image_path}")

        return InpaintResponse(
            session_id=session_id,
            edited_image_url=edited_image_path,
            original_image_url=original_image_path,
            version=version,
            edit_history=session.stage_data[edit_history_key],
            message=f"Image edited successfully (version {version})"
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Invalid input (mask, prompt, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to inpaint image: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inpainting failed: {str(e)}"
        )
