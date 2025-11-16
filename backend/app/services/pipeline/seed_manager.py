"""
Seed manager service for generating and managing seeds for video generation.
"""
import logging
import random
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.generation import Generation

logger = logging.getLogger(__name__)


def generate_seed() -> int:
    """
    Generate a random integer seed for video generation.
    
    Returns:
        int: Random seed value (0 to 2^31-1 range)
    """
    # Generate seed in valid integer range (0 to 2^31-1)
    seed = random.randint(0, 2**31 - 1)
    logger.debug(f"Generated seed: {seed}")
    return seed


def get_seed_for_generation(db: Session, generation_id: str) -> Optional[int]:
    """
    Get or generate seed for a generation.
    
    If the generation already has a seed_value, return it.
    Otherwise, generate a new seed, store it in the generation record, and return it.
    
    Args:
        db: Database session
        generation_id: Generation ID (UUID string)
    
    Returns:
        Optional[int]: Seed value for the generation, or None if generation not found
    
    Raises:
        ValueError: If generation_id is invalid
    """
    try:
        # Query generation record
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        
        if not generation:
            logger.warning(f"Generation {generation_id} not found")
            return None
        
        # If seed already exists, return it
        if generation.seed_value is not None:
            logger.debug(f"Retrieved existing seed {generation.seed_value} for generation {generation_id}")
            return generation.seed_value
        
        # Generate new seed
        seed = generate_seed()
        logger.info(f"Generated new seed {seed} for generation {generation_id}")
        
        # Store seed in generation record
        generation.seed_value = seed
        db.commit()
        db.refresh(generation)
        
        logger.info(f"Stored seed {seed} for generation {generation_id}")
        return seed
        
    except Exception as e:
        logger.error(f"Error getting seed for generation {generation_id}: {e}", exc_info=True)
        db.rollback()
        raise

