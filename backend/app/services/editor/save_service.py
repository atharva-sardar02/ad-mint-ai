"""
Save service for video editing session persistence.
Handles saving editing state to database and updating session status.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models.editing_session import EditingSession

logger = logging.getLogger(__name__)


def validate_editing_state(editing_state: Dict[str, Any]) -> bool:
    """
    Validate editing state structure before saving.
    
    Args:
        editing_state: Dictionary containing editing state
        
    Returns:
        True if valid, False otherwise
        
    Note:
        Basic validation - checks for required 'clips' key and structure.
        More comprehensive validation can be added as needed.
    """
    if not isinstance(editing_state, dict):
        return False
    
    if "clips" not in editing_state:
        return False
    
    if not isinstance(editing_state["clips"], list):
        return False
    
    # Validate each clip has required fields
    for clip in editing_state["clips"]:
        if not isinstance(clip, dict):
            return False
        if "id" not in clip:
            return False
        if "original_path" not in clip:
            return False
    
    return True


def save_editing_session(
    editing_session: EditingSession,
    editing_state: Optional[Dict[str, Any]] = None,
    db: Session = None
) -> EditingSession:
    """
    Save editing session state to database.
    
    This function:
    - Validates editing_state structure if provided
    - Updates editing_session with new state (or keeps existing if not provided)
    - Sets status to "saved"
    - Updates updated_at timestamp
    - Ensures original video path is preserved
    
    Args:
        editing_session: EditingSession model instance
        editing_state: Optional editing state to save (uses existing if not provided)
        db: Database session
        
    Returns:
        Updated EditingSession model instance
        
    Raises:
        ValueError: If editing_state structure is invalid
    """
    # Use provided editing_state or existing one
    if editing_state is not None:
        # Validate editing state structure
        if not validate_editing_state(editing_state):
            raise ValueError("Invalid editing_state structure")
        
        # Update editing state
        editing_session.editing_state = editing_state
        flag_modified(editing_session, "editing_state")
    else:
        # Use existing editing_state, just update status and timestamp
        if not editing_session.editing_state:
            raise ValueError("No editing_state available to save")
    
    # Ensure original video path is preserved
    if not editing_session.original_video_path:
        logger.warning(
            f"Editing session {editing_session.id} has no original_video_path. "
            "This should be set when session is created."
        )
    
    # Update status to "saved"
    editing_session.status = "saved"
    
    # Update timestamp
    editing_session.updated_at = datetime.utcnow()
    
    # Save to database
    if db:
        db.commit()
        db.refresh(editing_session)
    
    logger.info(
        f"Saved editing session {editing_session.id} for generation {editing_session.generation_id}. "
        f"Status: saved, Clips: {len(editing_session.editing_state.get('clips', []))}"
    )
    
    return editing_session

