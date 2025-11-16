"""
Trim service for video clip trimming operations.
Handles trim validation and editing session state updates.
"""
import logging
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.db.models.editing_session import EditingSession

logger = logging.getLogger(__name__)

MIN_CLIP_DURATION = 0.5  # Minimum clip duration in seconds


def validate_trim_points(
    clip_start_time: float,
    clip_end_time: float,
    trim_start: float,
    trim_end: float,
) -> tuple:
    """
    Validate trim points against clip boundaries and constraints.
    
    Args:
        clip_start_time: Original clip start time
        clip_end_time: Original clip end time
        trim_start: Trim start time (relative to clip start)
        trim_end: Trim end time (relative to clip start)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate trim start is not before clip start
    if trim_start < 0:
        return False, "Trim start cannot be before clip start"
    
    # Validate trim end is not after clip end
    clip_duration = clip_end_time - clip_start_time
    if trim_end > clip_duration:
        return False, "Trim end cannot be after clip end"
    
    # Validate trim start is before trim end
    if trim_start >= trim_end:
        return False, "Trim start must be before trim end"
    
    # Validate minimum clip duration
    trimmed_duration = trim_end - trim_start
    if trimmed_duration < MIN_CLIP_DURATION:
        return False, f"Trimmed clip duration must be at least {MIN_CLIP_DURATION} seconds"
    
    return True, None


def apply_trim_to_editing_session(
    editing_session: EditingSession,
    clip_id: str,
    trim_start: float,
    trim_end: float,
    db: Session
) -> Dict[str, Any]:
    """
    Apply trim operation to editing session state.
    
    Args:
        editing_session: EditingSession model instance
        clip_id: ID of the clip to trim
        trim_start: Trim start time (relative to clip start)
        trim_end: Trim end time (relative to clip start)
        db: Database session
        
    Returns:
        Updated clip structure with trim points
        
    Raises:
        ValueError: If clip not found or validation fails
    """
    editing_state = editing_session.editing_state or {}
    clips = editing_state.get("clips", [])
    
    # Find the clip to trim
    clip_to_trim = None
    for clip in clips:
        if clip.get("id") == clip_id:
            clip_to_trim = clip
            break
    
    if not clip_to_trim:
        raise ValueError(f"Clip {clip_id} not found in editing session")
    
    # Get original clip boundaries
    original_start = clip_to_trim.get("start_time", 0.0)
    original_end = clip_to_trim.get("end_time", 0.0)
    
    # Validate trim points
    is_valid, error_message = validate_trim_points(
        original_start,
        original_end,
        trim_start,
        trim_end
    )
    
    if not is_valid:
        raise ValueError(error_message or "Invalid trim points")
    
    # Update clip with trim points
    clip_to_trim["trim_start"] = trim_start
    clip_to_trim["trim_end"] = trim_end
    
    # Update editing state version
    editing_state["version"] = editing_state.get("version", 1) + 1
    
    # Save to database
    editing_session.editing_state = editing_state
    db.commit()
    db.refresh(editing_session)
    
    logger.info(
        f"Applied trim to clip {clip_id} in session {editing_session.id}: "
        f"trim_start={trim_start}, trim_end={trim_end}"
    )
    
    # Return updated clip structure
    return {
        "id": clip_to_trim["id"],
        "original_path": clip_to_trim.get("original_path"),
        "start_time": original_start,
        "end_time": original_end,
        "trim_start": trim_start,
        "trim_end": trim_end,
        "split_points": clip_to_trim.get("split_points", []),
        "merged_with": clip_to_trim.get("merged_with", []),
    }

