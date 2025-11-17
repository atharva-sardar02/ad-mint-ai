"""
Video generation route handlers.
"""
import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user
from app.db.models.generation import Generation, GenerationGroup
from app.db.models.user import User
from app.db.session import SessionLocal, get_db
from app.schemas.generation import (
    AdSpecification,
    CoherenceSettings,
    ComparisonGroupResponse,
    DeleteResponse,
    GenerateRequest,
    GenerateResponse,
    GenerationListResponse,
    GenerationListItem,
    ParallelGenerateRequest,
    ParallelGenerateResponse,
    QualityMetricsResponse,
    QualityMetricDetail,
    Scene,
    ScenePlan,
    StatusResponse,
    VariationDetail,
)
from app.services.coherence_settings import apply_defaults, get_settings_metadata, validate_settings
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
from app.services.pipeline.seed_manager import get_seed_for_generation
from app.services.pipeline.quality_control import evaluate_and_store_quality, regenerate_clip
from app.services.pipeline.time_estimation import estimate_generation_time, format_estimated_time

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
    
    # Track generation start time
    generation_start_time = time.time()
    
    # Create a new database session for the background task
    db = SessionLocal()
    try:
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            logger.error(f"[{generation_id}] Generation not found in background task")
            return
        
        # Store basic settings
        generation.model = preferred_model
        generation.num_clips = num_clips
        generation.use_llm = use_llm
        db.commit()
        
        logger.info(f"[{generation_id}] Generation record found, starting processing")
        logger.info(f"[{generation_id}] Basic settings: model={preferred_model}, num_clips={num_clips}, use_llm={use_llm}")
        
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
            
            # Seed Control: Generate and store seed if seed_control is enabled
            seed = None
            coherence_settings_dict = generation.coherence_settings or {}
            seed_control_enabled = coherence_settings_dict.get("seed_control", True)  # Default to True
            
            if seed_control_enabled:
                logger.info(f"[{generation_id}] Seed control enabled - generating seed for visual consistency")
                try:
                    seed = get_seed_for_generation(db, generation_id)
                    if seed:
                        logger.info(f"[{generation_id}] Using seed {seed} for all scenes in this generation")
                    else:
                        logger.warning(f"[{generation_id}] Seed control enabled but seed generation returned None - continuing without seed")
                except Exception as e:
                    # Seed generation is enhancement, not critical - continue without seed if it fails
                    logger.error(
                        f"[{generation_id}] Error generating seed for generation (database error or other issue): {e}. "
                        f"Continuing generation without seed control.",
                        exc_info=True
                    )
                    seed = None  # Explicitly set to None to ensure no seed is used
            else:
                logger.info(f"[{generation_id}] Seed control disabled - each scene will use different random seed")
            
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
                # Generate all video clips in parallel
                num_scenes = len(scene_plan.scenes)
                progress_start = 30
                progress_end = 70
                use_cache = should_cache_prompt(prompt)
                
                if use_cache:
                    logger.info(f"[{generation_id}] Cache enabled for this prompt")
                
                # Update progress to show we're starting parallel clip generation
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=progress_start,
                    current_step=f"Generating {num_scenes} video clips in parallel"
                )
                logger.info(f"[{generation_id}] Starting parallel generation of {num_scenes} clips")
                
                # Helper function to generate a single clip
                async def generate_single_clip(scene: Scene, scene_index: int) -> tuple[str, str, float, int]:
                    """Generate a single clip and return (clip_path, model_used, cost, scene_number)."""
                    scene_number = scene_index + 1  # 1-based for display
                    
                    # Check cancellation
                    if check_cancellation():
                        raise RuntimeError("Generation cancelled by user")
                    
                    logger.info(f"[{generation_id}] Starting clip {scene_number}/{num_scenes} - Scene type: {scene.scene_type}, Duration: {scene.duration}s")
                    logger.info(f"[{generation_id}] Visual prompt: {scene.visual_prompt[:80]}...")
                    
                    # Check cache first (scene index is 0-based)
                    cached_clip = None
                    model_used = None
                    if use_cache:
                        cached_clip = get_cached_clip(prompt, scene_index)
                    
                    if cached_clip:
                        logger.info(f"[{generation_id}] Using cached clip for scene {scene_number}: {cached_clip}")
                        clip_path = cached_clip
                        clip_cost = 0.0  # Cached clips are free
                        model_used = "cached"  # Mark as cached for logging
                    else:
                        # Update progress to show we're calling the API
                        update_generation_progress(
                            db=db,
                            generation_id=generation_id,
                            progress=progress_start,
                            current_step=f"Calling API for clip {scene_number} of {num_scenes} (parallel generation)"
                        )
                        
                        # Generate video clip
                        logger.info(f"[{generation_id}] Calling Replicate API for clip {scene_number}...")
                        clip_path, model_used = await generate_video_clip(
                            scene=scene,
                            output_dir=temp_output_dir,
                            generation_id=generation_id,
                            scene_number=scene_number,
                            cancellation_check=check_cancellation,
                            seed=seed,  # Pass seed for visual consistency (None if seed_control disabled)
                            preferred_model=preferred_model  # Pass preferred model if specified
                        )
                        logger.info(f"[{generation_id}] Clip {scene_number} generated successfully: {clip_path} (model: {model_used})")
                        
                        # Quality control evaluation (if enabled)
                        quality_passed = True
                        quality_details = {}
                        try:
                            quality_passed, quality_details = await evaluate_and_store_quality(
                                db=db,
                                generation_id=generation_id,
                                scene_number=scene_number,
                                clip_path=clip_path,
                                prompt_text=scene.visual_prompt,
                                coherence_settings=generation.coherence_settings
                            )
                            
                            # Log performance metrics
                            perf_info = quality_details.get("performance", {})
                            if perf_info:
                                eval_time = perf_info.get("evaluation_time_seconds", 0)
                                within_target = perf_info.get("within_target", True)
                                if not within_target:
                                    logger.warning(
                                        f"[{generation_id}] Quality evaluation exceeded target time: "
                                        f"{eval_time:.2f}s > 30s for clip {scene_number}"
                                    )
                            
                            if not quality_passed and not quality_details.get("skipped", False):
                                # Check if automatic regeneration is enabled in coherence settings
                                coherence_settings_dict = generation.coherence_settings or {}
                                automatic_regeneration_enabled = coherence_settings_dict.get("automatic_regeneration", False)
                                
                                # Log quality issue (metrics are stored, available via API)
                                logger.warning(
                                    f"[{generation_id}] Clip {scene_number} quality below threshold "
                                    f"(overall: {quality_details.get('scores', {}).get('overall_quality', 0):.2f}). "
                                    f"Quality metrics stored. Automatic regeneration: {'enabled' if automatic_regeneration_enabled else 'disabled'}."
                                )
                                
                                # Only trigger regeneration if explicitly enabled in coherence settings
                                if automatic_regeneration_enabled:
                                    logger.info(
                                        f"[{generation_id}] Automatic regeneration enabled. Triggering regeneration for clip {scene_number}."
                                    )
                                    
                                    # Update progress to show regeneration
                                    update_generation_progress(
                                        db=db,
                                        generation_id=generation_id,
                                        progress=progress_start,
                                        current_step=f"Regenerating clip {scene_number} due to quality issues"
                                    )
                                    
                                    # Attempt regeneration
                                    try:
                                        regenerated_clip_path, regen_success, regen_details = await regenerate_clip(
                                            db=db,
                                            generation_id=generation_id,
                                            scene_number=scene_number,
                                            scene=scene,
                                            output_dir=temp_output_dir,
                                            original_clip_path=clip_path,
                                            prompt_text=scene.visual_prompt,
                                            coherence_settings=generation.coherence_settings,
                                            cancellation_check=check_cancellation,
                                            seed=seed,
                                            preferred_model=preferred_model,
                                            max_attempts=3
                                        )
                                        
                                        if regenerated_clip_path and regen_success:
                                            # Use regenerated clip
                                            clip_path = regenerated_clip_path
                                            logger.info(
                                                f"[{generation_id}] Regeneration successful for clip {scene_number}. "
                                                f"New quality: {regen_details.get('overall_quality', 0):.2f}"
                                            )
                                        elif regenerated_clip_path:
                                            # Regeneration completed but quality still below threshold
                                            clip_path = regenerated_clip_path
                                            logger.warning(
                                                f"[{generation_id}] Regeneration completed for clip {scene_number} "
                                                f"but quality still below threshold. Using best available clip."
                                            )
                                        else:
                                            # Regeneration failed - use original clip
                                            logger.error(
                                                f"[{generation_id}] Regeneration failed for clip {scene_number}. "
                                                f"Using original clip despite quality issues."
                                            )
                                            
                                    except Exception as regen_error:
                                        logger.error(
                                            f"[{generation_id}] Error during regeneration for clip {scene_number}: {regen_error}",
                                            exc_info=True
                                        )
                                        # Continue with original clip on regeneration failure
                                else:
                                    # Automatic regeneration disabled - continue with original clip
                                    # Quality metrics are already stored and available via API
                                    logger.info(
                                        f"[{generation_id}] Continuing with clip {scene_number} despite quality below threshold. "
                                        f"Quality metrics available for review via API."
                                    )
                        except Exception as e:
                            logger.error(f"[{generation_id}] Quality evaluation failed for clip {scene_number}: {e}", exc_info=True)
                            # Graceful degradation: continue even if quality assessment fails
                            quality_passed = True
                        
                        # Cache the clip if caching is enabled
                        if use_cache:
                            cache_clip(prompt, scene_index, clip_path)
                        
                        # Calculate cost using the actual model that was used
                        model_cost_per_sec = MODEL_COSTS.get(model_used, 0.05)
                        clip_cost = model_cost_per_sec * scene.duration
                        logger.info(f"[{generation_id}] Clip {scene_number} cost calculated: ${clip_cost:.4f} (model: {model_used}, ${model_cost_per_sec}/sec × {scene.duration}s)")
                    
                    # Track cost with actual model used (only for non-cached clips)
                    if not cached_clip:
                        track_video_generation_cost(
                            db=db,
                            generation_id=generation_id,
                            scene_number=scene_number,
                            cost=clip_cost,
                            model_name=model_used
                        )
                    
                    return (clip_path, model_used, clip_cost, scene_number)
                
                # Generate all clips in parallel using asyncio.gather
                clip_tasks = [
                    generate_single_clip(scene, i) 
                    for i, scene in enumerate(scene_plan.scenes)
                ]
                
                # Wait for all clips to complete (in parallel)
                clip_results = await asyncio.gather(*clip_tasks, return_exceptions=True)
                
                # Process results and handle any errors
                clip_paths = []
                total_video_cost = 0.0
                completed_clips = 0
                
                for result in clip_results:
                    if isinstance(result, Exception):
                        logger.error(f"[{generation_id}] Clip generation failed: {result}", exc_info=True)
                        if "cancelled" in str(result).lower():
                            update_generation_status(
                                db=db,
                                generation_id=generation_id,
                                status="failed",
                                error_message="Cancelled by user"
                            )
                            return
                        raise result
                    
                    clip_path, model_used, clip_cost, scene_number = result
                    clip_paths.append(clip_path)
                    total_video_cost += clip_cost
                    completed_clips += 1
                    
                    logger.info(f"[{generation_id}] Clip {scene_number} completed: ${clip_cost:.4f}, total cost so far: ${total_video_cost:.4f} (model: {model_used})")
                    
                    # Update progress as clips complete
                    progress = int(progress_start + (completed_clips * (progress_end - progress_start) / num_scenes))
                    update_generation_progress(
                        db=db,
                        generation_id=generation_id,
                        progress=progress,
                        current_step=f"Completed {completed_clips}/{num_scenes} clips (parallel generation)"
                    )
                
                # Sort clip_paths by scene number to maintain order
                # Since clips are generated in parallel, they may complete out of order
                # We need to ensure they're ordered by scene number (1, 2, 3, ...)
                clip_paths_ordered = [None] * num_scenes
                for result in clip_results:
                    if not isinstance(result, Exception):
                        clip_path, _, _, scene_number = result
                        clip_paths_ordered[scene_number - 1] = clip_path
                
                # Filter out None values and ensure we have all clips
                clip_paths = [cp for cp in clip_paths_ordered if cp is not None]
                
                if len(clip_paths) != num_scenes:
                    logger.warning(
                        f"[{generation_id}] Expected {num_scenes} clips but got {len(clip_paths)}. "
                        f"Some clips may have failed."
                    )
                
                logger.info(f"[{generation_id}] All {len(clip_paths)} clips generated in parallel, total cost: ${total_video_cost:.4f}")
                
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
                
                # Check if color grading is enabled in coherence settings
                coherence_settings_dict = generation.coherence_settings or {}
                apply_color_grading = coherence_settings_dict.get("color_grading", False)
                logger.info(f"[{generation_id}] Color grading enabled: {apply_color_grading}")
                
                # Use output directory from config or default
                output_base_dir = "output"
                logger.info(f"[{generation_id}] Exporting to: {output_base_dir}")
                
                video_url, thumbnail_url = export_final_video(
                    video_path=video_with_audio,
                    brand_style=brand_style,
                    output_dir=output_base_dir,
                    generation_id=generation_id,
                    cancellation_check=check_cancellation,
                    apply_color_grading=apply_color_grading
                )
                logger.info(f"[{generation_id}] Final video exported - Video URL: {video_url}, Thumbnail URL: {thumbnail_url}")
                
                # Calculate generation time
                generation_elapsed = int(time.time() - generation_start_time)
                
                # Update Generation record with final URLs and generation time
                generation.video_url = video_url
                generation.thumbnail_url = thumbnail_url
                generation.completed_at = datetime.utcnow()
                generation.generation_time_seconds = generation_elapsed
                db.commit()
                
                logger.info(f"[{generation_id}] Generation completed in {generation_elapsed} seconds")
                
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
        request: GenerateRequest with prompt (minimum 10 characters)
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        GenerateResponse with generation_id and status
    
    Raises:
        HTTPException: 422 if validation fails (handled by FastAPI)
        HTTPException: 500 if LLM or scene planning fails
    """
    logger.info(f"Creating generation for user {current_user.id}, prompt length: {len(request.prompt)}")
    
    # Process coherence settings: apply defaults if not provided, validate if provided
    coherence_settings_dict = None
    if request.coherence_settings:
        # Validate provided settings
        is_valid, error_message = validate_settings(request.coherence_settings)
        if not is_valid:
            logger.warning(f"Invalid coherence settings: {error_message}")
            # Apply defaults instead of failing - backward compatibility
            coherence_settings = apply_defaults(None)
        else:
            coherence_settings = request.coherence_settings
        coherence_settings_dict = coherence_settings.model_dump()
    else:
        # Apply defaults if not provided
        coherence_settings = apply_defaults(None)
        coherence_settings_dict = coherence_settings.model_dump()
    
    logger.info(f"Coherence settings: {coherence_settings_dict}")
    
    # Create Generation record with status=pending
    generation = Generation(
        user_id=current_user.id,
        title=request.title,
        prompt=request.prompt,
        status="pending",
        progress=0,
        current_step="Initializing",
        coherence_settings=coherence_settings_dict
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
    
    return GenerateResponse(
        generation_id=generation_id,
        status="pending",
        message="Video generation started",
    )


@router.post("/generate/parallel", status_code=status.HTTP_202_ACCEPTED)
async def create_parallel_generation(
    request: ParallelGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ParallelGenerateResponse:
    """
    Start multiple video generations in parallel for comparison.
    
    Args:
        request: ParallelGenerateRequest with variations array (2-5) and comparison_type
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        ParallelGenerateResponse with group_id, generation_ids, and status
    
    Raises:
        HTTPException: 422 if validation fails (variation count, prompt length, coherence settings)
        HTTPException: 429 if rate limit exceeded
        HTTPException: 500 if group creation fails
    """
    logger.info(f"Creating parallel generation for user {current_user.id}, {len(request.variations)} variations, type: {request.comparison_type}")
    
    # Validate variation count (2-10)
    if len(request.variations) < 2 or len(request.variations) > 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "INVALID_VARIATION_COUNT",
                    "message": "Number of variations must be between 2 and 10"
                }
            }
        )
    
    # Validate all prompts
    for i, variation in enumerate(request.variations):
        if len(variation.prompt) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_PROMPT_LENGTH",
                        "message": f"Variation {i+1}: Prompt must be at least 10 characters"
                    }
                }
            )
        
        # Validate coherence settings if provided
        if variation.coherence_settings:
            is_valid, error_message = validate_settings(variation.coherence_settings)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {
                            "code": "INVALID_COHERENCE_SETTINGS",
                            "message": f"Variation {i+1}: {error_message}"
                        }
                    }
                )
    
    # Rate limiting: Check user's generation count in the last hour (PRD: 10 videos/hour per user)
    # For parallel generation, count each variation as a video
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_generation_count = db.query(func.count(Generation.id)).filter(
        Generation.user_id == current_user.id,
        Generation.created_at >= one_hour_ago
    ).scalar() or 0
    
    # Check if adding new variations would exceed the limit
    total_requested = len(request.variations)
    if recent_generation_count + total_requested > 10:
        remaining = max(0, 10 - recent_generation_count)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. You can generate {remaining} more video(s) in the next hour. (Limit: 10 videos/hour)"
                }
            }
        )
    
    # Create generation_group record
    try:
        generation_group = GenerationGroup(
            user_id=current_user.id,
            comparison_type=request.comparison_type
        )
        db.add(generation_group)
        db.commit()
        db.refresh(generation_group)
        group_id = generation_group.id
        logger.info(f"Created generation group {group_id}")
    except Exception as e:
        logger.error(f"Failed to create generation group: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "GROUP_CREATION_FAILED",
                    "message": "Failed to create generation group"
                }
            }
        )
    
    # Create generation records for each variation
    generation_ids = []
    errors = []
    
    for i, variation in enumerate(request.variations):
        try:
            # Process coherence settings: apply defaults if not provided, validate if provided
            coherence_settings_dict = None
            if variation.coherence_settings:
                coherence_settings = variation.coherence_settings
                coherence_settings_dict = coherence_settings.model_dump()
            else:
                # Apply defaults if not provided
                coherence_settings = apply_defaults(None)
                coherence_settings_dict = coherence_settings.model_dump()
            
            # Create Generation record with status=pending
            # Generate title from variation if not provided: "Variation {letter}" or use prompt preview
            variation_title = variation.title if hasattr(variation, 'title') and variation.title else None
            if not variation_title:
                # Auto-generate title based on variation index
                variation_letter = chr(65 + i)  # A, B, C, etc.
                variation_title = f"Variation {variation_letter}"
            
            generation = Generation(
                user_id=current_user.id,
                title=variation_title,
                prompt=variation.prompt,
                status="pending",
                progress=0,
                current_step="Initializing",
                coherence_settings=coherence_settings_dict,
                generation_group_id=group_id
            )
            db.add(generation)
            db.commit()
            db.refresh(generation)
            
            generation_ids.append(generation.id)
            logger.info(f"Created generation {generation.id} for variation {i+1}")
            
            # Start generation task concurrently using asyncio
            # This allows true parallel processing instead of sequential BackgroundTasks
            # The task will run in the background even after the response is sent
            # Extract per-variation settings
            variation_model = variation.model if hasattr(variation, 'model') else None
            variation_num_clips = variation.num_clips if hasattr(variation, 'num_clips') else None
            variation_use_llm = variation.use_llm if hasattr(variation, 'use_llm') else True
            
            # Determine if this is single clip generation (bypass pipeline)
            # Single clip mode: model is required, num_clips is set, and use_llm is False
            is_single_clip = (
                variation_model is not None and 
                variation_num_clips is not None and 
                variation_num_clips > 0 and
                variation_use_llm is False
            )
            
            if is_single_clip:
                # Use single clip generation (bypasses entire pipeline)
                if variation_model not in MODEL_COSTS:
                    logger.warning(f"Invalid model {variation_model} for variation {i+1}, skipping single clip generation")
                    errors.append(f"Variation {i+1}: Invalid model for single clip generation")
                    continue
                
                asyncio.create_task(process_single_clip_generation(
                    generation.id,
                    variation.prompt,
                    variation_model,
                    variation_num_clips
                ))
                logger.info(f"Started single clip generation task for generation {generation.id} (variation {i+1})")
            else:
                # Use full pipeline generation
                asyncio.create_task(process_generation(
                    generation.id, 
                    variation.prompt,
                    preferred_model=variation_model,
                    num_clips=variation_num_clips,
                    use_llm=variation_use_llm
                ))
                logger.info(f"Started full pipeline generation task for generation {generation.id} (variation {i+1})")
            
        except Exception as e:
            logger.error(f"Failed to create generation for variation {i+1}: {e}")
            errors.append(f"Variation {i+1}: {str(e)}")
            # Continue with other variations even if one fails
    
    # If all variations failed, return error
    if len(generation_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ALL_VARIATIONS_FAILED",
                    "message": "Failed to create any generation variations",
                    "errors": errors
                }
            }
        )
    
    # Log any partial failures
    if errors:
        logger.warning(f"Generation group {group_id} created with {len(errors)} failed variations: {errors}")
    
    logger.info(f"Created parallel generation group {group_id} with {len(generation_ids)} variations")
    
    # Calculate estimated generation time
    estimated_seconds = estimate_generation_time(request.variations, parallel=True)
    estimated_time_formatted = format_estimated_time(estimated_seconds)
    
    # Return immediately - processing happens in background
    return ParallelGenerateResponse(
        group_id=group_id,
        generation_ids=generation_ids,
        status="pending",
        message=f"Parallel generation started with {len(generation_ids)} variations",
        estimated_time_seconds=estimated_seconds,
        estimated_time_formatted=estimated_time_formatted
    )


@router.get("/queue", status_code=status.HTTP_200_OK)
async def get_generation_queue(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of active generations to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current queue of active video generations (pending and processing).
    Shows what's currently being generated to verify parallel execution.
    
    Args:
        limit: Maximum number of active generations to return (default: 50, max: 200)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Dict with active generations grouped by status, showing:
        - pending: Generations waiting to start
        - processing: Generations currently being processed
        - Each generation shows: id, title, prompt preview, progress, current_step, created_at
    """
    # Get active generations for the user (limit to most recent for performance)
    active_generations = db.query(Generation).filter(
        Generation.user_id == current_user.id,
        Generation.status.in_(["pending", "processing"])
    ).order_by(Generation.created_at.desc()).limit(limit).all()
    
    # Group by status
    pending = []
    processing = []
    
    for gen in active_generations:
        gen_info = {
            "id": gen.id,
            "title": gen.title,
            "prompt": gen.prompt[:100] + "..." if len(gen.prompt) > 100 else gen.prompt,
            "progress": gen.progress,
            "current_step": gen.current_step,
            "status": gen.status,
            "created_at": gen.created_at.isoformat() if gen.created_at else None,
            "num_scenes": gen.num_scenes,
            "generation_group_id": gen.generation_group_id,
        }
        
        if gen.status == "pending":
            pending.append(gen_info)
        elif gen.status == "processing":
            processing.append(gen_info)
    
    return {
        "pending": pending,
        "processing": processing,
        "total_active": len(active_generations),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/coherence/settings/defaults", status_code=status.HTTP_200_OK)
async def get_coherence_settings_defaults():
    """
    Get default coherence settings with metadata (recommended, cost impact, time impact, descriptions).
    
    Returns:
        Dict: Default coherence settings with metadata for each technique
    """
    metadata = get_settings_metadata()
    return metadata


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
    def get_public_path(relative_path: Optional[str]) -> Optional[str]:
        """Convert stored path to a public relative path."""
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
        video_url=get_public_path(generation.video_url),
        cost=generation.cost,
        error=generation.error_message,
        num_scenes=generation.num_scenes,
        available_clips=available_clips,
        seed_value=generation.seed_value
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
        available_clips=available_clips,
        seed_value=generation.seed_value
    )


@router.get("/comparison/{group_id}", response_model=ComparisonGroupResponse, status_code=status.HTTP_200_OK)
async def get_comparison_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ComparisonGroupResponse:
    """
    Get comparison group with all variations and metadata.
    
    Args:
        group_id: UUID of the generation group
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        ComparisonGroupResponse with all variations, metadata, and comparison details
    
    Raises:
        HTTPException: 404 if group not found
        HTTPException: 403 if user doesn't own the group
    """
    # Query generation group
    generation_group = db.query(GenerationGroup).filter(GenerationGroup.id == group_id).first()
    
    if not generation_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "GROUP_NOT_FOUND",
                    "message": "Generation group not found"
                }
            }
        )
    
    # Check authorization - user can only access their own comparison groups
    if generation_group.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to access generation group {group_id} owned by {generation_group.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You don't have permission to access this comparison group"
                }
            }
        )
    
    # Query all generations in the group
    generations = db.query(Generation).filter(Generation.generation_group_id == group_id).order_by(Generation.created_at).all()
    
    if not generations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NO_VARIATIONS_FOUND",
                    "message": "No variations found in this comparison group"
                }
            }
        )
    
    # Helper function to convert relative paths to full URLs
    def get_full_url(relative_path: Optional[str]) -> Optional[str]:
        """Convert relative path to full URL for frontend consumption."""
        if not relative_path:
            return None
        from app.core.config import settings
        # If already a full URL, return as-is
        if relative_path.startswith("http://") or relative_path.startswith("https://"):
            return relative_path
        # Convert relative path to full URL
        base_url = settings.STATIC_BASE_URL.rstrip("/")
        path = relative_path.lstrip("/")
        return f"{base_url}/{path}"
    
    # Build variations list
    variations = []
    total_cost = 0.0
    
    for gen in generations:
        # Calculate cost (default to 0 if not set)
        cost = gen.cost if gen.cost is not None else 0.0
        total_cost += cost
        
        variation = VariationDetail(
            generation_id=gen.id,
            prompt=gen.prompt,
            coherence_settings=gen.coherence_settings,
            status=gen.status,
            progress=gen.progress,
            video_url=get_full_url(gen.video_url),
            thumbnail_url=get_full_url(gen.thumbnail_url),
            cost=cost,
            generation_time_seconds=gen.generation_time_seconds,
            error_message=gen.error_message
        )
        variations.append(variation)
    
    # Calculate differences between variations
    differences = {}
    
    if generation_group.comparison_type == "settings":
        # For settings comparison: show which settings differ
        # Compare coherence_settings across all variations
        if len(variations) > 1:
            first_settings = variations[0].coherence_settings or {}
            differing_settings = {}
            
            for i, variation in enumerate(variations[1:], start=1):
                current_settings = variation.coherence_settings or {}
                for key in set(list(first_settings.keys()) + list(current_settings.keys())):
                    if first_settings.get(key) != current_settings.get(key):
                        if key not in differing_settings:
                            differing_settings[key] = {
                                "variation_0": first_settings.get(key),
                                f"variation_{i}": current_settings.get(key)
                            }
                        else:
                            differing_settings[key][f"variation_{i}"] = current_settings.get(key)
            
            if differing_settings:
                differences["settings"] = differing_settings
    
    elif generation_group.comparison_type == "prompt":
        # For prompt comparison: show prompt differences
        prompts = [v.prompt for v in variations]
        differences["prompts"] = prompts
    
    logger.debug(f"User {current_user.id} retrieved comparison group {group_id} with {len(variations)} variations")
    
    return ComparisonGroupResponse(
        group_id=group_id,
        comparison_type=generation_group.comparison_type,
        variations=variations,
        total_cost=total_cost,
        differences=differences if differences else None
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

    # Get total count before pagination (optimized: use count on primary key)
    total = query.with_entities(func.count(Generation.id)).scalar() or 0

    # Apply sorting
    if sort == "created_at_asc":
        query = query.order_by(Generation.created_at.asc())
    else:  # default to created_at_desc (newest first)
        query = query.order_by(Generation.created_at.desc())

    # Apply pagination
    generations = query.offset(offset).limit(limit).all()

    # Helper function to convert relative paths to full URLs (optimized for performance)
    def get_full_url(relative_path: Optional[str], skip_s3: bool = False) -> Optional[str]:
        """
        Convert relative path to full URL for frontend consumption.
        
        Args:
            relative_path: Relative file path
            skip_s3: If True, skip S3 presigned URL generation and return static URL (faster)
        """
        if not relative_path:
            return None
        from app.core.config import settings
        
        # If already a full URL, return as-is
        if relative_path.startswith("http://") or relative_path.startswith("https://"):
            return relative_path
        
        # If storage mode is S3 and we're not skipping
        if settings.STORAGE_MODE == "s3" and not skip_s3:
            try:
                from app.services.storage.s3_storage import get_s3_storage
                s3_storage = get_s3_storage()
                # Generate presigned URL (expires in 1 hour)
                presigned_url = s3_storage.generate_presigned_url(relative_path, expiration=3600)
                return presigned_url
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for {relative_path}: {e}, falling back to static URL")
                # Fall back to static URL if S3 fails
                base_url = settings.STATIC_BASE_URL.rstrip("/") if settings.STATIC_BASE_URL else ""
                path = relative_path.lstrip("/")
                return f"{base_url}/{path}" if base_url else relative_path
        else:
            # Convert relative path to full URL (local storage or S3 with skip_s3=True)
            base_url = settings.STATIC_BASE_URL.rstrip("/") if settings.STATIC_BASE_URL else ""
            path = relative_path.lstrip("/")
            return f"{base_url}/{path}" if base_url else relative_path
    
    # Pre-fetch variation labels for all generations in groups (optimize N+1 queries)
    # Get unique group IDs from the current page of generations
    group_ids = [gen.generation_group_id for gen in generations if gen.generation_group_id]
    group_ids = list(set(group_ids))  # Remove duplicates and convert to list
    
    # Fetch all generations in these groups, ordered by creation time
    group_generations_map = {}
    if group_ids:
        try:
            all_group_generations = db.query(Generation).filter(
                Generation.generation_group_id.in_(group_ids)
            ).order_by(Generation.created_at).all()
            
            # Group by generation_group_id and create index maps
            for group_id in group_ids:
                group_gens = [g for g in all_group_generations if g.generation_group_id == group_id]
                # Sort by created_at to ensure consistent ordering
                group_gens.sort(key=lambda g: g.created_at)
                # Create a map of generation_id -> index for quick lookup
                group_generations_map[group_id] = {
                    gen.id: idx for idx, gen in enumerate(group_gens)
                }
        except Exception as e:
            logger.error(f"Error fetching group generations: {e}")
            # Continue without variation labels if there's an error
    
    # Convert to Pydantic models
    # Optimize: Only generate S3 presigned URLs for completed videos (they have files)
    # For pending/processing videos, skip expensive S3 URL generation
    generation_items = []
    for gen in generations:
        # Calculate variation label if part of a parallel generation group
        variation_label = None
        if gen.generation_group_id and gen.generation_group_id in group_generations_map:
            idx = group_generations_map[gen.generation_group_id].get(gen.id)
            if idx is not None:
                # Convert index to letter (0 -> A, 1 -> B, etc.)
                variation_label = chr(65 + idx)  # 65 is ASCII for 'A'
        
        # Only generate S3 presigned URLs for completed videos (performance optimization)
        # Pending/processing videos don't have videos/thumbnails yet, so skip expensive S3 calls
        skip_s3_urls = gen.status not in ["completed"]
        
        generation_items.append(
            GenerationListItem(
                id=gen.id,
                title=gen.title,
                prompt=gen.prompt,
                status=gen.status,
                video_url=get_full_url(gen.video_url, skip_s3=skip_s3_urls),
                thumbnail_url=get_full_url(gen.thumbnail_url, skip_s3=skip_s3_urls),
                duration=gen.duration,
                cost=gen.cost,
                created_at=gen.created_at,
                completed_at=gen.completed_at,
                generation_group_id=gen.generation_group_id,
                variation_label=variation_label,
                coherence_settings=gen.coherence_settings,
                parent_generation_id=gen.parent_generation_id,
                model=gen.model,
                num_clips=gen.num_clips,
                use_llm=gen.use_llm,
                generation_time_seconds=gen.generation_time_seconds,
            )
        )

    logger.debug(
        f"User {current_user.id} retrieved {len(generation_items)} generations "
        f"(total: {total}, offset: {offset}, limit: {limit})"
    )

    return GenerationListResponse(
        total=total,
        limit=limit,
        offset=offset,
        generations=generation_items,
    )


@router.get("/generations/{generation_id}", response_model=GenerationListItem, status_code=status.HTTP_200_OK)
async def get_generation(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GenerationListItem:
    """
    Get a single video generation by ID.
    
    Args:
        generation_id: UUID of the generation
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        GenerationListItem with generation details
    
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
    
    # Helper function to convert relative paths to full URLs (reuse from get_generations)
    def get_full_url(relative_path: Optional[str], skip_s3: bool = False) -> Optional[str]:
        """Convert relative path to full URL for frontend consumption."""
        if not relative_path:
            return None
        from app.core.config import settings
        
        # If already a full URL, return as-is
        if relative_path.startswith("http://") or relative_path.startswith("https://"):
            return relative_path
        
        # If storage mode is S3 and we're not skipping
        if settings.STORAGE_MODE == "s3" and not skip_s3:
            try:
                from app.services.storage.s3_storage import get_s3_storage
                s3_storage = get_s3_storage()
                presigned_url = s3_storage.generate_presigned_url(relative_path, expiration=3600)
                return presigned_url
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for {relative_path}: {e}, falling back to static URL")
                base_url = settings.STATIC_BASE_URL.rstrip("/") if settings.STATIC_BASE_URL else ""
                path = relative_path.lstrip("/")
                return f"{base_url}/{path}" if base_url else relative_path
        else:
            base_url = settings.STATIC_BASE_URL.rstrip("/") if settings.STATIC_BASE_URL else ""
            path = relative_path.lstrip("/")
            return f"{base_url}/{path}" if base_url else relative_path
    
    # Calculate variation label if part of a parallel generation group
    variation_label = None
    if generation.generation_group_id:
        try:
            # Get all generations in the same group, ordered by creation time
            group_generations = db.query(Generation).filter(
                Generation.generation_group_id == generation.generation_group_id
            ).order_by(Generation.created_at).all()
            
            # Find index of this generation in the group
            for idx, gen in enumerate(group_generations):
                if gen.id == generation.id:
                    variation_label = chr(65 + idx)  # 65 is ASCII for 'A'
                    break
        except Exception as e:
            logger.error(f"Error calculating variation label: {e}")
    
    # Only generate S3 presigned URLs for completed videos
    skip_s3_urls = generation.status not in ["completed"]
    
    return GenerationListItem(
        id=generation.id,
        title=generation.title,
        prompt=generation.prompt,
        status=generation.status,
        video_url=get_full_url(generation.video_url, skip_s3=skip_s3_urls),
        thumbnail_url=get_full_url(generation.thumbnail_url, skip_s3=skip_s3_urls),
        duration=generation.duration,
        cost=generation.cost,
        created_at=generation.created_at,
        completed_at=generation.completed_at,
        generation_group_id=generation.generation_group_id,
        variation_label=variation_label,
        coherence_settings=generation.coherence_settings,
        parent_generation_id=generation.parent_generation_id,
        model=generation.model,
        num_clips=generation.num_clips,
        use_llm=generation.use_llm,
        generation_time_seconds=generation.generation_time_seconds,
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


@router.get("/generations/{generation_id}/quality", response_model=QualityMetricsResponse, status_code=status.HTTP_200_OK)
async def get_generation_quality_metrics(
    generation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QualityMetricsResponse:
    """
    Get quality metrics for all clips in a generation.
    
    Args:
        generation_id: UUID of the generation
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        QualityMetricsResponse with quality metrics for all clips and summary statistics
    
    Raises:
        HTTPException: 404 if generation not found
        HTTPException: 403 if user doesn't own the generation
    """
    from app.db.models.quality_metric import QualityMetric
    
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
    
    # Check authorization - user can only access their own quality metrics
    if generation.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to access quality metrics for generation {generation_id} owned by {generation.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You can only access quality metrics for your own generations"
                }
            }
        )
    
    # Query quality metrics for this generation
    quality_metrics = db.query(QualityMetric).filter(
        QualityMetric.generation_id == generation_id
    ).order_by(QualityMetric.scene_number.asc()).all()
    
    if not quality_metrics:
        # Return empty response if no quality metrics found
        return QualityMetricsResponse(
            generation_id=generation_id,
            clips=[],
            summary={
                "average_quality": 0.0,
                "total_clips": 0,
                "passed_count": 0,
                "failed_count": 0,
            }
        )
    
    # Convert to response format
    clip_details = [
        QualityMetricDetail(
            scene_number=metric.scene_number,
            clip_path=metric.clip_path,
            vbench_scores=metric.vbench_scores,
            overall_quality=metric.overall_quality,
            passed_threshold=metric.passed_threshold,
            regeneration_attempts=metric.regeneration_attempts,
            created_at=metric.created_at,
        )
        for metric in quality_metrics
    ]
    
    # Calculate summary statistics
    total_clips = len(quality_metrics)
    passed_count = sum(1 for m in quality_metrics if m.passed_threshold)
    failed_count = total_clips - passed_count
    average_quality = sum(m.overall_quality for m in quality_metrics) / total_clips if total_clips > 0 else 0.0
    
    logger.debug(
        f"User {current_user.id} retrieved quality metrics for generation {generation_id}: "
        f"{total_clips} clips, {passed_count} passed, {failed_count} failed, avg quality: {average_quality:.2f}"
    )
    
    return QualityMetricsResponse(
        generation_id=generation_id,
        clips=clip_details,
        summary={
            "average_quality": round(average_quality, 2),
            "total_clips": total_clips,
            "passed_count": passed_count,
            "failed_count": failed_count,
        }
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
    
    # Track generation start time
    generation_start_time = time.time()
    
    # Create a new database session for the background task
    db = SessionLocal()
    try:
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            logger.error(f"[{generation_id}] Generation not found in background task")
            return
        
        # Store basic settings
        generation.model = model_name
        generation.num_clips = num_clips
        generation.use_llm = False  # Single clip mode doesn't use LLM
        db.commit()
        
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
            
            # Update progress to show we're starting parallel clip generation
            update_generation_progress(
                db=db,
                generation_id=generation_id,
                progress=10,
                current_step=f"Generating {num_clips} clips in parallel with {model_name}"
            )
            logger.info(f"[{generation_id}] Starting parallel generation of {num_clips} clips")
            
            # Helper function to generate a single clip
            async def generate_single_clip_parallel(clip_index: int) -> tuple[str, str, float]:
                """Generate a single clip and return (clip_path, model_used, cost)."""
                # Check cancellation
                if check_cancellation():
                    raise RuntimeError("Generation cancelled by user")
                
                logger.info(f"[{generation_id}] Starting clip {clip_index}/{num_clips} with model {model_name}")
                
                clip_path, model_used = await generate_video_clip_with_model(
                    prompt=prompt,
                    duration=duration,
                    output_dir=temp_output_dir,
                    generation_id=generation_id,
                    model_name=model_name,
                    cancellation_check=check_cancellation,
                    clip_index=clip_index
                )
                
                clip_cost = MODEL_COSTS.get(model_used, 0.05) * duration
                logger.info(f"[{generation_id}] Clip {clip_index} generated: {clip_path} (cost: ${clip_cost:.4f})")
                
                # Track cost
                track_video_generation_cost(
                    db=db,
                    generation_id=generation_id,
                    scene_number=clip_index,
                    cost=clip_cost,
                    model_name=model_used
                )
                
                return (clip_path, model_used, clip_cost)
            
            # Generate all clips in parallel using asyncio.gather
            clip_tasks = [
                generate_single_clip_parallel(i) 
                for i in range(1, num_clips + 1)
            ]
            
            # Wait for all clips to complete (in parallel)
            clip_results = await asyncio.gather(*clip_tasks, return_exceptions=True)
            
            # Process results and handle any errors
            completed_clips = 0
            
            for i, result in enumerate(clip_results, start=1):
                if isinstance(result, Exception):
                    logger.error(f"[{generation_id}] Clip {i} generation failed: {result}", exc_info=True)
                    if "cancelled" in str(result).lower():
                        update_generation_status(
                            db=db,
                            generation_id=generation_id,
                            status="failed",
                            error_message="Cancelled by user"
                        )
                        return
                    update_generation_status(
                        db=db,
                        generation_id=generation_id,
                        status="failed",
                        error_message=f"Failed to generate clip {i}: {str(result)}"
                    )
                    return
                
                clip_path, model_used, clip_cost = result
                clip_paths.append(clip_path)
                total_cost += clip_cost
                completed_clips += 1
                
                logger.info(f"[{generation_id}] Clip {i} completed: ${clip_cost:.4f}, total cost so far: ${total_cost:.4f}")
                
                # Update progress as clips complete
                progress = int(10 + (completed_clips * 80 / num_clips))
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=progress,
                    current_step=f"Completed {completed_clips}/{num_clips} clips (parallel generation)"
                )
            
            logger.info(f"[{generation_id}] All {len(clip_paths)} clips generated in parallel, total cost: ${total_cost:.4f}")
            
            # Store clip paths
            generation.temp_clip_paths = clip_paths
            generation.num_scenes = len(clip_paths)
            
            # Calculate generation time
            generation_elapsed = int(time.time() - generation_start_time)
            generation.generation_time_seconds = generation_elapsed
            generation.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"[{generation_id}] Single clip generation completed in {generation_elapsed} seconds")
            
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
