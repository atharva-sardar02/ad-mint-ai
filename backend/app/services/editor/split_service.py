"""
Split service for video clip splitting operations.
Handles split validation and editing session state updates.
Note: Actual video splitting with MoviePy happens during export, not here.
"""
import logging
import uuid
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models.editing_session import EditingSession

logger = logging.getLogger(__name__)

MIN_CLIP_DURATION = 0.5  # Minimum clip duration in seconds


def validate_split_point(
    clip_start_time: float,
    clip_end_time: float,
    split_time: float,
) -> tuple:
    """
    Validate split point against clip boundaries and constraints.
    
    Args:
        clip_start_time: Original clip start time
        clip_end_time: Original clip end time
        split_time: Split time (relative to clip start)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    clip_duration = clip_end_time - clip_start_time
    
    # Validate split time is not at clip start
    if split_time <= 0:
        return False, "Split point cannot be at clip start"
    
    # Validate split time is not at clip end
    if split_time >= clip_duration:
        return False, "Split point cannot be at clip end"
    
    # Validate minimum clip duration for first resulting clip
    if split_time < MIN_CLIP_DURATION:
        return False, f"First clip duration must be at least {MIN_CLIP_DURATION} seconds"
    
    # Validate minimum clip duration for second resulting clip
    if (clip_duration - split_time) < MIN_CLIP_DURATION:
        return False, f"Second clip duration must be at least {MIN_CLIP_DURATION} seconds"
    
    return True, None


def apply_split_to_editing_session(
    editing_session: EditingSession,
    clip_id: str,
    split_time: float,
    db: Session
) -> Dict[str, Any]:
    """
    Apply split operation to editing session state.
    
    This function:
    - Validates the split point
    - Creates two new clips from the original clip
    - Replaces the original clip with the two new clips in editing_state
    - Preserves metadata for both clips
    
    Args:
        editing_session: EditingSession model instance
        clip_id: ID of the clip to split
        split_time: Split time (relative to clip start)
        db: Database session
        
    Returns:
        Dictionary with original_clip_id, new_clips array, and updated_state
        
    Raises:
        ValueError: If clip not found or validation fails
    """
    editing_state = editing_session.editing_state or {}
    clips = editing_state.get("clips", [])
    
    # Find the clip to split
    clip_to_split = None
    clip_index = -1
    for i, clip in enumerate(clips):
        if clip.get("id") == clip_id:
            clip_to_split = clip
            clip_index = i
            break
    
    if not clip_to_split:
        raise ValueError(f"Clip {clip_id} not found in editing session")
    
    # Get original clip boundaries
    original_start = clip_to_split.get("start_time", 0.0)
    original_end = clip_to_split.get("end_time", 0.0)
    clip_duration = original_end - original_start
    
    # Validate split point
    is_valid, error_message = validate_split_point(
        original_start,
        original_end,
        split_time
    )
    
    if not is_valid:
        raise ValueError(error_message or "Invalid split point")
    
    # Calculate boundaries for both clips
    first_clip_start = original_start
    first_clip_end = original_start + split_time
    second_clip_start = original_start + split_time
    second_clip_end = original_end
    
    # Preserve metadata from original clip
    original_metadata = {
        "original_path": clip_to_split.get("original_path"),
        "text_overlay": clip_to_split.get("text_overlay"),
        "scene_number": clip_to_split.get("scene_number"),
        "trim_start": clip_to_split.get("trim_start"),
        "trim_end": clip_to_split.get("trim_end"),
    }
    
    # Handle trimmed clips - validate split time is within effective (trimmed) boundaries
    # split_time is relative to clip start, same as trim_start and trim_end
    trim_start = original_metadata.get("trim_start")
    trim_end = original_metadata.get("trim_end")
    
    # If clip has been trimmed, validate split is within trimmed boundaries
    if trim_start is not None and split_time < trim_start:
        raise ValueError(f"Split point {split_time}s is before trimmed start {trim_start}s")
    if trim_end is not None and split_time > trim_end:
        raise ValueError(f"Split point {split_time}s is after trimmed end {trim_end}s")
    
    # Create first clip (from start to split point)
    # Generate unique clip IDs
    first_clip_id = f"{clip_id}-{str(uuid.uuid4())[:8]}"
    second_clip_id = f"{clip_id}-{str(uuid.uuid4())[:8]}"
    
    # Preserve track_index from original clip
    original_track_index = clip_to_split.get("track_index", 0)
    
    first_clip = {
        "id": first_clip_id,
        "original_path": original_metadata["original_path"],
        "start_time": first_clip_start,
        "end_time": first_clip_end,
        "trim_start": original_metadata.get("trim_start") if original_metadata.get("trim_start") is not None else None,
        "trim_end": None,  # Split point becomes the new end for first clip
        "split_points": clip_to_split.get("split_points", []),
        "merged_with": clip_to_split.get("merged_with", []),
        "text_overlay": original_metadata.get("text_overlay"),
        "scene_number": original_metadata.get("scene_number"),
        "track_index": original_track_index,
    }
    
    # Create second clip (from split point to end)
    second_clip = {
        "id": second_clip_id,
        "original_path": original_metadata["original_path"],
        "start_time": second_clip_start,
        "end_time": second_clip_end,
        "trim_start": None,  # Split point becomes the new start for second clip
        "trim_end": original_metadata.get("trim_end") if original_metadata.get("trim_end") is not None else None,
        "split_points": clip_to_split.get("split_points", []),
        "merged_with": clip_to_split.get("merged_with", []),
        "text_overlay": original_metadata.get("text_overlay"),
        "scene_number": original_metadata.get("scene_number"),
        "track_index": original_track_index,
    }
    
    # Replace original clip with two new clips in clips array
    new_clips = clips[:clip_index] + [first_clip, second_clip] + clips[clip_index + 1:]
    
    # Update editing state
    editing_state["clips"] = new_clips
    editing_state["version"] = editing_state.get("version", 1) + 1
    
    # Save to database
    editing_session.editing_state = editing_state
    flag_modified(editing_session, "editing_state")  # Tell SQLAlchemy JSON field changed
    db.commit()
    db.refresh(editing_session)
    
    logger.info(
        f"Applied split to clip {clip_id} in session {editing_session.id}: "
        f"split_time={split_time}, created clips {first_clip_id} and {second_clip_id}"
    )
    
    # Return split result
    return {
        "original_clip_id": clip_id,
        "new_clips": [
            {
                "clip_id": first_clip_id,
                "duration": first_clip_end - first_clip_start,
            },
            {
                "clip_id": second_clip_id,
                "duration": second_clip_end - second_clip_start,
            },
        ],
        "updated_state": editing_state,
    }

