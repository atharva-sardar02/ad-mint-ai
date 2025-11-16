"""
Video generation route handlers.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.generation import Generation
from app.db.models.user import User
from app.db.session import SessionLocal, get_db
from app.schemas.generation import (
    DeleteResponse,
    GenerateRequest,
    GenerateResponse,
    GenerationListResponse,
    GenerationListItem,
    ScenePlan,
    StatusResponse,
)
from app.services.cost_tracking import (
    track_video_generation_cost,
    track_complete_generation_cost,
    update_user_statistics_on_completion,
)
from app.services.cancellation import request_cancellation, handle_cancellation
from app.services.pipeline.progress_tracking import update_generation_progress, update_generation_status
from app.services.pipeline.llm_enhancement import enhance_prompt_with_llm
from app.services.pipeline.overlays import add_overlays_to_clips
from app.services.pipeline.scene_planning import plan_scenes, create_basic_scene_plan_from_prompt
from app.services.pipeline.stitching import stitch_video_clips
from app.services.pipeline.audio import add_audio_layer
from app.services.pipeline.export import export_final_video
from app.services.pipeline.cache import get_cached_clip, cache_clip, should_cache_prompt
from app.services.pipeline.video_generation import (
    generate_video_clip,
    generate_video_clip_with_model,
    MODEL_COSTS,
    REPLICATE_MODELS
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api", tags=["generations"])

# Text overlays are enabled - font loading uses system fonts with graceful fallback
TEXT_OVERLAYS_ENABLED = True


async def process_generation(
    generation_id: str, 
    prompt: str,
    preferred_model: Optional[str] = None,
    num_clips: Optional[int] = None,
    use_llm: bool = True
):
    """
    Background task to process video generation.
    This runs asynchronously after the API returns a response.
    """
    logger.info(f"[{generation_id}] Starting background generation task")
    logger.info(f"[{generation_id}] User prompt: {prompt[:100]}...")
    
    # Create a new database session for the background task
    db = SessionLocal()
    try:
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            logger.error(f"[{generation_id}] Generation not found in background task")
            return
        
        logger.info(f"[{generation_id}] Generation record found, starting processing")
        
        try:
            if use_llm:
                # Update status to processing
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=10,
                    current_step="LLM Enhancement",
                    status="processing"
                )
                logger.info(f"[{generation_id}] Status updated: processing (10%) - LLM Enhancement")
                
                # Call LLM enhancement service
                logger.info(f"[{generation_id}] Calling LLM enhancement service...")
                ad_spec = await enhance_prompt_with_llm(prompt)
                logger.info(f"[{generation_id}] LLM enhancement completed - Framework: {ad_spec.framework}, Scenes: {len(ad_spec.scenes)}")
                
                # Store LLM specification
                generation.llm_specification = ad_spec.model_dump()
                generation.framework = ad_spec.framework
                db.commit()
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=20,
                    current_step="Scene Planning"
                )
                logger.info(f"[{generation_id}] LLM specification stored, progress: 20% - Scene Planning")
                
                # Call scene planning module
                logger.info(f"[{generation_id}] Calling scene planning module...")
                scene_plan = plan_scenes(ad_spec, target_duration=15)
            else:
                # Skip LLM enhancement, create basic scene plan directly
                logger.info(f"[{generation_id}] LLM layer disabled, creating basic scene plan from prompt")
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=20,
                    current_step="Scene Planning (No LLM)",
                    status="processing"
                )
                
                # Create basic scene plan from prompt
                num_scenes_for_plan = num_clips if num_clips else 3
                scene_plan = create_basic_scene_plan_from_prompt(
                    prompt=prompt,
                    target_duration=15,
                    num_scenes=num_scenes_for_plan
                )
                
                # Store basic specification
                generation.framework = scene_plan.framework
                generation.llm_specification = None  # No LLM spec when disabled
                db.commit()
            logger.info(f"[{generation_id}] Scene planning completed - {len(scene_plan.scenes)} scenes planned, total duration: {scene_plan.total_duration}s")
            
            # If num_clips is specified, limit the scenes
            if num_clips is not None and num_clips > 0:
                logger.info(f"[{generation_id}] Limiting scenes to {num_clips} as requested")
                scene_plan.scenes = scene_plan.scenes[:num_clips]
                scene_plan.total_duration = sum(s.duration for s in scene_plan.scenes)
                logger.info(f"[{generation_id}] Adjusted to {len(scene_plan.scenes)} scenes, total duration: {scene_plan.total_duration}s")
            
            # Store scene plan
            generation.scene_plan = scene_plan.model_dump()
            generation.num_scenes = len(scene_plan.scenes)
            db.commit()
            logger.info(f"[{generation_id}] Scene plan stored in database")
            
            # Video Generation Stage (30-70% progress)
            logger.info(f"[{generation_id}] Starting video generation stage (30-70% progress)")
            logger.info(f"[{generation_id}] Will generate {len(scene_plan.scenes)} video clips")
            
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
                use_cache = should_cache_prompt(prompt)
                
                if use_cache:
                    logger.info(f"[{generation_id}] Cache enabled for this prompt")
                
                for i, scene in enumerate(scene_plan.scenes, start=1):
                    # Check cancellation before each scene
                    if check_cancellation():
                        logger.info(f"[{generation_id}] Generation cancelled before scene {i}")
                        update_generation_status(
                            db=db,
                            generation_id=generation_id,
                            status="failed",
                            error_message="Cancelled by user"
                        )
                        return
                    
                    # Update progress at start of clip generation
                    progress = int(progress_start + (i - 1) * progress_per_scene)
                    update_generation_progress(
                        db=db,
                        generation_id=generation_id,
                        progress=progress,
                        current_step=f"Generating video clip {i} of {num_scenes}"
                    )
                    
                    logger.info(f"[{generation_id}] Generating clip {i}/{num_scenes} - Scene type: {scene.scene_type}, Duration: {scene.duration}s")
                    logger.info(f"[{generation_id}] Visual prompt: {scene.visual_prompt[:80]}...")
                    
                    # Check cache first (scene index is 0-based)
                    cached_clip = None
                    model_used = None
                    if use_cache:
                        cached_clip = get_cached_clip(prompt, i - 1)
                    
                    if cached_clip:
                        logger.info(f"[{generation_id}] Using cached clip for scene {i}: {cached_clip}")
                        clip_path = cached_clip
                        clip_cost = 0.0  # Cached clips are free
                        model_used = "cached"  # Mark as cached for logging
                    else:
                        # Update progress to show we're calling the API (this can take 30-60+ seconds)
                        update_generation_progress(
                            db=db,
                            generation_id=generation_id,
                            progress=progress,
                            current_step=f"Calling API for clip {i} of {num_scenes} (this may take 30-60 seconds)"
                        )
                        
                        # Generate video clip
                        logger.info(f"[{generation_id}] Calling Replicate API for clip {i}...")
                        clip_path, model_used = await generate_video_clip(
                            scene=scene,
                            output_dir=temp_output_dir,
                            generation_id=generation_id,
                            scene_number=i,
                            cancellation_check=check_cancellation
                        )
                        logger.info(f"[{generation_id}] Clip {i} generated successfully: {clip_path} (model: {model_used})")
                        
                        # Cache the clip if caching is enabled
                        if use_cache:
                            cache_clip(prompt, i - 1, clip_path)
                        
                        # Calculate cost using the actual model that was used
                        model_cost_per_sec = MODEL_COSTS.get(model_used, 0.05)
                        clip_cost = model_cost_per_sec * scene.duration
                        logger.info(f"[{generation_id}] Clip {i} cost calculated: ${clip_cost:.4f} (model: {model_used}, ${model_cost_per_sec}/sec × {scene.duration}s)")
                    
                    clip_paths.append(clip_path)
                    total_video_cost += clip_cost
                    
                    # Update progress after clip completion (mid-point between start and next)
                    progress_after_clip = int(progress_start + i * progress_per_scene)
                    update_generation_progress(
                        db=db,
                        generation_id=generation_id,
                        progress=progress_after_clip,
                        current_step=f"Completed clip {i} of {num_scenes}"
                    )
                    
                    logger.info(f"[{generation_id}] Clip {i} cost: ${clip_cost:.4f}, total cost so far: ${total_video_cost:.4f} (model: {model_used})")
                    
                    # Track cost with actual model used (only for non-cached clips)
                    if not cached_clip:
                        track_video_generation_cost(
                            db=db,
                            generation_id=generation_id,
                            scene_number=i,
                            cost=clip_cost,
                            model_name=model_used
                        )
                
                # Store temp clip paths
                generation.temp_clip_paths = clip_paths
                db.commit()
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=70,
                    current_step="Adding text overlays"
                )
                logger.info(f"[{generation_id}] All {len(clip_paths)} video clips generated, progress: 70% - Adding text overlays")
                
                if TEXT_OVERLAYS_ENABLED:
                    # Add text overlays to all video clips
                    logger.info(f"[{generation_id}] Starting text overlay addition for {len(clip_paths)} clips...")
                    scene_plan_obj = ScenePlan(**generation.scene_plan)
                    overlay_output_dir = str(temp_dir / f"{generation_id}_overlays")
                    logger.info(f"[{generation_id}] Overlay output directory: {overlay_output_dir}")
                    overlay_paths = add_overlays_to_clips(
                        clip_paths=clip_paths,
                        scene_plan=scene_plan_obj,
                        output_dir=overlay_output_dir
                    )
                    logger.info(f"[{generation_id}] Text overlays added successfully to all clips")
                else:
                    # Fallback: use raw clips without overlays (should not happen with flag enabled)
                    overlay_paths = clip_paths
                    logger.warning(f"[{generation_id}] Text overlay stage disabled - using raw clips")
                
                # Update temp_clip_paths with overlay paths
                generation.temp_clip_paths = overlay_paths
                db.commit()
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=80,
                    current_step="Stitching video clips"
                )
                logger.info(f"[{generation_id}] Progress: 80% - Stitching video clips")
                
                # Check cancellation before stitching
                if check_cancellation():
                    logger.info(f"[{generation_id}] Generation cancelled before stitching")
                    update_generation_status(
                        db=db,
                        generation_id=generation_id,
                        status="failed",
                        error_message="Cancelled by user"
                    )
                    return
                
                # Video Stitching Stage (80% progress)
                logger.info(f"[{generation_id}] Stitching {len(overlay_paths)} video clips together...")
                stitched_output_dir = str(temp_dir / f"{generation_id}_stitched")
                stitched_output_path = str(Path(stitched_output_dir) / "stitched.mp4")
                logger.info(f"[{generation_id}] Stitched video will be saved to: {stitched_output_path}")
                stitched_video_path = stitch_video_clips(
                    clip_paths=overlay_paths,
                    output_path=stitched_output_path,
                    transitions=True,
                    cancellation_check=check_cancellation
                )
                logger.info(f"[{generation_id}] Video stitching completed: {stitched_video_path}")
                
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=90,
                    current_step="Adding audio layer"
                )
                logger.info(f"[{generation_id}] Progress: 90% - Adding audio layer")
                
                # Check cancellation before audio
                if check_cancellation():
                    logger.info(f"[{generation_id}] Generation cancelled before audio")
                    update_generation_status(
                        db=db,
                        generation_id=generation_id,
                        status="failed",
                        error_message="Cancelled by user"
                    )
                    return
                
                # Audio Layer Stage (85-90% progress)
                logger.info(f"[{generation_id}] Starting audio layer addition...")
                # Extract music style from LLM specification
                music_style = "professional"  # Default
                if generation.llm_specification:
                    brand_guidelines = generation.llm_specification.get("brand_guidelines", {})
                    mood = brand_guidelines.get("mood", "professional")
                    music_style = mood.lower() if mood else "professional"
                logger.info(f"[{generation_id}] Selected music style: {music_style}")
                
                audio_output_dir = str(temp_dir / f"{generation_id}_audio")
                audio_output_path = str(Path(audio_output_dir) / "with_audio.mp4")
                logger.info(f"[{generation_id}] Audio output path: {audio_output_path}")
                
                # Pass scene plan for transition detection
                scene_plan_obj = ScenePlan(**generation.scene_plan) if generation.scene_plan else None
                
                video_with_audio = add_audio_layer(
                    video_path=stitched_video_path,
                    music_style=music_style,
                    output_path=audio_output_path,
                    scene_plan=scene_plan_obj,
                    cancellation_check=check_cancellation
                )
                logger.info(f"[{generation_id}] Audio layer added successfully: {video_with_audio}")
                
                # Check cancellation before export
                if check_cancellation():
                    logger.info(f"[{generation_id}] Generation cancelled before export")
                    update_generation_status(
                        db=db,
                        generation_id=generation_id,
                        status="failed",
                        error_message="Cancelled by user"
                    )
                    return
                
                # Post-Processing and Export Stage
                logger.info(f"[{generation_id}] Starting final video export...")
                # Extract brand style from LLM specification
                brand_style = "default"  # Default
                if generation.llm_specification:
                    brand_guidelines = generation.llm_specification.get("brand_guidelines", {})
                    visual_style = brand_guidelines.get("visual_style_keywords", "default")
                    brand_style = visual_style.lower() if visual_style else "default"
                logger.info(f"[{generation_id}] Brand style: {brand_style}")
                
                # Use output directory from config or default
                output_base_dir = "output"
                logger.info(f"[{generation_id}] Exporting to: {output_base_dir}")
                
                video_url, thumbnail_url = export_final_video(
                    video_path=video_with_audio,
                    brand_style=brand_style,
                    output_dir=output_base_dir,
                    generation_id=generation_id,
                    cancellation_check=check_cancellation
                )
                logger.info(f"[{generation_id}] Final video exported - Video URL: {video_url}, Thumbnail URL: {thumbnail_url}")
                
                # Update Generation record with final URLs
                generation.video_url = video_url
                generation.thumbnail_url = thumbnail_url
                generation.completed_at = datetime.utcnow()
                db.commit()
                
                # Mark as completed
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=100,
                    current_step="Complete",
                    status="completed"
                )
                logger.info(f"[{generation_id}] Generation marked as completed in database")
                
                # Clean up temp files
                logger.info(f"[{generation_id}] Starting cleanup of temporary files...")
                try:
                    import shutil
                    temp_gen_dir = temp_dir / generation_id
                    if temp_gen_dir.exists():
                        shutil.rmtree(temp_gen_dir)
                    overlay_dir = temp_dir / f"{generation_id}_overlays"
                    if overlay_dir.exists():
                        shutil.rmtree(overlay_dir)
                    stitched_dir = temp_dir / f"{generation_id}_stitched"
                    if stitched_dir.exists():
                        shutil.rmtree(stitched_dir)
                    audio_dir = temp_dir / f"{generation_id}_audio"
                    if audio_dir.exists():
                        shutil.rmtree(audio_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp files: {e}")
                
                # Track complete generation cost
                track_complete_generation_cost(
                    db=db,
                    generation_id=generation_id,
                    video_cost=total_video_cost,
                    llm_cost=0.01  # Approximate LLM cost
                )
                
                # Update user statistics (total_generations and total_cost)
                # This must be called after track_complete_generation_cost() to ensure generation.cost is set
                update_user_statistics_on_completion(
                    db=db,
                    generation_id=generation_id
                )
                
                logger.info(
                    f"[{generation_id}] ✅ Generation completed successfully! "
                    f"Video: {video_url}, Thumbnail: {thumbnail_url}, Total cost: ${total_video_cost:.4f}"
                )
                
            except RuntimeError as e:
                if "cancelled" in str(e).lower():
                    # Already handled above
                    return
                logger.error(f"Video generation failed for {generation_id}: {e}", exc_info=True)
                update_generation_status(
                    db=db,
                    generation_id=generation_id,
                    status="failed",
                    error_message=str(e)
                )
                
        except ValueError as e:
            logger.error(f"Validation error in generation {generation_id}: {e}")
            update_generation_progress(
                db=db,
                generation_id=generation_id,
                progress=0,
                status="failed"
            )
            update_generation_status(
                db=db,
                generation_id=generation_id,
                status="failed",
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in generation {generation_id}: {e}", exc_info=True)
            update_generation_progress(
                db=db,
                generation_id=generation_id,
                progress=0,
                status="failed"
            )
            update_generation_status(
                db=db,
                generation_id=generation_id,
                status="failed",
                error_message=str(e)
            )
    finally:
        db.close()


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def create_generation(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
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
    
    # Add background task to process the generation
    # Pass model, num_clips, and use_llm if specified
    background_tasks.add_task(
        process_generation, 
        generation_id, 
        request.prompt,
        request.model,
        request.num_clips,
        request.use_llm if request.use_llm is not None else True
    )
    
    # Return immediately - processing happens in background
    return GenerateResponse(
        generation_id=generation_id,
        status="pending",
        message="Video generation started"
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
    
    # Count available clips
    available_clips = len(generation.temp_clip_paths) if generation.temp_clip_paths else 0
    
    # Helper function to convert relative paths to full URLs
    def get_full_url(relative_path: Optional[str]) -> Optional[str]:
        """Convert relative path to full URL for frontend consumption."""
        if not relative_path:
            return None
        from app.core.config import settings
        
        # If already a full URL, return as-is
        if relative_path.startswith("http://") or relative_path.startswith("https://"):
            return relative_path
        
        # If storage mode is S3, generate presigned URL
        if settings.STORAGE_MODE == "s3":
            try:
                from app.services.storage.s3_storage import get_s3_storage
                s3_storage = get_s3_storage()
                # Generate presigned URL (expires in 1 hour)
                presigned_url = s3_storage.generate_presigned_url(relative_path, expiration=3600)
                return presigned_url
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for {relative_path}: {e}, falling back to static URL")
                # Fall back to static URL if S3 fails
                base_url = settings.STATIC_BASE_URL.rstrip("/")
                path = relative_path.lstrip("/")
                return f"{base_url}/{path}"
        else:
            # Convert relative path to full URL (local storage)
            base_url = settings.STATIC_BASE_URL.rstrip("/")
            path = relative_path.lstrip("/")
            return f"{base_url}/{path}"
    
    return StatusResponse(
        generation_id=generation.id,
        status=generation.status,
        progress=generation.progress,
        current_step=generation.current_step,
        video_url=get_full_url(generation.video_url),
        cost=generation.cost,
        error=generation.error_message,
        num_scenes=generation.num_scenes,
        available_clips=available_clips
    )


@router.post("/generations/{generation_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_generation(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StatusResponse:
    """
    Cancel an in-progress video generation.
    
    Args:
        generation_id: UUID of the generation
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        StatusResponse with updated status
    
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
        HTTPException: 400 if generation cannot be cancelled
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
    
    # Check authorization - user can only cancel their own generations
    if generation.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to cancel generation {generation_id} owned by {generation.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to cancel this generation"
                }
            }
        )
    
    # Check if generation can be cancelled
    if generation.status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "CANNOT_CANCEL",
                    "message": f"Cannot cancel generation with status '{generation.status}'"
                }
            }
        )
    
    # Request cancellation
    if not request_cancellation(db, generation_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "CANCELLATION_FAILED",
                    "message": "Failed to request cancellation"
                }
            }
        )
    
    # Handle cancellation (update status, cleanup)
    handle_cancellation(db, generation_id, cleanup_temp_files=True)
    
    # Refresh generation to get updated status
    db.refresh(generation)
    
    # Count available clips
    available_clips = len(generation.temp_clip_paths) if generation.temp_clip_paths else 0
    
    logger.info(f"User {current_user.id} cancelled generation {generation_id}")
    
    return StatusResponse(
        generation_id=generation.id,
        status=generation.status,
        progress=generation.progress,
        current_step=generation.current_step,
        video_url=generation.video_url,
        cost=generation.cost,
        error=generation.error_message,
        num_scenes=generation.num_scenes,
        available_clips=available_clips
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

    # Helper function to convert relative paths to full URLs (reuse same logic as status endpoint)
    def get_full_url(relative_path: Optional[str]) -> Optional[str]:
        """Convert relative path to full URL for frontend consumption."""
        if not relative_path:
            return None
        from app.core.config import settings
        
        # If already a full URL, return as-is
        if relative_path.startswith("http://") or relative_path.startswith("https://"):
            return relative_path
        
        # If storage mode is S3, generate presigned URL
        if settings.STORAGE_MODE == "s3":
            try:
                from app.services.storage.s3_storage import get_s3_storage
                s3_storage = get_s3_storage()
                # Generate presigned URL (expires in 1 hour)
                presigned_url = s3_storage.generate_presigned_url(relative_path, expiration=3600)
                return presigned_url
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for {relative_path}: {e}, falling back to static URL")
                # Fall back to static URL if S3 fails
                base_url = settings.STATIC_BASE_URL.rstrip("/")
                path = relative_path.lstrip("/")
                return f"{base_url}/{path}"
        else:
            # Convert relative path to full URL (local storage)
            base_url = settings.STATIC_BASE_URL.rstrip("/")
            path = relative_path.lstrip("/")
            return f"{base_url}/{path}"
    
    # Convert to Pydantic models
    generation_items = [
        GenerationListItem(
            id=gen.id,
            prompt=gen.prompt,
            status=gen.status,
            video_url=get_full_url(gen.video_url),
            thumbnail_url=get_full_url(gen.thumbnail_url),
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


@router.get("/clips/{generation_id}/{scene_number}")
async def download_clip(
    generation_id: str,
    scene_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FileResponse:
    """
    Download an individual scene clip from a generation.
    
    Args:
        generation_id: UUID of the generation
        scene_number: Scene number (1-based)
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        FileResponse: The video clip file
    
    Raises:
        HTTPException: 404 if generation or clip not found
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
        logger.warning(f"User {current_user.id} attempted to download clip from generation {generation_id} owned by {generation.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to access this generation"
                }
            }
        )
    
    # Check if generation has temp clip paths
    if not generation.temp_clip_paths or scene_number > len(generation.temp_clip_paths):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CLIP_NOT_FOUND",
                    "message": f"Clip {scene_number} not found for this generation"
                }
            }
        )
    
    # Get the clip path (scene_number is 1-based, array is 0-based)
    clip_path = generation.temp_clip_paths[scene_number - 1]
    
    # Check if file exists
    clip_file = Path(clip_path)
    if not clip_file.exists():
        logger.error(f"Clip file not found: {clip_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CLIP_FILE_NOT_FOUND",
                    "message": f"Clip file not found on server"
                }
            }
        )
    
    # Return the file
    filename = f"{generation_id}_scene_{scene_number}.mp4"
    logger.info(f"User {current_user.id} downloading clip {scene_number} from generation {generation_id}")
    
    return FileResponse(
        path=clip_path,
        media_type="video/mp4",
        filename=filename
    )


@router.post("/generate-single-clip", status_code=status.HTTP_202_ACCEPTED)
async def create_single_clip_generation(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GenerateResponse:
    """
    Generate a single video clip without using the full pipeline.
    Bypasses LLM enhancement, scene planning, and stitching.
    
    Args:
        request: GenerateRequest with prompt, model (required), and optional num_clips
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        GenerateResponse with generation_id and status
    
    Raises:
        HTTPException: 422 if validation fails, 400 if model not specified
    """
    if not request.model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "MODEL_REQUIRED",
                    "message": "Model selection is required for single clip generation"
                }
            }
        )
    
    if request.model not in MODEL_COSTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_MODEL",
                    "message": f"Model '{request.model}' is not available. Available models: {list(MODEL_COSTS.keys())}"
                }
            }
        )
    
    logger.info(f"Creating single clip generation for user {current_user.id}, model: {request.model}")
    
    # Create Generation record with status=pending
    generation = Generation(
        user_id=current_user.id,
        prompt=request.prompt,
        status="pending",
        progress=0,
        current_step="Initializing single clip generation"
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)
    
    generation_id = generation.id
    logger.info(f"Created single clip generation {generation_id}")
    
    # Add background task to process the single clip generation
    background_tasks.add_task(
        process_single_clip_generation,
        generation_id,
        request.prompt,
        request.model,
        request.num_clips or 1
    )
    
    # Return immediately - processing happens in background
    return GenerateResponse(
        generation_id=generation_id,
        status="pending",
        message="Single clip generation started"
    )


async def process_single_clip_generation(
    generation_id: str,
    prompt: str,
    model_name: str,
    num_clips: int = 1
):
    """
    Background task to generate single clip(s) without pipeline.
    """
    logger.info(f"[{generation_id}] Starting single clip generation task")
    logger.info(f"[{generation_id}] Model: {model_name}, Clips: {num_clips}, Prompt: {prompt[:100]}...")
    
    # Create a new database session for the background task
    db = SessionLocal()
    try:
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            logger.error(f"[{generation_id}] Generation not found in background task")
            return
        
        try:
            # Update status to processing
            update_generation_progress(
                db=db,
                generation_id=generation_id,
                progress=10,
                current_step="Generating video clip(s)",
                status="processing"
            )
            
            # Setup temp storage directory
            temp_dir = Path("output/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_output_dir = str(temp_dir / generation_id)
            
            # Create cancellation check function
            def check_cancellation() -> bool:
                db.refresh(generation)
                return generation.cancellation_requested if generation else False
            
            clip_paths = []
            total_cost = 0.0
            duration = 5  # Default duration for single clips
            
            # Generate the requested number of clips
            for i in range(1, num_clips + 1):
                if check_cancellation():
                    logger.info(f"[{generation_id}] Generation cancelled before clip {i}")
                    update_generation_status(
                        db=db,
                        generation_id=generation_id,
                        status="failed",
                        error_message="Cancelled by user"
                    )
                    return
                
                progress = int(10 + (i - 1) * (80 / num_clips))
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=progress,
                    current_step=f"Generating clip {i} of {num_clips} with {model_name}"
                )
                
                logger.info(f"[{generation_id}] Generating clip {i}/{num_clips} with model {model_name}")
                
                try:
                    clip_path, model_used = await generate_video_clip_with_model(
                        prompt=prompt,
                        duration=duration,
                        output_dir=temp_output_dir,
                        generation_id=generation_id,
                        model_name=model_name,
                        cancellation_check=check_cancellation,
                        clip_index=i
                    )
                    
                    clip_paths.append(clip_path)
                    clip_cost = MODEL_COSTS.get(model_used, 0.05) * duration
                    total_cost += clip_cost
                    
                    logger.info(f"[{generation_id}] Clip {i} generated: {clip_path} (cost: ${clip_cost:.4f})")
                    
                    # Track cost
                    track_video_generation_cost(
                        db=db,
                        generation_id=generation_id,
                        scene_number=i,
                        cost=clip_cost,
                        model_name=model_used
                    )
                    
                except Exception as e:
                    logger.error(f"[{generation_id}] Failed to generate clip {i}: {e}", exc_info=True)
                    update_generation_status(
                        db=db,
                        generation_id=generation_id,
                        status="failed",
                        error_message=f"Failed to generate clip {i}: {str(e)}"
                    )
                    return
            
            # Store clip paths
            generation.temp_clip_paths = clip_paths
            generation.num_scenes = len(clip_paths)
            db.commit()
            
            # Update progress to completed
            update_generation_progress(
                db=db,
                generation_id=generation_id,
                progress=100,
                current_step="Completed",
                status="completed"
            )
            
            # Update total cost (single clip generation doesn't use LLM, so llm_cost=0)
            track_complete_generation_cost(
                db=db,
                generation_id=generation_id,
                video_cost=total_cost,
                llm_cost=0.0
            )
            
            # Update user statistics
            update_user_statistics_on_completion(db=db, generation_id=generation_id)
            
            logger.info(f"[{generation_id}] Single clip generation completed successfully. Total cost: ${total_cost:.4f}")
            
        except Exception as e:
            logger.error(f"[{generation_id}] Error in single clip generation: {e}", exc_info=True)
            update_generation_status(
                db=db,
                generation_id=generation_id,
                status="failed",
                error_message=str(e)
            )
    finally:
        db.close()


@router.delete("/generations/{generation_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def delete_generation(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """
    Delete a video generation and its associated files.
    
    Args:
        generation_id: UUID of the generation to delete
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        DeleteResponse: Success message and generation_id
    
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user doesn't own the generation
        HTTPException: 404 if generation not found
        HTTPException: 500 if deletion fails
    """
    # Store user_id early to avoid lazy loading issues
    user_id = current_user.id
    logger.info(f"User {user_id} requesting deletion of generation {generation_id}")
    
    # Query the generation (don't need to load user relationship, just check user_id)
    generation = db.query(Generation).filter(Generation.id == generation_id).first()
    
    if not generation:
        logger.warning(f"Generation {generation_id} not found for deletion request by user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GENERATION_NOT_FOUND",
                    "message": "Generation not found"
                }
            }
        )
    
    # Verify ownership
    if generation.user_id != user_id:
        logger.warning(f"User {user_id} attempted to delete generation {generation_id} owned by {generation.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to delete this generation"
                }
            }
        )
    
    try:
        # Delete video file if it exists
        if generation.video_path and os.path.exists(generation.video_path):
            try:
                os.remove(generation.video_path)
                logger.info(f"Deleted video file: {generation.video_path}")
            except FileNotFoundError:
                logger.warning(f"Video file not found (may have been already deleted): {generation.video_path}")
            except Exception as e:
                logger.error(f"Error deleting video file {generation.video_path}: {e}")
                # Continue with deletion even if file deletion fails
        
        # Delete thumbnail file if it exists
        if generation.thumbnail_url:
            try:
                # Parse thumbnail URL - could be file path or HTTP URL
                thumbnail_path = None
                if generation.thumbnail_url.startswith("http://") or generation.thumbnail_url.startswith("https://"):
                    # Extract path from URL if it's a local file URL
                    # For now, skip HTTP URLs (they're served, not stored locally)
                    logger.info(f"Thumbnail is HTTP URL, skipping file deletion: {generation.thumbnail_url}")
                else:
                    # Assume it's a file path
                    thumbnail_path = generation.thumbnail_url
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                        logger.info(f"Deleted thumbnail file: {thumbnail_path}")
                    else:
                        logger.warning(f"Thumbnail file not found (may have been already deleted): {thumbnail_path}")
            except FileNotFoundError:
                logger.warning(f"Thumbnail file not found (may have been already deleted): {generation.thumbnail_url}")
            except Exception as e:
                logger.error(f"Error deleting thumbnail file {generation.thumbnail_url}: {e}")
                # Continue with deletion even if thumbnail deletion fails
        
        # Delete database record
        # Note: We delete by ID to avoid foreign key constraint checks on user relationship
        db.query(Generation).filter(Generation.id == generation_id).delete()
        db.commit()
        
        logger.info(f"Successfully deleted generation {generation_id} for user {user_id}")
        
        return DeleteResponse(
            message="Video deleted successfully",
            generation_id=generation_id
        )
        
    except Exception as e:
        # Log error using stored user_id to avoid triggering user table query
        logger.error(f"Error deleting generation {generation_id} for user {user_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "DELETION_FAILED",
                    "message": "Failed to delete generation"
                }
            }
        )
