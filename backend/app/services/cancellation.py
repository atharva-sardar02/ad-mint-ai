"""
Cancellation service for handling generation cancellation requests.
"""
import logging
import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.generation import Generation

logger = logging.getLogger(__name__)


def request_cancellation(
    db: Session,
    generation_id: str
) -> bool:
    """
    Request cancellation of a generation by setting the cancellation_requested flag.
    
    Args:
        db: Database session
        generation_id: Generation ID
    
    Returns:
        bool: True if cancellation was requested successfully, False if generation not found
    """
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        logger.error(f"Generation {generation_id} not found for cancellation request")
        return False
    
    # Only allow cancellation if generation is pending or processing
    if generation.status not in ["pending", "processing"]:
        logger.warning(
            f"Cannot cancel generation {generation_id} with status '{generation.status}'"
        )
        return False
    
    generation.cancellation_requested = True
    db.commit()
    
    logger.info(f"Cancellation requested for generation {generation_id}")
    return True


def check_cancellation(
    db: Session,
    generation_id: str
) -> bool:
    """
    Check if cancellation has been requested for a generation.
    
    Args:
        db: Database session
        generation_id: Generation ID
    
    Returns:
        bool: True if cancellation requested, False otherwise
    """
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        return False
    
    return generation.cancellation_requested if generation else False


def handle_cancellation(
    db: Session,
    generation_id: str,
    cleanup_temp_files: bool = True
) -> None:
    """
    Handle cancellation by updating status and cleaning up temp files.
    
    Args:
        db: Database session
        generation_id: Generation ID
        cleanup_temp_files: Whether to clean up temporary files (default: True)
    """
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        logger.error(f"Generation {generation_id} not found for cancellation handling")
        return
    
    # Update status to failed with cancellation message
    generation.status = "failed"
    generation.error_message = "Cancelled by user"
    db.commit()
    
    logger.info(f"Generation {generation_id} marked as cancelled")
    
    # Clean up temp files if requested
    if cleanup_temp_files:
        cleanup_generation_temp_files(generation_id)


def cleanup_generation_temp_files(generation_id: str) -> None:
    """
    Clean up temporary files for a generation.
    
    Args:
        generation_id: Generation ID
    """
    temp_dir = Path("output/temp")
    
    # List of directories to clean up
    dirs_to_clean = [
        temp_dir / generation_id,
        temp_dir / f"{generation_id}_overlays",
        temp_dir / f"{generation_id}_stitched",
        temp_dir / f"{generation_id}_audio",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                logger.info(f"Cleaned up temp directory: {dir_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {dir_path}: {e}")

