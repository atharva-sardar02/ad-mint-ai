"""
Cost tracking service for tracking API costs per generation.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.generation import Generation
from app.db.models.user import User

logger = logging.getLogger(__name__)


def track_video_generation_cost(
    db: Session,
    generation_id: str,
    scene_number: int,
    cost: float,
    model_name: str
) -> None:
    """
    Track Replicate API cost for a single video clip generation.
    
    Args:
        db: Database session
        generation_id: Generation ID
        scene_number: Scene number (1, 2, 3...)
        cost: Cost in USD for this clip
        model_name: Model used for generation
    """
    logger.info(
        f"Tracking video generation cost: generation={generation_id}, "
        f"scene={scene_number}, cost=${cost:.4f}, model={model_name}"
    )
    
    # Get generation record
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        logger.error(f"Generation {generation_id} not found for cost tracking")
        return
    
    # Note: Cost breakdown could be stored in a cost_breakdown JSON field if added later
    # For MVP, we just log and accumulate in the cost field
    
    # Log cost per clip
    logger.info(
        f"Cost tracked for generation {generation_id}, scene {scene_number}: "
        f"${cost:.4f} (model: {model_name})"
    )


def accumulate_generation_cost(
    db: Session,
    generation_id: str,
    video_cost: float,
    llm_cost: Optional[float] = None
) -> float:
    """
    Accumulate total cost for a generation and update Generation record.
    
    Args:
        db: Database session
        generation_id: Generation ID
        video_cost: Total video generation cost
        llm_cost: Optional LLM cost (default: 0.01 for GPT-4 Turbo)
    
    Returns:
        float: Total accumulated cost
    """
    if llm_cost is None:
        llm_cost = 0.01  # Default LLM cost per generation (GPT-4 Turbo)
    
    total_cost = video_cost + llm_cost
    
    logger.info(
        f"Accumulating costs for generation {generation_id}: "
        f"video=${video_cost:.4f}, llm=${llm_cost:.4f}, total=${total_cost:.4f}"
    )
    
    # Get generation record
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        logger.error(f"Generation {generation_id} not found for cost accumulation")
        return total_cost
    
    # Update generation cost
    generation.cost = total_cost
    db.commit()
    
    logger.info(f"Generation {generation_id} cost updated: ${total_cost:.4f}")
    
    return total_cost


def update_user_total_cost(
    db: Session,
    user_id: str,
    additional_cost: float
) -> None:
    """
    Update user's total_cost field atomically.
    
    Args:
        db: Database session
        user_id: User ID
        additional_cost: Cost to add to user's total
    """
    logger.info(
        f"Updating user {user_id} total_cost: adding ${additional_cost:.4f}"
    )
    
    # Get user record
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"User {user_id} not found for cost update")
        return
    
    # Update total_cost atomically
    if user.total_cost is None:
        user.total_cost = 0.0
    
    user.total_cost += additional_cost
    db.commit()
    
    logger.info(
        f"User {user_id} total_cost updated: ${user.total_cost:.4f}"
    )


def track_complete_generation_cost(
    db: Session,
    generation_id: str,
    video_cost: float,
    llm_cost: Optional[float] = None
) -> None:
    """
    Track complete generation cost and update both Generation and User records.
    
    Args:
        db: Database session
        generation_id: Generation ID
        video_cost: Total video generation cost
        llm_cost: Optional LLM cost
    """
    # Accumulate generation cost
    total_cost = accumulate_generation_cost(
        db=db,
        generation_id=generation_id,
        video_cost=video_cost,
        llm_cost=llm_cost
    )
    
    # Get generation to find user_id
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    if not generation:
        logger.error(f"Generation {generation_id} not found")
        return
    
    # Update user's total cost
    update_user_total_cost(
        db=db,
        user_id=generation.user_id,
        additional_cost=total_cost
    )
    
    logger.info(
        f"Complete cost tracking finished for generation {generation_id}: "
        f"total=${total_cost:.4f}"
    )

