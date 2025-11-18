"""
Image generation service for generating images using Replicate API.
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import replicate
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Replicate text-to-image model configurations
# Default model: Flux (Black Forest Labs) - High quality text-to-image generation
# Note: Model names may change on Replicate. Check https://replicate.com/explore for current models
REPLICATE_IMAGE_MODELS = {
    "default": "black-forest-labs/flux-schnell",  # Updated: flux returns 404, using flux-schnell as default
    "flux": "black-forest-labs/flux-schnell",  # Updated: flux returns 404, mapping to flux-schnell
    "flux-dev": "black-forest-labs/flux-dev",
    "flux-schnell": "black-forest-labs/flux-schnell",
    "nano-banana": "google/nano-banana",
    "sdxl-turbo": "stability-ai/sdxl-turbo",
    "stable-diffusion": "stability-ai/stable-diffusion",
    # Fallback models
    "fallback_1": "black-forest-labs/flux-schnell",
    "fallback_2": "google/nano-banana",
    "fallback_3": "stability-ai/sdxl-turbo",
    "fallback_4": "stability-ai/stable-diffusion",
}

# Cost per image generation (approximate, varies by model)
MODEL_COSTS = {
    "black-forest-labs/flux": 0.005,  # Default - premium quality
    "black-forest-labs/flux-dev": 0.004,  # Development version
    "black-forest-labs/flux-schnell": 0.003,  # Faster version
    "google/nano-banana": 0.002,  # Google Nano Banana - supports image input
    "stability-ai/sdxl-turbo": 0.002,  # Faster, slightly lower quality
    "stability-ai/stable-diffusion": 0.001,  # Legacy fallback
    # Legacy models (may not be available)
    "stability-ai/sdxl": 0.003,
}

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 30  # seconds

# Supported aspect ratios (standard models)
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "4:3": (1152, 896),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
}

# Nano Banana specific aspect ratios (uses string format, not dimensions)
NANO_BANANA_ASPECT_RATIOS = [
    "match_input_image",
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9"
]


@dataclass
class ImageGenerationResult:
    """Result of a single image generation."""
    image_path: str
    image_url: str
    model_name: str
    seed: Optional[int]
    aspect_ratio: str
    prompt: str
    cost: float
    generation_time: float
    timestamp: str


async def generate_images(
    prompt: str,
    num_variations: int = 8,
    aspect_ratio: str = "16:9",
    seed: Optional[int] = None,
    model_name: str = "black-forest-labs/flux-schnell",  # Updated: flux returns 404
    output_dir: Optional[Path] = None,
    image_input: Optional[List[str]] = None,
    negative_prompt: Optional[str] = None
) -> List[ImageGenerationResult]:
    """
    Generate multiple image variations using Replicate API.
    
    Args:
        prompt: Enhanced image prompt text
        num_variations: Number of image variations to generate (1-8, default: 8)
        aspect_ratio: Aspect ratio string (1:1, 4:3, 16:9, 9:16)
        seed: Optional seed value for reproducibility
        model_name: Replicate model identifier (default: stability-ai/sdxl)
        output_dir: Optional output directory for saving images
        image_input: Optional list of image URIs for image-to-image generation (nano-banana only)
        negative_prompt: Optional negative prompt to avoid unwanted elements
    
    Returns:
        List[ImageGenerationResult]: List of generated image results
    
    Raises:
        ValueError: If API key is missing, invalid parameters, or model not found
        RuntimeError: If image generation fails after all retries
    """
    if not settings.REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN not configured")
        raise ValueError("Replicate API token is not configured")
    
    # Validate parameters
    if num_variations < 1 or num_variations > 8:
        raise ValueError(f"num_variations must be between 1 and 8, got {num_variations}")
    
    # Validate aspect ratio based on model
    if model_name == "google/nano-banana":
        if aspect_ratio not in NANO_BANANA_ASPECT_RATIOS:
            # Map common ratios to nano-banana format
            ratio_map = {
                "1:1": "1:1",
                "4:3": "4:3",
                "16:9": "16:9",
                "9:16": "9:16",
            }
            if aspect_ratio in ratio_map:
                aspect_ratio = ratio_map[aspect_ratio]
            else:
                aspect_ratio = "16:9"  # Default fallback
        width, height = None, None  # Nano-banana doesn't use width/height
    else:
        if aspect_ratio not in ASPECT_RATIOS:
            raise ValueError(f"aspect_ratio must be one of {list(ASPECT_RATIOS.keys())}, got {aspect_ratio}")
        width, height = ASPECT_RATIOS[aspect_ratio]
    
    if model_name not in MODEL_COSTS:
        raise ValueError(f"Model '{model_name}' not found in available models")
    
    logger.info(
        f"Generating {num_variations} image variations with model {model_name} "
        f"(aspect_ratio: {aspect_ratio}, seed: {seed})"
    )
    logger.debug(f"Prompt: {prompt[:100]}...")
    
    results: List[ImageGenerationResult] = []
    total_cost = 0.0
    
    # Determine models to try (primary + fallbacks)
    models_to_try = [model_name]
    if model_name in REPLICATE_IMAGE_MODELS.values() or model_name in REPLICATE_IMAGE_MODELS:
        # Add fallback models if primary is in our list
        if model_name == REPLICATE_IMAGE_MODELS["default"] or model_name == "black-forest-labs/flux-schnell" or model_name == "black-forest-labs/flux":
            models_to_try.extend([
                REPLICATE_IMAGE_MODELS["flux-schnell"],
                REPLICATE_IMAGE_MODELS["fallback_1"],
                REPLICATE_IMAGE_MODELS["fallback_2"],
                REPLICATE_IMAGE_MODELS["fallback_3"]
            ])
        else:
            # For other models, add default fallbacks
            models_to_try.extend([
                REPLICATE_IMAGE_MODELS["default"],
                REPLICATE_IMAGE_MODELS["fallback_1"],
                REPLICATE_IMAGE_MODELS["fallback_2"]
            ])
    
    # Remove duplicates while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]
    
    async def generate_single_image(index: int) -> Optional[ImageGenerationResult]:
        """Generate a single image variation with retry and fallback logic."""
        start_time = time.time()
        last_error = None
        image_url = None
        model_used = None
        
        # Use different seed for each variation if seed not provided
        variation_seed = seed if seed is not None else None
        
        # Try models in order until one succeeds
        for current_model in models_to_try:
            try:
                logger.debug(f"Attempting image {index+1}/{num_variations} with model: {current_model}")
                
                # Generate image with retry logic
                image_url = await _generate_with_retry(
                    model_name=current_model,
                    prompt=prompt,
                    width=width,
                    height=height,
                    aspect_ratio=aspect_ratio,
                    seed=variation_seed,
                    image_input=image_input,
                    negative_prompt=negative_prompt
                )
                model_used = current_model
                break  # Success, exit model loop
                
            except RuntimeError as e:
                last_error = e
                logger.warning(
                    f"Model {current_model} failed for image {index+1}/{num_variations}: {e}. "
                    f"Trying fallback model..."
                )
                continue
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Unexpected error with model {current_model} for image {index+1}/{num_variations}: {e}. "
                    f"Trying fallback model..."
                )
                continue
        
        # Check if we got a successful generation
        if image_url is None:
            logger.error(f"All models failed for image {index+1}/{num_variations}: {last_error}")
            return None  # Return None to indicate failure
        
        # Download image if output_dir provided
        try:
            image_path = None
            if output_dir:
                image_path = await _download_image(
                    image_url=image_url,
                    output_dir=output_dir,
                    index=index + 1
                )
            
            generation_time = time.time() - start_time
            cost = MODEL_COSTS.get(model_used, MODEL_COSTS.get(model_name, 0.003))
            
            result = ImageGenerationResult(
                image_path=image_path or image_url,
                image_url=image_url,
                model_name=model_used or model_name,
                seed=variation_seed,
                aspect_ratio=aspect_ratio,
                prompt=prompt,
                cost=cost,
                generation_time=generation_time,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            logger.info(
                f"Image {index + 1}/{num_variations} generated successfully "
                f"(model: {model_used}, cost: ${cost:.4f}, time: {generation_time:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process image {index + 1}/{num_variations}: {e}", exc_info=True)
            return None  # Return None to indicate failure
    
    # Generate all images in parallel
    logger.info(f"Generating {num_variations} images in parallel...")
    generation_tasks = [generate_single_image(i) for i in range(num_variations)]
    generation_results_list = await asyncio.gather(*generation_tasks, return_exceptions=True)
    
    # Process results and filter out failures
    for i, result in enumerate(generation_results_list):
        if isinstance(result, Exception):
            logger.error(f"Image {i+1}/{num_variations} generation raised exception: {result}", exc_info=True)
            continue
        if result is None:
            continue  # Already logged in generate_single_image
        results.append(result)
        total_cost += result.cost
    
    if not results:
        raise RuntimeError("All image generations failed")
    
    logger.info(
        f"Generated {len(results)}/{num_variations} images successfully "
        f"(total cost: ${total_cost:.4f})"
    )
    
    return results


async def _generate_with_retry(
    model_name: str,
    prompt: str,
    width: Optional[int],
    height: Optional[int],
    aspect_ratio: str = "16:9",
    seed: Optional[int] = None,
    image_input: Optional[List[str]] = None,
    negative_prompt: Optional[str] = None
) -> str:
    """
    Generate image with retry logic and exponential backoff.
    
    Args:
        model_name: Replicate model identifier
        prompt: Image prompt text
        width: Image width in pixels (None for nano-banana which uses aspect_ratio string)
        height: Image height in pixels (None for nano-banana which uses aspect_ratio string)
        aspect_ratio: Aspect ratio string (used by nano-banana, ignored by standard models)
        seed: Optional seed value for reproducibility (not supported by nano-banana)
        image_input: Optional list of image URIs for image-to-image generation (nano-banana only)
        negative_prompt: Optional negative prompt to avoid unwanted elements
    
    Returns:
        str: URL to the generated image
    
    Raises:
        RuntimeError: If generation fails after all retries
    """
    client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
    
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(
                f"Calling Replicate API (model: {model_name}, attempt {attempt}/{MAX_RETRIES})"
            )
            
            # Prepare input parameters for Replicate
            # Nano Banana uses different input format
            if model_name == "google/nano-banana":
                input_params = {
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio if aspect_ratio in NANO_BANANA_ASPECT_RATIOS else "16:9",
                    "output_format": "png",  # or "jpg"
                }
                # Add negative prompt if provided
                if negative_prompt:
                    input_params["negative_prompt"] = negative_prompt
                    logger.debug(f"Using negative prompt: {negative_prompt[:50]}...")
                # Add image_input if provided (for image-to-image generation)
                # Replicate SDK automatically uploads file objects when passed in input
                # It converts them to URLs internally (we see HTTP 201 to /v1/files in logs)
                if image_input:
                    processed_images = []
                    for img_path in image_input:
                        img_path_obj = Path(img_path) if isinstance(img_path, str) else None
                        
                        # If it's already a URL, use it directly
                        if isinstance(img_path, str) and img_path.startswith(("http://", "https://")):
                            processed_images.append(img_path)
                            logger.debug(f"Using existing URL: {img_path}")
                        elif img_path_obj and img_path_obj.exists():
                            # Local file - open and pass file object directly
                            # Replicate SDK will automatically upload it and convert to URL
                            try:
                                f_obj = open(img_path_obj, "rb")
                                processed_images.append(f_obj)
                                logger.debug(f"Passing file object to Replicate (auto-upload): {img_path}")
                            except Exception as e:
                                logger.error(f"Failed to open file {img_path}: {e}")
                        else:
                            logger.warning(f"Invalid image input (not a file or URL): {img_path}")
                    
                    if processed_images:
                        input_params["image_input"] = processed_images
                        logger.info(f"Using {len(processed_images)} image(s) for image-to-image generation")
                    else:
                        logger.warning("No valid images processed for image_input, skipping image conditioning")
            else:
                # Standard models use width/height
                input_params = {
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                }
                # Add negative prompt if provided
                if negative_prompt:
                    input_params["negative_prompt"] = negative_prompt
                    logger.debug(f"Using negative prompt: {negative_prompt[:50]}...")
                # Add seed parameter if provided
                if seed is not None:
                    input_params["seed"] = seed
            
            # Create prediction
            prediction = client.predictions.create(
                model=model_name,
                input=input_params
            )
            
            # Poll for completion
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                await asyncio.sleep(2)  # Poll every 2 seconds
                prediction = client.predictions.get(prediction.id)
            
            # Handle result
            if prediction.status == "succeeded":
                if not prediction.output:
                    raise RuntimeError("Image generation succeeded but no output URL")
                
                # Output may be a URL string or list of URLs
                if isinstance(prediction.output, list):
                    image_url = prediction.output[0]
                else:
                    image_url = prediction.output
                
                logger.info(f"Image generation succeeded (attempt {attempt})")
                return image_url
            
            elif prediction.status == "failed":
                error_msg = prediction.error or "Unknown error"
                raise RuntimeError(f"Image generation failed: {error_msg}")
            
            elif prediction.status == "canceled":
                raise RuntimeError("Image generation was canceled")
            
        except replicate.exceptions.ReplicateError as e:
            last_error = e
            # Check if it's a rate limit error (status 429)
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
            
            # Don't retry on validation errors (422)
            if "422" in str(e) or "validation" in error_str:
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
        f"Image generation failed after {MAX_RETRIES} attempts: {last_error}"
    )


def prepare_image_for_replicate(image_path: str) -> str:
    """
    Prepare an image file path for use with Replicate's image_input parameter.
    
    This function just validates the file exists and returns the absolute path.
    The actual file upload to Replicate happens in _generate_with_retry.
    
    Args:
        image_path: Path to local image file
    
    Returns:
        str: Absolute file path (will be uploaded to Replicate in _generate_with_retry)
    
    Raises:
        FileNotFoundError: If image file doesn't exist
    """
    image_path_obj = Path(image_path)
    if not image_path_obj.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Return absolute path - will be uploaded to Replicate in _generate_with_retry
    return str(image_path_obj.absolute())


async def _download_image(
    image_url: str,
    output_dir: Path,
    index: int
) -> str:
    """
    Download image from URL to local file.
    
    Args:
        image_url: URL of the image to download
        output_dir: Directory to save the image
        index: Image index (for filename)
    
    Returns:
        str: Path to the downloaded image file
    
    Raises:
        RuntimeError: If download fails
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.debug(f"Downloading image from {image_url}")
            response = await client.get(image_url)
            response.raise_for_status()
            
            # Determine file extension from content type or URL
            content_type = response.headers.get("content-type", "")
            if "png" in content_type or image_url.endswith(".png"):
                ext = "png"
            elif "jpeg" in content_type or "jpg" in content_type or image_url.endswith((".jpg", ".jpeg")):
                ext = "jpg"
            else:
                ext = "png"  # Default to PNG
            
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save image (will be renamed by quality rank later)
            image_path = output_dir / f"image_{index:03d}.{ext}"
            with open(image_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Image downloaded successfully to {image_path}")
            return str(image_path)
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to download image from {image_url}: {e}")
        raise RuntimeError(f"Image download failed: {e}")

