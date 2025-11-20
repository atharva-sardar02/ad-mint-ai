"""
Video generation route handlers.
"""

import asyncio
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
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
from app.services.pipeline.overlays import add_overlays_to_clips, extract_brand_name, add_brand_overlay_to_final_video
from app.services.pipeline.scene_planning import plan_scenes, create_basic_scene_plan_from_prompt
from app.services.pipeline.stitching import stitch_video_clips
from app.services.pipeline.audio import add_audio_layer
from app.services.pipeline.export import export_final_video
from app.services.pipeline.cache import get_cached_clip, cache_clip, should_cache_prompt
from app.services.pipeline.video_generation import (
    generate_video_clip,
    generate_video_clip_with_model,
)
from app.services.video_generation_standalone import (
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
    target_duration: Optional[int] = None,
    use_llm: bool = True,
    image_path: Optional[str] = None,
    refinement_instructions: Optional[dict] = None,
    brand_name: Optional[str] = None,
    use_advanced_image_generation: bool = False,
    advanced_image_quality_threshold: float = 30.0,
    advanced_image_num_variations: int = 4,
    advanced_image_max_enhancement_iterations: int = 4,
):
    """
    Background task to process video generation.
    This runs asynchronously after the API returns a response.
    """
    logger.info(f"[{generation_id}] ========== STARTING GENERATION TASK ==========")
    logger.info(f"[{generation_id}] Parameters received:")
    logger.info(f"[{generation_id}]   - prompt: {prompt[:100]}...")
    logger.info(f"[{generation_id}]   - preferred_model: {preferred_model}")
    logger.info(f"[{generation_id}]   - target_duration: {target_duration}")
    logger.info(f"[{generation_id}]   - use_llm: {use_llm}")
    logger.info(f"[{generation_id}]   - image_path: {image_path}")
    logger.info(f"[{generation_id}]   - refinement_instructions: {refinement_instructions}")
    logger.info(f"[{generation_id}]   - brand_name: {brand_name}")
    
    # Track generation start time
    generation_start_time = time.time()
    
    # Create a new database session for the background task
    logger.info(f"[{generation_id}] Creating database session...")
    db = SessionLocal()
    try:
        logger.info(f"[{generation_id}] Querying generation record from database...")
        generation = db.query(Generation).filter(Generation.id == generation_id).first()
        if not generation:
            logger.error(f"[{generation_id}] ❌ Generation not found in background task - generation_id: {generation_id}")
            return
        
        logger.info(f"[{generation_id}] ✅ Generation record found: id={generation.id}, status={generation.status}, user_id={generation.user_id}")
        
        # Use target_duration if provided, otherwise default to 15 seconds
        target_duration_seconds = target_duration if target_duration and target_duration > 0 else 15
        logger.info(f"[{generation_id}] Setting generation parameters: model={preferred_model}, target_duration={target_duration_seconds}s, use_llm={use_llm}")
        generation.model = preferred_model
        generation.use_llm = use_llm
        db.commit()
        logger.info(f"[{generation_id}] ✅ Generation parameters saved to database")
        
        logger.info(f"[{generation_id}] ========== STARTING PROCESSING ==========")
        logger.info(f"[{generation_id}] Basic settings: model={preferred_model}, target_duration={target_duration_seconds}s, use_llm={use_llm}")
        
        try:
            # STEP 1: Plan detailed storyboard using LLM
            # This creates detailed prompts for each scene that will be used for both images and videos
            from app.services.pipeline.storyboard_planner import plan_storyboard
            from app.services.pipeline.image_generation import generate_image
            from app.services.pipeline.image_generation_batch import (
                generate_images_with_sequential_references,
                generate_enhanced_reference_images_with_sequential_references,
                _build_enhanced_image_prompt
            )
            
            storyboard_plan = None
            consistency_markers = None
            scene_detailed_prompts = []
            
            if use_llm:
                # Update status to storyboard planning
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=5,
                    current_step="Storyboard Planning",
                    status="processing"
                )
                logger.info(f"[{generation_id}] Status updated: processing (5%) - Storyboard Planning")
                
                logger.info(f"[{generation_id}] Planning detailed storyboard with LLM...")
                logger.info(f"[{generation_id}] Calling plan_storyboard with:")
                logger.info(f"[{generation_id}]   - user_prompt: {prompt[:100]}...")
                logger.info(f"[{generation_id}]   - reference_image_path: {image_path}")
                logger.info(f"[{generation_id}]   - target_duration: {target_duration_seconds}")
                try:
                    # LLM will decide number of scenes based on target_duration
                    logger.info(f"[{generation_id}] ⏳ Awaiting plan_storyboard()...")
                    storyboard_plan = await plan_storyboard(
                        user_prompt=prompt,
                        reference_image_path=image_path,
                        target_duration=target_duration_seconds,
                    )
                    logger.info(f"[{generation_id}] ✅ plan_storyboard() completed successfully")
                    logger.info(f"[{generation_id}] Storyboard plan keys: {list(storyboard_plan.keys()) if storyboard_plan else 'None'}")
                    
                    # Extract consistency markers and detailed prompts
                    consistency_markers = storyboard_plan.get("consistency_markers", {})
                    scenes = storyboard_plan.get("scenes", [])
                    
                    # Extract detailed prompts for video generation (keep for backward compatibility)
                    scene_detailed_prompts = [
                        scene.get("detailed_prompt", "") 
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    
                    # Extract enhanced image generation prompts (new detailed prompts for better cohesion)
                    # Fallback to detailed_prompt if image_generation_prompt not available
                    scene_image_generation_prompts = [
                        scene.get("image_generation_prompt") or scene.get("detailed_prompt", "")
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    
                    # Extract continuity notes and consistency guidelines for enhanced prompts
                    scene_continuity_notes = [
                        scene.get("image_continuity_notes", "")
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    scene_consistency_guidelines = [
                        scene.get("visual_consistency_guidelines", "")
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    scene_transition_notes = [
                        scene.get("scene_transition_notes", "")
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    
                    # Extract start and end image prompts for Kling 2.5 Turbo
                    scene_start_prompts = [
                        scene.get("start_image_prompt", "") 
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    scene_end_prompts = [
                        scene.get("end_image_prompt", "") 
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    
                    # Extract subject presence information for each scene
                    scene_subject_presence = [
                        scene.get("subject_presence", "full")  # Default to "full" for backward compatibility
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    scene_subject_timing = [
                        scene.get("subject_appearance_timing", "")
                        for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                    ]
                    
                    logger.info(f"[{generation_id}] ✅ Storyboard plan created with {len(scenes)} detailed scenes")
                    logger.info(f"[{generation_id}] Consistency markers: {consistency_markers}")
                    
                    # OPTIONAL REFINEMENT STEP: Refine specific scenes or prompts if requested
                    # This allows fine-tuning before generating images/videos
                    # Can be triggered via API parameter or manual review
                    if refinement_instructions:
                        logger.info(f"[{generation_id}] Refining storyboard based on instructions: {refinement_instructions}")
                        from app.services.pipeline.storyboard_planner import refine_storyboard_prompts
                        try:
                            storyboard_plan = await refine_storyboard_prompts(
                                storyboard_plan=storyboard_plan,
                                refinement_instructions=refinement_instructions,
                                max_retries=2,
                            )
                            # Re-extract prompts after refinement
                            scenes = storyboard_plan.get("scenes", [])
                            scene_detailed_prompts = [
                                scene.get("detailed_prompt", "") 
                                for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                            ]
                            scene_image_generation_prompts = [
                                scene.get("image_generation_prompt") or scene.get("detailed_prompt", "")
                                for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                            ]
                            scene_continuity_notes = [
                                scene.get("image_continuity_notes", "")
                                for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                            ]
                            scene_consistency_guidelines = [
                                scene.get("visual_consistency_guidelines", "")
                                for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                            ]
                            scene_transition_notes = [
                                scene.get("scene_transition_notes", "")
                                for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                            ]
                            scene_start_prompts = [
                                scene.get("start_image_prompt", "") 
                                for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                            ]
                            scene_end_prompts = [
                                scene.get("end_image_prompt", "") 
                                for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                            ]
                            logger.info(f"[{generation_id}] ✅ Storyboard refined successfully")
                        except Exception as e:
                            logger.warning(f"[{generation_id}] Storyboard refinement failed: {e}. Continuing with original storyboard.")
                    
                    # Store storyboard plan and markers
                    if generation.coherence_settings is None:
                        generation.coherence_settings = {}
                    generation.coherence_settings["consistency_markers"] = consistency_markers
                    generation.coherence_settings["storyboard_plan"] = storyboard_plan
                    db.commit()
                    logger.info(f"[{generation_id}] ✅ Storyboard plan saved to coherence_settings with {len(scenes)} scenes")
                    
                except Exception as e:
                    logger.error(f"[{generation_id}] ❌ Failed to plan storyboard: {e}", exc_info=True)
                    logger.error(f"[{generation_id}] Exception type: {type(e).__name__}")
                    logger.error(f"[{generation_id}] Exception message: {str(e)}")
                    logger.warning(f"[{generation_id}] Falling back to basic scene plan without LLM enhancement")
                    # Fall through to basic scene plan creation below
                    storyboard_plan = None
                    consistency_markers = None
                    scene_detailed_prompts = []
                    scene_start_prompts = []
                    scene_end_prompts = []
            
            # STEP 2: Generate images (reference, start, end) using detailed prompts + markers + sequential references
            if storyboard_plan and scene_detailed_prompts:
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=15,
                    current_step="Generating Reference Images",
                    status="processing"
                )
                logger.info(f"[{generation_id}] Status updated: processing (15%) - Generating Reference Images")
                
                # Setup image output directory
                image_dir = Path("output/temp/images") / generation_id
                image_dir.mkdir(parents=True, exist_ok=True)
                
                logger.info(f"[{generation_id}] Generating {len(scene_image_generation_prompts)} enhanced reference images with prompt enhancement and quality scoring...")
                try:
                    # Generate enhanced reference images with prompt enhancement, quality scoring, and sequential chaining
                    # STEP: Use user's provided image as the FIRST reference image directly
                    # All subsequent images will be generated using sequential chaining starting from user's image
                    user_initial_reference = image_path if image_path else None
                    
                    # Enhance reference image prompts based on subject_presence
                    enhanced_reference_prompts = []
                    for idx, prompt in enumerate(scene_image_generation_prompts):
                        subject_presence = scene_subject_presence[idx] if idx < len(scene_subject_presence) else "full"
                        if subject_presence == "none":
                            # Add instruction that this scene does NOT include the subject
                            enhanced_prompt = f"{prompt} | IMPORTANT: This scene does NOT include the main subject. Focus on environment, atmosphere, and supporting elements. Maintain visual style consistency with other scenes."
                            enhanced_reference_prompts.append(enhanced_prompt)
                        else:
                            # Subject is present - use original prompt
                            enhanced_reference_prompts.append(prompt)
                    
                    # Generate reference images for each scene
                    # If user provided an image, use it directly as the first reference image
                    # Then generate remaining images using sequential chaining starting from user's image
                    if user_initial_reference:
                        logger.info(f"[{generation_id}] User provided reference image - using it directly as first scene reference image")
                        logger.info(f"[{generation_id}] All subsequent reference images will be generated using sequential chaining for consistency")
                        
                        # Copy user's image to the first scene reference image location
                        user_ref_path = Path(user_initial_reference)
                        if user_ref_path.exists():
                            # Copy user's image to scene 1 reference location
                            first_scene_ref_path = image_dir / f"{generation_id}_scene_1.png"
                            shutil.copy2(user_ref_path, first_scene_ref_path)
                            first_reference_image = str(first_scene_ref_path)
                            logger.info(f"[{generation_id}] ✅ Copied user's reference image to first scene: {first_reference_image}")
                            
                            # Generate remaining reference images (scenes 2, 3, etc.) using sequential chaining
                            # Start the chain with the user's image
                            if len(enhanced_reference_prompts) > 1:
                                remaining_prompts = enhanced_reference_prompts[1:]  # Skip first prompt (using user's image)
                                
                                if use_advanced_image_generation:
                                    logger.info(f"[{generation_id}] 🚀 ADVANCED IMAGE GENERATION enabled for remaining scenes...")
                                    remaining_reference_images = await generate_enhanced_reference_images_with_sequential_references(
                                        prompts=remaining_prompts,
                                        output_dir=str(image_dir),
                                        generation_id=generation_id,
                                        consistency_markers=consistency_markers,
                                        continuity_notes=scene_continuity_notes[1:] if scene_continuity_notes and len(scene_continuity_notes) > 1 else None,
                                        consistency_guidelines=scene_consistency_guidelines[1:] if scene_consistency_guidelines and len(scene_consistency_guidelines) > 1 else None,
                                        transition_notes=scene_transition_notes[1:] if scene_transition_notes and len(scene_transition_notes) > 1 else None,
                                        initial_reference_image=first_reference_image,  # Start chain with user's image
                                        cancellation_check=lambda: db.query(Generation).filter(Generation.id == generation_id).first().cancellation_requested if db.query(Generation).filter(Generation.id == generation_id).first() else False,
                                        quality_threshold=advanced_image_quality_threshold,
                                        num_variations=advanced_image_num_variations,
                                        max_enhancement_iterations=advanced_image_max_enhancement_iterations,
                                        scene_offset=1,  # Start from scene 2 (idx 1)
                                    )
                                    logger.info(f"[{generation_id}] ✅ Generated {len(remaining_reference_images)} remaining reference images with ADVANCED mode")
                                else:
                                    remaining_reference_images = await generate_images_with_sequential_references(
                                        prompts=remaining_prompts,
                                        output_dir=str(image_dir),
                                        generation_id=generation_id,
                                        consistency_markers=consistency_markers,
                                        continuity_notes=scene_continuity_notes[1:] if scene_continuity_notes and len(scene_continuity_notes) > 1 else None,
                                        consistency_guidelines=scene_consistency_guidelines[1:] if scene_consistency_guidelines and len(scene_consistency_guidelines) > 1 else None,
                                        transition_notes=scene_transition_notes[1:] if scene_transition_notes and len(scene_transition_notes) > 1 else None,
                                        initial_reference_image=first_reference_image,  # Start chain with user's image
                                        cancellation_check=lambda: db.query(Generation).filter(Generation.id == generation_id).first().cancellation_requested if db.query(Generation).filter(Generation.id == generation_id).first() else False,
                                        scene_offset=1,  # Start from scene 2 (idx 1)
                                    )
                                    logger.info(f"[{generation_id}] ✅ Generated {len(remaining_reference_images)} remaining reference images with sequential chaining")
                                
                                # Combine: user's image (first) + generated images (remaining)
                                reference_image_paths = [first_reference_image] + remaining_reference_images
                            else:
                                # Only one scene - just use user's image
                                reference_image_paths = [first_reference_image]
                            
                            logger.info(f"[{generation_id}] ✅ Total {len(reference_image_paths)} reference images: user's image (scene 1) + {len(reference_image_paths) - 1} generated images")
                        else:
                            logger.warning(f"[{generation_id}] User reference image not found: {user_initial_reference}, falling back to sequential generation")
                            user_initial_reference = None  # Fall through to sequential generation
                    else:
                        # Fallback: Use sequential chaining if no master reference
                        # Check if advanced image generation is enabled
                        
                        if use_advanced_image_generation:
                            logger.info(f"[{generation_id}] 🚀 ADVANCED IMAGE GENERATION enabled - using prompt enhancement & quality scoring...")
                            logger.info(f"[{generation_id}] Settings: num_variations={advanced_image_num_variations}, quality_threshold={advanced_image_quality_threshold}, max_iterations={advanced_image_max_enhancement_iterations}")
                            
                            reference_image_paths = await generate_enhanced_reference_images_with_sequential_references(
                                prompts=enhanced_reference_prompts,  # Use enhanced prompts that respect subject_presence
                                output_dir=str(image_dir),
                                generation_id=generation_id,
                                consistency_markers=consistency_markers,
                                continuity_notes=scene_continuity_notes,
                                consistency_guidelines=scene_consistency_guidelines,
                                transition_notes=scene_transition_notes,
                                initial_reference_image=None,  # No initial reference in fallback mode
                                cancellation_check=lambda: db.query(Generation).filter(Generation.id == generation_id).first().cancellation_requested if db.query(Generation).filter(Generation.id == generation_id).first() else False,
                                quality_threshold=advanced_image_quality_threshold,
                                num_variations=advanced_image_num_variations,
                                max_enhancement_iterations=advanced_image_max_enhancement_iterations,
                            )
                            
                            logger.info(f"[{generation_id}] ✅ Generated {len(reference_image_paths)} reference images with ADVANCED mode (2-agent enhancement + 4-model scoring + best selection)")
                        else:
                            logger.info(f"[{generation_id}] Using standard sequential chaining for scene reference images...")
                            reference_image_paths = await generate_images_with_sequential_references(
                                prompts=enhanced_reference_prompts,  # Use enhanced prompts that respect subject_presence
                                output_dir=str(image_dir),
                                generation_id=generation_id,
                                consistency_markers=consistency_markers,
                                continuity_notes=scene_continuity_notes,
                                consistency_guidelines=scene_consistency_guidelines,
                                transition_notes=scene_transition_notes,
                                initial_reference_image=None,  # No initial reference in fallback mode
                                cancellation_check=lambda: db.query(Generation).filter(Generation.id == generation_id).first().cancellation_requested if db.query(Generation).filter(Generation.id == generation_id).first() else False,
                            )
                            
                            logger.info(f"[{generation_id}] ✅ Generated {len(reference_image_paths)} reference images with sequential chaining (coherent across all scenes)")
                    
                    # Generate start images (for Kling 2.5 Turbo) - SEQUENTIALLY for visual cohesion
                    # CRITICAL: Generate ALL start images in one sequential batch to maintain visual cohesion
                    # Start Image 1 → Start Image 2 → Start Image 3 → Start Image 4 (each uses previous as reference)
                    # Strategy: Start with Scene 1's reference image, then chain start images sequentially
                    # IMPORTANT: Respect subject_presence - enhance prompts accordingly
                    start_image_paths = []
                    if scene_start_prompts:
                        logger.info(f"[{generation_id}] Generating {len(scene_start_prompts)} start images SEQUENTIALLY (unique moments, visually cohesive)...")
                        
                        # Build enhanced prompts for all start images
                        enhanced_start_prompts = []
                        for idx, start_prompt in enumerate(scene_start_prompts):
                            subject_presence = scene_subject_presence[idx] if idx < len(scene_subject_presence) else "full"
                            subject_timing = scene_subject_timing[idx] if idx < len(scene_subject_timing) else ""
                            
                            # Determine if subject should be in start image based on subject_presence
                            subject_in_start = subject_presence in ("full", "appears_at_start", "appears_mid_scene") or (
                                subject_presence == "partial" and "start" in subject_timing.lower()
                            )
                            
                            if subject_in_start:
                                logger.info(f"[{generation_id}] Start image {idx+1} - subject appears at start, maintaining visual cohesion")
                                enhanced_start_prompt = f"{start_prompt} | CRITICAL: Maintain exact visual consistency with the reference image - same subject appearance, same colors, same lighting, same style. This is a different moment/pose but must look like it's from the same visual universe."
                            else:
                                logger.info(f"[{generation_id}] Start image {idx+1} - subject does NOT appear at start (subject_presence: {subject_presence})")
                                # Subject not in start frame - emphasize style consistency but no subject
                                enhanced_start_prompt = f"{start_prompt} | CRITICAL: Maintain exact visual consistency with the reference image for style, colors, lighting, and environment - but this frame does NOT include the subject. This is an establishing shot or scene before subject appears."
                            
                            enhanced_start_prompts.append(enhanced_start_prompt)
                        
                        # Generate ALL start images sequentially in one batch
                        # Use Scene 1's reference image (user's image if provided) as the initial reference to start the chain
                        initial_start_reference = reference_image_paths[0] if reference_image_paths else None
                        if user_initial_reference and initial_start_reference:
                            # If user provided image, use it directly as initial reference for start images
                            # This ensures start images are consistent with user's image
                            initial_start_reference = reference_image_paths[0]  # This is the user's image (copied to scene 1 location)
                            logger.info(f"[{generation_id}] Using user's reference image as initial reference for start images")
                        start_image_paths = await generate_images_with_sequential_references(
                            prompts=enhanced_start_prompts,  # All start prompts at once
                            output_dir=str(image_dir / "start"),
                            generation_id=generation_id,
                            consistency_markers=consistency_markers,
                            continuity_notes=None,  # Start frames don't need continuity notes
                            consistency_guidelines=scene_consistency_guidelines if scene_consistency_guidelines else None,
                            transition_notes=None,  # Start frames don't need transition notes
                            initial_reference_image=initial_start_reference,  # Use Scene 1's reference (user's image) to start the chain
                            cancellation_check=lambda: db.query(Generation).filter(Generation.id == generation_id).first().cancellation_requested if db.query(Generation).filter(Generation.id == generation_id).first() else False,
                            scene_offset=0,  # Start from 1 (idx+1 happens inside generate_images_with_sequential_references)
                        )
                        logger.info(f"[{generation_id}] ✅ Generated {len(start_image_paths)} start images SEQUENTIALLY (unique moments, visually cohesive, subject presence respected)")
                    
                    # Generate end images (for Kling 2.5 Turbo) - SEQUENTIALLY for visual cohesion
                    # CRITICAL: Generate ALL end images in one sequential batch to maintain visual cohesion
                    # End Image 1 → End Image 2 → End Image 3 → End Image 4 (each uses previous as reference)
                    # Strategy: Start with Scene 1's reference image, then chain end images sequentially
                    # IMPORTANT: Respect subject_presence - enhance prompts accordingly
                    end_image_paths = []
                    if scene_end_prompts:
                        logger.info(f"[{generation_id}] Generating {len(scene_end_prompts)} end images SEQUENTIALLY (unique moments, visually cohesive)...")
                        
                        # Build enhanced prompts for all end images
                        enhanced_end_prompts = []
                        for idx, end_prompt in enumerate(scene_end_prompts):
                            subject_presence = scene_subject_presence[idx] if idx < len(scene_subject_presence) else "full"
                            subject_timing = scene_subject_timing[idx] if idx < len(scene_subject_timing) else ""
                            
                            # Determine if subject should be in end image based on subject_presence
                            subject_in_end = subject_presence in ("full", "appears_at_end", "appears_mid_scene") or (
                                subject_presence == "partial" and ("end" in subject_timing.lower() or "until end" in subject_timing.lower())
                            )
                            
                            if subject_in_end:
                                logger.info(f"[{generation_id}] End image {idx+1} - subject appears at end, maintaining visual cohesion")
                                enhanced_end_prompt = f"{end_prompt} | CRITICAL: Maintain exact visual consistency with the reference image - same subject appearance, same colors, same lighting, same style. This is a different moment/pose but must look like it's from the same visual universe."
                            else:
                                logger.info(f"[{generation_id}] End image {idx+1} - subject does NOT appear at end (subject_presence: {subject_presence})")
                                # Subject not in end frame - emphasize style consistency but no subject
                                enhanced_end_prompt = f"{end_prompt} | CRITICAL: Maintain exact visual consistency with the reference image for style, colors, lighting, and environment - but this frame does NOT include the subject. This is a scene after subject has exited or before subject appears."
                            
                            enhanced_end_prompts.append(enhanced_end_prompt)
                        
                        # Generate ALL end images sequentially in one batch
                        # Use Scene 1's reference image (user's image if provided) as the initial reference to start the chain
                        initial_end_reference = reference_image_paths[0] if reference_image_paths else None
                        if user_initial_reference and initial_end_reference:
                            # If user provided image, use it directly as initial reference for end images
                            # This ensures end images are consistent with user's image
                            initial_end_reference = reference_image_paths[0]  # This is the user's image (copied to scene 1 location)
                            logger.info(f"[{generation_id}] Using user's reference image as initial reference for end images")
                        end_image_paths = await generate_images_with_sequential_references(
                            prompts=enhanced_end_prompts,  # All end prompts at once
                            output_dir=str(image_dir / "end"),
                            generation_id=generation_id,
                            consistency_markers=consistency_markers,
                            continuity_notes=None,  # End frames don't need continuity notes
                            consistency_guidelines=scene_consistency_guidelines if scene_consistency_guidelines else None,
                            transition_notes=None,  # End frames don't need transition notes
                            initial_reference_image=initial_end_reference,  # Use Scene 1's reference (user's image) to start the chain
                            cancellation_check=lambda: db.query(Generation).filter(Generation.id == generation_id).first().cancellation_requested if db.query(Generation).filter(Generation.id == generation_id).first() else False,
                            scene_offset=0,  # Start from 1 (idx+1 happens inside generate_images_with_sequential_references)
                        )
                        logger.info(f"[{generation_id}] ✅ Generated {len(end_image_paths)} end images SEQUENTIALLY (unique moments, visually cohesive, subject presence respected)")
                    
                    # Store image paths and enhanced prompts in storyboard plan
                    from app.services.pipeline.image_generation_batch import _build_enhanced_image_prompt
                    import os
                    
                    def normalize_path(path: str) -> str:
                        """Convert absolute path to relative path for storage."""
                        if not path:
                            return path
                        # If already relative, return as-is
                        if not os.path.isabs(path):
                            return path
                        # Convert absolute path to relative
                        # Paths are like: D:\gauntlet-ai\ad-mint-ai\backend\output\temp\images\...
                        # We want: output/temp/images/...
                        backend_dir = Path(__file__).parent.parent.parent  # backend directory
                        try:
                            relative_path = os.path.relpath(path, backend_dir)
                            # Normalize to forward slashes for URLs
                            return relative_path.replace("\\", "/")
                        except ValueError:
                            # If path is on different drive (Windows), extract the relative part
                            # Find "output" in the path and take everything from there
                            if "output" in path:
                                idx = path.find("output")
                                return path[idx:].replace("\\", "/")
                            return path.replace("\\", "/")
                    
                    for idx, scene in enumerate(storyboard_plan.get("scenes", [])):
                        if idx < len(reference_image_paths):
                            scene["reference_image_path"] = normalize_path(reference_image_paths[idx])
                            # Store the actual enhanced prompt used for image generation
                            # Use image_generation_prompt if available, otherwise fallback to detailed_prompt
                            base_prompt = scene.get("image_generation_prompt") or scene.get("detailed_prompt", "")
                            continuity_note = scene_continuity_notes[idx] if idx < len(scene_continuity_notes) else None
                            consistency_guideline = scene_consistency_guidelines[idx] if idx < len(scene_consistency_guidelines) else None
                            transition_note = scene_transition_notes[idx] if idx < len(scene_transition_notes) else None
                            scene["reference_image_prompt"] = _build_enhanced_image_prompt(
                                base_prompt=base_prompt,
                                consistency_markers=consistency_markers,
                                continuity_note=continuity_note,
                                consistency_guideline=consistency_guideline,
                                transition_note=transition_note,
                                scene_number=idx + 1,
                            )
                        
                        if idx < len(start_image_paths):
                            scene["start_image_path"] = normalize_path(start_image_paths[idx])
                            # Store the actual enhanced prompt used for start image generation
                            base_prompt = scene.get("start_image_prompt", "")
                            consistency_guideline = scene_consistency_guidelines[idx] if idx < len(scene_consistency_guidelines) else None
                            scene["start_image_enhanced_prompt"] = _build_enhanced_image_prompt(
                                base_prompt=base_prompt,
                                consistency_markers=consistency_markers,
                                continuity_note=None,  # Start frames don't need continuity
                                consistency_guideline=consistency_guideline,
                                transition_note=None,  # Start frames don't need transition
                                scene_number=idx + 1,
                            )
                        
                        if idx < len(end_image_paths):
                            scene["end_image_path"] = normalize_path(end_image_paths[idx])
                            # Store the actual enhanced prompt used for end image generation
                            base_prompt = scene.get("end_image_prompt", "")
                            consistency_guideline = scene_consistency_guidelines[idx] if idx < len(scene_consistency_guidelines) else None
                            scene["end_image_enhanced_prompt"] = _build_enhanced_image_prompt(
                                base_prompt=base_prompt,
                                consistency_markers=consistency_markers,
                                continuity_note=None,  # End frames don't need continuity
                                consistency_guideline=consistency_guideline,
                                transition_note=None,  # End frames don't need transition
                                scene_number=idx + 1,
                            )
                    
                    # Ensure coherence_settings exists before updating
                    if generation.coherence_settings is None:
                        generation.coherence_settings = {}
                    generation.coherence_settings["storyboard_plan"] = storyboard_plan
                    db.commit()
                    logger.info(f"[{generation_id}] ✅ Storyboard plan updated with image paths and saved to coherence_settings")
                    
                except Exception as e:
                    logger.error(f"[{generation_id}] Failed to generate images: {e}", exc_info=True)
                    raise
            
            # STEP 3: Create scene plan from storyboard for video generation
            if storyboard_plan:
                scenes_data = storyboard_plan.get("scenes", [])
                scenes = []
                
                for scene_data in scenes_data:
                    detailed_prompt = scene_data.get("detailed_prompt", "")
                    reference_image_path = scene_data.get("reference_image_path")
                    start_image_path = scene_data.get("start_image_path")
                    end_image_path = scene_data.get("end_image_path")
                    
                    # Create Scene object with detailed prompt and images
                    scenes.append(
                        Scene(
                            scene_number=scene_data.get("scene_number", 0),
                            scene_type=scene_data.get("aida_stage", "Scene"),
                            visual_prompt=detailed_prompt,  # Use detailed prompt from storyboard
                            model_prompts={},  # Can be populated later if needed
                            reference_image_path=reference_image_path,  # Generated reference image
                            start_image_path=start_image_path,  # Generated start image (for Kling 2.5 Turbo)
                            end_image_path=end_image_path,  # Generated end image (for Kling 2.5 Turbo)
                            text_overlay=None,  # Can be added later
                            duration=int(scene_data.get("duration_seconds", 4)),
                            sound_design=None,  # Can be added later
                        )
                    )
                
                scene_plan = ScenePlan(
                    scenes=scenes,
                    total_duration=sum(s.duration for s in scenes),
                    framework="AIDA",
                )
                
                logger.info(f"[{generation_id}] Scene plan created from storyboard: {len(scenes)} scenes")
            else:
                # Fallback: Create basic scene plan without LLM (when storyboard planning fails or use_llm is False)
                logger.info(f"[{generation_id}] Creating basic scene plan without LLM enhancement")
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=10,
                    current_step="Creating Basic Scene Plan",
                    status="processing"
                )
                
                # Create basic scene plan from prompt
                # For basic scene plan (fallback), use target_duration
                from app.services.pipeline.scene_planning import create_basic_scene_plan_from_prompt
                scene_plan = create_basic_scene_plan_from_prompt(
                    prompt=prompt,
                    target_duration=target_duration_seconds,
                    num_scenes=None  # Let it decide based on target_duration
                )
                logger.info(f"[{generation_id}] Basic scene plan created: {len(scene_plan.scenes)} scenes")
                
                # Store basic specification
                generation.framework = scene_plan.framework
                generation.llm_specification = None  # No LLM spec when disabled
                db.commit()
            
            logger.info(f"[{generation_id}] Scene planning completed - {len(scene_plan.scenes)} scenes planned, total duration: {scene_plan.total_duration}s")
            
            # No need to limit scenes - LLM has already decided based on target_duration
            logger.info(f"[{generation_id}] Using {len(scene_plan.scenes)} scenes as planned by LLM, total duration: {scene_plan.total_duration}s")
            
            # Store scene plan
            scene_plan_dict = scene_plan.model_dump()
            
            # Add advanced image generation metadata to scene plan
            scene_plan_dict['advanced_image_generation_used'] = use_advanced_image_generation
            if use_advanced_image_generation:
                scene_plan_dict['advanced_image_settings'] = {
                    'quality_threshold': advanced_image_quality_threshold,
                    'num_variations': advanced_image_num_variations,
                    'max_enhancement_iterations': advanced_image_max_enhancement_iterations
                }
            
            generation.scene_plan = scene_plan_dict
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
                        # IMPORTANT: For Kling 2.5 Turbo Pro, prioritize start_image and end_image for frame control
                        # Each scene should have its OWN start_image and end_image (different frames for each scene)
                        # Reference image is used for style/character consistency but doesn't override start/end frames
                        # CRITICAL: Respect subject_presence - only use reference image if subject should be in the scene
                        scene_data_from_storyboard = None
                        if storyboard_plan and "scenes" in storyboard_plan:
                            scenes_list = storyboard_plan.get("scenes", [])
                            scene_idx = scene_number - 1
                            if 0 <= scene_idx < len(scenes_list):
                                scene_data_from_storyboard = scenes_list[scene_idx]
                        
                        subject_presence = scene_data_from_storyboard.get("subject_presence", "full") if scene_data_from_storyboard else "full"
                        subject_timing = scene_data_from_storyboard.get("subject_appearance_timing", "") if scene_data_from_storyboard else ""
                        
                        # Determine which images to use based on subject_presence
                        scene_reference_image = None
                        if subject_presence != "none":
                            # Only use reference image if subject appears in this scene
                            scene_reference_image = scene.reference_image_path if scene.reference_image_path else (image_path if subject_presence == "full" else None)
                        
                        scene_start_image = scene.start_image_path  # Each scene has its own start image (different first frame)
                        scene_end_image = scene.end_image_path  # Each scene has its own end image (different last frame)
                        
                        logger.info(f"[{generation_id}] Calling Replicate API for clip {scene_number}...")
                        logger.info(f"[{generation_id}] Using detailed prompt: {scene.visual_prompt[:100]}...")
                        logger.info(f"[{generation_id}] Scene {scene_number} subject_presence: {subject_presence}")
                        logger.info(f"[{generation_id}] Scene {scene_number} images:")
                        if scene_reference_image:
                            logger.info(f"[{generation_id}]   - Reference image (style consistency, subject present): {scene_reference_image}")
                        else:
                            logger.info(f"[{generation_id}]   - No reference image (subject_presence='{subject_presence}' - scene doesn't include subject)")
                        if scene_start_image:
                            logger.info(f"[{generation_id}]   - Start image (first frame - UNIQUE to this scene): {scene_start_image}")
                        else:
                            logger.warning(f"[{generation_id}]   - No start image for scene {scene_number} - video will start from prompt")
                        if scene_end_image:
                            logger.info(f"[{generation_id}]   - End image (last frame - UNIQUE to this scene): {scene_end_image}")
                        else:
                            logger.warning(f"[{generation_id}]   - No end image for scene {scene_number} - video will end from prompt")
                        
                        clip_path, model_used = await generate_video_clip(
                            scene=scene,
                            output_dir=temp_output_dir,
                            generation_id=generation_id,
                            scene_number=scene_number,
                            cancellation_check=check_cancellation,
                            seed=seed,  # Pass seed for visual consistency (None if seed_control disabled)
                            preferred_model=preferred_model,  # Pass preferred model if specified
                            # PRIORITY: start_image and end_image control the actual frames (each scene has different frames)
                            # reference_image is for style consistency (shared subject/style across scenes)
                            start_image_path=scene_start_image,  # PRIMARY: Controls first frame (unique per scene)
                            end_image_path=scene_end_image,  # PRIMARY: Controls last frame (unique per scene)
                            reference_image_path=scene_reference_image,  # SECONDARY: Style consistency (shared across scenes)
                            consistency_markers=consistency_markers,  # Pass shared markers for cohesion
                        )
                        logger.info(f"[{generation_id}] Clip {scene_number} generated successfully: {clip_path} (model: {model_used})")
                        
                        # Store the enhanced video generation prompt in storyboard_plan
                        # Always reload from database to get latest version and avoid race conditions
                        try:
                            from app.services.pipeline.video_generation import _enhance_prompt_with_markers
                            import json
                            import copy
                            
                            # Reload generation and storyboard_plan from database
                            db.refresh(generation)
                            
                            # Get storyboard_plan from database (always use fresh copy)
                            current_storyboard_plan = None
                            if generation.coherence_settings and "storyboard_plan" in generation.coherence_settings:
                                current_storyboard_plan = generation.coherence_settings["storyboard_plan"]
                                # Handle JSON string case
                                if isinstance(current_storyboard_plan, str):
                                    current_storyboard_plan = json.loads(current_storyboard_plan)
                            
                            # Only proceed if we have a valid storyboard_plan
                            if current_storyboard_plan and isinstance(current_storyboard_plan, dict):
                                scenes_list = current_storyboard_plan.get("scenes", [])
                                scene_idx = scene_number - 1
                                
                                if 0 <= scene_idx < len(scenes_list):
                                    # Deep copy to avoid modifying the database object directly
                                    updated_storyboard_plan = copy.deepcopy(current_storyboard_plan)
                                    scene_data = updated_storyboard_plan["scenes"][scene_idx]
                                    
                                    base_video_prompt = scene.visual_prompt
                                    
                                    # Enhance prompt with consistency markers
                                    enhanced_video_prompt = _enhance_prompt_with_markers(
                                        base_prompt=base_video_prompt,
                                        consistency_markers=consistency_markers
                                    )
                                    
                                    # Add subject presence information to video prompt if available
                                    scene_subject_presence_info = scene_data.get("subject_presence", "full")
                                    scene_subject_timing_info = scene_data.get("subject_appearance_timing", "")
                                    if scene_subject_presence_info and scene_subject_presence_info != "full":
                                        # Add explicit instruction about subject presence
                                        if scene_subject_presence_info == "none":
                                            enhanced_video_prompt += " | IMPORTANT: This scene does NOT include the main subject. Focus on environment, atmosphere, and supporting elements."
                                        elif scene_subject_presence_info == "partial":
                                            enhanced_video_prompt += f" | IMPORTANT: Subject appears only partially in this scene. {scene_subject_timing_info}"
                                        elif scene_subject_presence_info in ("appears_at_start", "appears_at_end", "appears_mid_scene", "disappears_mid_scene"):
                                            enhanced_video_prompt += f" | IMPORTANT: Subject {scene_subject_presence_info.replace('_', ' ')}. {scene_subject_timing_info}"
                                    
                                    scene_data["video_generation_prompt"] = enhanced_video_prompt
                                    scene_data["video_generation_model"] = model_used
                                    scene_data["video_generation_base_prompt"] = base_video_prompt
                                    
                                    # Update storyboard_plan in database
                                    generation.coherence_settings["storyboard_plan"] = updated_storyboard_plan
                                    db.commit()
                                    logger.info(f"[{generation_id}] ✅ Updated storyboard_plan with video generation prompt for scene {scene_number} (model: {model_used})")
                                else:
                                    logger.warning(f"[{generation_id}] Scene index {scene_idx} out of range for storyboard_plan scenes (total: {len(scenes_list)}, scene_number: {scene_number})")
                            else:
                                logger.debug(f"[{generation_id}] No storyboard_plan in database for scene {scene_number} - skipping prompt storage (this is normal if use_llm was False)")
                        except Exception as e:
                            # Don't fail the entire generation if prompt storage fails
                            logger.warning(f"[{generation_id}] Failed to store video generation prompt for scene {scene_number}: {e}. Continuing without storing prompt.")
                        
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
                            # Rollback the session if quality evaluation failed (e.g., missing table)
                            # This ensures subsequent database operations can proceed
                            try:
                                db.rollback()
                            except Exception as rollback_error:
                                logger.warning(f"[{generation_id}] Error rolling back session after quality evaluation failure: {rollback_error}")
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
                    # Add text overlays to all video clips (with error handling)
                    logger.info(f"[{generation_id}] Starting text overlay addition for {len(clip_paths)} clips...")
                    try:
                        scene_plan_obj = ScenePlan(**generation.scene_plan)
                        overlay_output_dir = str(temp_dir / f"{generation_id}_overlays")
                        logger.info(f"[{generation_id}] Overlay output directory: {overlay_output_dir}")
                        overlay_paths = add_overlays_to_clips(
                            clip_paths=clip_paths,
                            scene_plan=scene_plan_obj,
                            output_dir=overlay_output_dir
                        )
                        logger.info(f"[{generation_id}] Text overlays added successfully to all clips")
                    except Exception as e:
                        logger.warning(f"[{generation_id}] Text overlay addition failed: {e}. Continuing without overlays.")
                        overlay_paths = clip_paths  # Fallback to raw clips
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
                
                # Pass LLM specification to audio layer for sound_design extraction
                llm_spec = generation.llm_specification if generation.llm_specification else None
                
                # Add audio layer (with error handling - don't fail generation if audio fails)
                try:
                    video_with_audio = add_audio_layer(
                        video_path=stitched_video_path,
                        music_style=music_style,
                        output_path=audio_output_path,
                        scene_plan=scene_plan_obj,
                        cancellation_check=check_cancellation,
                        llm_specification=llm_spec,  # Pass LLM spec for sound_design
                    )
                    logger.info(f"[{generation_id}] Audio layer added successfully: {video_with_audio}")
                except Exception as e:
                    logger.warning(f"[{generation_id}] Audio layer addition failed: {e}. Continuing without audio.")
                    # Fallback: use stitched video without audio
                    video_with_audio = stitched_video_path
                
                # Check cancellation before brand overlay
                if check_cancellation():
                    logger.info(f"[{generation_id}] Generation cancelled before brand overlay")
                    update_generation_status(
                        db=db,
                        generation_id=generation_id,
                        status="failed",
                        error_message="Cancelled by user"
                    )
                    return
                
                # Brand Overlay Stage (after audio, before export)
                logger.info(f"[{generation_id}] Adding brand overlay to final video...")
                update_generation_progress(
                    db=db,
                    generation_id=generation_id,
                    progress=92,
                    current_step="Adding brand overlay"
                )
                
                # ALWAYS prioritize user-provided brand name
                # Only extract from prompt if user did NOT provide a brand name
                if brand_name:
                    logger.info(f"[{generation_id}] Using user-provided brand name: {brand_name}")
                else:
                    # Only try extraction if user didn't provide one
                    extracted_brand = extract_brand_name(prompt)
                    if extracted_brand:
                        brand_name = extracted_brand
                        logger.info(f"[{generation_id}] Extracted brand name from prompt: {brand_name}")
                    else:
                        logger.info(f"[{generation_id}] No brand name provided and none found in prompt - skipping brand overlay")
                
                # Add brand overlay if brand name found (with error handling)
                if brand_name:
                    try:
                        brand_overlay_output_path = str(Path(audio_output_dir) / "with_brand_overlay.mp4")
                        video_with_brand = add_brand_overlay_to_final_video(
                            video_path=video_with_audio,
                            brand_name=brand_name,
                            output_path=brand_overlay_output_path,
                            duration=2.0  # Show brand for 2 seconds at the end
                        )
                        logger.info(f"[{generation_id}] Brand overlay added successfully: {video_with_brand}")
                        video_for_export = video_with_brand
                    except Exception as e:
                        logger.warning(f"[{generation_id}] Brand overlay addition failed: {e}. Continuing without brand overlay.")
                        video_for_export = video_with_audio  # Fallback to video without brand overlay
                else:
                    logger.info(f"[{generation_id}] No brand name found in prompt, skipping brand overlay")
                    video_for_export = video_with_audio
                
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
                    video_path=video_for_export,
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
            logger.error(f"[{generation_id}] ========== UNEXPECTED ERROR ==========")
            logger.error(f"[{generation_id}] Exception type: {type(e).__name__}")
            logger.error(f"[{generation_id}] Exception message: {str(e)}")
            logger.error(f"[{generation_id}] Full traceback:", exc_info=True)
            
            # Create user-friendly error message
            error_str = str(e)
            logger.error(f"[{generation_id}] Error string: {error_str}")
            if "refused" in error_str.lower() or "content filtering" in error_str.lower():
                user_error = "The AI model refused to process this request. This may be due to content filtering. Please try rephrasing your prompt or using different wording."
            elif "storyboard planning failed" in error_str.lower():
                user_error = f"Failed to create storyboard: {error_str}. Please try again with a different prompt."
            else:
                user_error = f"Generation failed: {error_str[:200]}"  # Truncate long errors
            
            update_generation_progress(
                db=db,
                generation_id=generation_id,
                progress=0,
                status="failed",
                current_step="Error occurred"
            )
            update_generation_status(
                db=db,
                generation_id=generation_id,
                status="failed",
                error_message=user_error
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
        request: GenerateRequest with prompt (10-2000 characters)
        current_user: Authenticated user (from JWT)
        db: Database session
    
    Returns:
        GenerateResponse with generation_id and status
    
    Raises:
        HTTPException: 422 if validation fails (handled by FastAPI)
        HTTPException: 500 if LLM or scene planning fails
    """
    logger.info(f"========== /api/generate ENDPOINT CALLED ==========")
    logger.info(f"User ID: {current_user.id}")
    logger.info(f"Request received:")
    logger.info(f"  - prompt length: {len(request.prompt)}")
    logger.info(f"  - prompt preview: {request.prompt[:100]}...")
    logger.info(f"  - title: {request.title}")
    logger.info(f"  - model: {request.model}")
    logger.info(f"  - target_duration: {request.target_duration}")
    logger.info(f"  - use_llm: {request.use_llm}")
    logger.info(f"  - coherence_settings: {request.coherence_settings}")
    logger.info(f"  - refinement_instructions: {request.refinement_instructions}")
    logger.info(f"  - brand_name: {request.brand_name}")
    
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
    # Pass model, target_duration, use_llm, refinement_instructions, brand_name, and advanced image generation settings if specified
    background_tasks.add_task(
        process_generation,
        generation_id,
        request.prompt,
        request.model,
        request.target_duration,  # Use target_duration instead of num_clips
        request.use_llm if request.use_llm is not None else True,
        None,  # image_path (for /api/generate endpoint, no image)
        request.refinement_instructions,  # Pass refinement instructions
        request.brand_name,  # Pass brand name if provided
        request.use_advanced_image_generation or False,  # Advanced image generation flag
        request.advanced_image_quality_threshold or 30.0,  # Quality threshold
        request.advanced_image_num_variations or 4,  # Number of variations
        request.advanced_image_max_enhancement_iterations or 4,  # Max enhancement iterations
    )
    logger.info(f"[{generation_id}] ✅ Background task added successfully")
    
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
        if len(variation.prompt) < 10 or len(variation.prompt) > 2000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_PROMPT_LENGTH",
                        "message": f"Variation {i+1}: Prompt must be between 10 and 2000 characters"
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
            
            # Extract per-variation settings
            variation_model = variation.model if hasattr(variation, 'model') else None
            variation_target_duration = variation.target_duration if hasattr(variation, 'target_duration') else None
            variation_use_llm = variation.use_llm if hasattr(variation, 'use_llm') else True
            variation_brand_name = variation.brand_name if hasattr(variation, 'brand_name') else None
            
            # Determine if this is single clip generation (bypass pipeline)
            # Single clip mode: model is required and use_llm is False (target_duration not used for single clip)
            is_single_clip = (
                variation_model is not None and 
                variation_use_llm is False
            )
            
            if is_single_clip:
                # Use single clip generation (bypasses entire pipeline)
                if variation_model not in MODEL_COSTS:
                    logger.warning(f"Invalid model {variation_model} for variation {i+1}, skipping single clip generation")
                    errors.append(f"Variation {i+1}: Invalid model for single clip generation")
                    continue
                
                # Single clip generation still uses num_clips (legacy function)
                # Default to 1 clip for single clip mode
                background_tasks.add_task(
                    process_single_clip_generation,
                    generation.id,
                    variation.prompt,
                    variation_model,
                    1  # Single clip mode always generates 1 clip
                )
                logger.info(f"Started single clip generation task for generation {generation.id} (variation {i+1})")
            else:
                # Use full pipeline generation
                background_tasks.add_task(
                    process_generation,
                    generation.id, 
                    variation.prompt,
                    variation_model,  # preferred_model
                    variation_target_duration,  # target_duration
                    variation_use_llm,  # use_llm
                    None,  # image_path
                    None,  # refinement_instructions
                    variation_brand_name,  # brand_name
                )
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
        
        # Normalize path: convert backslashes to forward slashes (handle Windows paths)
        normalized_path = relative_path.replace("\\", "/")
        
        # If storage mode is S3, generate presigned URL
        if settings.STORAGE_MODE == "s3":
            try:
                from app.services.storage.s3_storage import get_s3_storage
                s3_storage = get_s3_storage()
                # Generate presigned URL (expires in 1 hour)
                presigned_url = s3_storage.generate_presigned_url(normalized_path, expiration=3600)
                return presigned_url
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for {normalized_path}: {e}, falling back to static URL")
                # Fall back to static URL if S3 fails
                base_url = settings.STATIC_BASE_URL.rstrip("/")
                # Remove "output/" prefix if present (since base_url already includes /output)
                path = normalized_path.lstrip("/")
                if path.startswith("output/"):
                    path = path[7:]  # Remove "output/" prefix
                return f"{base_url}/{path}"
        else:
            # Convert relative path to full URL (local storage)
            # Static files are mounted at /output, so paths like "output/temp/images/..." 
            # should become "http://localhost:8000/output/temp/images/..."
            base_url = settings.STATIC_BASE_URL.rstrip("/")
            # Remove "output/" prefix if present (since base_url already includes /output)
            path = normalized_path.lstrip("/")
            if path.startswith("output/"):
                path = path[7:]  # Remove "output/" prefix (7 chars: "output/")
            return f"{base_url}/{path}"
    
    # Extract storyboard plan from coherence_settings and convert image paths to URLs
    storyboard_plan = None
    if generation.coherence_settings:
        # Log coherence_settings structure for debugging
        logger.debug(f"[{generation_id}] coherence_settings type: {type(generation.coherence_settings)}, keys: {list(generation.coherence_settings.keys()) if isinstance(generation.coherence_settings, dict) else 'N/A'}")
        
        if isinstance(generation.coherence_settings, dict) and "storyboard_plan" in generation.coherence_settings:
            storyboard_plan_data = generation.coherence_settings["storyboard_plan"]
            
            # Handle case where storyboard_plan might be stored as a string (JSON)
            if isinstance(storyboard_plan_data, str):
                try:
                    import json
                    storyboard_plan_data = json.loads(storyboard_plan_data)
                except json.JSONDecodeError:
                    logger.warning(f"[{generation_id}] Failed to parse storyboard_plan JSON string")
                    storyboard_plan_data = None
            
            if storyboard_plan_data:
                # Deep copy to preserve all fields including llm_input, llm_output, and all scene prompts
                import copy
                storyboard_plan = copy.deepcopy(storyboard_plan_data) if isinstance(storyboard_plan_data, dict) else storyboard_plan_data
                
                # Convert image paths to public URLs for each scene (preserve all other fields)
                if isinstance(storyboard_plan, dict) and "scenes" in storyboard_plan:
                    for scene in storyboard_plan["scenes"]:
                        if isinstance(scene, dict):
                            # Convert image paths to URLs (add URL fields without removing path fields)
                            if "reference_image_path" in scene and scene["reference_image_path"]:
                                scene["reference_image_url"] = get_public_path(scene["reference_image_path"])
                            if "start_image_path" in scene and scene["start_image_path"]:
                                scene["start_image_url"] = get_public_path(scene["start_image_path"])
                            if "end_image_path" in scene and scene["end_image_path"]:
                                scene["end_image_url"] = get_public_path(scene["end_image_path"])
                
                # Ensure llm_input and llm_output are preserved (they should be from deepcopy, but verify)
                logger.debug(f"[{generation_id}] Storyboard plan keys: {list(storyboard_plan.keys()) if isinstance(storyboard_plan, dict) else 'N/A'}")
                if isinstance(storyboard_plan, dict):
                    if "llm_input" in storyboard_plan:
                        logger.debug(f"[{generation_id}] LLM input present in storyboard_plan")
                    if "llm_output" in storyboard_plan:
                        logger.debug(f"[{generation_id}] LLM output present in storyboard_plan")
                    # Log scene prompt fields for debugging
                    if "scenes" in storyboard_plan:
                        for idx, scene in enumerate(storyboard_plan["scenes"]):
                            if isinstance(scene, dict):
                                scene_keys = list(scene.keys())
                                logger.debug(f"[{generation_id}] Scene {idx+1} keys: {scene_keys}")
                                if "video_generation_prompt" in scene:
                                    logger.debug(f"[{generation_id}] Scene {idx+1} has video_generation_prompt")
                                if "reference_image_prompt" in scene:
                                    logger.debug(f"[{generation_id}] Scene {idx+1} has reference_image_prompt")
        else:
            logger.debug(f"[{generation_id}] No storyboard_plan in coherence_settings. Available keys: {list(generation.coherence_settings.keys()) if isinstance(generation.coherence_settings, dict) else 'N/A'}")
            
            # Fallback: Try to reconstruct storyboard from scene_plan if it has image paths
            # This helps with videos generated earlier that might have images but no storyboard_plan stored
            if generation.scene_plan and isinstance(generation.scene_plan, dict):
                scenes = generation.scene_plan.get("scenes", [])
                if scenes and any(scene.get("reference_image_path") for scene in scenes if isinstance(scene, dict)):
                    logger.info(f"[{generation_id}] Attempting to reconstruct storyboard from scene_plan")
                    try:
                        # Reconstruct a basic storyboard structure from scene_plan
                        reconstructed_scenes = []
                        consistency_markers = generation.coherence_settings.get("consistency_markers", {}) if generation.coherence_settings else {}
                        
                        for scene in scenes:
                            if isinstance(scene, dict):
                                reconstructed_scene = {
                                    "scene_number": scene.get("scene_number", 0),
                                    "aida_stage": scene.get("scene_type", "Scene"),
                                    "detailed_prompt": scene.get("visual_prompt", ""),
                                    "reference_image_path": scene.get("reference_image_path"),
                                    "start_image_path": scene.get("start_image_path"),
                                    "end_image_path": scene.get("end_image_path"),
                                    "duration_seconds": scene.get("duration", 4),
                                }
                                reconstructed_scenes.append(reconstructed_scene)
                        
                        if reconstructed_scenes:
                            storyboard_plan = {
                                "consistency_markers": consistency_markers,
                                "scenes": reconstructed_scenes
                            }
                            logger.info(f"[{generation_id}] Successfully reconstructed storyboard from scene_plan with {len(reconstructed_scenes)} scenes")
                            
                            # Convert image paths to public URLs
                            for scene in storyboard_plan["scenes"]:
                                if "reference_image_path" in scene and scene["reference_image_path"]:
                                    scene["reference_image_url"] = get_public_path(scene["reference_image_path"])
                                if "start_image_path" in scene and scene["start_image_path"]:
                                    scene["start_image_url"] = get_public_path(scene["start_image_path"])
                                if "end_image_path" in scene and scene["end_image_path"]:
                                    scene["end_image_url"] = get_public_path(scene["end_image_path"])
                    except Exception as e:
                        logger.warning(f"[{generation_id}] Failed to reconstruct storyboard from scene_plan: {e}")
    else:
        logger.debug(f"[{generation_id}] coherence_settings is None or empty")
        
        # Fallback: Try to reconstruct from scene_plan even if coherence_settings is None
        if generation.scene_plan and isinstance(generation.scene_plan, dict):
            scenes = generation.scene_plan.get("scenes", [])
            if scenes and any(scene.get("reference_image_path") for scene in scenes if isinstance(scene, dict)):
                logger.info(f"[{generation_id}] Attempting to reconstruct storyboard from scene_plan (no coherence_settings)")
                try:
                    reconstructed_scenes = []
                    for scene in scenes:
                        if isinstance(scene, dict):
                            reconstructed_scene = {
                                "scene_number": scene.get("scene_number", 0),
                                "aida_stage": scene.get("scene_type", "Scene"),
                                "detailed_prompt": scene.get("visual_prompt", ""),
                                "reference_image_path": scene.get("reference_image_path"),
                                "start_image_path": scene.get("start_image_path"),
                                "end_image_path": scene.get("end_image_path"),
                                "duration_seconds": scene.get("duration", 4),
                            }
                            reconstructed_scenes.append(reconstructed_scene)
                    
                    if reconstructed_scenes:
                        storyboard_plan = {
                            "consistency_markers": {},
                            "scenes": reconstructed_scenes
                        }
                        logger.info(f"[{generation_id}] Successfully reconstructed storyboard from scene_plan with {len(reconstructed_scenes)} scenes")
                        
                        # Convert image paths to public URLs
                        for scene in storyboard_plan["scenes"]:
                            if "reference_image_path" in scene and scene["reference_image_path"]:
                                scene["reference_image_url"] = get_public_path(scene["reference_image_path"])
                            if "start_image_path" in scene and scene["start_image_path"]:
                                scene["start_image_url"] = get_public_path(scene["start_image_path"])
                            if "end_image_path" in scene and scene["end_image_path"]:
                                scene["end_image_url"] = get_public_path(scene["end_image_path"])
                except Exception as e:
                    logger.warning(f"[{generation_id}] Failed to reconstruct storyboard from scene_plan: {e}")
    
    # Extract advanced image generation metadata from scene_plan
    advanced_image_generation_used = None
    if generation.scene_plan and isinstance(generation.scene_plan, dict):
        advanced_image_generation_used = generation.scene_plan.get('advanced_image_generation_used', False)
    
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
        seed_value=generation.seed_value,
        storyboard_plan=storyboard_plan,
        advanced_image_generation_used=advanced_image_generation_used
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
        # Normalize path: convert backslashes to forward slashes (handle Windows paths)
        normalized_path = relative_path.replace("\\", "/")
        # Convert relative path to full URL
        base_url = settings.STATIC_BASE_URL.rstrip("/")
        # Remove "output/" prefix if present (since base_url already includes /output)
        path = normalized_path.lstrip("/")
        if path.startswith("output/"):
            path = path[7:]  # Remove "output/" prefix
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
                # Normalize path: convert backslashes to forward slashes
                normalized_path = relative_path.replace("\\", "/")
                base_url = settings.STATIC_BASE_URL.rstrip("/") if settings.STATIC_BASE_URL else ""
                # Remove "output/" prefix if present (since base_url already includes /output)
                path = normalized_path.lstrip("/")
                if path.startswith("output/"):
                    path = path[7:]  # Remove "output/" prefix
                return f"{base_url}/{path}" if base_url else relative_path
        else:
            # Convert relative path to full URL (local storage or S3 with skip_s3=True)
            # Normalize path: convert backslashes to forward slashes
            normalized_path = relative_path.replace("\\", "/")
            base_url = settings.STATIC_BASE_URL.rstrip("/") if settings.STATIC_BASE_URL else ""
            # Remove "output/" prefix if present (since base_url already includes /output)
            path = normalized_path.lstrip("/")
            if path.startswith("output/"):
                path = path[7:]  # Remove "output/" prefix
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
                # Normalize path: convert backslashes to forward slashes
                normalized_path = relative_path.replace("\\", "/")
                base_url = settings.STATIC_BASE_URL.rstrip("/") if settings.STATIC_BASE_URL else ""
                # Remove "output/" prefix if present (since base_url already includes /output)
                path = normalized_path.lstrip("/")
                if path.startswith("output/"):
                    path = path[7:]  # Remove "output/" prefix
                return f"{base_url}/{path}" if base_url else relative_path
        else:
            # Normalize path: convert backslashes to forward slashes
            normalized_path = relative_path.replace("\\", "/")
            base_url = settings.STATIC_BASE_URL.rstrip("/") if settings.STATIC_BASE_URL else ""
            # Remove "output/" prefix if present (since base_url already includes /output)
            path = normalized_path.lstrip("/")
            if path.startswith("output/"):
                path = path[7:]  # Remove "output/" prefix
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
    # Single clip generation always generates 1 clip (legacy function still uses num_clips parameter)
    background_tasks.add_task(
        process_single_clip_generation,
        generation_id,
        request.prompt,
        request.model,
        1  # Single clip mode always generates 1 clip
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
                
                # Retrieve consistency markers if available
                markers = None
                if generation.coherence_settings and "consistency_markers" in generation.coherence_settings:
                    markers = generation.coherence_settings["consistency_markers"]
                
                clip_path, model_used = await generate_video_clip_with_model(
                    prompt=prompt,
                    duration=duration,
                    output_dir=temp_output_dir,
                    generation_id=generation_id,
                    model_name=model_name,
                    cancellation_check=check_cancellation,
                    clip_index=clip_index,
                    consistency_markers=markers,  # Pass shared markers for cohesion
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
