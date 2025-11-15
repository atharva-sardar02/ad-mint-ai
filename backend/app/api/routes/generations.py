"""
Video generation route handlers.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.generation import Generation
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.generation import (
    GenerateRequest,
    GenerateResponse,
    GenerationListResponse,
    GenerationListItem,
    ScenePlan,
    StatusResponse,
)
from app.services.cost_tracking import track_video_generation_cost, track_complete_generation_cost
from app.services.pipeline.llm_enhancement import enhance_prompt_with_llm
from app.services.pipeline.overlays import add_overlays_to_clips
from app.services.pipeline.scene_planning import plan_scenes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generations"])


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def create_generation(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GenerateResponse:
    """
    Start a new video generation from a user prompt.
    
    Args:
        request: GenerateRequest with prompt (10-500 characters)
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        GenerateResponse with generation_id and status
    
    Raises:
        HTTPException: 422 if validation fails (handled by FastAPI)
        HTTPException: 500 if LLM or scene planning fails
    """
    logger.info(f"Creating generation for user {current_user.id}, prompt length: {len(request.prompt)}")
    
    # Create Generation record with status=pending
    generation = Generation(
        user_id=current_user.id,
        prompt=request.prompt,
        status="pending",
        progress=0,
        current_step="Initializing"
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)
    
    generation_id = generation.id
    logger.info(f"Created generation {generation_id}")
    
    try:
        # Update status to processing
        generation.status = "processing"
        generation.progress = 10
        generation.current_step = "LLM Enhancement"
        db.commit()
        
        # Call LLM enhancement service
        logger.info(f"Calling LLM enhancement for generation {generation_id}")
        ad_spec = await enhance_prompt_with_llm(request.prompt)
        
        # Store LLM specification
        generation.llm_specification = ad_spec.model_dump()
        generation.framework = ad_spec.framework
        generation.progress = 20
        generation.current_step = "Scene Planning"
        db.commit()
        
        # Call scene planning module
        logger.info(f"Calling scene planning for generation {generation_id}")
        scene_plan = plan_scenes(ad_spec, target_duration=15)
        
        # Store scene plan
        generation.scene_plan = scene_plan.model_dump()
        generation.num_scenes = len(scene_plan.scenes)
        db.commit()
        
        # Video Generation Stage (30-70% progress)
        logger.info(f"Starting video generation for generation {generation_id}")
        
        # Setup temp storage directory
        temp_dir = Path("output/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_output_dir = str(temp_dir / generation_id)
        
        # Create cancellation check function
        def check_cancellation() -> bool:
            db.refresh(generation)
            return generation.cancellation_requested if generation else False
        
        try:
            # Generate all video clips
            num_scenes = len(scene_plan.scenes)
            progress_start = 30
            progress_end = 70
            progress_per_scene = (progress_end - progress_start) / num_scenes if num_scenes > 0 else 0
            
            clip_paths = []
            total_video_cost = 0.0
            
            for i, scene in enumerate(scene_plan.scenes, start=1):
                # Check cancellation before each scene
                if check_cancellation():
                    logger.info(f"Generation {generation_id} cancelled before scene {i}")
                    generation.status = "failed"
                    generation.error_message = "Cancelled by user"
                    db.commit()
                    raise RuntimeError("Generation cancelled by user")
                
                # Update progress
                progress = int(progress_start + (i - 1) * progress_per_scene)
                generation.progress = progress
                generation.current_step = f"Generating video clip {i} of {num_scenes}"
                db.commit()
                
                logger.info(f"Generating clip {i}/{num_scenes} for generation {generation_id}")
                
                # Generate video clip
                from app.services.pipeline.video_generation import generate_video_clip, MODEL_COSTS, REPLICATE_MODELS
                
                clip_path = await generate_video_clip(
                    scene=scene,
                    output_dir=temp_output_dir,
                    generation_id=generation_id,
                    scene_number=i,
                    cancellation_check=check_cancellation
                )
                clip_paths.append(clip_path)
                
                # Track cost per clip (approximate - actual cost from API response would be better)
                model_cost_per_sec = MODEL_COSTS.get(REPLICATE_MODELS["primary"], 0.05)
                clip_cost = model_cost_per_sec * scene.duration
                total_video_cost += clip_cost
                
                track_video_generation_cost(
                    db=db,
                    generation_id=generation_id,
                    scene_number=i,
                    cost=clip_cost,
                    model_name=REPLICATE_MODELS["primary"]
                )
            
            # Store temp clip paths
            generation.temp_clip_paths = clip_paths
            generation.progress = 70
            generation.current_step = "Adding text overlays"
            db.commit()
            
            # Add text overlays to all clips
            logger.info(f"Adding text overlays to {len(clip_paths)} clips")
            scene_plan_obj = ScenePlan(**generation.scene_plan)
            overlay_output_dir = str(temp_dir / f"{generation_id}_overlays")
            overlay_paths = add_overlays_to_clips(
                clip_paths=clip_paths,
                scene_plan=scene_plan_obj,
                output_dir=overlay_output_dir
            )
            
            # Update temp_clip_paths with overlay paths
            generation.temp_clip_paths = overlay_paths
            generation.progress = 70  # Still at 70% - stitching comes next (in future story)
            generation.current_step = "Video clips with overlays complete"
            db.commit()
            
            # Track complete generation cost
            track_complete_generation_cost(
                db=db,
                generation_id=generation_id,
                video_cost=total_video_cost,
                llm_cost=0.01  # Approximate LLM cost
            )
            
            logger.info(
                f"Generation {generation_id} video generation complete - "
                f"{len(overlay_paths)} clips, cost: ${total_video_cost:.4f}"
            )
            
        except RuntimeError as e:
            if "cancelled" in str(e).lower():
                # Already handled above
                raise HTTPException(
                    status_code=status.HTTP_200_OK,
                    detail={
                        "error": {
                            "code": "GENERATION_CANCELLED",
                            "message": "Generation was cancelled by user"
                        }
                    }
                )
            logger.error(f"Video generation failed for {generation_id}: {e}", exc_info=True)
            generation.status = "failed"
            generation.error_message = str(e)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "VIDEO_GENERATION_FAILED",
                        "message": f"Video generation failed: {str(e)}"
                    }
                }
            )
        
        logger.info(f"Generation {generation_id} initialized successfully - framework: {scene_plan.framework}, scenes: {generation.num_scenes}")
        
        return GenerateResponse(
            generation_id=generation_id,
            status="pending",
            message="Video generation started"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in generation {generation_id}: {e}")
        generation.status = "failed"
        generation.error_message = str(e)
        generation.progress = 0
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "GENERATION_FAILED",
                    "message": f"Failed to process prompt: {str(e)}"
                }
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in generation {generation_id}: {e}", exc_info=True)
        generation.status = "failed"
        generation.error_message = str(e)
        generation.progress = 0
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "GENERATION_FAILED",
                    "message": "An unexpected error occurred during generation"
                }
            }
        )


@router.get("/status/{generation_id}", status_code=status.HTTP_200_OK)
async def get_generation_status(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StatusResponse:
    """
    Get the status and progress of a video generation.
    
    Args:
        generation_id: UUID of the generation
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        StatusResponse with current status, progress, and step
    
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
    """
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GENERATION_NOT_FOUND",
                    "message": "Generation not found"
                }
            }
        )
    
    # Check authorization - user can only access their own generations
    if generation.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to access generation {generation_id} owned by {generation.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to access this generation"
                }
            }
        )
    
    return StatusResponse(
        generation_id=generation.id,
        status=generation.status,
        progress=generation.progress,
        current_step=generation.current_step,
        video_url=generation.video_url,
        cost=generation.cost,
        error=generation.error_message
    )


@router.get("/generations", response_model=GenerationListResponse)
async def get_generations(
    limit: int = Query(default=20, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(
        default=None,
        description="Filter by status (pending, processing, completed, failed)",
    ),
    q: Optional[str] = Query(
        default=None, description="Search term for prompt text (case-insensitive)"
    ),
    sort: str = Query(
        default="created_at_desc",
        description="Sort order (created_at_desc, created_at_asc)",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerationListResponse:
    """
    Get paginated list of user's video generations.

    Args:
        limit: Number of results per page (1-100, default: 20)
        offset: Pagination offset (default: 0)
        status: Optional status filter (pending, processing, completed, failed)
        q: Optional search term for prompt text (case-insensitive substring match)
        sort: Sort order (created_at_desc or created_at_asc, default: created_at_desc)
        current_user: Current authenticated user (from dependency)
        db: Database session

    Returns:
        GenerationListResponse with total, limit, offset, and generations array

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 422 if validation fails (handled by FastAPI)
    """
    # Build base query - filter by user_id
    query = db.query(Generation).filter(Generation.user_id == current_user.id)

    # Apply status filter if provided
    if status:
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_STATUS",
                        "message": f"Status must be one of: {', '.join(valid_statuses)}",
                    }
                },
            )
        query = query.filter(Generation.status == status)

    # Apply search filter if provided (case-insensitive substring match on prompt)
    if q:
        query = query.filter(Generation.prompt.ilike(f"%{q}%"))

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    if sort == "created_at_asc":
        query = query.order_by(Generation.created_at.asc())
    else:  # default to created_at_desc (newest first)
        query = query.order_by(Generation.created_at.desc())

    # Apply pagination
    generations = query.offset(offset).limit(limit).all()

    # Convert to Pydantic models
    generation_items = [
        GenerationListItem(
            id=gen.id,
            prompt=gen.prompt,
            status=gen.status,
            video_url=gen.video_url,
            thumbnail_url=gen.thumbnail_url,
            duration=gen.duration,
            cost=gen.cost,
            created_at=gen.created_at,
            completed_at=gen.completed_at,
        )
        for gen in generations
    ]

    logger.info(
        f"User {current_user.id} retrieved {len(generation_items)} generations "
        f"(total: {total}, offset: {offset}, limit: {limit})"
    )

    return GenerationListResponse(
        total=total,
        limit=limit,
        offset=offset,
        generations=generation_items,
    )
