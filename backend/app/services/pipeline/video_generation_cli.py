"""
Video generation CLI service for generating videos with automatic VBench quality scoring.

This service supports three modes:
- Text-to-video: Generate videos from text prompts
- Image-to-video: Generate videos from hero frame images + motion prompts
- Storyboard mode: Generate videos from storyboard start/end frames with enhanced motion prompts
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.services.pipeline.video_generation import (
    generate_video_clip_with_model,
    MODEL_COSTS,
    REPLICATE_MODELS,
)

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Metadata for a generated video."""
    file_path: str
    rank: int
    vbench_scores: Dict[str, float]  # All 16 VBench dimensions + overall
    generation_params: Dict  # prompt, model, settings, seed, timestamp, cost


@dataclass
class VideoGenerationResult:
    """Result of video generation for a single mode."""
    videos: List[VideoMetadata]  # Sorted by quality score
    generation_trace: Dict  # Complete trace with prompts, videos, scores, costs, timestamps
    mode: str  # "text-to-video" or "image-to-video" or "storyboard"
    hero_frame_path: Optional[str] = None  # If image-to-video mode
    storyboard_ref: Optional[str] = None  # If storyboard mode


@dataclass
class StoryboardVideoGenerationResult:
    """Result of storyboard video generation."""
    storyboard_path: str  # Path to storyboard_enhanced_motion_prompts.json
    clips: List[Dict]  # With videos per clip
    clip_results: List[VideoGenerationResult]  # For each clip
    clip_frame_paths: Dict  # Mapping clip numbers to start/end frame paths
    unified_narrative_path: Optional[str] = None  # Preserved from Story 9.1
    summary: Dict = field(default_factory=dict)  # Overall statistics


async def generate_text_to_video(
    prompt: str,
    num_attempts: int = 3,
    model_name: str = "kwaivgi/kling-v2.1",
    duration: int = 5,
    negative_prompt: Optional[str] = None,
    output_dir: Path = None,
    seed: Optional[int] = None,
) -> VideoGenerationResult:
    """
    Generate videos from text prompt (text-to-video mode).
    
    Args:
        prompt: Text prompt for video generation
        num_attempts: Number of video attempts to generate (default: 3)
        model_name: Replicate model name (default: openai/sora-2)
        duration: Video duration in seconds (default: 5)
        negative_prompt: Optional negative prompt
        output_dir: Output directory for videos
        seed: Optional seed for reproducibility
    
    Returns:
        VideoGenerationResult with generated videos (not yet scored)
    """
    if output_dir is None:
        raise ValueError("output_dir is required")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating {num_attempts} text-to-video attempts with model {model_name}")
    
    videos: List[VideoMetadata] = []
    generation_trace = {
        "mode": "text-to-video",
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "model": model_name,
        "duration": duration,
        "num_attempts": num_attempts,
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "videos": [],
        "costs": [],
    }
    
    total_cost = 0.0
    
    for attempt in range(1, num_attempts + 1):
        generation_id = f"text_to_video_{int(time.time())}_{attempt}"
        
        try:
            logger.info(f"Generating video attempt {attempt}/{num_attempts}")
            
            # Generate video
            video_path, model_used = await generate_video_clip_with_model(
                prompt=prompt,
                duration=duration,
                output_dir=str(output_dir),
                generation_id=generation_id,
                model_name=model_name,
            )
            
            # Calculate cost
            cost = MODEL_COSTS.get(model_used, 0.05) * duration
            total_cost += cost
            
            # Create metadata (scores will be added later by quality scoring service)
            video_metadata = VideoMetadata(
                file_path=video_path,
                rank=0,  # Will be set after ranking
                vbench_scores={},  # Will be populated by quality scoring
                generation_params={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "model": model_used,
                    "duration": duration,
                    "seed": seed,
                    "timestamp": datetime.now().isoformat(),
                    "cost": cost,
                    "attempt": attempt,
                },
            )
            
            videos.append(video_metadata)
            
            # Add to trace
            generation_trace["videos"].append({
                "attempt": attempt,
                "file_path": video_path,
                "model": model_used,
                "cost": cost,
            })
            generation_trace["costs"].append(cost)
            
            logger.info(f"Video attempt {attempt} generated successfully: {video_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate video attempt {attempt}: {e}", exc_info=True)
            generation_trace["videos"].append({
                "attempt": attempt,
                "error": str(e),
            })
            continue
    
    generation_trace["total_cost"] = total_cost
    
    return VideoGenerationResult(
        videos=videos,
        generation_trace=generation_trace,
        mode="text-to-video",
    )


async def generate_image_to_video(
    hero_frame_path: str,
    motion_prompt: str,
    num_attempts: int = 3,
    model_name: str = "kwaivgi/kling-v2.1",
    duration: int = 5,
    negative_prompt: Optional[str] = None,
    output_dir: Path = None,
    seed: Optional[int] = None,
    end_frame_path: Optional[str] = None,
) -> VideoGenerationResult:
    """
    Generate videos from hero frame image + motion prompt (image-to-video mode).
    
    Args:
        hero_frame_path: Path to hero frame image
        motion_prompt: Motion prompt for video generation
        num_attempts: Number of video attempts to generate (default: 3)
        model_name: Replicate model name (default: openai/sora-2)
        duration: Video duration in seconds (default: 5)
        negative_prompt: Optional negative prompt
        output_dir: Output directory for videos
        seed: Optional seed for reproducibility
    
    Returns:
        VideoGenerationResult with generated videos (not yet scored)
    """
    if output_dir is None:
        raise ValueError("output_dir is required")
    
    # Validate hero frame exists
    hero_frame = Path(hero_frame_path)
    if not hero_frame.exists():
        raise FileNotFoundError(f"Hero frame not found: {hero_frame_path}")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating {num_attempts} image-to-video attempts with model {model_name}")
    logger.info(f"Start frame (start_image): {hero_frame_path}")
    if end_frame_path:
        logger.info(f"End frame (end_image): {end_frame_path} - Using for smooth transition (Kling v2.1)")
    else:
        logger.info("End frame: Not provided - Using start frame only")
    logger.info(f"Motion prompt: {motion_prompt[:100]}...")
    
    videos: List[VideoMetadata] = []
    generation_trace = {
        "mode": "image-to-video",
        "hero_frame_path": str(hero_frame.absolute()),
        "motion_prompt": motion_prompt,
        "negative_prompt": negative_prompt,
        "model": model_name,
        "duration": duration,
        "num_attempts": num_attempts,
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "videos": [],
        "costs": [],
    }
    
    total_cost = 0.0
    
    # Use motion prompt for image-to-video generation
    # The image will be passed to the API via image_input parameter
    
    for attempt in range(1, num_attempts + 1):
        generation_id = f"image_to_video_{int(time.time())}_{attempt}"
        
        try:
            logger.info(f"Generating video attempt {attempt}/{num_attempts}")
            logger.info(f"Using hero frame: {hero_frame_path} for image-to-video generation")
            
            # Generate video with image input (image-to-video mode)
            video_path, model_used = await generate_video_clip_with_model(
                prompt=motion_prompt,
                duration=duration,
                output_dir=str(output_dir),
                generation_id=generation_id,
                model_name=model_name,
                image_input=str(hero_frame.absolute()),
                end_image_input=end_frame_path,
                negative_prompt=negative_prompt,
            )
            
            # Calculate cost
            cost = MODEL_COSTS.get(model_used, 0.05) * duration
            total_cost += cost
            
            # Create metadata
            video_metadata = VideoMetadata(
                file_path=video_path,
                rank=0,  # Will be set after ranking
                vbench_scores={},  # Will be populated by quality scoring
                generation_params={
                    "hero_frame_path": str(hero_frame.absolute()),
                    "motion_prompt": motion_prompt,
                    "negative_prompt": negative_prompt,
                    "model": model_used,
                    "duration": duration,
                    "seed": seed,
                    "timestamp": datetime.now().isoformat(),
                    "cost": cost,
                    "attempt": attempt,
                },
            )
            
            videos.append(video_metadata)
            
            # Add to trace
            generation_trace["videos"].append({
                "attempt": attempt,
                "file_path": video_path,
                "model": model_used,
                "cost": cost,
            })
            generation_trace["costs"].append(cost)
            
            logger.info(f"Video attempt {attempt} generated successfully: {video_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate video attempt {attempt}: {e}", exc_info=True)
            generation_trace["videos"].append({
                "attempt": attempt,
                "error": str(e),
            })
            continue
    
    generation_trace["total_cost"] = total_cost
    
    return VideoGenerationResult(
        videos=videos,
        generation_trace=generation_trace,
        mode="image-to-video",
        hero_frame_path=str(hero_frame.absolute()),
    )


async def generate_storyboard_videos(
    storyboard_json_path: str,
    num_attempts: int = 3,
    model_name: str = "kwaivgi/kling-v2.1",
    duration: int = 5,
    negative_prompt: Optional[str] = None,
    output_dir: Path = None,
    seed: Optional[int] = None,
) -> StoryboardVideoGenerationResult:
    """
    Generate videos from storyboard start/end frames with enhanced motion prompts (storyboard mode).
    
    Args:
        storyboard_json_path: Path to storyboard_enhanced_motion_prompts.json from Story 9.1
        num_attempts: Number of video attempts per clip (default: 3)
        model_name: Replicate model name (default: openai/sora-2)
        duration: Video duration in seconds (default: 5)
        negative_prompt: Optional negative prompt
        output_dir: Output directory for videos
        seed: Optional seed for reproducibility
    
    Returns:
        StoryboardVideoGenerationResult with generated videos per clip (not yet scored)
    """
    import json
    
    if output_dir is None:
        raise ValueError("output_dir is required")
    
    # Load and validate storyboard JSON
    storyboard_path = Path(storyboard_json_path)
    if not storyboard_path.exists():
        raise FileNotFoundError(f"Storyboard JSON not found: {storyboard_json_path}")
    
    with open(storyboard_path, "r", encoding="utf-8") as f:
        storyboard_data = json.load(f)
    
    # Validate JSON structure
    if "clips" not in storyboard_data:
        raise ValueError("Storyboard JSON missing 'clips' array")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating videos for {len(storyboard_data['clips'])} clips from storyboard")
    
    clip_results: List[VideoGenerationResult] = []
    clips_data: List[Dict] = []
    clip_frame_paths = storyboard_data.get("clip_frame_paths", {})
    unified_narrative_path = storyboard_data.get("unified_narrative_path")
    
    for clip_data in storyboard_data["clips"]:
        clip_number = clip_data.get("clip_number")
        enhanced_motion_prompt = clip_data.get("enhanced_motion_prompt")
        start_frame_path = clip_data.get("start_frame_path")
        end_frame_path = clip_data.get("end_frame_path")
        
        if not clip_number:
            logger.warning("Clip missing clip_number, skipping")
            continue
        
        if not enhanced_motion_prompt:
            logger.warning(f"Clip {clip_number} missing enhanced_motion_prompt, skipping")
            continue
        
        if not start_frame_path:
            logger.warning(f"Clip {clip_number} missing start_frame_path, skipping")
            continue
        
        # Validate frame images exist - resolve relative paths
        # Paths in JSON are relative to backend/ directory (e.g., "output/storyboards/...")
        start_frame = Path(start_frame_path)
        if not start_frame.exists():
            # Try relative to storyboard directory
            start_frame = storyboard_path.parent / start_frame_path
            if not start_frame.exists():
                # Try relative to backend directory (common case)
                backend_dir = Path(__file__).parent.parent.parent  # Go up from app/services/pipeline to backend
                start_frame = backend_dir / start_frame_path
                if not start_frame.exists():
                    logger.warning(f"Clip {clip_number} start frame not found: {start_frame_path}, skipping")
                    logger.warning(f"  Tried: {Path(start_frame_path).absolute()}")
                    logger.warning(f"  Tried: {storyboard_path.parent / start_frame_path}")
                    logger.warning(f"  Tried: {backend_dir / start_frame_path}")
                    continue
        
        logger.info(f"Clip {clip_number}: Using start frame: {start_frame.absolute()}")
        
        # Create clip-specific output directory
        clip_output_dir = output_dir / f"clip_{clip_number:03d}"
        clip_output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating videos for clip {clip_number}")
        logger.info(f"Start frame: {start_frame}")
        logger.info(f"Enhanced motion prompt: {enhanced_motion_prompt[:100]}...")
        
        # Generate videos for this clip using image-to-video mode
        # DEFAULT BEHAVIOR: Use end_frame if available for better continuity (Kling v2.1 supports this)
        # This ensures smooth transitions between clips in storyboard mode
        end_frame_path_resolved = None
        if end_frame_path:
            end_frame = Path(end_frame_path)
            if not end_frame.exists():
                end_frame = storyboard_path.parent / end_frame_path
            if not end_frame.exists():
                backend_dir = Path(__file__).parent.parent.parent
                end_frame = backend_dir / end_frame_path
            if end_frame.exists():
                end_frame_path_resolved = str(end_frame.absolute())
                logger.info(f"Clip {clip_number}: Using end frame for smooth transition: {end_frame.absolute()}")
            else:
                logger.warning(f"Clip {clip_number}: End frame not found, using start frame only: {end_frame_path}")
        else:
            logger.info(f"Clip {clip_number}: No end frame specified, using start frame only")
        
        clip_result = await generate_image_to_video(
            hero_frame_path=str(start_frame.absolute()),
            motion_prompt=enhanced_motion_prompt,
            num_attempts=num_attempts,
            model_name=model_name,
            duration=duration,
            negative_prompt=negative_prompt,
            output_dir=clip_output_dir,
            seed=seed,
            end_frame_path=end_frame_path_resolved,
        )
        
        # Update clip result with storyboard context
        clip_result.storyboard_ref = str(storyboard_path.absolute())
        clip_result.generation_trace["clip_number"] = clip_number
        clip_result.generation_trace["start_frame_path"] = str(start_frame.absolute())
        if end_frame_path:
            end_frame = Path(end_frame_path)
            if not end_frame.exists():
                end_frame = storyboard_path.parent / end_frame_path
            if not end_frame.exists():
                # Try relative to backend directory
                backend_dir = Path(__file__).parent.parent.parent
                end_frame = backend_dir / end_frame_path
            if end_frame.exists():
                clip_result.generation_trace["end_frame_path"] = str(end_frame.absolute())
                logger.info(f"Clip {clip_number}: Using end frame: {end_frame.absolute()}")
        
        clip_results.append(clip_result)
        
        # Store clip data
        clips_data.append({
            "clip_number": clip_number,
            "videos": [v.file_path for v in clip_result.videos],
            "start_frame_path": str(start_frame.absolute()),
            "end_frame_path": str(end_frame.absolute()) if end_frame_path else None,
        })
    
    # Calculate summary statistics
    total_clips = len(clip_results)
    total_videos = sum(len(cr.videos) for cr in clip_results)
    total_cost = sum(cr.generation_trace.get("total_cost", 0.0) for cr in clip_results)
    
    summary = {
        "total_clips": total_clips,
        "total_videos": total_videos,
        "total_cost": total_cost,
        "timestamp": datetime.now().isoformat(),
    }
    
    return StoryboardVideoGenerationResult(
        storyboard_path=str(storyboard_path.absolute()),
        clips=clips_data,
        clip_results=clip_results,
        clip_frame_paths=clip_frame_paths,
        unified_narrative_path=unified_narrative_path,
        summary=summary,
    )

