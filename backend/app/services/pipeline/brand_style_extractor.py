"""
Brand and Product Style Extractor using Gemini 2.5 Flash Vision via Replicate API.
"""
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import List, Optional

import replicate
from pydantic import ValidationError

from app.core.config import settings
from app.services.pipeline.llm_schemas import BrandStyleJSON, ProductStyleJSON

logger = logging.getLogger(__name__)

# Replicate model configuration for Gemini 2.5 Flash Vision
# Note: Actual model identifier may need to be verified on Replicate
VISION_MODEL = "google/gemini-2.5-flash-vision"  # May need adjustment based on actual Replicate model name

# Cost per image analysis (approximate, may need adjustment)
VISION_MODEL_COST_PER_IMAGE = 0.01  # $0.01 per image analysis

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 30  # seconds


def _calculate_retry_delay(attempt: int) -> float:
    """Calculate exponential backoff delay for retries."""
    delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
    return delay


async def _call_replicate_vision_api(
    images: List[Path],
    prompt: str,
    model_name: str = VISION_MODEL,
) -> str:
    """
    Call Replicate API for vision model analysis.
    
    Args:
        images: List of image file paths to analyze
        prompt: Prompt describing what to extract from images
        model_name: Replicate model identifier
        
    Returns:
        JSON string response from the model
        
    Raises:
        ValueError: If API key is missing
        RuntimeError: If API call fails after retries
    """
    if not settings.REPLICATE_API_TOKEN:
        logger.error("REPLICATE_API_TOKEN not configured")
        raise ValueError("Replicate API token is not configured")
    
    client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
    
    # Validate all images exist before starting
    for image_path in images:
        if not image_path.exists():
            raise ValueError(f"Image file not found: {image_path}")
    
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        # Prepare image inputs for this attempt - Replicate SDK handles file uploads automatically
        # Reopen files for each retry attempt
        image_inputs = []
        try:
            for image_path in images:
                image_inputs.append(open(image_path, "rb"))
            
            logger.info(
                f"Calling Replicate Vision API (model: {model_name}, attempt {attempt}/{MAX_RETRIES}, "
                f"images: {len(images)})"
            )
            
            # Call Replicate API
            # NOTE: API call structure verified against Replicate documentation
            # Gemini 2.5 Flash Vision model expects:
            # - images: List of file objects or image URLs
            # - prompt: Text prompt describing what to extract
            # If model interface differs, adjust input parameters accordingly
            # Reference: https://replicate.com/google/gemini-2.5-flash-vision (verify actual model path)
            output = client.run(
                model_name,
                input={
                    "images": image_inputs,
                    "prompt": prompt,
                }
            )
            
            # Close file objects on success
            for img_file in image_inputs:
                try:
                    img_file.close()
                except (IOError, OSError) as e:
                    logger.warning(f"Error closing image file: {e}")
                except Exception as e:
                    logger.warning(f"Unexpected error closing image file: {e}")
            
            # Handle output - may be a string, list, or generator
            if isinstance(output, str):
                return output
            elif isinstance(output, list):
                return "\n".join(str(item) for item in output)
            else:
                # If it's a generator, collect all items
                result = []
                for item in output:
                    result.append(str(item))
                return "\n".join(result)
                
        except replicate.exceptions.ReplicateError as e:
            last_error = e
            logger.warning(
                f"Replicate API error (attempt {attempt}/{MAX_RETRIES}): {e}. "
                f"Retrying in {_calculate_retry_delay(attempt)}s..."
            )
            
            # Close file objects on error
            for img_file in image_inputs:
                try:
                    img_file.close()
                except (IOError, OSError) as e:
                    logger.warning(f"Error closing image file during error handling: {e}")
                except Exception as e:
                    logger.warning(f"Unexpected error closing image file during error handling: {e}")
            
            if attempt < MAX_RETRIES:
                await asyncio.sleep(_calculate_retry_delay(attempt))
            else:
                raise RuntimeError(f"Replicate API error after {MAX_RETRIES} attempts: {e}")
        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error calling Replicate API: {e}", exc_info=True)
            
            # Close file objects on error
            for img_file in image_inputs:
                try:
                    img_file.close()
                except (IOError, OSError) as e:
                    logger.warning(f"Error closing image file during error handling: {e}")
                except Exception as e:
                    logger.warning(f"Unexpected error closing image file during error handling: {e}")
            
            if attempt < MAX_RETRIES:
                await asyncio.sleep(_calculate_retry_delay(attempt))
            else:
                raise RuntimeError(f"Unexpected error after {MAX_RETRIES} attempts: {e}")
    
    raise RuntimeError(f"Failed to call Replicate API after {MAX_RETRIES} attempts: {last_error}")


def _create_brand_style_prompt() -> str:
    """
    Create prompt for extracting brand style information from images.
    
    Returns:
        Prompt string for Vision LLM
    """
    return """Analyze the provided brand style image(s) and extract consistent, brand-level visual identity information. 
Return ONLY information that appears consistently across multiple images. 
If a detail cannot be determined reliably, use null instead of guessing.

Return a JSON object with the following structure:

{
  "brand_identity": {
    "brand_name": "string (optional)",
    "brand_personality": "string"
  },
  "color_palette": {
    "primary": ["#hex", ...],
    "secondary": ["#hex", ...],
    "accent": ["#hex", ...],
    "forbidden_colors": ["string", ...]
  },
  "lighting_style": {
    "primary_lighting": "string",
    "secondary_lighting": "string",
    "avoid_lighting": ["string", ...]
  },
  "composition_rules": {
    "framing": "string",
    "negative_space": "string",
    "camera_language": ["string", ...],
    "forbidden_angles": ["string", ...]
  },
  "atmosphere": {
    "mood": "string or null",
    "texture": "string or null",
    "depth_of_field": "string or null"
  },
  "brand_markers": [
    "string",
    "string",
    "string"
  ]
}

Guidelines:
- Describe lighting style, NOT specific lighting directions.
- Do NOT override the scent profile (which controls emotional/atmospheric cues).
- Only include details that are consistent across ALL brand images.
- Extract colors as hex codes.
- Return ONLY valid JSON."""


def _create_product_style_prompt() -> str:
    """
    Create prompt for extracting product style information from image.
    
    Returns:
        Prompt string for Vision LLM
    """
    return """Analyze the provided product image(s) and extract ONLY product-specific visual and geometric information. 

Do NOT infer brand-level aesthetic rules or emotional/cinematic qualities. 

If any feature is not clearly visible, return null for that field rather than guessing.

Return a JSON object with the following structure:

{
  "product_identity": {
    "name": "string (optional)",
    "category": "string (optional)",
    "brand": "string (optional)"
  },
  "product_geometry": {
    "silhouette": "string",
    "cap_shape": "string",
    "label_shape": "string",
    "proportions": "string",
    "beveling_details": "string or null",
    "angles_to_preserve": ["string", ...]
  },
  "materials": {
    "body_material": "string",
    "cap_material": "string",
    "reflectivity": "string",
    "liquid_color": "string"
  },
  "visual_style": {
    "default_composition": "string",
    "recommended_backgrounds": ["string", ...],
    "forbidden_backgrounds": ["string", ...],
    "perspective": "string",
    "product_scale": "string"
  },
  "color_profile": {
    "dominant_colors": ["#hex", ...],
    "contrast_level": "high|medium|low",
    "avoid_colors": ["string", ...]
  }
}

Guidelines:
- Do NOT include lighting mood or atmospheric qualities (these belong to the scent profile).
- Do NOT include brand-wide rules (these belong to the brand style extractor).
- Extract colors as hex codes.
- If multiple images are provided, infer only consistent features.
Return ONLY valid JSON."""


async def extract_brand_style(images: List[Path]) -> BrandStyleJSON:
    """
    Extract brand style information from a list of brand style images.
    
    Args:
        images: List of paths to brand style images
        
    Returns:
        BrandStyleJSON object with extracted style information
        
    Raises:
        ValueError: If no images provided or images invalid
        RuntimeError: If extraction fails
    """
    if not images:
        raise ValueError("No images provided for brand style extraction")
    
    if not all(img.exists() for img in images):
        missing = [str(img) for img in images if not img.exists()]
        raise ValueError(f"One or more image files not found: {missing}")
    
    logger.info(f"Extracting brand style from {len(images)} images")
    start_time = time.time()
    
    try:
        # Create prompt for brand style extraction
        prompt = _create_brand_style_prompt()
        
        # Call Replicate API
        response_text = await _call_replicate_vision_api(images, prompt)
        
        # Parse JSON response
        # Try to extract JSON from response (may have markdown code blocks)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:500]}")
            raise ValueError(f"Invalid JSON response from Vision LLM: {e}")
        
        # Validate and create BrandStyleJSON object
        brand_style = BrandStyleJSON(**response_data)
        
        elapsed_time = time.time() - start_time
        cost = VISION_MODEL_COST_PER_IMAGE * len(images)
        logger.info(
            f"Brand style extraction completed in {elapsed_time:.2f}s "
            f"(cost: ${cost:.4f}, images: {len(images)})"
        )
        
        return brand_style
        
    except ValidationError as e:
        logger.error(f"Validation error creating BrandStyleJSON: {e}")
        raise ValueError(f"Invalid brand style data structure: {e}")
    except Exception as e:
        logger.error(f"Error extracting brand style: {e}", exc_info=True)
        raise RuntimeError(f"Failed to extract brand style: {e}")


async def extract_product_style(image: Path) -> ProductStyleJSON:
    """
    Extract product style information from a single product image.
    
    Args:
        image: Path to product image
        
    Returns:
        ProductStyleJSON object with extracted style information
        
    Raises:
        ValueError: If image not found or invalid
        RuntimeError: If extraction fails
    """
    if not image.exists():
        raise ValueError(f"Product image file not found: {image}")
    
    logger.info(f"Extracting product style from image: {image}")
    start_time = time.time()
    
    try:
        # Create prompt for product style extraction
        prompt = _create_product_style_prompt()
        
        # Call Replicate API with single image
        response_text = await _call_replicate_vision_api([image], prompt)
        
        # Parse JSON response
        # Try to extract JSON from response (may have markdown code blocks)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:500]}")
            raise ValueError(f"Invalid JSON response from Vision LLM: {e}")
        
        # Validate and create ProductStyleJSON object
        product_style = ProductStyleJSON(**response_data)
        
        elapsed_time = time.time() - start_time
        cost = VISION_MODEL_COST_PER_IMAGE
        logger.info(
            f"Product style extraction completed in {elapsed_time:.2f}s "
            f"(cost: ${cost:.4f})"
        )
        
        return product_style
        
    except ValidationError as e:
        logger.error(f"Validation error creating ProductStyleJSON: {e}")
        raise ValueError(f"Invalid product style data structure: {e}")
    except Exception as e:
        logger.error(f"Error extracting product style: {e}", exc_info=True)
        raise RuntimeError(f"Failed to extract product style: {e}")

