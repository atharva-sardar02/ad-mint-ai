"""
Video Generation Service for Master Mode.

Generates videos from scene parameters using Veo 3.1, then stitches them together.
"""
import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.pipeline.video_generation import generate_video_clip_with_model
from app.services.master_mode.video_stitcher import stitch_master_mode_videos

logger = logging.getLogger(__name__)


async def generate_scene_video(
    scene_params: Dict[str, Any],
    output_dir: Path,
    scene_number: int,
    generation_id: str
) -> Optional[str]:
    """
    Generate a video for a single scene using Veo 3.1.
    
    Args:
        scene_params: Video generation parameters for the scene
        output_dir: Directory to save the generated video
        scene_number: Scene number for logging
        generation_id: Unique generation ID
        
    Returns:
        Path to generated video file or None if failed
    """
    try:
        logger.info(f"[Video Gen] Scene {scene_number}: Starting video generation")
        
        # Extract parameters
        prompt = scene_params["prompt"]
        duration = scene_params["duration"]
        aspect_ratio = scene_params.get("aspect_ratio", "16:9")
        resolution = scene_params.get("resolution", "1080p")
        generate_audio = scene_params.get("generate_audio", True)
        negative_prompt = scene_params.get("negative_prompt")
        reference_images = scene_params.get("reference_images")
        
        # Create temporary output directory for this scene
        temp_output_dir = output_dir / f"temp_scene_{scene_number}"
        temp_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Log generation details
        logger.info(f"[Video Gen] Scene {scene_number}: Duration={duration}s, Resolution={resolution}, R2V={'Yes' if reference_images else 'No'}")
        logger.info(f"[Video Gen] Scene {scene_number}: Prompt length: {len(prompt)} characters ({len(prompt.split())} words)")
        if reference_images:
            logger.info(f"[Video Gen] Scene {scene_number}: Using {len(reference_images)} reference images for ultra-realistic R2V mode")
        
        # Call existing video generation service with full quality parameters
        result = await generate_video_clip_with_model(
            prompt=prompt,
            duration=duration,
            output_dir=str(temp_output_dir),
            generation_id=generation_id,
            model_name="google/veo-3.1",
            resolution=resolution,
            generate_audio=generate_audio,
            negative_prompt=negative_prompt,
            reference_images=reference_images
        )
        
        # Handle tuple return value (path, cost) or just path
        if isinstance(result, tuple):
            video_path, cost = result
            # cost might be a string already formatted, or a float
            if isinstance(cost, (int, float)):
                logger.info(f"[Video Gen] Scene {scene_number}: Video generated with cost ${cost:.2f}")
            else:
                logger.info(f"[Video Gen] Scene {scene_number}: Video generated with cost {cost}")
        else:
            video_path = result
        
        if video_path and os.path.exists(video_path):
            # Move video to output directory with scene number
            output_path = output_dir / f"scene_{scene_number:02d}.mp4"
            shutil.copy2(video_path, output_path)
            
            # Clean up temp directory
            try:
                shutil.rmtree(temp_output_dir)
            except:
                pass
            
            logger.info(f"[Video Gen] Scene {scene_number}: Video generated successfully -> {output_path}")
            return str(output_path)
        else:
            logger.error(f"[Video Gen] Scene {scene_number}: Video generation failed")
            return None
            
    except Exception as e:
        logger.error(f"[Video Gen] Scene {scene_number}: Error generating video: {e}", exc_info=True)
        return None


async def generate_all_scene_videos(
    video_params_list: List[Dict[str, Any]],
    output_dir: Path,
    generation_id: str,
    max_parallel: int = 4
) -> List[Optional[str]]:
    """
    Generate videos for all scenes in parallel.
    
    Args:
        video_params_list: List of video generation parameters for each scene
        output_dir: Directory to save generated videos
        generation_id: Unique generation ID
        max_parallel: Maximum number of parallel video generations (default: 4)
        
    Returns:
        List of video paths (or None for failed scenes)
    """
    logger.info(f"[Video Gen] Generating {len(video_params_list)} scene videos (max {max_parallel} parallel)")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate videos with controlled parallelism using semaphore
    semaphore = asyncio.Semaphore(max_parallel)
    
    async def generate_with_semaphore(scene_params: Dict[str, Any], scene_num: int):
        async with semaphore:
            return await generate_scene_video(scene_params, output_dir, scene_num, generation_id)
    
    # Create tasks for all scenes
    tasks = [
        generate_with_semaphore(params, params["scene_number"])
        for params in video_params_list
    ]
    
    # Run all tasks
    video_paths = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to None
    video_paths = [
        path if not isinstance(path, Exception) else None
        for path in video_paths
    ]
    
    successful = sum(1 for path in video_paths if path is not None)
    logger.info(f"[Video Gen] Generated {successful}/{len(video_params_list)} videos successfully")
    
    return video_paths


def extract_transitions_from_cohesion(
    cohesion_analysis: Dict[str, Any]
) -> List[str]:
    """
    Extract transition types from cohesion analysis.
    
    Args:
        cohesion_analysis: Cohesion analysis with pairwise transitions
        
    Returns:
        List of transition types for each scene boundary
    """
    transitions = []
    
    # Get pairwise analysis
    pair_wise = cohesion_analysis.get("pair_wise_analysis", [])
    
    for pair in pair_wise:
        # Default transition based on transition score
        score = pair.get("transition_score", 70)
        
        if score >= 85:
            transition = "crossfade"  # Smooth transition for high scores
        elif score >= 70:
            transition = "cut"  # Direct cut for medium scores
        else:
            transition = "fade"  # Fade for lower scores
        
        transitions.append(transition)
    
    # If no pairwise analysis, use default crossfades
    if not transitions and cohesion_analysis.get("total_scenes", 0) > 1:
        total_scenes = cohesion_analysis["total_scenes"]
        transitions = ["crossfade"] * (total_scenes - 1)
    
    logger.info(f"[Video Gen] Extracted transitions: {transitions}")
    return transitions


async def generate_and_stitch_videos(
    video_params_list: List[Dict[str, Any]],
    cohesion_analysis: Dict[str, Any],
    output_dir: Path,
    final_output_path: Path,
    generation_id: str,
    max_parallel: int = 4
) -> Optional[str]:
    """
    Generate all scene videos and stitch them together into final video.
    
    Args:
        video_params_list: List of video generation parameters for each scene
        cohesion_analysis: Cohesion analysis with transition information
        output_dir: Directory to save individual scene videos
        final_output_path: Path for the final stitched video
        generation_id: Unique generation ID
        max_parallel: Maximum number of parallel video generations
        
    Returns:
        Path to final stitched video or None if failed
    """
    try:
        logger.info(f"[Master Mode Video] Starting video generation and stitching")
        start_time = datetime.now()
        
        # Step 1: Generate all scene videos in parallel
        logger.info(f"[Master Mode Video] Step 1: Generating {len(video_params_list)} scene videos")
        video_paths = await generate_all_scene_videos(
            video_params_list=video_params_list,
            output_dir=output_dir,
            generation_id=generation_id,
            max_parallel=max_parallel
        )
        
        # Check if all videos were generated
        failed_scenes = [i + 1 for i, path in enumerate(video_paths) if path is None]
        if failed_scenes:
            logger.error(f"[Master Mode Video] Failed to generate videos for scenes: {failed_scenes}")
            if len(failed_scenes) == len(video_paths):
                logger.error(f"[Master Mode Video] All videos failed to generate")
                return None
        
        # Filter out None values (failed videos)
        valid_video_paths = [path for path in video_paths if path is not None]
        
        if not valid_video_paths:
            logger.error(f"[Master Mode Video] No valid videos to stitch")
            return None
        
        logger.info(f"[Master Mode Video] Generated {len(valid_video_paths)} videos successfully")
        
        # Step 2: Extract transitions from cohesion analysis
        logger.info(f"[Master Mode Video] Step 2: Extracting transitions")
        transitions = extract_transitions_from_cohesion(cohesion_analysis)
        
        # Adjust transitions if some videos failed
        if len(valid_video_paths) < len(video_params_list):
            transitions = transitions[:len(valid_video_paths) - 1]
        
        # Step 3: Stitch videos together using Master Mode stitcher
        logger.info(f"[Master Mode Video] Step 3: Stitching {len(valid_video_paths)} videos")
        logger.info(f"[Master Mode Video] Transitions: {transitions}")
        
        final_video_path = stitch_master_mode_videos(
            video_paths=valid_video_paths,
            output_path=str(final_output_path),
            transitions=transitions
        )
        
        if final_video_path:
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[Master Mode Video] Successfully created final video: {final_video_path}")
            logger.info(f"[Master Mode Video] Total time: {duration:.1f}s")
            return final_video_path
        else:
            logger.error(f"[Master Mode Video] Failed to stitch videos")
            return None
            
    except Exception as e:
        logger.error(f"[Master Mode Video] Error in video generation and stitching: {e}", exc_info=True)
        return None

