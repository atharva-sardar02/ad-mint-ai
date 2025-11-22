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


def update_user_statistics_on_completion(
    db: Session,
    generation_id: str
) -> None:
    """
    Update user statistics (total_generations and total_cost) when generation completes.
    
    This function increments user.total_generations by 1 and adds generation.cost
    to user.total_cost atomically within a single database transaction.
    
    Args:
        db: Database session
        generation_id: Generation ID that completed
    
    Raises:
        Logs errors but does not raise exceptions to avoid breaking generation completion flow
    """
    try:
        # Get generation record to find user_id and cost
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            logger.error(f"Generation {generation_id} not found for statistics update")
            return
        
        if generation.cost is None:
            logger.warning(
                f"Generation {generation_id} has no cost set. "
                f"Statistics update skipped. Cost should be set before calling this function."
            )
            return
        
        # Get user record
        user = db.query(User).filter(User.id == generation.user_id).first()
        if not user:
            logger.error(f"User {generation.user_id} not found for statistics update")
            return
        
        # Store initial values for logging
        initial_generations = user.total_generations or 0
        initial_cost = user.total_cost or 0.0
        
        # Update statistics atomically within transaction
        if user.total_generations is None:
            user.total_generations = 0
        user.total_generations += 1
        
        if user.total_cost is None:
            user.total_cost = 0.0
        user.total_cost += generation.cost
        
        # Commit transaction (atomic update)
        db.commit()
        
        logger.info(
            f"User statistics updated for user {user.id}: "
            f"total_generations {initial_generations} → {user.total_generations}, "
            f"total_cost ${initial_cost:.4f} → ${user.total_cost:.4f} "
            f"(added ${generation.cost:.4f} from generation {generation_id})"
        )
    except Exception as e:
        # Log error but don't raise - statistics update failure shouldn't break generation completion
        logger.error(
            f"Error updating user statistics for generation {generation_id}: {e}",
            exc_info=True
        )
        # Rollback transaction on error
        db.rollback()


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


def track_vision_llm_cost(
    db: Session,
    user_id: str,
    cost: float,
    operation_type: str = "brand_style_extraction",
    image_count: int = 1,
    update_user_total: bool = True
) -> None:
    """
    Track Vision LLM API cost for style extraction operations.
    
    Args:
        db: Database session
        user_id: User ID
        operation_type: Type of operation ("brand_style_extraction" or "product_style_extraction")
        cost: Cost in USD for this operation
        image_count: Number of images analyzed
        update_user_total: Whether to update user's total_cost field (default: True)
    """
    logger.info(
        f"Tracking Vision LLM cost: user={user_id}, "
        f"operation={operation_type}, cost=${cost:.4f}, images={image_count}"
    )
    
    # Log cost per operation
    logger.info(
        f"Vision LLM cost tracked for user {user_id}, operation {operation_type}: "
        f"${cost:.4f} ({image_count} images)"
    )
    
    # Update user's total_cost if requested
    if update_user_total:
        update_user_total_cost(db=db, user_id=user_id, additional_cost=cost)
    
    # Note: Vision LLM costs are tracked per user and can be included in generation costs
    # if extraction happens during generation. For standalone extraction operations,
    # costs are logged and optionally added to user's total_cost.


def accumulate_generation_cost_with_vision_llm(
    db: Session,
    generation_id: str,
    video_cost: float,
    llm_cost: Optional[float] = None,
    vision_llm_cost: Optional[float] = None
) -> float:
    """
    Accumulate total cost for a generation including Vision LLM costs.
    
    Args:
        db: Database session
        generation_id: Generation ID
        video_cost: Total video generation cost
        llm_cost: Optional LLM cost (default: 0.01 for GPT-4 Turbo)
        vision_llm_cost: Optional Vision LLM cost for style extraction
    
    Returns:
        float: Total accumulated cost
    """
    if llm_cost is None:
        llm_cost = 0.01  # Default LLM cost per generation (GPT-4 Turbo)
    
    if vision_llm_cost is None:
        vision_llm_cost = 0.0  # No Vision LLM cost by default
    
    total_cost = video_cost + llm_cost + vision_llm_cost
    
    logger.info(
        f"Accumulating costs for generation {generation_id}: "
        f"video=${video_cost:.4f}, llm=${llm_cost:.4f}, "
        f"vision_llm=${vision_llm_cost:.4f}, total=${total_cost:.4f}"
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

