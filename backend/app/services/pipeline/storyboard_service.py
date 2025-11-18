"""
Storyboard service for creating start and end frames for video clips.

This service breaks video prompts into clips, generates start/end frame prompts,
and creates storyboard images using the image generation service.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.services.pipeline.scene_planning import create_basic_scene_plan_from_prompt, ScenePlan
from app.services.image_generation import (
    generate_images,
    ImageGenerationResult,
    prepare_image_for_replicate
)
from app.services.pipeline.storyboard_prompt_enhancement import (
    enhance_storyboard_prompts,
    StoryboardEnhancementResult
)

logger = logging.getLogger(__name__)


@dataclass
class ClipStoryboard:
    """Storyboard data for a single video clip."""
    clip_number: int
    start_frame_path: str
    end_frame_path: str
    start_frame_prompt: str
    end_frame_prompt: str
    motion_description: str
    camera_movement: str
    shot_size: str
    perspective: str
    lens_type: str
    clip_description: str


@dataclass
class StoryboardResult:
    """Complete storyboard result with all clips and metadata."""
    clips: List[ClipStoryboard]
    metadata: Dict[str, Any]
    output_dir: str
    timestamp: str


async def create_storyboard(
    prompt: str,
    num_clips: int = 3,
    aspect_ratio: str = "16:9",
    reference_image_path: Optional[str] = None,
    output_dir: Optional[Path] = None,
    total_duration: int = 15,
    story_type: str = "sensory_experience"
) -> StoryboardResult:
    """
    Create a storyboard with start and end frames for video clips.
    
    Args:
        prompt: Video clip prompt
        num_clips: Number of scenes/clips to create (1-10, default: 3)
        aspect_ratio: Aspect ratio for frames (default: "16:9")
        reference_image_path: Optional path to best image from 8-2 for storyboard prompt enhancement
        output_dir: Output directory for storyboard files (default: output/storyboards/{timestamp})
        total_duration: Total duration of the final video in seconds (default: 15, valid range: 15-60)
        story_type: Story type for narrative structure (default: "sensory_experience"). Options: transformation, reveal_discovery, journey_path, problem_solution, sensory_experience, symbolic_metaphor, micro_drama, montage
    
    Returns:
        StoryboardResult with clips, metadata, and file paths
    """
    logger.info(f"Creating storyboard: {num_clips} clips, aspect_ratio={aspect_ratio}, reference_image={reference_image_path}, total_duration={total_duration}s, story_type={story_type}")
    
    # Validate num_clips (scenes)
    num_clips = max(1, min(10, num_clips))  # Allow 1-10 scenes
    
    # Setup output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output") / "storyboards" / timestamp
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Enhance storyboard prompts if reference image provided
    # NOTE: Always use original prompt (not image-enhanced) for storyboard enhancement
    # The storyboard enhancement focuses on narrative/story structure, while the reference
    # image provides visual coherence (brand colors, style, etc.)
    storyboard_enhancement_result: Optional[StoryboardEnhancementResult] = None
    if reference_image_path:
        logger.info("Enhancing storyboard prompts using reference image...")
        try:
            storyboard_enhancement_result = await enhance_storyboard_prompts(
                total_duration=total_duration,
                original_prompt=prompt,  # Use original prompt, not image-enhanced version
                reference_image_path=reference_image_path,
                num_scenes=num_clips,
                max_iterations=3,
                score_threshold=85.0,
                trace_dir=output_dir / "storyboard_enhancement_trace",
                story_type=story_type
            )
            logger.info(f"Storyboard prompts enhanced: {storyboard_enhancement_result.final_scores.get('overall', 0):.1f}/100 average score")
        except Exception as e:
            logger.error(f"Storyboard prompt enhancement failed: {e}")
            raise RuntimeError(f"Storyboard prompt enhancement failed (fail fast): {e}")
    
    # Step 2: Plan scenes (break prompt into clips) - only if not using storyboard enhancement
    if not storyboard_enhancement_result:
        logger.info(f"Planning {num_clips} clips from prompt...")
        scene_plan = create_basic_scene_plan_from_prompt(
            prompt=prompt,
            target_duration=15,
            num_scenes=num_clips
        )
        logger.info(f"Scene plan created: {len(scene_plan.scenes)} scenes")
    else:
        # Create dummy scene plan for metadata compatibility
        scene_plan = ScenePlan(
            scenes=[],
            total_duration=15,
            framework="Sensory Journey"
        )
    
    # Step 3: Prepare reference image for sequential generation (if provided)
    reference_image_uri: Optional[str] = None
    if reference_image_path:
        try:
            reference_image_uri = prepare_image_for_replicate(reference_image_path)
            logger.info(f"Reference image prepared for sequential generation: {reference_image_uri}")
        except Exception as e:
            logger.warning(f"Failed to prepare reference image for sequential generation: {e}. Continuing without image conditioning.")
            reference_image_uri = None
    
    # Step 4: Generate start/end frame prompts and motion descriptions for each clip
    clip_storyboards: List[ClipStoryboard] = []
    failed_clips: List[Dict[str, Any]] = []
    previous_frame_path: Optional[str] = None  # Track previous frame for sequential generation
    
    # Use enhanced prompts if available, otherwise use generic generation
    if storyboard_enhancement_result:
        # Use enhanced prompts from storyboard enhancement service
        for scene_prompt_set in storyboard_enhancement_result.scene_prompts:
            i = scene_prompt_set.scene_number
            logger.info(f"Processing clip {i}/{num_clips} (using enhanced prompts)...")
            
            start_frame_prompt = scene_prompt_set.start_frame_prompt
            end_frame_prompt = scene_prompt_set.end_frame_prompt
            motion_desc = scene_prompt_set.motion_description
            
            # Generate camera metadata (basic, since VideoDirectorGPT is backlog)
            camera_movement, shot_size, perspective, lens_type = _generate_camera_metadata(
                scene_prompt_set.scene_type,
                i,
                num_clips
            )
            
            try:
                # Generate start frame image with sequential conditioning
                logger.info(f"Generating start frame for clip {i}...")
                try:
                    # Prepare image_input for sequential generation
                    # First clip: use reference image only
                    # Subsequent clips: use reference image + previous clip's end frame
                    image_input_list: Optional[List[str]] = None
                    model_name = "black-forest-labs/flux-schnell"  # Default model
                    
                    if reference_image_uri:
                        # Use nano-banana for image-to-image generation
                        model_name = "google/nano-banana"
                        if i == 1:
                            # First clip start: reference image only
                            image_input_list = [reference_image_uri]
                            logger.debug(f"Clip {i} start frame: conditioning with reference image only")
                        elif previous_frame_path:
                            # Subsequent clips: reference + previous frame
                            previous_frame_uri = prepare_image_for_replicate(previous_frame_path)
                            image_input_list = [reference_image_uri, previous_frame_uri]
                            logger.debug(f"Clip {i} start frame: conditioning with reference image + previous frame")
                        else:
                            # Fallback: reference image only
                            image_input_list = [reference_image_uri]
                            logger.debug(f"Clip {i} start frame: conditioning with reference image only (no previous frame)")
                    
                    start_frame_results = await generate_images(
                        prompt=start_frame_prompt,
                        num_variations=1,  # Single image for storyboard
                        aspect_ratio=aspect_ratio,
                        output_dir=output_dir,
                        model_name=model_name,
                        image_input=image_input_list
                    )
                    
                    if not start_frame_results:
                        raise RuntimeError(f"Image generation returned empty results for start frame")
                    
                    start_frame_result = start_frame_results[0]
                    start_frame_path = start_frame_result.image_path or start_frame_result.image_url
                    
                    # Rename start frame to clip_XXX_start.png
                    if start_frame_result.image_path:
                        start_frame_file = Path(start_frame_result.image_path)
                        new_start_path = output_dir / f"clip_{i:03d}_start.png"
                        if start_frame_file.exists():
                            start_frame_file.rename(new_start_path)
                            start_frame_path = str(new_start_path)
                except Exception as e:
                    logger.error(f"Failed to generate start frame for clip {i}: {e}")
                    failed_clips.append({
                        "clip_number": i,
                        "error": "start_frame_generation_failed",
                        "error_message": str(e)
                    })
                    # Continue to try end frame, but mark clip as failed
                    start_frame_path = None
                
                # Generate end frame image with sequential conditioning
                logger.info(f"Generating end frame for clip {i}...")
                try:
                    # Prepare image_input for end frame generation
                    # End frame: reference image + current clip's start frame
                    image_input_list: Optional[List[str]] = None
                    model_name = "black-forest-labs/flux-schnell"  # Default model
                    
                    if reference_image_uri and start_frame_path:
                        # Use nano-banana for image-to-image generation
                        model_name = "google/nano-banana"
                        start_frame_uri = prepare_image_for_replicate(start_frame_path)
                        image_input_list = [reference_image_uri, start_frame_uri]
                        logger.debug(f"Clip {i} end frame: conditioning with reference image + start frame")
                    elif reference_image_uri:
                        # Fallback: reference image only
                        model_name = "google/nano-banana"
                        image_input_list = [reference_image_uri]
                        logger.debug(f"Clip {i} end frame: conditioning with reference image only")
                    
                    end_frame_results = await generate_images(
                        prompt=end_frame_prompt,
                        num_variations=1,  # Single image for storyboard
                        aspect_ratio=aspect_ratio,
                        output_dir=output_dir,
                        model_name=model_name,
                        image_input=image_input_list
                    )
                    
                    if not end_frame_results:
                        raise RuntimeError(f"Image generation returned empty results for end frame")
                    
                    end_frame_result = end_frame_results[0]
                    end_frame_path = end_frame_result.image_path or end_frame_result.image_url
                    
                    # Rename end frame to clip_XXX_end.png
                    if end_frame_result.image_path:
                        end_frame_file = Path(end_frame_result.image_path)
                        new_end_path = output_dir / f"clip_{i:03d}_end.png"
                        if end_frame_file.exists():
                            end_frame_file.rename(new_end_path)
                            end_frame_path = str(new_end_path)
                except Exception as e:
                    logger.error(f"Failed to generate end frame for clip {i}: {e}")
                    failed_clips.append({
                        "clip_number": i,
                        "error": "end_frame_generation_failed",
                        "error_message": str(e)
                    })
                    # Mark end frame as failed
                    end_frame_path = None
                
                # Only create clip storyboard if both frames were generated successfully
                if start_frame_path and end_frame_path:
                    clip_storyboard = ClipStoryboard(
                        clip_number=i,
                        start_frame_path=start_frame_path,
                        end_frame_path=end_frame_path,
                        start_frame_prompt=start_frame_prompt,
                        end_frame_prompt=end_frame_prompt,
                        motion_description=motion_desc,
                        camera_movement=camera_movement,
                        shot_size=shot_size,
                        perspective=perspective,
                        lens_type=lens_type,
                        clip_description=scene_prompt_set.scene_type  # Use scene type as description
                    )
                    
                    clip_storyboards.append(clip_storyboard)
                    # Update previous_frame_path for next clip's sequential generation
                    previous_frame_path = end_frame_path
                    logger.info(f"Clip {i} storyboard complete")
                else:
                    logger.warning(f"Clip {i} storyboard incomplete - missing frames")
                    failed_clips.append({
                        "clip_number": i,
                        "error": "incomplete_frames",
                        "error_message": f"Start frame: {'OK' if start_frame_path else 'FAILED'}, End frame: {'OK' if end_frame_path else 'FAILED'}"
                    })
            
            except Exception as e:
                logger.error(f"Unexpected error processing clip {i}: {e}", exc_info=True)
                failed_clips.append({
                    "clip_number": i,
                    "error": "unexpected_error",
                    "error_message": str(e)
                })
                # Continue with next clip
                continue
    else:
        # Use generic prompt generation (original flow)
        logger.info(f"Planning {num_clips} clips from prompt...")
        scene_plan = create_basic_scene_plan_from_prompt(
            prompt=prompt,
            target_duration=15,
            num_scenes=num_clips
        )
        logger.info(f"Scene plan created: {len(scene_plan.scenes)} scenes")
        
        for i, scene in enumerate(scene_plan.scenes, start=1):
            logger.info(f"Processing clip {i}/{num_clips}...")
            
            try:
                # Generate start/end frame prompts from scene visual prompt
                start_frame_prompt, end_frame_prompt, motion_desc = _generate_frame_prompts(
                    scene.visual_prompt,
                    scene.scene_type,
                    i,
                    num_clips
                )
                
                # Generate camera metadata (basic, since VideoDirectorGPT is backlog)
                camera_movement, shot_size, perspective, lens_type = _generate_camera_metadata(
                    scene.scene_type,
                    i,
                    num_clips
                )
                
                # Generate start frame image with sequential conditioning
                logger.info(f"Generating start frame for clip {i}...")
                try:
                    # Prepare image_input for sequential generation
                    # First clip: use reference image only
                    # Subsequent clips: use reference image + previous clip's end frame
                    image_input_list: Optional[List[str]] = None
                    model_name = "black-forest-labs/flux-schnell"  # Default model
                    
                    if reference_image_uri:
                        # Use nano-banana for image-to-image generation
                        model_name = "google/nano-banana"
                        if i == 1:
                            # First clip start: reference image only
                            image_input_list = [reference_image_uri]
                            logger.debug(f"Clip {i} start frame: conditioning with reference image only")
                        elif previous_frame_path:
                            # Subsequent clips: reference + previous frame
                            previous_frame_uri = prepare_image_for_replicate(previous_frame_path)
                            image_input_list = [reference_image_uri, previous_frame_uri]
                            logger.debug(f"Clip {i} start frame: conditioning with reference image + previous frame")
                        else:
                            # Fallback: reference image only
                            image_input_list = [reference_image_uri]
                            logger.debug(f"Clip {i} start frame: conditioning with reference image only (no previous frame)")
                    
                    start_frame_results = await generate_images(
                        prompt=start_frame_prompt,
                        num_variations=1,  # Single image for storyboard
                        aspect_ratio=aspect_ratio,
                        output_dir=output_dir,
                        model_name=model_name,
                        image_input=image_input_list
                    )
                    
                    if not start_frame_results:
                        raise RuntimeError(f"Image generation returned empty results for start frame")
                    
                    start_frame_result = start_frame_results[0]
                    start_frame_path = start_frame_result.image_path or start_frame_result.image_url
                    
                    # Rename start frame to clip_XXX_start.png
                    if start_frame_result.image_path:
                        start_frame_file = Path(start_frame_result.image_path)
                        new_start_path = output_dir / f"clip_{i:03d}_start.png"
                        if start_frame_file.exists():
                            start_frame_file.rename(new_start_path)
                            start_frame_path = str(new_start_path)
                except Exception as e:
                    logger.error(f"Failed to generate start frame for clip {i}: {e}")
                    failed_clips.append({
                        "clip_number": i,
                        "error": "start_frame_generation_failed",
                        "error_message": str(e)
                    })
                    # Continue to try end frame, but mark clip as failed
                    start_frame_path = None
                
                # Generate end frame image with sequential conditioning
                logger.info(f"Generating end frame for clip {i}...")
                try:
                    # Prepare image_input for end frame generation
                    # End frame: reference image + current clip's start frame
                    image_input_list: Optional[List[str]] = None
                    model_name = "black-forest-labs/flux-schnell"  # Default model
                    
                    if reference_image_uri and start_frame_path:
                        # Use nano-banana for image-to-image generation
                        model_name = "google/nano-banana"
                        start_frame_uri = prepare_image_for_replicate(start_frame_path)
                        image_input_list = [reference_image_uri, start_frame_uri]
                        logger.debug(f"Clip {i} end frame: conditioning with reference image + start frame")
                    elif reference_image_uri:
                        # Fallback: reference image only
                        model_name = "google/nano-banana"
                        image_input_list = [reference_image_uri]
                        logger.debug(f"Clip {i} end frame: conditioning with reference image only")
                    
                    end_frame_results = await generate_images(
                        prompt=end_frame_prompt,
                        num_variations=1,  # Single image for storyboard
                        aspect_ratio=aspect_ratio,
                        output_dir=output_dir,
                        model_name=model_name,
                        image_input=image_input_list
                    )
                    
                    if not end_frame_results:
                        raise RuntimeError(f"Image generation returned empty results for end frame")
                    
                    end_frame_result = end_frame_results[0]
                    end_frame_path = end_frame_result.image_path or end_frame_result.image_url
                    
                    # Rename end frame to clip_XXX_end.png
                    if end_frame_result.image_path:
                        end_frame_file = Path(end_frame_result.image_path)
                        new_end_path = output_dir / f"clip_{i:03d}_end.png"
                        if end_frame_file.exists():
                            end_frame_file.rename(new_end_path)
                            end_frame_path = str(new_end_path)
                except Exception as e:
                    logger.error(f"Failed to generate end frame for clip {i}: {e}")
                    failed_clips.append({
                        "clip_number": i,
                        "error": "end_frame_generation_failed",
                        "error_message": str(e)
                    })
                    # Mark end frame as failed
                    end_frame_path = None
                
                # Only create clip storyboard if both frames were generated successfully
                if start_frame_path and end_frame_path:
                    clip_storyboard = ClipStoryboard(
                        clip_number=i,
                        start_frame_path=start_frame_path,
                        end_frame_path=end_frame_path,
                        start_frame_prompt=start_frame_prompt,
                        end_frame_prompt=end_frame_prompt,
                        motion_description=motion_desc,
                        camera_movement=camera_movement,
                        shot_size=shot_size,
                        perspective=perspective,
                        lens_type=lens_type,
                        clip_description=scene.visual_prompt
                    )
                    
                    clip_storyboards.append(clip_storyboard)
                    # Update previous_frame_path for next clip's sequential generation
                    previous_frame_path = end_frame_path
                    logger.info(f"Clip {i} storyboard complete")
                else:
                    logger.warning(f"Clip {i} storyboard incomplete - missing frames")
                    failed_clips.append({
                        "clip_number": i,
                        "error": "incomplete_frames",
                        "error_message": f"Start frame: {'OK' if start_frame_path else 'FAILED'}, End frame: {'OK' if end_frame_path else 'FAILED'}"
                    })
            
            except Exception as e:
                logger.error(f"Unexpected error processing clip {i}: {e}", exc_info=True)
                failed_clips.append({
                    "clip_number": i,
                    "error": "unexpected_error",
                    "error_message": str(e)
                })
                # Continue with next clip
                continue
    
    # Check if we have any successful clips
    if not clip_storyboards:
        raise RuntimeError(
            f"Failed to generate any storyboard clips. Errors: {failed_clips}"
        )
    
    # Log partial success if some clips failed
    if failed_clips:
        logger.warning(
            f"Storyboard generation completed with {len(failed_clips)} failed clips. "
            f"Successfully generated {len(clip_storyboards)}/{num_clips} clips."
        )
    
    # Step 4: Create metadata
    metadata = {
        "prompt": prompt,
        "reference_image_path": reference_image_path,
        "storyboard_enhancement_used": storyboard_enhancement_result is not None,
        "unified_narrative_path": storyboard_enhancement_result.unified_narrative_path if storyboard_enhancement_result and storyboard_enhancement_result.unified_narrative_path else None,
        "narrative_summary": storyboard_enhancement_result.unified_narrative_json.get("overall_story", {}).get("narrative", "") if storyboard_enhancement_result and storyboard_enhancement_result.unified_narrative_json else None,
        "num_clips": num_clips,
        "aspect_ratio": aspect_ratio,
        "framework": storyboard_enhancement_result.extracted_visual_elements.get("framework", scene_plan.framework) if storyboard_enhancement_result else scene_plan.framework,
        "story_type": story_type,
        "total_duration": total_duration,
        "clips": [
            {
                "clip_number": clip.clip_number,
                "description": clip.clip_description,
                "duration": storyboard_enhancement_result.unified_narrative_json.get("scene_durations", {}).get(f"scene_{clip.clip_number}", total_duration // num_clips) if storyboard_enhancement_result and storyboard_enhancement_result.unified_narrative_json else (total_duration // num_clips),
                "start_frame_prompt": clip.start_frame_prompt,
                "end_frame_prompt": clip.end_frame_prompt,
                "motion_description": clip.motion_description,
                "camera_movement": clip.camera_movement,
                "shot_size": clip.shot_size,
                "perspective": clip.perspective,
                "lens_type": clip.lens_type,
                "start_frame_path": clip.start_frame_path,
                "end_frame_path": clip.end_frame_path
            }
            for clip in clip_storyboards
        ],
        "shot_list": [
            {
                "clip_number": clip.clip_number,
                "camera_movement": clip.camera_movement,
                "shot_size": clip.shot_size,
                "perspective": clip.perspective,
                "lens_type": clip.lens_type
            }
            for clip in clip_storyboards
        ],
        "scene_dependencies": _generate_scene_dependencies(num_clips),
        "narrative_flow": _generate_narrative_flow(num_clips, scene_plan.framework),
        "consistency_groupings": _generate_consistency_groupings(clip_storyboards),
        "failed_clips": failed_clips if failed_clips else None,
        "partial_success": len(failed_clips) > 0 if failed_clips else False,
        "created_at": datetime.now().isoformat()
    }
    
    # Save metadata JSON
    metadata_path = output_dir / "storyboard_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Storyboard created: {len(clip_storyboards)} clips, saved to {output_dir}")
    
    return StoryboardResult(
        clips=clip_storyboards,
        metadata=metadata,
        output_dir=str(output_dir),
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    )


def _generate_frame_prompts(
    scene_prompt: str,
    scene_type: str,
    clip_number: int,
    total_clips: int
) -> tuple[str, str, str]:
    """
    Generate start frame prompt, end frame prompt, and motion description from scene prompt.
    
    Args:
        scene_prompt: Original scene visual prompt
        scene_type: Scene type (e.g., "Attention", "Problem")
        clip_number: Current clip number (1-based)
        total_clips: Total number of clips
    
    Returns:
        Tuple of (start_frame_prompt, end_frame_prompt, motion_description)
    """
    # Start frame: Initial state, establishing shot
    if clip_number == 1:
        start_frame_prompt = f"{scene_prompt}. Opening scene, establishing shot, initial state, cinematic quality, professional composition"
    else:
        start_frame_prompt = f"{scene_prompt}. Scene transition, initial state, dynamic composition, engaging visuals"
    
    # End frame: Final state, resolution or transition
    if clip_number == total_clips:
        end_frame_prompt = f"{scene_prompt}. Closing scene, final state, call to action, professional finish, resolution"
    else:
        end_frame_prompt = f"{scene_prompt}. Scene transition, final state, dynamic composition, leading to next scene"
    
    # Motion description: What happens between start and end
    motion_descriptions = {
        "opening": "Camera slowly pushes in from wide establishing shot to medium shot, subject comes into focus",
        "middle": "Smooth camera movement with subject motion, dynamic composition shift",
        "closing": "Camera pulls back slightly, subject moves to final position, scene resolves"
    }
    
    if clip_number == 1:
        motion_desc = motion_descriptions["opening"]
    elif clip_number == total_clips:
        motion_desc = motion_descriptions["closing"]
    else:
        motion_desc = motion_descriptions["middle"]
    
    # Add scene-specific motion hints
    if "opening" in scene_prompt.lower() or "establishing" in scene_prompt.lower():
        motion_desc += ", establishing the scene and context"
    elif "closing" in scene_prompt.lower() or "call to action" in scene_prompt.lower():
        motion_desc += ", emphasizing the call to action"
    else:
        motion_desc += ", maintaining visual continuity"
    
    return start_frame_prompt, end_frame_prompt, motion_desc


def _generate_camera_metadata(
    scene_type: str,
    clip_number: int,
    total_clips: int
) -> tuple[str, str, str, str]:
    """
    Generate camera metadata for a clip.
    
    Args:
        scene_type: Scene type (e.g., "Attention", "Problem")
        clip_number: Current clip number (1-based)
        total_clips: Total number of clips
    
    Returns:
        Tuple of (camera_movement, shot_size, perspective, lens_type)
    """
    # Camera movement based on clip position
    if clip_number == 1:
        camera_movement = "Push in from wide to medium"
    elif clip_number == total_clips:
        camera_movement = "Pull back slightly, static finish"
    else:
        camera_movement = "Smooth pan or dolly movement"
    
    # Shot size based on clip position
    if clip_number == 1:
        shot_size = "Wide shot"
    elif clip_number == total_clips:
        shot_size = "Medium to close-up"
    else:
        shot_size = "Medium shot"
    
    # Perspective
    if clip_number == 1:
        perspective = "Eye level, establishing"
    elif clip_number == total_clips:
        perspective = "Eye level, slightly elevated"
    else:
        perspective = "Eye level, dynamic"
    
    # Lens type
    if clip_number == 1:
        lens_type = "24-35mm wide angle"
    elif clip_number == total_clips:
        lens_type = "50-85mm standard to telephoto"
    else:
        lens_type = "35-50mm standard"
    
    return camera_movement, shot_size, perspective, lens_type


def _generate_scene_dependencies(num_clips: int) -> List[Dict[str, Any]]:
    """
    Generate scene dependencies (which clips depend on which).
    
    Args:
        num_clips: Total number of clips
    
    Returns:
        List of dependency dictionaries
    """
    dependencies = []
    for i in range(1, num_clips + 1):
        deps = []
        if i > 1:
            deps.append({
                "depends_on": i - 1,
                "type": "narrative_flow",
                "description": f"Continues narrative from clip {i-1}"
            })
        dependencies.append({
            "clip_number": i,
            "dependencies": deps
        })
    return dependencies


def _generate_narrative_flow(num_clips: int, framework: str) -> str:
    """
    Generate narrative flow description.
    
    Args:
        num_clips: Total number of clips
        framework: Framework used (PAS, BAB, AIDA)
    
    Returns:
        Narrative flow description string
    """
    flow_templates = {
        "PAS": f"Problem → Agitation → Solution across {num_clips} clips",
        "BAB": f"Before → After → Bridge across {num_clips} clips",
        "AIDA": f"Attention → Interest → Desire → Action across {num_clips} clips"
    }
    
    return flow_templates.get(framework, f"Linear narrative flow across {num_clips} clips")


def _generate_consistency_groupings(clip_storyboards: List[ClipStoryboard]) -> List[Dict[str, Any]]:
    """
    Generate consistency groupings for clips that should maintain visual consistency.
    
    Note: This is a basic implementation. VideoDirectorGPT planning (Story 7.3 Phase 2)
    will enhance this with more sophisticated consistency detection when available.
    
    Args:
        clip_storyboards: List of clip storyboards
    
    Returns:
        List of consistency grouping dictionaries
    """
    if not clip_storyboards:
        return []
    
    groupings = []
    
    # Basic grouping: Group consecutive clips with similar camera settings
    # In VideoDirectorGPT, this would be more sophisticated (character/product identity, etc.)
    current_group = {
        "group_id": 1,
        "clip_numbers": [],
        "consistency_type": "visual_style",
        "description": "Clips with similar visual style and camera settings"
    }
    
    for i, clip in enumerate(clip_storyboards):
        # Start new group if camera settings change significantly
        if i > 0:
            prev_clip = clip_storyboards[i - 1]
            # Check if camera settings are similar (basic heuristic)
            camera_changed = (
                prev_clip.shot_size != clip.shot_size or
                prev_clip.perspective != clip.perspective
            )
            
            if camera_changed and current_group["clip_numbers"]:
                # Finalize current group
                groupings.append(current_group)
                # Start new group
                current_group = {
                    "group_id": len(groupings) + 1,
                    "clip_numbers": [],
                    "consistency_type": "visual_style",
                    "description": "Clips with similar visual style and camera settings"
                }
        
        current_group["clip_numbers"].append(clip.clip_number)
    
    # Add final group
    if current_group["clip_numbers"]:
        groupings.append(current_group)
    
    # If all clips are in one group, add a note about potential sub-groupings
    if len(groupings) == 1 and len(clip_storyboards) > 2:
        groupings[0]["description"] += " (VideoDirectorGPT planning may identify sub-groupings for character/product consistency)"
    
    return groupings

