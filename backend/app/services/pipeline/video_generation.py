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
# Default model: Sora 2 (OpenAI) - State-of-the-art realism with exceptional physics
# Top models ranked by quality: Sora 2, Veo 3, Wan 2.5, PixVerse V5, Kling 2.5 Turbo, Hailuo 02, Seedance 1.0
REPLICATE_MODELS = {
    "default": "openai/sora-2",  # Sora 2 - Recommended default
    "veo_3": "google/veo-3",
    "pixverse_v5": "pixverse/pixverse-v5",
    "kling_2_5": "klingai/kling-2.5-turbo",
    "hailuo_02": "minimax-ai/hailuo-02",
    "seedance_1": "bytedance/seedance-1",
    # Legacy models (kept for backward compatibility)
    "primary": "bytedance/seedance-1-lite",
    "fallback_1": "minimax-ai/minimax-video-01",
    "fallback_2": "klingai/kling-video",
    "fallback_3": "runway/gen3-alpha-turbo",
    "sora_2": "openai/sora-2"
}

# Cost per second of video (approximate, varies by model)
# Updated costs for 2025 models
MODEL_COSTS = {
    # Top-tier models
    "openai/sora-2": 0.10,  # Default - state-of-the-art
    "google/veo-3": 0.12,  # Premium cinematic quality
    "pixverse/pixverse-v5": 0.06,  # Balanced quality & cost
    "klingai/kling-2.5-turbo": 0.07,  # Fast cinematic
    "minimax-ai/hailuo-02": 0.09,  # Physics proficiency
    "bytedance/seedance-1": 0.05,  # Multi-shot specialist
    # Legacy models
    "bytedance/seedance-1-lite": 0.04,
    "minimax-ai/minimax-video-01": 0.05,
    "klingai/kling-video": 0.06,
    "runway/gen3-alpha-turbo": 0.08,
}

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 30  # seconds

# Model seed parameter support mapping
# Maps model name to (seed_parameter_name, verified_support)
# Most models use "seed" as the parameter name
MODEL_SEED_SUPPORT = {
    # Newer models (2025) - most use "seed" parameter
    "openai/sora-2": ("seed", True),  # Sora-2 uses "seed" parameter (OpenAI standard)
    "google/veo-3": ("seed", False),  # Likely supports seed, but not verified
    "pixverse/pixverse-v5": ("seed", False),  # Likely supports seed, but not verified
    "klingai/kling-2.5-turbo": ("seed", False),  # Likely supports seed, but not verified
    "minimax-ai/hailuo-02": ("seed", False),  # Likely supports seed, but not verified
    "bytedance/seedance-1": ("seed", False),  # Likely supports seed, but not verified
    # Legacy models - verified support
    "bytedance/seedance-1-lite": ("seed", True),
    "minimax-ai/minimax-video-01": ("seed", True),
    "klingai/kling-video": ("seed", True),
    "runway/gen3-alpha-turbo": ("seed", True),
    # Note: Some models may use different parameter names:
    # - "random_seed" (less common)
    # - "noise_seed" (rare)
    # If a model doesn't support seed, Replicate API will ignore it silently
}


async def generate_video_clip_with_model(
    prompt: str,
    duration: int,
    output_dir: str,
    generation_id: str,
    model_name: str,
    cancellation_check: Optional[callable] = None,
    clip_index: Optional[int] = None
) -> tuple[str, str]:
    """
    Generate a single video clip with a specific model (bypasses pipeline).
    
    Args:
        prompt: Visual prompt for video generation
        duration: Duration in seconds (3-7)
        output_dir: Directory to save the generated clip
        generation_id: Generation ID for logging and cost tracking
        model_name: Specific model to use (must be in REPLICATE_MODELS or MODEL_COSTS)
        cancellation_check: Optional function to check if generation should be cancelled
        clip_index: Optional index for multiple clips (used in filename)
    
    Returns:
        tuple[str, str]: (Path to the generated video clip file, Model name used)
    
    Raises:
        ValueError: If API key is missing or invalid, or model not found
        RuntimeError: If video generation fails
    """
    if not settings.REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN not configured")
        raise ValueError("Replicate API token is not configured")
    
    # Validate model name
    if model_name not in MODEL_COSTS:
        raise ValueError(f"Model '{model_name}' not found in available models")
    
    # Check cancellation before starting
    if cancellation_check and cancellation_check():
        raise RuntimeError("Generation cancelled by user")
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename (with index if generating multiple clips)
    if clip_index is not None:
        clip_filename = f"{generation_id}_single_clip_{clip_index}.mp4"
    else:
        clip_filename = f"{generation_id}_single_clip.mp4"
    clip_path = output_path / clip_filename
    
    logger.info(f"Generating single clip with model {model_name} (generation {generation_id})")
    logger.debug(f"Visual prompt: {prompt[:100]}...")
    logger.debug(f"Target duration: {duration}s")
    
    try:
        # Generate video with retry logic
        video_url = await _generate_with_retry(
            model_name=model_name,
            prompt=prompt,
            duration=duration,
            cancellation_check=cancellation_check,
            reference_image_path=None,
            scene_number=clip_index,
        )
        
        # Download video clip
        logger.info(f"Downloading video clip from {video_url}")
        await _download_video(video_url, clip_path)
        
        # Validate video (duration and aspect ratio)
        await _validate_video(clip_path, duration)
        
        # Track cost
        cost = MODEL_COSTS.get(model_name, 0.05) * duration
        logger.info(
            f"Video clip generated successfully (model: {model_name}, cost: ${cost:.4f})"
        )
        
        # Return both clip path and model name used
        return (str(clip_path), model_name)
        
    except Exception as e:
        logger.error(f"Failed to generate clip with model {model_name}: {e}", exc_info=True)
        raise RuntimeError(f"Video generation failed with model {model_name}: {e}")


async def generate_video_clip(
    scene: Scene,
    output_dir: str,
    generation_id: str,
    scene_number: int,
    cancellation_check: Optional[callable] = None,
    seed: Optional[int] = None,
    preferred_model: Optional[str] = None,
    reference_image_path: Optional[str] = None,
) -> tuple[str, str]:
    """
    Generate a video clip from a scene using Replicate API.
    
    Args:
        scene: Scene object with visual_prompt and duration
        output_dir: Directory to save the generated clip
        generation_id: Generation ID for logging and cost tracking
        scene_number: Scene number for logging
        cancellation_check: Optional function to check if generation should be cancelled
        seed: Optional seed value for visual consistency across scenes
    
    Returns:
        tuple[str, str]: (Path to the generated video clip file, Model name used)
    
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
    
    # Try models in order: preferred_model (if specified) -> default (Sora 2) -> fallback chain
    models_to_try = []
    if preferred_model and preferred_model in MODEL_COSTS:
        models_to_try.append(preferred_model)
        logger.info(f"Using preferred model: {preferred_model}")
    else:
        # Use Sora 2 as default when no model is specified
        models_to_try.append(REPLICATE_MODELS["default"])
        logger.info(f"Using default model: {REPLICATE_MODELS['default']}")
    
    # Add fallback chain (only models that exist and work)
    # Removed models that return 404: 
    # - klingai/kling-2.5-turbo (404)
    # - klingai/kling-video (404)
    # - runway/gen3-alpha-turbo (404)
    # - bytedance/seedance-1 (404)
    # - minimax-ai/hailuo-02 (404)
    models_to_try.extend([
        REPLICATE_MODELS["veo_3"],  # May have rate limits but exists
        REPLICATE_MODELS["pixverse_v5"],  # Reliable fallback
        # Legacy fallbacks (verified to exist)
        REPLICATE_MODELS["primary"],  # bytedance/seedance-1-lite
        REPLICATE_MODELS["fallback_1"],  # minimax-ai/minimax-video-01
    ])
    
    # Remove duplicates while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]
    
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
                cancellation_check=cancellation_check,
                seed=seed,
                reference_image_path=reference_image_path,
                scene_number=scene_number,
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
            
            # Return both clip path and model name used for accurate cost tracking
            return (str(clip_path), model_name)
            
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
    cancellation_check: Optional[callable] = None,
    seed: Optional[int] = None,
    reference_image_path: Optional[str] = None,
    scene_number: Optional[int] = None,
) -> str:
    """
    Generate video with retry logic and exponential backoff.
    
    Args:
        model_name: Replicate model identifier
        prompt: Visual prompt for video generation
        duration: Target duration in seconds (3-7)
        cancellation_check: Optional function to check cancellation
        seed: Optional seed value for visual consistency
    
    Returns:
        str: URL to the generated video
    
    Raises:
        RuntimeError: If generation fails after all retries
    """
    client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
    
    last_error = None
    use_seed = seed is not None  # Track whether to use seed (may be disabled if model doesn't support it)
    
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
            if model_name == "openai/sora-2":
                # Sora-2 requires aspect_ratio as "portrait" or "landscape"
                input_params = {
                    "prompt": prompt,
                    "duration": duration,
                    "aspect_ratio": "portrait",  # Vertical for MVP
                    "quality": "high",  # Request high quality output
                }
            elif model_name == "google/veo-3":
                # Veo 3 only supports duration values: 4, 6, or 8 seconds
                # Round to nearest valid duration
                valid_durations = [4, 6, 8]
                veo_duration = min(valid_durations, key=lambda x: abs(x - duration))
                if veo_duration != duration:
                    logger.debug(f"Veo-3: Rounding duration from {duration}s to {veo_duration}s (valid values: 4, 6, 8)")
                input_params = {
                    "prompt": prompt,
                    "duration": veo_duration,
                    "aspect_ratio": "9:16",  # Vertical for MVP
                }
            elif model_name == "pixverse/pixverse-v5":
                # PixVerse requires quality as resolution string: "360p", "540p", "720p", "1080p"
                input_params = {
                    "prompt": prompt,
                    "duration": duration,
                    "aspect_ratio": "9:16",  # Vertical for MVP
                    "quality": "1080p",  # Use resolution string instead of "high"
                }
                # Log exact Sora-2 prompt being sent
                scene_info = f"SCENE {scene_number}" if scene_number else "SCENE"
                logger.info("=" * 80)
                logger.info(f"EXACT SORA-2 PROMPT FOR {scene_info} (duration: {duration}s):")
                logger.info("=" * 80)
                logger.info(prompt)
                logger.info("=" * 80)
                if reference_image_path:
                    logger.info(f"Reference image path: {reference_image_path}")
                logger.info("=" * 80)
                # If a reference image is available, pass it as media so Sora can
                # condition on the actual product visuals instead of inferred text.
                if reference_image_path:
                    try:
                        # Verify file exists and is accessible
                        image_path_obj = Path(reference_image_path)
                        if not image_path_obj.exists():
                            logger.error(
                                f"Reference image file does not exist: {reference_image_path}"
                            )
                        else:
                            # Replicate Python SDK: For Sora-2, try "image" parameter first
                            # The SDK should handle file upload automatically
                            # If that doesn't work, we'll try input_reference with file object
                            absolute_path = str(image_path_obj.absolute())
                            
                            # Try "image" parameter (common Replicate parameter name)
                            # The SDK will automatically upload local files
                            input_params["image"] = absolute_path
                            logger.info(
                                f"Attached reference image for Sora-2: {reference_image_path} "
                                f"(size: {image_path_obj.stat().st_size} bytes, "
                                f"readable: {os.access(image_path_obj, os.R_OK)}, parameter: image)"
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to attach reference image '{reference_image_path}' "
                            f"for Sora-2: {e}",
                            exc_info=True
                        )
                        if image_file_handle:
                            image_file_handle.close()
                            image_file_handle = None
            else:
                # Other models use aspect ratio as ratio string
                input_params = {
                    "prompt": prompt,
                    "duration": duration,
                    "aspect_ratio": "9:16",  # Vertical for MVP
                }
                # Log exact prompt for other models too
                scene_info = f"SCENE {scene_number}" if scene_number else "SCENE"
                logger.info("=" * 80)
                logger.info(f"EXACT PROMPT FOR {model_name} - {scene_info} (duration: {duration}s):")
                logger.info("=" * 80)
                logger.info(prompt)
                logger.info("=" * 80)
            
            # Add seed parameter if provided and not disabled (for visual consistency)
            # Note: Not all Replicate models support seed parameter - API will ignore if unsupported
            if use_seed and seed is not None:
                # Get model-specific seed parameter name (defaults to "seed")
                seed_param_name, verified = MODEL_SEED_SUPPORT.get(
                    model_name, 
                    ("seed", False)  # Default to "seed" if model not in mapping
                )
                
                # Add seed parameter with model-specific name
                input_params[seed_param_name] = seed
                logger.debug(
                    f"Using {seed_param_name}={seed} for video generation with model {model_name}"
                )
                
                # Log warning for models with unverified seed support
                if not verified:
                    logger.warning(
                        f"Seed parameter ({seed_param_name}) provided for model {model_name} - "
                        f"seed support not verified. API will ignore if model doesn't support it."
                    )
            
            # Create prediction
            # Note: If model doesn't support seed parameter, Replicate API will ignore it silently
            # or return an error. We handle errors in the exception handlers below.
            # Track file handles that need to be closed
            file_handles_to_close = []
            if "input_reference" in input_params and hasattr(input_params["input_reference"], "read"):
                file_handles_to_close.append(input_params["input_reference"])
            
            try:
                prediction = client.predictions.create(
                    model=model_name,
                    input=input_params
                )
            finally:
                # Close any file handles after API call (Replicate SDK reads them immediately)
                for fh in file_handles_to_close:
                    try:
                        fh.close()
                    except Exception:
                        pass
            
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
            
        except replicate.exceptions.ReplicateError as e:
            last_error = e
            # Check if it's a rate limit error (status 429) or validation error
            error_str = str(e).lower()
            is_rate_limit = "429" in error_str or "rate limit" in error_str or "too many requests" in error_str
            
            if is_rate_limit and attempt < MAX_RETRIES:
                # Exponential backoff for rate limits
                delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
                logger.warning(
                    f"Rate limit hit (attempt {attempt}/{MAX_RETRIES}). "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                continue
            
            # Check if error is related to unsupported seed parameter
            # Check for common seed parameter names in error message
            seed_param_name, _ = MODEL_SEED_SUPPORT.get(model_name, ("seed", False))
            seed_error_keywords = ["seed", "random_seed", "noise_seed", seed_param_name]
            is_seed_error = (
                use_seed and 
                any(keyword in error_str for keyword in seed_error_keywords) and 
                ("invalid" in error_str or "not supported" in error_str or "unknown" in error_str or "unexpected" in error_str)
            )
            
            if is_seed_error:
                logger.warning(
                    f"Model {model_name} may not support {seed_param_name} parameter: {e}. "
                    f"Retrying without seed parameter..."
                )
                # Disable seed for remaining attempts if seed parameter caused the error
                if attempt < MAX_RETRIES:
                    use_seed = False  # Disable seed for future attempts
                    logger.info(f"Retrying {model_name} without seed parameter (attempt {attempt + 1}/{MAX_RETRIES})")
                    delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
                    await asyncio.sleep(delay)
                    continue
            
            # Handle validation errors (422) - try alternative parameter names for reference image
            if ("422" in str(e) or "validation" in error_str) and model_name == "openai/sora-2" and reference_image_path:
                # Try alternative parameter names for reference image
                image_path_obj = Path(reference_image_path)
                
                if "image" in input_params and image_path_obj.exists():
                    # If "image" parameter failed, try "input_reference" with file object
                    logger.warning(
                        f"Parameter 'image' failed for Sora-2 (error: {str(e)[:100]}), "
                        f"trying 'input_reference' with file object..."
                    )
                    try:
                        # Remove failed "image" parameter
                        del input_params["image"]
                        # Try with opened file object - keep it open for the API call
                        image_file_handle = open(image_path_obj, "rb")
                        input_params["input_reference"] = image_file_handle
                        logger.info(f"Retrying with input_reference parameter (file object)")
                        # Retry the API call immediately (same attempt)
                        continue
                    except Exception as retry_error:
                        logger.error(f"Failed to retry with input_reference: {retry_error}")
                        if 'image_file_handle' in locals():
                            image_file_handle.close()
                
                elif "input_reference" in str(e).lower() and image_path_obj.exists():
                    # If input_reference failed, try without reference image (Sora-2 should still work)
                    logger.warning(
                        f"Reference image parameter failed for Sora-2, trying without reference image..."
                    )
                    try:
                        # Remove reference image parameter and retry
                        if "image" in input_params:
                            del input_params["image"]
                        if "input_reference" in input_params:
                            del input_params["input_reference"]
                        logger.info(f"Retrying Sora-2 without reference image")
                        continue
                    except Exception as retry_error:
                        logger.error(f"Failed to retry without reference image: {retry_error}")
                
                # If all parameter attempts failed, raise the error (will trigger fallback model)
                logger.error(
                    f"Sora-2 failed with reference image parameters. Error: {e}. "
                    f"Will fall back to alternative model."
                )
                raise RuntimeError(f"Invalid parameters for model {model_name}: {e}")
            elif "422" in str(e) or "validation" in error_str:
                # For other models or non-image validation errors, fail immediately
                raise RuntimeError(f"Invalid parameters for model {model_name}: {e}")
            
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
            clip_path, model_used = await generate_video_clip(
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

