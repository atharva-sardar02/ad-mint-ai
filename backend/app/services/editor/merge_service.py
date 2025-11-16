"""
Merge service for video clip merging operations.
Handles adjacency validation and editing session state updates.
Note: Actual video merging with MoviePy happens during export, not here.
"""
import logging
import uuid
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models.editing_session import EditingSession

logger = logging.getLogger(__name__)

MIN_CLIP_DURATION = 0.5  # Minimum clip duration in seconds


def validate_clip_adjacency(
    clips: List[Dict[str, Any]],
    clip_ids: List[str]
) -> tuple:
    """
    Validate that selected clips are adjacent and in sequence.
    
    Args:
        clips: List of all clips in editing state
        clip_ids: List of clip IDs to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(clip_ids) < 2:
        return False, "At least 2 clips are required for merging"
    
    # Find clips to merge
    clips_to_merge = []
    for clip in clips:
        if clip.get("id") in clip_ids:
            clips_to_merge.append(clip)
    
    if len(clips_to_merge) != len(clip_ids):
        missing_ids = set(clip_ids) - {c.get("id") for c in clips_to_merge}
        return False, f"Some clips not found: {missing_ids}"
    
    # Sort clips by start_time to check sequence
    sorted_clips = sorted(clips_to_merge, key=lambda c: c.get("start_time", 0))
    
    # Check if clips are in sequence (no gaps)
    for i in range(len(sorted_clips) - 1):
        current_clip = sorted_clips[i]
        next_clip = sorted_clips[i + 1]
        
        current_end = current_clip.get("end_time", 0)
        next_start = next_clip.get("start_time", 0)
        
        # Check if clips are adjacent (allow small floating point tolerance)
        gap = abs(current_end - next_start)
        if gap > 0.01:
            return False, f"Clips are not adjacent: gap of {gap:.3f}s between clips"
    
    # Verify clips are in correct order in timeline
    # Find positions in clips array
    clip_indices: List[int] = []
    sorted_all_clips = sorted(clips, key=lambda c: c.get("start_time", 0))
    
    for selected_clip in sorted_clips:
        clip_id = selected_clip.get("id")
        for idx, clip in enumerate(sorted_all_clips):
            if clip.get("id") == clip_id:
                clip_indices.append(idx)
                break
    
    # Check if indices are consecutive
    clip_indices.sort()
    for i in range(len(clip_indices) - 1):
        if clip_indices[i + 1] - clip_indices[i] != 1:
            return False, "Clips are not in consecutive order in timeline"
    
    return True, None


def apply_merge_to_editing_session(
    editing_session: EditingSession,
    clip_ids: List[str],
    db: Session
) -> Dict[str, Any]:
    """
    Apply merge operation to editing session state.
    
    This function:
    - Validates clip adjacency
    - Creates merged clip from selected clips
    - Replaces selected clips with merged clip in editing_state
    - Preserves metadata from all merged clips
    
    Args:
        editing_session: EditingSession model instance
        clip_ids: List of clip IDs to merge (must be adjacent)
        db: Database session
        
    Returns:
        Dictionary with merged_clip_id, new_duration, and updated_state
        
    Raises:
        ValueError: If clips not found, not adjacent, or validation fails
    """
    editing_state = editing_session.editing_state or {}
    clips = editing_state.get("clips", [])
    
    # Validate adjacency
    is_valid, error_message = validate_clip_adjacency(clips, clip_ids)
    if not is_valid:
        raise ValueError(error_message or "Clips are not adjacent")
    
    # Find clips to merge
    clips_to_merge = []
    clip_indices = []
    for i, clip in enumerate(clips):
        if clip.get("id") in clip_ids:
            clips_to_merge.append(clip)
            clip_indices.append(i)
    
    if len(clips_to_merge) != len(clip_ids):
        missing_ids = set(clip_ids) - {c.get("id") for c in clips_to_merge}
        raise ValueError(f"Some clips not found: {missing_ids}")
    
    # Sort clips by start_time
    sorted_clips = sorted(clips_to_merge, key=lambda c: c.get("start_time", 0))
    
    # Calculate merged clip boundaries
    merged_start_time = sorted_clips[0].get("start_time", 0)
    merged_end_time = sorted_clips[-1].get("end_time", 0)
    merged_duration = merged_end_time - merged_start_time
    
    # Validate minimum duration
    if merged_duration < MIN_CLIP_DURATION:
        raise ValueError(
            f"Merged clip duration {merged_duration:.2f}s is below minimum {MIN_CLIP_DURATION}s"
        )
    
    # Preserve metadata from all merged clips
    # Combine text overlays (if any)
    text_overlays = []
    scene_numbers = []
    original_paths = []
    
    for clip in sorted_clips:
        if clip.get("text_overlay"):
            text_overlays.append(clip.get("text_overlay"))
        if clip.get("scene_number"):
            scene_numbers.append(clip.get("scene_number"))
        if clip.get("original_path"):
            original_paths.append(clip.get("original_path"))
    
    # Use first clip's original_path (all should be same or similar)
    merged_original_path = original_paths[0] if original_paths else sorted_clips[0].get("original_path", "")
    
    # Use first scene number (or combine if needed)
    merged_scene_number = scene_numbers[0] if scene_numbers else sorted_clips[0].get("scene_number", 1)
    
    # Combine text overlays (for now, use first one - could be enhanced to merge multiple)
    merged_text_overlay = text_overlays[0] if text_overlays else None
    
    # Preserve trim points if any clips have been trimmed
    trim_starts = [c.get("trim_start") for c in sorted_clips if c.get("trim_start") is not None]
    trim_ends = [c.get("trim_end") for c in sorted_clips if c.get("trim_end") is not None]
    
    merged_trim_start = min(trim_starts) if trim_starts else None
    merged_trim_end = max(trim_ends) if trim_ends else None
    
    # Generate new clip ID for merged clip
    merged_clip_id = f"merged-{str(uuid.uuid4())[:8]}"
    
    # Create merged clip
    merged_clip = {
        "id": merged_clip_id,
        "original_path": merged_original_path,
        "start_time": merged_start_time,
        "end_time": merged_end_time,
        "trim_start": merged_trim_start,
        "trim_end": merged_trim_end,
        "split_points": [],  # Merged clips don't have split points
        "merged_with": clip_ids,  # Track which clips were merged
        "text_overlay": merged_text_overlay,
        "scene_number": merged_scene_number,
    }
    
    # Replace clips with merged clip
    # Remove clips in reverse order to maintain indices
    clip_indices.sort(reverse=True)
    new_clips = clips.copy()
    for idx in clip_indices:
        new_clips.pop(idx)
    
    # Insert merged clip at the position of the first removed clip
    insert_position = min(clip_indices) if clip_indices else 0
    new_clips.insert(insert_position, merged_clip)
    
    # Sort clips by start_time to maintain order
    new_clips.sort(key=lambda c: c.get("start_time", 0))
    
    # Update editing state
    editing_state["clips"] = new_clips
    editing_state["version"] = editing_state.get("version", 1) + 1
    
    # Save to database
    editing_session.editing_state = editing_state
    flag_modified(editing_session, "editing_state")  # Tell SQLAlchemy JSON field changed
    db.commit()
    db.refresh(editing_session)
    
    logger.info(
        f"Applied merge to clips {clip_ids} in session {editing_session.id}: "
        f"created merged clip {merged_clip_id} with duration {merged_duration:.2f}s"
    )
    
    # Return merge result
    return {
        "merged_clip_id": merged_clip_id,
        "new_duration": merged_duration,
        "updated_state": editing_state,
    }

