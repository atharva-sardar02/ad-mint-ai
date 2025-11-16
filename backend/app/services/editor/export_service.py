"""
Export service for video editing export operations.
Handles processing editing state, applying edits, and creating exported video.
"""
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Callable
from uuid import uuid4

from moviepy import VideoFileClip
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.editing_session import EditingSession
from app.db.models.generation import Generation
from app.services.pipeline.stitching import stitch_video_clips
from app.services.pipeline.audio import add_audio_layer
from app.services.pipeline.export import export_final_video

logger = logging.getLogger(__name__)

# Export progress stages
EXPORT_STAGES = [
    (10, "Export started"),
    (20, "Trim operations applied"),
    (30, "Split clips processed"),
    (40, "Merge operations applied"),
    (50, "Clips concatenated"),
    (60, "Audio layer applied"),
    (70, "Color grading applied"),
    (80, "Video encoding"),
    (90, "Thumbnail generation"),
    (100, "Export complete"),
]


def _validate_file_path(file_path: str, allowed_dirs: List[str]) -> bool:
    """
    Validate that a file path is within allowed directories to prevent path traversal.
    
    Args:
        file_path: File path to validate
        allowed_dirs: List of allowed base directories
        
    Returns:
        True if path is valid, False otherwise
    """
    try:
        abs_path = os.path.normcase(os.path.abspath(file_path))
        for allowed_dir in allowed_dirs:
            abs_allowed = os.path.normcase(os.path.abspath(str(allowed_dir)))
            if abs_path.startswith(abs_allowed):
                return True
        return False
    except Exception:
        return False


def _resolve_clip_path(file_path: str) -> str:
    """
    Resolve clip paths that may be stored as relative (e.g., /output/temp/clip.mp4).

    Args:
        file_path: Original clip path from editing_state

    Returns:
        Absolute path to the clip.
    """
    if not file_path:
        return file_path

    path_obj = Path(file_path)
    if path_obj.is_absolute():
        return str(path_obj)

    normalized = file_path.replace("\\", "/").lstrip("/\\")
    base_output = Path(getattr(settings, "OUTPUT_DIR", "output"))
    if not base_output.is_absolute():
        base_output = Path.cwd() / base_output

    # If path already starts with "output/", drop the prefix to avoid duplication
    if normalized.lower().startswith("output/"):
        normalized = normalized.split("/", 1)[1] if "/" in normalized else ""

    resolved_path = (base_output / normalized).resolve()
    return str(resolved_path)


def process_clip_with_edits(
    clip_state: Dict[str, Any],
    temp_dir: str,
    cancellation_check: Optional[Callable] = None
) -> str:
    """
    Process a single clip by applying trim operations.
    
    Note: Split clips are already separated in editing_state (split_service creates
    two separate clips). Merged clips are already merged (merge_service creates
    one merged clip). This function processes each clip independently.
    
    Args:
        clip_state: Clip state dictionary from editing_state
        temp_dir: Temporary directory for processed clips
        cancellation_check: Optional function to check for cancellation
        
    Returns:
        Path to processed clip file
        
    Raises:
        ValueError: If clip path is invalid or not found
        RuntimeError: If export is cancelled
    """
    if cancellation_check and cancellation_check():
        raise RuntimeError("Export cancelled by user")
    
    original_path = clip_state.get("original_path")
    if not original_path:
        raise ValueError(f"Clip {clip_state.get('id', 'unknown')} has no original_path")

    resolved_original_path = _resolve_clip_path(original_path)
    
    # Validate file path is within expected directories (prevent path traversal)
    # For MVP, allow paths in output directory and temp directories
    from app.core.config import settings
    output_dir_setting = Path(getattr(settings, 'OUTPUT_DIR', 'output'))
    if not output_dir_setting.is_absolute():
        output_dir_setting = Path.cwd() / output_dir_setting
    allowed_dirs = [
        output_dir_setting,
        Path(temp_dir).resolve(),
        Path(resolved_original_path).parent,
    ]
    
    if not _validate_file_path(resolved_original_path, allowed_dirs):
        raise ValueError(f"Clip path {original_path} is not in allowed directories")
    
    if not os.path.exists(resolved_original_path):
        raise ValueError(f"Clip original_path not found: {original_path}")
    
    # Load original clip
    original_clip = VideoFileClip(resolved_original_path)
    clip = original_clip
    clips_to_close = [original_clip]
    
    try:
        # Apply trim operations if present
        trim_start = clip_state.get("trim_start")
        trim_end = clip_state.get("trim_end")
        
        if trim_start is not None or trim_end is not None:
            # Calculate actual trim times relative to clip start
            clip_start = clip_state.get("start_time", 0.0)
            clip_end = clip_state.get("end_time", clip.duration)
            
            # Trim start: relative to clip start_time
            actual_start = trim_start if trim_start is not None else clip_start
            actual_end = trim_end if trim_end is not None else clip_end
            
            # Ensure trim points are within clip bounds
            actual_start = max(0, min(actual_start, clip.duration))
            actual_end = max(actual_start + 0.5, min(actual_end, clip.duration))  # Min 0.5s duration
            
            # Apply trim using subclip
            trimmed_clip = clip.subclip(actual_start, actual_end)
            clips_to_close.append(trimmed_clip)
            clip = trimmed_clip
        
        # Save processed clip to temp directory
        clip_id = clip_state.get("id", str(uuid4()))
        output_path = os.path.join(temp_dir, f"processed-{clip_id}.mp4")
        
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            preset='medium',
            logger=None  # Suppress MoviePy logs
        )
        
        return output_path
        
    finally:
        for clip_obj in clips_to_close:
            try:
                clip_obj.close()
            except Exception:
                pass


def export_edited_video(
    editing_session: EditingSession,
    output_dir: str,
    export_generation_id: str,
    cancellation_check: Optional[Callable] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Tuple[str, str]:
    """
    Export edited video by processing editing state and applying all edits.
    
    This function:
    - Loads editing session and editing_state
    - Processes clips in order: applies trim operations to each clip
    - Note: Split clips are already separated in editing_state (split_service
      creates two separate clips). Merged clips are already merged (merge_service
      creates one merged clip). No special handling needed for split/merged clips.
    - Concatenates all processed clips with transitions
    - Applies audio layer (reuse from original or regenerate)
    - Applies color grading (reuse export service from pipeline)
    - Exports final video to output directory
    - Generates thumbnail for exported video
    - Returns exported video path and generation_id
    
    Args:
        editing_session: EditingSession model instance
        output_dir: Base output directory for videos
        export_generation_id: Generation ID to use for exported video (already created for tracking)
        cancellation_check: Optional function to check for cancellation
        progress_callback: Optional function(progress: int, step: str) to report progress
        
    Returns:
        Tuple[str, str]: (exported_video_path, export_generation_id)
        
    Raises:
        ValueError: If editing_state is invalid or clips not found
        RuntimeError: If export processing fails or is cancelled
    """
    if progress_callback:
        progress_callback(10, "Export started")
    
    if cancellation_check and cancellation_check():
        raise RuntimeError("Export cancelled by user")
    
    editing_state = editing_session.editing_state
    if not editing_state:
        raise ValueError("Editing session has no editing_state")
    
    clips_state = editing_state.get("clips", [])
    if not clips_state:
        raise ValueError("Editing state has no clips")
    
    logger.info(
        f"Starting export for editing session {editing_session.id} "
        f"with {len(clips_state)} clips"
    )
    
    # Create temporary directory for processed clips
    temp_dir = tempfile.mkdtemp(prefix="export-")
    
    try:
        # Stage 1: Process clips with trim operations
        # Note: Split clips are already separated in clips_state (split_service creates two clips).
        # Merged clips are already merged (merge_service creates one merged clip).
        # We process each clip independently, applying trim operations.
        processed_clip_paths = []
        num_clips = len(clips_state)
        
        for idx, clip_state in enumerate(clips_state):
            if cancellation_check and cancellation_check():
                raise RuntimeError("Export cancelled by user")
            
            try:
                processed_path = process_clip_with_edits(
                    clip_state=clip_state,
                    temp_dir=temp_dir,
                    cancellation_check=cancellation_check
                )
                processed_clip_paths.append(processed_path)
                
                # Update progress: 20-40% for clip processing
                if progress_callback:
                    clip_progress = 20 + int((idx + 1) / num_clips * 20)  # 20-40%
                    progress_callback(clip_progress, f"Processing clip {idx + 1}/{num_clips}")
            except Exception as e:
                logger.error(f"Failed to process clip {clip_state.get('id')}: {e}")
                raise RuntimeError(f"Failed to process clip: {e}")
        
        if cancellation_check and cancellation_check():
            raise RuntimeError("Export cancelled by user")
        
        # Stage 2: Concatenate all processed clips
        if progress_callback:
            progress_callback(50, "Concatenating clips")
        
        if not processed_clip_paths:
            raise ValueError("No processed clips to concatenate")
        
        # Use stitching service to concatenate clips with transitions
        stitched_output_path = os.path.join(temp_dir, "stitched.mp4")
        stitch_video_clips(
            clip_paths=processed_clip_paths,
            output_path=stitched_output_path,
            transitions=True,
            cancellation_check=cancellation_check
        )
        
        if cancellation_check and cancellation_check():
            raise RuntimeError("Export cancelled by user")
        
        # Stage 3: Apply audio layer
        # Get original generation to reuse audio settings
        original_generation = editing_session.generation
        music_style = "professional"  # Default music style
        scene_plan = None
        if original_generation and original_generation.scene_plan:
            try:
                from app.schemas.generation import ScenePlan
                scene_plan = ScenePlan(**original_generation.scene_plan)
            except Exception as e:
                logger.warning(f"Failed to parse scene_plan for audio: {e}")
        
        if progress_callback:
            progress_callback(60, "Applying audio layer")
        
        if cancellation_check and cancellation_check():
            raise RuntimeError("Export cancelled by user")
        
        audio_output_path = os.path.join(temp_dir, "with_audio.mp4")
        add_audio_layer(
            video_path=stitched_output_path,
            music_style=music_style,
            output_path=audio_output_path,
            scene_plan=scene_plan,
            cancellation_check=cancellation_check
        )
        
        if cancellation_check and cancellation_check():
            raise RuntimeError("Export cancelled by user")
        
        # Stage 4: Apply color grading and export final video
        # Extract brand style from original generation metadata (if available)
        brand_style = "professional"  # Default
        if original_generation and original_generation.llm_specification:
            try:
                brand_guidelines = original_generation.llm_specification.get("brand_guidelines", {})
                visual_style = brand_guidelines.get("visual_style_keywords", "professional")
                brand_style = visual_style.lower() if visual_style else "professional"
                logger.info(f"Extracted brand style from generation: {brand_style}")
            except Exception as e:
                logger.warning(f"Failed to extract brand style from generation: {e}")
        
        if progress_callback:
            progress_callback(70, "Applying color grading")
        
        video_url, thumbnail_url = export_final_video(
            video_path=audio_output_path,
            brand_style=brand_style,
            output_dir=output_dir,
            generation_id=export_generation_id,
            cancellation_check=cancellation_check
        )
        
        if progress_callback:
            progress_callback(80, "Encoding video")
            progress_callback(90, "Generating thumbnail")
            progress_callback(100, "Export complete")
        
        # video_url is already a relative path like "videos/{generation_id}.mp4"
        # Construct full path for storage
        exported_video_path = os.path.join(output_dir, video_url)
        
        logger.info(
            f"Export completed for editing session {editing_session.id}: "
            f"video={exported_video_path}, generation_id={export_generation_id}"
        )
        
        return exported_video_path, export_generation_id
        
    finally:
        # Cleanup temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")

