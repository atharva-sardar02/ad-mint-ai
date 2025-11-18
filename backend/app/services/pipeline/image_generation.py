"""
Image generation service using Nano Banana (Google Gemini 2.5 Flash Image) on Replicate.
Generates consistent images using markers for cohesion across scenes.
"""
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

import replicate
import httpx

from app.core.config import settings
from app.services.pipeline.video_generation import MAX_RETRIES, POLL_INTERVAL

logger = logging.getLogger(__name__)

# Nano Banana model on Replicate
NANO_BANANA_MODEL = "google/nano-banana"

# Cost per image (approximate)
IMAGE_COST = 0.01  # $0.01 per image (estimate)

# Polling timeout
MAX_POLLING_TIME = 300  # 5 minutes for image generation


async def generate_image(
    prompt: str,
    output_dir: str,
    generation_id: str,
    scene_number: Optional[int] = None,
    consistency_markers: Optional[dict] = None,
    reference_image_path: Optional[str] = None,
    cancellation_check: Optional[callable] = None,
) -> str:
    """
    Generate an image using Nano Banana on Replicate.
    
    Args:
        prompt: Text prompt for image generation
        output_dir: Directory to save the generated image
        generation_id: Generation ID for logging
        scene_number: Optional scene number for filename
        consistency_markers: Optional dict with style markers for consistency
        reference_image_path: Optional path to reference image for visual consistency
                             (Nano Banana supports character/style consistency via reference images)
        cancellation_check: Optional function to check if generation should be cancelled
    
    Returns:
        str: Path to the generated image file
    
    Raises:
        ValueError: If API token is missing
        RuntimeError: If image generation fails
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
    
    # Generate unique filename
    if scene_number is not None:
        image_filename = f"{generation_id}_scene_{scene_number}.png"
    else:
        image_filename = f"{generation_id}_image.png"
    image_path = output_path / image_filename
    
    logger.info(f"Generating image with Nano Banana (generation {generation_id})")
    logger.debug(f"Prompt: {prompt[:100]}...")
    
    # Build enhanced prompt with consistency markers
    enhanced_prompt = _build_prompt_with_markers(prompt, consistency_markers)
    logger.debug(f"Enhanced prompt: {enhanced_prompt[:150]}...")
    
    try:
        # Generate image with retry logic
        image_url = await _generate_image_with_retry(
            prompt=enhanced_prompt,
            reference_image_path=reference_image_path,
            cancellation_check=cancellation_check,
        )
        
        # Download image
        logger.info(f"Downloading image from {image_url}")
        await _download_image(image_url, image_path)
        
        logger.info(f"Image generated successfully: {image_path}")
        return str(image_path)
        
    except Exception as e:
        logger.error(f"Failed to generate image: {e}", exc_info=True)
        raise RuntimeError(f"Image generation failed: {e}")


def _build_prompt_with_markers(
    base_prompt: str,
    consistency_markers: Optional[dict] = None,
) -> str:
    """
    Build enhanced prompt with consistency markers.
    
    Markers can include:
    - style: "cinematic", "modern", "minimalist", etc.
    - color_palette: "warm tones", "cool blues", etc.
    - lighting: "soft natural light", "dramatic shadows", etc.
    - composition: "rule of thirds", "centered", etc.
    - mood: "energetic", "calm", "professional", etc.
    """
    if not consistency_markers:
        return base_prompt
    
    marker_parts = []
    
    if "style" in consistency_markers:
        marker_parts.append(f"Style: {consistency_markers['style']}")
    if "color_palette" in consistency_markers:
        marker_parts.append(f"Color palette: {consistency_markers['color_palette']}")
    if "lighting" in consistency_markers:
        marker_parts.append(f"Lighting: {consistency_markers['lighting']}")
    if "composition" in consistency_markers:
        marker_parts.append(f"Composition: {consistency_markers['composition']}")
    if "mood" in consistency_markers:
        marker_parts.append(f"Mood: {consistency_markers['mood']}")
    
    if marker_parts:
        markers_text = ", ".join(marker_parts)
        return f"{base_prompt}. {markers_text}"
    
    return base_prompt


async def _generate_image_with_retry(
    prompt: str,
    reference_image_path: Optional[str] = None,
    cancellation_check: Optional[callable] = None,
) -> str:
    """
    Generate image with retry logic and exponential backoff.
    
    Args:
        prompt: Enhanced prompt with consistency markers
        reference_image_path: Optional path to reference image for visual consistency
        cancellation_check: Optional cancellation check function
    
    Returns:
        str: URL to the generated image
    
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
                f"Calling Nano Banana API (attempt {attempt}/{MAX_RETRIES})"
            )
            
            # Prepare input parameters for Nano Banana
            # Based on Replicate docs, nano-banana accepts:
            # - prompt: text prompt
            # - num_outputs: number of images (default 1)
            # - aspect_ratio: "1:1", "16:9", "9:16", etc.
            # - seed: optional seed for consistency
            # - reference_image: optional reference image for character/style consistency
            input_params = {
                "prompt": prompt,
                "num_outputs": 1,
                "aspect_ratio": "9:16",  # Vertical for mobile ads
            }
            
            # Add reference image if provided (for visual consistency)
            # Nano Banana supports character and style consistency via reference images
            file_handles_to_close = []
            if reference_image_path:
                try:
                    image_path_obj = Path(reference_image_path)
                    if not image_path_obj.exists():
                        logger.warning(f"Reference image not found: {reference_image_path}, continuing without reference")
                    else:
                        # Open file as binary for Replicate SDK
                        image_file_handle = open(image_path_obj, "rb")
                        input_params["reference_image"] = image_file_handle
                        file_handles_to_close.append(image_file_handle)
                        logger.info(
                            f"✅ Using reference image for consistency: {reference_image_path} "
                            f"(size: {image_path_obj.stat().st_size} bytes)"
                        )
                except Exception as e:
                    logger.warning(f"Failed to load reference image: {e}, continuing without reference")
            
            logger.info(f"Generating image with Nano Banana: {prompt[:80]}...")
            if reference_image_path:
                logger.info(f"  Using reference image for visual consistency")
            
            # Create prediction
            try:
                prediction = client.predictions.create(
                    model=NANO_BANANA_MODEL,
                    input=input_params
                )
            finally:
                # Close file handles after API call (Replicate SDK reads them immediately)
                for fh in file_handles_to_close:
                    try:
                        fh.close()
                    except Exception:
                        pass
            
            # Poll for completion
            poll_start_time = time.time()
            poll_attempts = 0
            
            while prediction.status not in ["succeeded", "failed", "canceled"]:
                # Check timeout
                elapsed_time = time.time() - poll_start_time
                if elapsed_time > MAX_POLLING_TIME:
                    logger.error(
                        f"Polling timeout after {elapsed_time:.0f}s for Nano Banana "
                        f"(prediction_id: {prediction.id})"
                    )
                    try:
                        client.predictions.cancel(prediction.id)
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"Image generation timeout: Prediction did not complete within {MAX_POLLING_TIME}s"
                    )
                
                # Check cancellation during polling
                if cancellation_check and cancellation_check():
                    try:
                        client.predictions.cancel(prediction.id)
                    except Exception:
                        pass
                    raise RuntimeError("Generation cancelled by user")
                
                poll_attempts += 1
                # Log progress every 30 seconds
                if poll_attempts % 15 == 0:
                    logger.info(
                        f"Polling Nano Banana prediction (ID: {prediction.id}): "
                        f"status={prediction.status}, elapsed={elapsed_time:.0f}s"
                    )
                
                await asyncio.sleep(POLL_INTERVAL)
                
                # Refresh prediction status
                prediction = client.predictions.get(prediction.id)
            
            # Check final status
            if prediction.status == "succeeded":
                # Nano Banana returns a list of image URLs
                output = prediction.output
                if isinstance(output, list) and len(output) > 0:
                    image_url = output[0]
                    if isinstance(image_url, str):
                        logger.info(f"Image generated successfully: {image_url}")
                        return image_url
                    else:
                        raise RuntimeError(f"Unexpected output format: {type(image_url)}")
                elif isinstance(output, str):
                    logger.info(f"Image generated successfully: {output}")
                    return output
                else:
                    raise RuntimeError(f"Unexpected output format: {type(output)}")
            elif prediction.status == "failed":
                error_msg = getattr(prediction, "error", "Unknown error")
                raise RuntimeError(f"Image generation failed: {error_msg}")
            elif prediction.status == "canceled":
                raise RuntimeError("Image generation was canceled")
            else:
                raise RuntimeError(f"Unexpected prediction status: {prediction.status}")
                
        except RuntimeError:
            # Re-raise cancellation and timeout errors
            raise
        except Exception as e:
            last_error = e
            logger.warning(
                f"Image generation attempt {attempt} failed: {e}",
                exc_info=True
            )
            if attempt < MAX_RETRIES:
                delay = min(2 ** attempt, 30)
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                continue
    
    # All attempts failed
    raise RuntimeError(
        f"Image generation failed after {MAX_RETRIES} attempts: {last_error}"
    )


async def _download_image(image_url: str, output_path: Path) -> None:
    """Download image from URL to local path."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(image_url)
        response.raise_for_status()
        
        output_path.write_bytes(response.content)
        logger.info(f"Image downloaded to {output_path} ({len(response.content)} bytes)")

