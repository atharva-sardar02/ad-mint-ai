"""
Service for deleting clips from editing sessions.
"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models.editing_session import EditingSession

logger = logging.getLogger(__name__)


def delete_clip_from_editing_session(
    editing_session: EditingSession,
    clip_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Delete a clip from the editing session.
    
    Args:
        editing_session: EditingSession model instance
        clip_id: ID of the clip to delete
        db: Database session
        
    Returns:
        Updated editing state
        
    Raises:
        ValueError: If clip not found or validation fails
    """
    editing_state = editing_session.editing_state or {}
    clips = editing_state.get("clips", [])
    
    # Find the clip to delete
    clip_index = -1
    for i, clip in enumerate(clips):
        if clip.get("id") == clip_id:
            clip_index = i
            break
    
    if clip_index == -1:
        raise ValueError(f"Clip {clip_id} not found in editing session")
    
    # Remove the clip from the clips array
    deleted_clip = clips.pop(clip_index)
    
    # Update editing state
    editing_state["clips"] = clips
    editing_state["version"] = editing_state.get("version", 1) + 1
    
    # Save to database
    editing_session.editing_state = editing_state
    
    # Mark the JSON field as modified so SQLAlchemy knows to save it
    flag_modified(editing_session, "editing_state")
    
    db.commit()
    db.refresh(editing_session)
    
    logger.info(
        f"Deleted clip {clip_id} from session {editing_session.id}. "
        f"Remaining clips: {len(clips)}"
    )
    
    return editing_state

