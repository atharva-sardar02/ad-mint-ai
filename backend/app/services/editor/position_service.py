"""
Position service for video clip position and track management.
Handles updating clip positions and track assignments in editing session state.
"""
import logging
from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models.editing_session import EditingSession

logger = logging.getLogger(__name__)


def update_clip_position(
    editing_session: EditingSession,
    clip_id: str,
    new_start_time: float,
    new_track_index: int = 0,
    db: Session = None
) -> Dict[str, Any]:
    """
    Update clip position and track assignment in editing session state.
    
    Args:
        editing_session: EditingSession model instance
        clip_id: ID of the clip to move
        new_start_time: New start time for the clip
        new_track_index: New track index (0-based)
        db: Database session
        
    Returns:
        Updated clip structure
        
    Raises:
        ValueError: If clip not found
    """
    editing_state = editing_session.editing_state or {}
    clips = editing_state.get("clips", [])
    
    # Find the clip to update
    clip_to_update = None
    for clip in clips:
        if clip.get("id") == clip_id:
            clip_to_update = clip
            break
    
    if not clip_to_update:
        raise ValueError(f"Clip {clip_id} not found in editing session")
    
    # Calculate new end_time based on duration
    original_start = clip_to_update.get("start_time", 0.0)
    original_end = clip_to_update.get("end_time", 0.0)
    duration = original_end - original_start
    
    # If trim values exist, use trimmed duration
    trim_start = clip_to_update.get("trim_start")
    trim_end = clip_to_update.get("trim_end")
    if trim_start is not None and trim_end is not None:
        duration = trim_end - trim_start
    
    # Update clip position and track
    clip_to_update["start_time"] = new_start_time
    clip_to_update["end_time"] = new_start_time + duration
    clip_to_update["track_index"] = new_track_index
    
    # Update editing state version
    editing_state["version"] = editing_state.get("version", 1) + 1
    
    # Save to database
    editing_session.editing_state = editing_state
    flag_modified(editing_session, "editing_state")
    if db:
        db.commit()
        db.refresh(editing_session)
    
    logger.info(
        f"Updated clip {clip_id} position in session {editing_session.id}: "
        f"start_time={new_start_time}, track_index={new_track_index}"
    )
    
    return clip_to_update

