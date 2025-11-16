"""
Video editor route handlers.
"""
import logging
import asyncio
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.generation import Generation
from app.db.models.editing_session import EditingSession
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.editor import (
    EditorDataResponse,
    TrimClipRequest,
    TrimClipResponse,
    SplitClipRequest,
    SplitClipResponse,
    MergeClipsRequest,
    MergeClipsResponse,
    SaveSessionRequest,
    SaveSessionResponse,
    ExportVideoRequest,
    ExportVideoResponse,
    ExportStatusResponse,
    ClipInfo,
)
from app.services.editor.editor_service import (
    extract_clips_from_generation,
    get_or_create_editing_session,
    get_full_url,
)
from app.services.editor.trim_service import apply_trim_to_editing_session
from app.services.editor.split_service import apply_split_to_editing_session
from app.services.editor.merge_service import apply_merge_to_editing_session
from app.services.editor.save_service import save_editing_session
from app.services.editor.export_service import export_edited_video, EXPORT_STAGES
from app.services.pipeline.progress_tracking import update_generation_progress, update_generation_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["editor"])


@router.get("/editor/{generation_id}", response_model=EditorDataResponse, status_code=status.HTTP_200_OK)
async def get_editor_data(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> EditorDataResponse:
    """
    Get editor data for a video generation.
    
    This endpoint:
    - Verifies user ownership of the generation
    - Loads generation record and extracts scene clips
    - Creates or loads editing session record
    - Returns editor data including clips, metadata, and URLs
    
    Args:
        generation_id: UUID of the generation to edit
        current_user: Authenticated user (from JWT)
        db: Database session
        
    Returns:
        EditorDataResponse with generation_id, original_video_url, clips array,
        total_duration, aspect_ratio, and framework
        
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
    """
    logger.info(f"User {current_user.id} requesting editor data for generation {generation_id}")
    
    # Load generation record
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        logger.warning(f"Generation {generation_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GENERATION_NOT_FOUND",
                    "message": "Generation not found"
                }
            }
        )
    
    # Verify user ownership
    if generation.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to access generation {generation_id} "
            f"owned by {generation.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to edit this generation"
                }
            }
        )
    
    # Extract original scene clips from generation
    original_clips = extract_clips_from_generation(generation, db)
    
    # Create or load editing session
    editing_session = get_or_create_editing_session(
        generation=generation,
        user_id=current_user.id,
        db=db
    )
    
    # Reconstruct clips from editing_state if it exists and has been modified
    clips = original_clips
    trim_state = {}
    if editing_session.editing_state:
        editing_state = editing_session.editing_state
        clips_state = editing_state.get("clips", [])
        
        # Check if editing_state has been modified (e.g., splits, trims)
        # If clips_state length differs from original_clips, or has different IDs, reconstruct
        original_clip_ids = {clip.clip_id for clip in original_clips}
        state_clip_ids = {clip_state.get("id") for clip_state in clips_state if clip_state.get("id")}
        
        if len(clips_state) != len(original_clips) or state_clip_ids != original_clip_ids:
            # Reconstruct clips from editing_state (handles splits, etc.)
            clips = []
            original_clips_map = {clip.clip_id: clip for clip in original_clips}
            
            for clip_state in clips_state:
                clip_id = clip_state.get("id")
                original_clip = original_clips_map.get(clip_id)
                
                # Calculate duration from start_time and end_time
                start_time = clip_state.get("start_time", 0.0)
                end_time = clip_state.get("end_time", 0.0)
                duration = end_time - start_time
                
                # Use original clip as base for metadata, or create minimal structure
                if original_clip:
                    clip_info = ClipInfo(
                        clip_id=clip_id,
                        scene_number=clip_state.get("scene_number", original_clip.scene_number),
                        original_path=clip_state.get("original_path", original_clip.original_path),
                        clip_url=original_clip.clip_url,  # Use original clip URL
                        duration=duration,
                        start_time=start_time,
                        end_time=end_time,
                        thumbnail_url=original_clip.thumbnail_url,
                        text_overlay=clip_state.get("text_overlay") or original_clip.text_overlay,
                    )
                else:
                    # Fallback for split clips that don't match original clips
                    clip_info = ClipInfo(
                        clip_id=clip_id,
                        scene_number=clip_state.get("scene_number", 1),
                        original_path=clip_state.get("original_path", ""),
                        clip_url="",  # Will need to be set from original clip path
                        duration=duration,
                        start_time=start_time,
                        end_time=end_time,
                        thumbnail_url=None,
                        text_overlay=clip_state.get("text_overlay"),
                    )
                    # Try to find matching original clip by original_path
                    matching_original = next(
                        (c for c in original_clips if c.original_path == clip_info.original_path),
                        None
                    )
                    if matching_original:
                        clip_info.clip_url = matching_original.clip_url
                        clip_info.thumbnail_url = matching_original.thumbnail_url
                        if not clip_info.scene_number:
                            clip_info.scene_number = matching_original.scene_number
                
                clips.append(clip_info)
                
                # Extract trim state
                trim_start = clip_state.get("trim_start")
                trim_end = clip_state.get("trim_end")
                if trim_start is not None or trim_end is not None:
                    trim_state[clip_id] = {
                        "trimStart": trim_start if trim_start is not None else 0.0,
                        "trimEnd": trim_end if trim_end is not None else duration,
                    }
        else:
            # No splits, just extract trim state
            for clip_state in clips_state:
                clip_id = clip_state.get("id")
                trim_start = clip_state.get("trim_start")
                trim_end = clip_state.get("trim_end")
                if clip_id and (trim_start is not None or trim_end is not None):
                    original_clip = next((c for c in original_clips if c.clip_id == clip_id), None)
                    if original_clip:
                        trim_state[clip_id] = {
                            "trimStart": trim_start if trim_start is not None else 0.0,
                            "trimEnd": trim_end if trim_end is not None else original_clip.duration,
                        }
    
    # Calculate total duration from clips
    total_duration = sum(clip.duration for clip in clips) if clips else 0.0
    
    # Get original video URL
    original_video_url = get_full_url(generation.video_url) or ""
    original_video_path = generation.video_path or ""
    
    logger.info(
        f"Returning editor data for generation {generation_id}: "
        f"{len(clips)} clips, total duration {total_duration}s, "
        f"{len(trim_state)} clips with trim state"
    )
    
    return EditorDataResponse(
        generation_id=generation.id,
        original_video_url=original_video_url,
        original_video_path=original_video_path,
        clips=clips,
        total_duration=total_duration,
        aspect_ratio=generation.aspect_ratio or "9:16",
        framework=generation.framework,
        trim_state=trim_state if trim_state else None,
    )


@router.post("/editor/{generation_id}/trim", response_model=TrimClipResponse, status_code=status.HTTP_200_OK)
async def trim_clip(
    generation_id: str,
    request: TrimClipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TrimClipResponse:
    """
    Trim a video clip by adjusting start and end points.
    
    This endpoint:
    - Verifies user ownership of the generation
    - Validates trim points against clip boundaries
    - Updates editing session state with trim operation
    - Returns updated clip information
    
    Args:
        generation_id: UUID of the generation to edit
        request: TrimClipRequest with clip_id, trim_start, and trim_end
        current_user: Authenticated user (from JWT)
        db: Database session
        
    Returns:
        TrimClipResponse with updated clip information
        
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
        HTTPException: 400 if trim points are invalid
    """
    logger.info(
        f"User {current_user.id} requesting trim for clip {request.clip_id} "
        f"in generation {generation_id}"
    )
    
    # Load generation record
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        logger.warning(f"Generation {generation_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GENERATION_NOT_FOUND",
                    "message": "Generation not found"
                }
            }
        )
    
    # Verify user ownership
    if generation.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to trim clip in generation {generation_id} "
            f"owned by {generation.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to edit this generation"
                }
            }
        )
    
    # Require existing editing session with saved edits
    editing_session = (
        db.query(EditingSession)
        .filter(
            EditingSession.generation_id == generation_id,
            EditingSession.user_id == current_user.id,
        )
        .first()
    )
    
    if not editing_session:
        logger.error(f"Editing session not found for generation {generation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EDITING_SESSION_NOT_FOUND",
                    "message": "Editing session not found. Please save your edits before exporting.",
                }
            },
        )
    
    try:
        # Apply trim operation
        updated_clip = apply_trim_to_editing_session(
            editing_session=editing_session,
            clip_id=request.clip_id,
            trim_start=request.trim_start,
            trim_end=request.trim_end,
            db=db
        )
        
        # Calculate new duration
        new_duration = updated_clip["trim_end"] - updated_clip["trim_start"]
        
        logger.info(
            f"Successfully trimmed clip {request.clip_id} in generation {generation_id}: "
            f"new duration {new_duration}s"
        )
        
        return TrimClipResponse(
            message="Clip trimmed successfully",
            clip_id=request.clip_id,
            new_duration=new_duration,
            updated_state=editing_session.editing_state,
        )
    except ValueError as e:
        logger.warning(f"Invalid trim request for clip {request.clip_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_TRIM_POINTS",
                    "message": str(e)
                }
            }
        )


@router.post("/editor/{generation_id}/split", response_model=SplitClipResponse, status_code=status.HTTP_200_OK)
async def split_clip(
    generation_id: str,
    request: SplitClipRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SplitClipResponse:
    """
    Split a video clip at the specified time point.
    
    This endpoint:
    - Verifies user ownership of the generation
    - Validates split point against clip boundaries
    - Updates editing session state with split operation (creates two clips from one)
    - Returns updated clip information with two new clips
    
    Args:
        generation_id: UUID of the generation to edit
        request: SplitClipRequest with clip_id and split_time
        current_user: Authenticated user (from JWT)
        db: Database session
        
    Returns:
        SplitClipResponse with original_clip_id, new_clips array, and updated_state
        
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
        HTTPException: 400 if split point is invalid
    """
    logger.info(
        f"User {current_user.id} requesting split for clip {request.clip_id} "
        f"at time {request.split_time} in generation {generation_id}"
    )
    
    # Load generation record
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        logger.warning(f"Generation {generation_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GENERATION_NOT_FOUND",
                    "message": "Generation not found"
                }
            }
        )
    
    # Verify user ownership
    if generation.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to split clip in generation {generation_id} "
            f"owned by {generation.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to edit this generation"
                }
            }
        )
    
    # Require an existing editing session (exports should only run after edits are saved)
    editing_session = (
        db.query(EditingSession)
        .filter(EditingSession.generation_id == generation_id)
        .filter(EditingSession.user_id == current_user.id)
        .first()
    )
    
    if not editing_session:
        logger.error(f"Editing session not found for generation {generation_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EDITING_SESSION_NOT_FOUND",
                    "message": "Editing session not found. Save your edits before exporting."
                }
            },
        )
    
    try:
        # Apply split operation
        split_result = apply_split_to_editing_session(
            editing_session=editing_session,
            clip_id=request.clip_id,
            split_time=request.split_time,
            db=db
        )
        
        logger.info(
            f"Successfully split clip {request.clip_id} in generation {generation_id}: "
            f"created clips {split_result['new_clips'][0]['clip_id']} and {split_result['new_clips'][1]['clip_id']}"
        )
        
        return SplitClipResponse(
            message="Clip split successfully",
            original_clip_id=split_result["original_clip_id"],
            new_clips=split_result["new_clips"],
            updated_state=split_result["updated_state"],
        )
    except ValueError as e:
        logger.warning(f"Invalid split request for clip {request.clip_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_SPLIT_POINT",
                    "message": str(e)
                }
            }
        )


@router.post("/editor/{generation_id}/merge", response_model=MergeClipsResponse, status_code=status.HTTP_200_OK)
async def merge_clips(
    generation_id: str,
    request: MergeClipsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MergeClipsResponse:
    """
    Merge multiple adjacent video clips into a single continuous clip.
    
    This endpoint:
    - Verifies user ownership of the generation
    - Validates that clips are adjacent and in sequence
    - Updates editing session state with merge operation (combines clips into one)
    - Returns updated clip information with merged clip
    
    Args:
        generation_id: UUID of the generation to edit
        request: MergeClipsRequest with clip_ids array (must be adjacent)
        current_user: Authenticated user (from JWT)
        db: Database session
        
    Returns:
        MergeClipsResponse with merged clip information
        
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
        HTTPException: 400 if clips are not adjacent or validation fails
    """
    logger.info(
        f"User {current_user.id} requesting merge for clips {request.clip_ids} "
        f"in generation {generation_id}"
    )
    
    # Load generation record
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        logger.warning(f"Generation {generation_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GENERATION_NOT_FOUND",
                    "message": "Generation not found"
                }
            }
        )
    
    # Verify user ownership
    if generation.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to merge clips in generation {generation_id} "
            f"owned by {generation.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to edit this generation"
                }
            }
        )
    
    # Require existing editing session (user must have saved edits)
    editing_session = (
        db.query(EditingSession)
        .filter(EditingSession.generation_id == generation_id)
        .filter(EditingSession.user_id == current_user.id)
        .first()
    )
    
    if not editing_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EDITING_SESSION_NOT_FOUND",
                    "message": "Editing session not found. Save your edits before exporting."
                }
            },
        )
    
    try:
        # Apply merge operation
        merge_result = apply_merge_to_editing_session(
            editing_session=editing_session,
            clip_ids=request.clip_ids,
            db=db
        )
        
        logger.info(
            f"Successfully merged clips {request.clip_ids} in generation {generation_id}: "
            f"created merged clip {merge_result['merged_clip_id']} with duration {merge_result['new_duration']:.2f}s"
        )
        
        return MergeClipsResponse(
            message="Clips merged successfully",
            merged_clip_id=merge_result["merged_clip_id"],
            new_duration=merge_result["new_duration"],
            updated_state=merge_result["updated_state"],
        )
    except ValueError as e:
        logger.warning(f"Invalid merge request for clips {request.clip_ids}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_MERGE_REQUEST",
                    "message": str(e)
                }
            }
        )


@router.post("/editor/{generation_id}/save", response_model=SaveSessionResponse, status_code=status.HTTP_200_OK)
async def save_editing_session_endpoint(
    generation_id: str,
    request: SaveSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SaveSessionResponse:
    """
    Save current editing session state.
    
    This endpoint:
    - Verifies user ownership of the generation
    - Updates editing session with current state (or uses provided state)
    - Sets session status to "saved"
    - Preserves original video path
    - Returns saved session information
    
    Args:
        generation_id: UUID of the generation to save
        request: SaveSessionRequest with optional editing_state
        current_user: Authenticated user (from JWT)
        db: Database session
        
    Returns:
        SaveSessionResponse with session_id and saved_at timestamp
        
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
        HTTPException: 400 if editing_state is invalid
    """
    logger.info(
        f"User {current_user.id} requesting save for generation {generation_id}"
    )
    
    # Load generation record
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        logger.warning(f"Generation {generation_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GENERATION_NOT_FOUND",
                    "message": "Generation not found"
                }
            }
        )
    
    # Verify user ownership
    if generation.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to save generation {generation_id} "
            f"owned by {generation.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to save this generation"
                }
            }
        )
    
    # Require an existing editing session (export only after user saves edits)
    editing_session = (
        db.query(EditingSession)
        .filter(EditingSession.generation_id == generation_id)
        .filter(EditingSession.user_id == current_user.id)
        .first()
    )
    
    if not editing_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EDITING_SESSION_NOT_FOUND",
                    "message": "Editing session not found. Save your edits before exporting."
                }
            },
        )
    
    try:
        # Save editing session
        updated_session = save_editing_session(
            editing_session=editing_session,
            editing_state=request.editing_state,
            db=db
        )
        
        # Format saved_at timestamp
        saved_at = updated_session.updated_at.isoformat() if updated_session.updated_at else datetime.utcnow().isoformat()
        
        logger.info(
            f"Successfully saved editing session {updated_session.id} for generation {generation_id}"
        )
        
        return SaveSessionResponse(
            message="Editing session saved successfully",
            session_id=updated_session.id,
            saved_at=saved_at,
        )
    except ValueError as e:
        logger.warning(f"Invalid save request for generation {generation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_EDITING_STATE",
                    "message": str(e)
                }
            }
        )


def process_export_task(
    export_id: str,
    editing_session_id: str,
    generation_id: str,
    user_id: str
):
    """
    Background task to process video export.
    
    Args:
        export_id: Export generation ID
        editing_session_id: Editing session ID
        generation_id: Original generation ID
        user_id: User ID
    """
    from app.db.session import get_db
    from app.db.models.editing_session import EditingSession
    
    # Create new database session for background task
    db_session = next(get_db())
    
    try:
        # Load editing session
        editing_session = db_session.query(EditingSession).filter(
            EditingSession.id == editing_session_id
        ).first()
        
        if not editing_session:
            logger.error(f"Editing session {editing_session_id} not found for export")
            update_generation_status(
                db=db_session,
                generation_id=export_id,
                status="failed",
                error_message="Editing session not found"
            )
            return
        
        # Progress callback to update generation progress
        def progress_callback(progress: int, step: str):
            update_generation_progress(
                db=db_session,
                generation_id=export_id,
                progress=progress,
                current_step=step,
                status="processing"
            )
        
        # Cancellation check
        def check_cancellation() -> bool:
            export_gen = db_session.query(Generation).filter(Generation.id == export_id).first()
            return export_gen.cancellation_requested if export_gen else False
        
        # Process export
        output_dir = "output"  # Base output directory
        exported_video_path, export_gen_id = export_edited_video(
            editing_session=editing_session,
            output_dir=output_dir,
            export_generation_id=export_id,
            cancellation_check=check_cancellation,
            progress_callback=progress_callback
        )
        
        # Update editing session with exported video path
        editing_session.exported_video_path = exported_video_path
        editing_session.status = "exported"
        db_session.commit()
        
        # Update export generation with video paths
        # exported_video_path is full path, but we need relative path for video_url
        # Extract relative path from exported_video_path (e.g., "output/videos/{id}.mp4" -> "videos/{id}.mp4")
        relative_video_path = exported_video_path.replace("output/", "").replace("\\", "/")
        if relative_video_path.startswith("/"):
            relative_video_path = relative_video_path[1:]
        
        export_generation = db_session.query(Generation).filter(Generation.id == export_id).first()
        if export_generation:
            export_generation.video_path = exported_video_path
            export_generation.video_url = get_full_url(relative_video_path)
            # Note: thumbnail_url will be set by export service (it returns thumbnail_url as relative path)
            export_generation.status = "completed"
            export_generation.progress = 100
            export_generation.current_step = "Export complete"
            db_session.commit()
        
        logger.info(f"Export completed successfully: export_id={export_id}, video_path={exported_video_path}")
        
    except Exception as e:
        logger.error(f"Export failed for export_id={export_id}: {e}", exc_info=True)
        update_generation_status(
            db=db_session,
            generation_id=export_id,
            status="failed",
            error_message=str(e)
        )
        # Update editing session status back to saved
        try:
            editing_session = db_session.query(EditingSession).filter(
                EditingSession.id == editing_session_id
            ).first()
            if editing_session:
                editing_session.status = "saved"
                db_session.commit()
        except Exception:
            pass
    finally:
        db_session.close()


@router.post("/editor/{generation_id}/export", response_model=ExportVideoResponse, status_code=status.HTTP_202_ACCEPTED)
async def export_video_endpoint(
    generation_id: str,
    request: ExportVideoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ExportVideoResponse:
    """
    Export edited video with all edits applied.
    
    This endpoint:
    - Verifies user ownership of the generation
    - Creates export job (new Generation record for tracking)
    - Starts asynchronous export processing
    - Returns export_id and status endpoint for polling
    
    Args:
        generation_id: UUID of the generation to export
        request: ExportVideoRequest (no required fields)
        background_tasks: FastAPI BackgroundTasks for async processing
        current_user: Authenticated user (from JWT)
        db: Database session
        
    Returns:
        ExportVideoResponse with export_id and status
        
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
        HTTPException: 400 if editing session is invalid
    """
    logger.info(
        f"User {current_user.id} requesting export for generation {generation_id}"
    )
    
    # Load generation record
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        logger.warning(f"Generation {generation_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GENERATION_NOT_FOUND",
                    "message": "Generation not found"
                }
            }
        )
    
    # Verify user ownership
    if generation.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to export generation {generation_id} "
            f"owned by {generation.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to export this generation"
                }
            }
        )
    
    # Require existing editing session (export only after user has edits saved)
    editing_session = (
        db.query(EditingSession)
        .filter(EditingSession.generation_id == generation_id)
        .filter(EditingSession.user_id == current_user.id)
        .first()
    )
    
    if not editing_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EDITING_SESSION_NOT_FOUND",
                    "message": "Editing session not found. Save your edits before exporting."
                }
            },
        )
    
    # Check if editing session has been modified (has edits)
    if not editing_session.editing_state or not editing_session.editing_state.get("clips"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NO_EDITS_TO_EXPORT",
                    "message": "No edits found to export. Please make edits before exporting."
                }
            }
        )
    
    # Create new Generation record for exported video (export_id = new generation_id)
    # This will track export progress
    export_generation = Generation(
        id=str(uuid4()),
        user_id=current_user.id,
        prompt=f"Edited version of: {generation.prompt}",
        duration=generation.duration,
        aspect_ratio=generation.aspect_ratio,
        status="processing",
        progress=0,
        current_step="Export started",
        framework=generation.framework,
        parent_generation_id=generation_id,  # Link to original generation
    )
    
    db.add(export_generation)
    db.commit()
    db.refresh(export_generation)
    
    export_id = export_generation.id
    
    # Start export processing in background
    background_tasks.add_task(
        process_export_task,
        export_id=export_id,
        editing_session_id=editing_session.id,
        generation_id=generation_id,
        user_id=current_user.id
    )
    
    # Estimate time (rough estimate: 2 minutes for 15s video)
    estimated_time_seconds = 120
    
    logger.info(
        f"Export started for generation {generation_id}: export_id={export_id}"
    )
    
    return ExportVideoResponse(
        message="Video export started",
        export_id=export_id,
        status="processing",
        estimated_time_seconds=estimated_time_seconds,
    )


@router.get("/editor/export/{export_id}/status", response_model=ExportStatusResponse, status_code=status.HTTP_200_OK)
async def get_export_status(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ExportStatusResponse:
    """
    Get export status and progress.
    
    Args:
        export_id: Export job ID (Generation ID for exported video)
        current_user: Authenticated user (from JWT)
        db: Database session
        
    Returns:
        ExportStatusResponse with progress, status, and current step
        
    Raises:
        HTTPException: 404 if export not found
        HTTPException: 403 if user doesn't own the export
    """
    # Load export generation record
    export_generation = db.query(Generation).filter(Generation.id == export_id).first()
    
    if not export_generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "EXPORT_NOT_FOUND",
                    "message": "Export not found"
                }
            }
        )
    
    # Verify user ownership
    if export_generation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to view this export"
                }
            }
        )
    
    # Calculate estimated time remaining based on progress
    estimated_time_remaining = None
    if export_generation.status == "processing" and export_generation.progress < 100:
        # Rough estimate: 120 seconds total, remaining based on progress
        total_estimated = 120
        remaining = int(total_estimated * (1 - export_generation.progress / 100))
        estimated_time_remaining = max(0, remaining)
    
    return ExportStatusResponse(
        export_id=export_id,
        status=export_generation.status,
        progress=float(export_generation.progress or 0),
        current_step=export_generation.current_step or "Processing",
        estimated_time_remaining=estimated_time_remaining,
    )

