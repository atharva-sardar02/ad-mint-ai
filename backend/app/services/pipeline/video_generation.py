"""
Video generation service for generating video clips using Replicate API.
"""
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import List, Optional
import replicate
import httpx

from app.core.config import settings
from app.schemas.generation import Scene, ScenePlan

logger = logging.getLogger(__name__)

# Replicate model configurations
# Primary model: Seedance-1-Lite (ByteDance)
# Fallback models: Minimax Video-01, Kling 1.5, Runway Gen-3 Alpha Turbo
REPLICATE_MODELS = {
    "primary": "bytedance/seedance-1-lite",
    "fallback_1": "minimax-ai/minimax-video-01",
    "fallback_2": "klingai/kling-video",
    "fallback_3": "runway/gen3-alpha-turbo"
}

# Cost per second of video (approximate, varies by model)
# Seedance-1-Lite: ~$0.04/sec (estimated), Minimax: ~$0.05/sec, Kling: ~$0.06/sec, Runway: ~$0.08/sec
MODEL_COSTS = {
    "bytedance/seedance-1-lite": 0.04,
    "minimax-ai/minimax-video-01": 0.05,
    "klingai/kling-video": 0.06,
    "runway/gen3-alpha-turbo": 0.08
}

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 30  # seconds


async def generate_video_clip(
    scene: Scene,
    output_dir: str,
    generation_id: str,
    scene_number: int,
    cancellation_check: Optional[callable] = None
) -> str:
    """
    Generate a video clip from a scene using Replicate API.
    
    Args:
        scene: Scene object with visual_prompt and duration
        output_dir: Directory to save the generated clip
        generation_id: Generation ID for logging and cost tracking
        scene_number: Scene number for logging
        cancellation_check: Optional function to check if generation should be cancelled
    
    Returns:
        str: Path to the generated video clip file
    
    Raises:
        ValueError: If API key is missing or invalid
        RuntimeError: If video generation fails after all retries and fallbacks
    """
    if not settings.REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN not configured")
        raise ValueError("Replicate API token is not configured")
    
    # Check cancellation before starting
    if cancellation_check and cancellation_check():
        raise RuntimeError("Generation cancelled by user")
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename for this clip
    clip_filename = f"{generation_id}_scene_{scene_number}.mp4"
    clip_path = output_path / clip_filename
    
    logger.info(
        f"Generating video clip for scene {scene_number} (generation {generation_id})"
    )
    logger.debug(f"Visual prompt: {scene.visual_prompt[:100]}...")
    logger.debug(f"Target duration: {scene.duration}s")
    
    # Try models in order: primary -> fallback_1 -> fallback_2 -> fallback_3
    models_to_try = [
        REPLICATE_MODELS["primary"],
        REPLICATE_MODELS["fallback_1"],
        REPLICATE_MODELS["fallback_2"],
        REPLICATE_MODELS["fallback_3"]
    ]
    
    last_error = None
    
    for model_name in models_to_try:
        logger.info(f"Attempting video generation with model: {model_name}")
        
        try:
            # Check cancellation before each model attempt
            if cancellation_check and cancellation_check():
                raise RuntimeError("Generation cancelled by user")
            
            # Generate video with retry logic
            video_url = await _generate_with_retry(
                model_name=model_name,
                prompt=scene.visual_prompt,
                duration=scene.duration,
                cancellation_check=cancellation_check
            )
            
            # Download video clip
            logger.info(f"Downloading video clip from {video_url}")
            await _download_video(video_url, clip_path)
            
            # Validate video (duration and aspect ratio)
            await _validate_video(clip_path, scene.duration)
            
            # Track cost
            cost = MODEL_COSTS.get(model_name, 0.05) * scene.duration
            logger.info(
                f"Video clip generated successfully (scene {scene_number}, "
                f"model: {model_name}, cost: ${cost:.4f})"
            )
            
            return str(clip_path)
            
        except RuntimeError as e:
            # Cancellation - re-raise immediately
            if "cancelled" in str(e).lower():
                raise
            last_error = e
            logger.warning(
                f"Model {model_name} failed for scene {scene_number}: {e}. "
                f"Trying fallback model..."
            )
            continue
        except Exception as e:
            last_error = e
            logger.warning(
                f"Unexpected error with model {model_name} for scene {scene_number}: {e}. "
                f"Trying fallback model..."
            )
            continue
    
    # All models failed
    logger.error(
        f"All video generation models failed for scene {scene_number} "
        f"(generation {generation_id})"
    )
    raise RuntimeError(
        f"Video generation failed after trying all models: {last_error}"
    )


async def _generate_with_retry(
    model_name: str,
    prompt: str,
    duration: int,
    cancellation_check: Optional[callable] = None
) -> str:
    """
    Generate video with retry logic and exponential backoff.
    
    Args:
        model_name: Replicate model identifier
        prompt: Visual prompt for video generation
        duration: Target duration in seconds (3-7)
        cancellation_check: Optional function to check cancellation
    
    Returns:
        str: URL to the generated video
    
    Raises:
        RuntimeError: If generation fails after all retries
    """
    client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
    
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Check cancellation before each retry
            if cancellation_check and cancellation_check():
                raise RuntimeError("Generation cancelled by user")
            
            logger.debug(
                f"Calling Replicate API (model: {model_name}, attempt {attempt}/{MAX_RETRIES})"
            )
            
            # Prepare input parameters for Replicate
            # Note: Model-specific parameters may vary - adjust based on actual API
            input_params = {
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": "9:16",  # Vertical for MVP
            }
            
            # Create prediction
            prediction = client.predictions.create(
                model=model_name,
                input=input_params
            )
            
            # Poll for completion
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                # Check cancellation during polling
                if cancellation_check and cancellation_check():
                    # Cancel the prediction if possible
                    try:
                        client.predictions.cancel(prediction.id)
                    except Exception:
                        pass
                    raise RuntimeError("Generation cancelled by user")
                
                await asyncio.sleep(2)  # Poll every 2 seconds
                prediction = client.predictions.get(prediction.id)
            
            # Handle result
            if prediction.status == "succeeded":
                if not prediction.output:
                    raise RuntimeError("Video generation succeeded but no output URL")
                
                # Output may be a URL string or list of URLs
                if isinstance(prediction.output, list):
                    video_url = prediction.output[0]
                else:
                    video_url = prediction.output
                
                logger.info(f"Video generation succeeded (attempt {attempt})")
                return video_url
            
            elif prediction.status == "failed":
                error_msg = prediction.error or "Unknown error"
                raise RuntimeError(f"Video generation failed: {error_msg}")
            
            elif prediction.status == "canceled":
                raise RuntimeError("Video generation was canceled")
            
        except replicate.exceptions.RateLimitError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                # Exponential backoff for rate limits
                delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
                logger.warning(
                    f"Rate limit hit (attempt {attempt}/{MAX_RETRIES}). "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                continue
            raise RuntimeError(f"Rate limit exceeded after {MAX_RETRIES} attempts: {e}")
        
        except replicate.exceptions.ReplicateError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                # Exponential backoff for other API errors
                delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
                logger.warning(
                    f"Replicate API error (attempt {attempt}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                continue
            raise RuntimeError(f"Replicate API error after {MAX_RETRIES} attempts: {e}")
        
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
                logger.warning(
                    f"Unexpected error (attempt {attempt}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                continue
            raise RuntimeError(f"Unexpected error after {MAX_RETRIES} attempts: {e}")
    
    # All retries failed
    raise RuntimeError(
        f"Video generation failed after {MAX_RETRIES} attempts: {last_error}"
    )


async def _download_video(video_url: str, output_path: Path) -> None:
    """
    Download video from URL to local file.
    
    Args:
        video_url: URL of the video to download
        output_path: Path to save the video file
    
    Raises:
        RuntimeError: If download fails
    """
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
            logger.debug(f"Downloading video from {video_url}")
            response = await client.get(video_url)
            response.raise_for_status()
            
            # Write to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Video downloaded successfully to {output_path}")
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to download video from {video_url}: {e}")
        raise RuntimeError(f"Video download failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading video: {e}")
        raise RuntimeError(f"Video download failed: {e}")


async def _validate_video(video_path: Path, expected_duration: int) -> None:
    """
    Validate video duration and aspect ratio.
    
    Args:
        video_path: Path to the video file
        expected_duration: Expected duration in seconds
    
    Raises:
        RuntimeError: If validation fails
    """
    try:
        if not video_path.exists():
            raise RuntimeError(f"Video file not found: {video_path}")
        
        file_size = video_path.stat().st_size
        if file_size == 0:
            raise RuntimeError(f"Video file is empty: {video_path}")
        
        # Validate duration and aspect ratio using ffprobe (via subprocess)
        # ffprobe is available as part of ffmpeg, which MoviePy requires
        import subprocess
        import json
        
        try:
            # Use ffprobe to get video metadata
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "stream=width,height,duration",
                "-of", "json",
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(
                    f"ffprobe failed for {video_path}: {result.stderr}. "
                    f"Skipping detailed validation."
                )
                # Fallback: basic validation passed
                logger.debug(
                    f"Video validation passed (basic): {video_path} "
                    f"(size: {file_size} bytes, expected duration: {expected_duration}s)"
                )
                return
            
            # Parse ffprobe output
            metadata = json.loads(result.stdout)
            
            if "streams" not in metadata or len(metadata["streams"]) == 0:
                logger.warning(f"No video streams found in {video_path}")
                return
            
            # Get first video stream
            video_stream = None
            for stream in metadata["streams"]:
                if stream.get("width") and stream.get("height"):
                    video_stream = stream
                    break
            
            if not video_stream:
                logger.warning(f"No valid video stream found in {video_path}")
                return
            
            # Validate aspect ratio (9:16 for MVP)
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))
            
            if width > 0 and height > 0:
                aspect_ratio = width / height
                expected_aspect = 9 / 16  # 0.5625
                tolerance = 0.1  # Allow 10% tolerance
                
                if abs(aspect_ratio - expected_aspect) > tolerance:
                    logger.warning(
                        f"Video aspect ratio {width}:{height} ({aspect_ratio:.3f}) "
                        f"does not match expected 9:16 ({expected_aspect:.3f}) "
                        f"for {video_path}"
                    )
                    # Don't fail for aspect ratio mismatch in MVP, just warn
            
            # Validate duration
            duration_str = video_stream.get("duration")
            if duration_str:
                try:
                    actual_duration = float(duration_str)
                    # Allow 2 seconds tolerance (videos can be slightly off)
                    duration_tolerance = 2.0
                    
                    if abs(actual_duration - expected_duration) > duration_tolerance:
                        logger.warning(
                            f"Video duration {actual_duration:.2f}s does not match "
                            f"expected {expected_duration}s (tolerance: {duration_tolerance}s) "
                            f"for {video_path}"
                        )
                        # Don't fail for duration mismatch in MVP, just warn
                    
                    logger.debug(
                        f"Video validation passed: {video_path} "
                        f"(duration: {actual_duration:.2f}s, "
                        f"resolution: {width}x{height}, "
                        f"aspect: {aspect_ratio:.3f})"
                    )
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse duration from ffprobe output: {duration_str}")
            else:
                logger.warning(f"No duration found in video stream for {video_path}")
        
        except FileNotFoundError:
            # ffprobe not found - fallback to basic validation
            logger.warning(
                "ffprobe not found. Video validation limited to file existence check. "
                "Install ffmpeg for full validation."
            )
            logger.debug(
                f"Video validation passed (basic): {video_path} "
                f"(size: {file_size} bytes, expected duration: {expected_duration}s)"
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"ffprobe timeout for {video_path}. Skipping detailed validation.")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse ffprobe output for {video_path}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error during video validation for {video_path}: {e}")
            # Don't fail validation if ffprobe has issues
        
    except Exception as e:
        logger.error(f"Video validation failed: {e}")
        raise RuntimeError(f"Video validation failed: {e}")


async def generate_all_clips(
    scene_plan: ScenePlan,
    output_dir: str,
    generation_id: str,
    cancellation_check: Optional[callable] = None
) -> List[str]:
    """
    Generate video clips for all scenes in the scene plan.
    
    Args:
        scene_plan: ScenePlan with scenes to generate
        output_dir: Directory to save clips
        generation_id: Generation ID for logging
        cancellation_check: Optional function to check cancellation
    
    Returns:
        List[str]: List of paths to generated video clips
    
    Raises:
        RuntimeError: If generation fails
    """
    logger.info(
        f"Generating {len(scene_plan.scenes)} video clips for generation {generation_id}"
    )
    
    clip_paths = []
    
    # Generate clips sequentially (can be parallelized later if API allows)
    for i, scene in enumerate(scene_plan.scenes, start=1):
        # Check cancellation before each scene
        if cancellation_check and cancellation_check():
            logger.info(f"Generation cancelled before scene {i}")
            raise RuntimeError("Generation cancelled by user")
        
        try:
            clip_path = await generate_video_clip(
                scene=scene,
                output_dir=output_dir,
                generation_id=generation_id,
                scene_number=i,
                cancellation_check=cancellation_check
            )
            clip_paths.append(clip_path)
            logger.info(f"Scene {i}/{len(scene_plan.scenes)} completed")
            
        except RuntimeError as e:
            if "cancelled" in str(e).lower():
                raise
            logger.error(f"Failed to generate clip for scene {i}: {e}")
            raise
    
    logger.info(
        f"All {len(clip_paths)} video clips generated successfully "
        f"for generation {generation_id}"
    )
    
    return clip_paths

