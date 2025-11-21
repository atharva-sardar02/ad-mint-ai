"""
Image inpainting service using SDXL-inpaint on Replicate.
Allows users to replace specific regions of images using AI inpainting.
"""
import asyncio
import base64
import io
import logging
import time
from pathlib import Path
from typing import Optional

import replicate
import httpx
from PIL import Image

from app.core.config import settings
from app.services.pipeline.video_generation import MAX_RETRIES, POLL_INTERVAL

logger = logging.getLogger(__name__)

# SDXL-inpaint model on Replicate
SDXL_INPAINT_MODEL = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

# Polling timeout
MAX_POLLING_TIME = 300  # 5 minutes for inpainting


async def inpaint_image(
    image_path: str,
    mask_base64: str,
    prompt: str,
    negative_prompt: str = "blurry, low quality, distorted, deformed",
    output_dir: str = None,
    image_id: Optional[int] = None,
) -> str:
    """
    Inpaint an image using SDXL-inpaint on Replicate.

    Args:
        image_path: Path to the original image
        mask_base64: Base64-encoded binary mask (1=replace, 0=preserve)
        prompt: Text prompt describing the replacement content
        negative_prompt: Text prompt for what to avoid
        output_dir: Directory to save the edited image (defaults to same dir as original)
        image_id: Optional image ID for filename

    Returns:
        str: Path to the edited image file

    Raises:
        ValueError: If API token is missing or inputs are invalid
        RuntimeError: If inpainting fails
    """
    if not settings.REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN not configured")
        raise ValueError("Replicate API token is not configured")

    if not image_path or not Path(image_path).exists():
        raise ValueError(f"Image not found: {image_path}")

    if not mask_base64:
        raise ValueError("Mask data is required")

    if not prompt or not prompt.strip():
        raise ValueError("Prompt is required")

    # Load original image
    try:
        original_image = Image.open(image_path)
        logger.info(f"Loaded image: {image_path} (size: {original_image.size})")
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")

    # Decode and convert mask from base64 to PIL Image
    try:
        mask_image = _decode_mask(mask_base64, original_image.size)
        logger.info(f"Decoded mask (size: {mask_image.size})")
    except Exception as e:
        raise ValueError(f"Failed to decode mask: {e}")

    # Determine output path
    if output_dir is None:
        output_dir = str(Path(image_path).parent)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate unique filename for edited image
    original_filename = Path(image_path).stem
    if image_id is not None:
        edited_filename = f"{original_filename}_edited_{image_id}.png"
    else:
        timestamp = int(time.time())
        edited_filename = f"{original_filename}_edited_{timestamp}.png"
    edited_path = output_path / edited_filename

    logger.info(f"Starting inpainting with SDXL-inpaint")
    logger.debug(f"Prompt: {prompt}")
    logger.debug(f"Negative prompt: {negative_prompt}")

    try:
        # Generate inpainted image with retry logic
        edited_image_url = await _inpaint_with_retry(
            original_image=original_image,
            mask_image=mask_image,
            prompt=prompt,
            negative_prompt=negative_prompt,
        )

        # Download edited image
        logger.info(f"Downloading edited image from {edited_image_url}")
        await _download_image(edited_image_url, edited_path)

        logger.info(f"Inpainting completed successfully: {edited_path}")
        return str(edited_path)

    except Exception as e:
        logger.error(f"Failed to inpaint image: {e}", exc_info=True)
        raise RuntimeError(f"Inpainting failed: {e}")


def _decode_mask(mask_base64: str, image_size: tuple) -> Image.Image:
    """
    Decode base64 mask data to PIL Image.

    Args:
        mask_base64: Base64-encoded binary mask data
        image_size: (width, height) tuple from original image

    Returns:
        PIL.Image: Grayscale mask image (L mode)
    """
    try:
        # Decode base64 to bytes
        mask_bytes = base64.b64decode(mask_base64)

        # Convert bytes to PIL Image
        # Mask format: 1 byte per pixel (0 or 255)
        width, height = image_size
        expected_size = width * height

        if len(mask_bytes) != expected_size:
            # Try to parse as PNG/JPEG image instead of raw bytes
            try:
                mask_image = Image.open(io.BytesIO(mask_bytes))
                # Convert to grayscale and resize if needed
                mask_image = mask_image.convert("L")
                if mask_image.size != image_size:
                    mask_image = mask_image.resize(image_size, Image.LANCZOS)
                return mask_image
            except Exception:
                raise ValueError(
                    f"Invalid mask size: expected {expected_size} bytes for {width}x{height} image, "
                    f"got {len(mask_bytes)} bytes"
                )

        # Create grayscale image from raw bytes
        mask_image = Image.frombytes("L", image_size, mask_bytes)

        # Ensure binary mask (0 or 255)
        # SDXL-inpaint expects: white (255) = areas to replace, black (0) = areas to keep
        mask_image = mask_image.point(lambda x: 255 if x > 128 else 0)

        return mask_image

    except base64.binascii.Error as e:
        raise ValueError(f"Invalid base64 encoding: {e}")
    except Exception as e:
        raise ValueError(f"Failed to decode mask: {e}")


async def _inpaint_with_retry(
    original_image: Image.Image,
    mask_image: Image.Image,
    prompt: str,
    negative_prompt: str,
) -> str:
    """
    Perform inpainting with retry logic and exponential backoff.

    Args:
        original_image: Original PIL Image
        mask_image: Mask PIL Image (grayscale)
        prompt: Replacement prompt
        negative_prompt: Negative prompt

    Returns:
        str: URL to the inpainted image

    Raises:
        RuntimeError: If inpainting fails after all retries
    """
    client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(
                f"Calling SDXL-inpaint API (attempt {attempt}/{MAX_RETRIES})"
            )

            # Convert PIL Images to file-like objects for Replicate
            # Save to BytesIO to avoid writing temporary files
            original_buffer = io.BytesIO()
            original_image.save(original_buffer, format="PNG")
            original_buffer.seek(0)

            mask_buffer = io.BytesIO()
            mask_image.save(mask_buffer, format="PNG")
            mask_buffer.seek(0)

            # Prepare input parameters for SDXL-inpaint
            # Based on Replicate docs, sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b accepts:
            # - image: input image
            # - mask: mask image (white = inpaint, black = keep)
            # - prompt: text prompt for inpainting
            # - negative_prompt: what to avoid
            # - num_inference_steps: quality (default 50)
            # - guidance_scale: prompt adherence (default 7.5)
            input_params = {
                "image": original_buffer,
                "mask": mask_buffer,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
            }

            logger.info(f"Inpainting with SDXL: {prompt[:80]}...")

            # Create prediction
            prediction = client.predictions.create(
                model=SDXL_INPAINT_MODEL,
                input=input_params
            )

            # Poll for completion
            poll_start_time = time.time()
            poll_attempts = 0

            while prediction.status not in ["succeeded", "failed", "canceled"]:
                # Check timeout
                elapsed_time = time.time() - poll_start_time
                if elapsed_time > MAX_POLLING_TIME:
                    logger.error(
                        f"Polling timeout after {elapsed_time:.0f}s for SDXL-inpaint "
                        f"(prediction_id: {prediction.id})"
                    )
                    try:
                        client.predictions.cancel(prediction.id)
                    except Exception:
                        pass
                    raise RuntimeError(
                        f"Inpainting timeout: Prediction did not complete within {MAX_POLLING_TIME}s"
                    )

                poll_attempts += 1
                # Log progress every 30 seconds
                if poll_attempts % 15 == 0:
                    logger.info(
                        f"Polling SDXL-inpaint prediction (ID: {prediction.id}): "
                        f"status={prediction.status}, elapsed={elapsed_time:.0f}s"
                    )

                await asyncio.sleep(POLL_INTERVAL)

                # Refresh prediction status
                prediction = client.predictions.get(prediction.id)

            # Check final status
            if prediction.status == "succeeded":
                # SDXL-inpaint returns a list of image URLs
                output = prediction.output
                if isinstance(output, list) and len(output) > 0:
                    image_url = output[0]
                    if isinstance(image_url, str):
                        logger.info(f"Inpainting succeeded: {image_url}")
                        return image_url
                    else:
                        raise RuntimeError(f"Unexpected output format: {type(image_url)}")
                elif isinstance(output, str):
                    logger.info(f"Inpainting succeeded: {output}")
                    return output
                else:
                    raise RuntimeError(f"Unexpected output format: {type(output)}")
            elif prediction.status == "failed":
                error_msg = getattr(prediction, "error", "Unknown error")
                raise RuntimeError(f"Inpainting failed: {error_msg}")
            elif prediction.status == "canceled":
                raise RuntimeError("Inpainting was canceled")
            else:
                raise RuntimeError(f"Unexpected prediction status: {prediction.status}")

        except RuntimeError:
            # Re-raise timeout errors immediately
            raise
        except Exception as e:
            last_error = e
            logger.warning(
                f"Inpainting attempt {attempt} failed: {e}",
                exc_info=True
            )
            if attempt < MAX_RETRIES:
                delay = min(2 ** attempt, 30)
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                continue

    # All attempts failed
    raise RuntimeError(
        f"Inpainting failed after {MAX_RETRIES} attempts: {last_error}"
    )


async def _download_image(image_url: str, output_path: Path) -> None:
    """Download image from URL to local path."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(image_url)
        response.raise_for_status()

        output_path.write_bytes(response.content)
        logger.info(f"Image downloaded to {output_path} ({len(response.content)} bytes)")
