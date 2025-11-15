"""
Progress tracking service for updating generation status and progress.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.generation import Generation

logger = logging.getLogger(__name__)


def update_generation_progress(
    db: Session,
    generation_id: str,
    progress: int,
    current_step: Optional[str] = None,
    status: Optional[str] = None
) -> None:
    """
    Update generation progress, current step, and optionally status.
    
    Args:
        db: Database session
        generation_id: Generation ID
        progress: Progress percentage (0-100)
        current_step: Optional current step description
        status: Optional status update (pending, processing, completed, failed)
    """
    if progress < 0 or progress > 100:
        logger.warning(f"Invalid progress value {progress} for generation {generation_id}, clamping to 0-100")
        progress = max(0, min(100, progress))
    
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        logger.error(f"Generation {generation_id} not found for progress update")
        return
    
    generation.progress = progress
    if current_step is not None:
        generation.current_step = current_step
    if status is not None:
        generation.status = status
    
    db.commit()
    db.refresh(generation)  # Refresh to ensure changes are visible to other connections
    
    logger.info(
        f"Progress updated for generation {generation_id}: "
        f"progress={progress}%, step='{current_step}', status='{status or generation.status}'"
    )


def update_generation_status(
    db: Session,
    generation_id: str,
    status: str,
    error_message: Optional[str] = None
) -> None:
    """
    Update generation status and optionally error message.
    
    Args:
        db: Database session
        generation_id: Generation ID
        status: Status value (pending, processing, completed, failed)
        error_message: Optional error message for failed status
    """
    valid_statuses = ["pending", "processing", "completed", "failed"]
    if status not in valid_statuses:
        logger.error(f"Invalid status '{status}' for generation {generation_id}")
        return
    
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        logger.error(f"Generation {generation_id} not found for status update")
        return
    
    generation.status = status
    if error_message is not None:
        generation.error_message = error_message
    
    db.commit()
    
    logger.info(
        f"Status updated for generation {generation_id}: status='{status}'"
        + (f", error='{error_message}'" if error_message else "")
    )


def update_generation_step(
    db: Session,
    generation_id: str,
    current_step: str
) -> None:
    """
    Update only the current step description.
    
    Args:
        db: Database session
        generation_id: Generation ID
        current_step: Current step description
    """
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        logger.error(f"Generation {generation_id} not found for step update")
        return
    
    generation.current_step = current_step
    db.commit()
    
    logger.info(f"Step updated for generation {generation_id}: step='{current_step}'")

