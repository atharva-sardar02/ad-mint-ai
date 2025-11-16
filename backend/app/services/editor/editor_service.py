"""
Editor service for extracting scene clips and managing editing sessions.
"""
import logging
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.generation import Generation
from app.db.models.editing_session import EditingSession
from app.schemas.editor import ClipInfo
from app.schemas.generation import ScenePlan, Scene

logger = logging.getLogger(__name__)


def get_full_url(relative_path: Optional[str]) -> Optional[str]:
    """
    Convert relative path to full URL for frontend consumption.
    
    Args:
        relative_path: Relative file path or full URL
        
    Returns:
        Full URL or None if path is empty
    """
    if not relative_path:
        return None
    
    # If already a full URL, return as-is
    if relative_path.startswith("http://") or relative_path.startswith("https://"):
        return relative_path
    
    # Convert relative path to full URL
    base_url = settings.STATIC_BASE_URL.rstrip("/")
    path = relative_path.lstrip("/")
    return f"{base_url}/{path}"


def extract_clips_from_generation(
    generation: Generation,
    db: Session
) -> List[ClipInfo]:
    """
    Extract scene clip information from a generation record.
    
    Args:
        generation: Generation model instance
        db: Database session
        
    Returns:
        List of ClipInfo objects with clip metadata
        
    Note:
        This function extracts clips from temp_clip_paths (preferred) or
        reconstructs from scene_plan if temp_clip_paths is not available.
        If neither is available, returns empty list and logs a warning.
    """
    clips = []
    
    # Try to extract from temp_clip_paths first (preferred method)
    if generation.temp_clip_paths:
        scene_plan_data = None
        if generation.scene_plan:
            try:
                scene_plan_data = ScenePlan(**generation.scene_plan)
            except Exception as e:
                logger.warning(f"Failed to parse scene_plan for generation {generation.id}: {e}")
        
        # Calculate cumulative start times for each clip
        cumulative_time = 0.0
        
        for i, clip_path in enumerate(generation.temp_clip_paths, start=1):
            # Get scene duration from scene_plan if available
            scene_duration = 5.0  # Default duration
            text_overlay = None
            
            if scene_plan_data and i <= len(scene_plan_data.scenes):
                scene = scene_plan_data.scenes[i - 1]  # 0-based index
                scene_duration = float(scene.duration)
                # Extract text overlay metadata
                if scene.text_overlay:
                    text_overlay = {
                        "text": scene.text_overlay.text,
                        "position": scene.text_overlay.position,
                        "font_size": scene.text_overlay.font_size,
                        "color": scene.text_overlay.color,
                        "animation": scene.text_overlay.animation,
                    }
            
            start_time = cumulative_time
            end_time = cumulative_time + scene_duration
            
            # Generate clip URL
            clip_url = get_full_url(clip_path)
            if not clip_url:
                # If get_full_url returns None, try constructing from path
                clip_url = get_full_url(str(clip_path))
            
            # Generate clip ID
            clip_id = f"clip-{generation.id}-{i}"
            
            # For thumbnail, we could generate one or use a placeholder
            # For now, we'll leave it as None (can be enhanced later)
            thumbnail_url = None
            
            clip_info = ClipInfo(
                clip_id=clip_id,
                scene_number=i,
                original_path=str(clip_path),
                clip_url=clip_url or str(clip_path),
                duration=scene_duration,
                start_time=start_time,
                end_time=end_time,
                thumbnail_url=thumbnail_url,
                text_overlay=text_overlay,
            )
            clips.append(clip_info)
            
            cumulative_time = end_time
    
    # Fallback: reconstruct from scene_plan if temp_clip_paths is not available
    elif generation.scene_plan:
        logger.warning(
            f"Generation {generation.id} has scene_plan but no temp_clip_paths. "
            "Cannot extract clips without file paths."
        )
        # Note: We can't create ClipInfo without actual file paths
        # This case should be handled by the caller
    
    else:
        logger.warning(
            f"Generation {generation.id} has neither temp_clip_paths nor scene_plan. "
            "Cannot extract clips."
        )
    
    return clips


def get_or_create_editing_session(
    generation: Generation,
    user_id: str,
    db: Session
) -> EditingSession:
    """
    Get existing editing session or create a new one for a generation.
    
    Args:
        generation: Generation model instance
        user_id: User ID who owns the generation
        db: Database session
        
    Returns:
        EditingSession model instance (existing or newly created)
    """
    # Check if editing session already exists
    existing_session = (
        db.query(EditingSession)
        .filter(EditingSession.generation_id == generation.id)
        .filter(EditingSession.user_id == user_id)
        .first()
    )
    
    if existing_session:
        logger.info(f"Found existing editing session {existing_session.id} for generation {generation.id}")
        return existing_session
    
    # Create new editing session
    # Initialize editing_state with clips from generation
    clips = extract_clips_from_generation(generation, db)
    
    # Build initial editing state
    editing_state = {
        "clips": [
            {
                "id": clip.clip_id,
                "original_path": clip.original_path,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "trim_start": None,
                "trim_end": None,
                "split_points": [],
                "merged_with": [],
                "scene_number": clip.scene_number,
                "text_overlay": clip.text_overlay,
            }
            for clip in clips
        ],
        "version": 1,
    }
    
    session_id = str(uuid4())
    new_session = EditingSession(
        id=session_id,
        generation_id=generation.id,
        user_id=user_id,
        original_video_path=generation.video_path or "",
        editing_state=editing_state,
        status="active",
    )
    
    db.add(new_session)
    db.commit()
    
    # Note: Avoiding db.refresh() and attribute access after commit for testing compatibility
    logger.info(f"Created new editing session {session_id} for generation {generation.id}")
    return new_session

