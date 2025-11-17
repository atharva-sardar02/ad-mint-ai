"""
Batch image generation with sequential reference image consistency.
Generates multiple images where each subsequent image uses the previous one as reference.
"""
import logging
from pathlib import Path
from typing import List, Optional

from app.services.pipeline.image_generation import generate_image

logger = logging.getLogger(__name__)


async def generate_images_with_sequential_references(
    prompts: List[str],
    output_dir: str,
    generation_id: str,
    consistency_markers: Optional[dict] = None,
    cancellation_check: Optional[callable] = None,
) -> List[str]:
    """
    Generate multiple images sequentially, using each previous image as reference for the next.
    
    This ensures visual consistency across all generated images by:
    1. Generating the first image with consistency markers
    2. Using the first image as reference for the second image
    3. Using the second image as reference for the third image
    4. And so on...
    
    Args:
        prompts: List of prompts, one per image
        output_dir: Directory to save generated images
        generation_id: Generation ID for logging
        consistency_markers: Optional dict with style markers for consistency
        cancellation_check: Optional function to check if generation should be cancelled
    
    Returns:
        List[str]: List of paths to generated images (in order)
    
    Example:
        prompts = [
            "A person jogging in a park",
            "The same person checking their phone",
            "The same person at a gym"
        ]
        # Image 2 will use Image 1 as reference
        # Image 3 will use Image 2 as reference
        # All share the same consistency markers
    """
    if not prompts:
        return []
    
    image_paths = []
    previous_image_path = None
    
    for idx, prompt in enumerate(prompts, start=1):
        # Check cancellation
        if cancellation_check and cancellation_check():
            raise RuntimeError("Image generation cancelled by user")
        
        logger.info(f"[{generation_id}] Generating image {idx}/{len(prompts)}")
        logger.debug(f"Prompt: {prompt[:80]}...")
        
        if previous_image_path:
            logger.info(f"[{generation_id}] Using previous image as reference for visual consistency")
        
        # Generate image with:
        # - Consistency markers (text-based style guidance)
        # - Previous image as reference (visual consistency)
        image_path = await generate_image(
            prompt=prompt,
            output_dir=output_dir,
            generation_id=generation_id,
            scene_number=idx,
            consistency_markers=consistency_markers,
            reference_image_path=previous_image_path,  # Use previous image as reference
            cancellation_check=cancellation_check,
        )
        
        image_paths.append(image_path)
        previous_image_path = image_path  # Use this image as reference for next
        
        logger.info(f"[{generation_id}] Image {idx} generated: {image_path}")
    
    logger.info(f"[{generation_id}] ✅ All {len(image_paths)} images generated with sequential references")
    return image_paths

