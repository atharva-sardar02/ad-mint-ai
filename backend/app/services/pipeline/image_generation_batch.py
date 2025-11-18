"""
Batch image generation with sequential reference image consistency.
Generates multiple images where each subsequent image uses the previous one as reference.
"""
import logging
from pathlib import Path
from typing import List, Optional

from app.services.pipeline.image_generation import generate_image

logger = logging.getLogger(__name__)


def _build_enhanced_image_prompt(
    base_prompt: str,
    consistency_markers: Optional[dict] = None,
    continuity_note: Optional[str] = None,
    consistency_guideline: Optional[str] = None,
    transition_note: Optional[str] = None,
    scene_number: int = 1,
) -> str:
    """
    Build an enhanced prompt for image generation that includes:
    - Base prompt (detailed image_generation_prompt from LLM)
    - Consistency markers (style, color, lighting, etc.)
    - **SUBJECT DESCRIPTION** (most critical - exact specs of the main subject)
    - Continuity notes (how this scene relates to previous scenes)
    - Consistency guidelines (per-scene specific instructions)
    - Transition notes (how the scene transitions from previous)
    
    This creates a comprehensive prompt that maximizes visual cohesion, 
    especially SUBJECT IDENTITY consistency (e.g., same perfume bottle across all scenes).
    """
    parts = [base_prompt]
    
    # Add SUBJECT DESCRIPTION first (highest priority for consistency)
    # Only add if subject appears in this scene
    if consistency_markers and "subject_description" in consistency_markers:
        subject_desc = consistency_markers["subject_description"]
        # Check if this is a scene where the subject should appear
        # If scene_number == 1, we're establishing the subject specification
        # For other scenes, only add if the base_prompt indicates subject presence
        # (The LLM's base_prompt will naturally exclude subject mentions if subject_presence is "none")
        if scene_number == 1:
            parts.append(f" | PRIMARY SUBJECT SPECIFICATION: {subject_desc}")
        else:
            # For scenes 2+, only emphasize subject consistency if the base prompt mentions the subject
            # This prevents forcing the subject into scenes where it shouldn't appear
            parts.append(f" | SUBJECT CONSISTENCY (if subject appears in this scene): {subject_desc} - If the subject appears in this scene, it must be the EXACT SAME subject with IDENTICAL appearance as established in Scene 1")
    
    # Add other consistency markers
    if consistency_markers:
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
            parts.append(" | " + ", ".join(marker_parts))
    
    # Add continuity notes (for scenes 2+)
    if continuity_note and scene_number > 1:
        parts.append(f" | Continuity: {continuity_note}")
    
    # Add consistency guidelines
    if consistency_guideline:
        parts.append(f" | Consistency Guidelines: {consistency_guideline}")
    
    # Add transition notes (for scenes 2+)
    if transition_note and scene_number > 1:
        parts.append(f" | Transition: {transition_note}")
    
    # For scenes 2+, add explicit instruction to maintain visual coherence with previous scenes
    if scene_number > 1:
        parts.append(" | IMPORTANT: Maintain visual consistency with previous scenes - same characters, same style, same color palette, same lighting, same overall aesthetic")
    
    # For ALL scenes (including scene 1), add strong visual consistency instruction
    # This ensures start/end images maintain cohesion even though they show different moments
    parts.append(" | CRITICAL VISUAL CONSISTENCY: This image must maintain exact visual consistency with the reference image - ESPECIALLY THE SUBJECT MUST BE IDENTICAL (same exact design, same exact appearance, same exact proportions, same exact colors, same exact materials), same lighting direction, same style, same visual universe. Even though this is a different moment/pose, it must look like it's from the same scene/shot with the EXACT SAME subject.")
    
    enhanced = " ".join(parts)
    
    # Log the enhancement for debugging
    if continuity_note or consistency_guideline or transition_note:
        logger.debug(f"[Scene {scene_number}] Enhanced prompt includes continuity/consistency/transition notes")
    
    return enhanced


async def generate_images_with_sequential_references(
    prompts: List[str],
    output_dir: str,
    generation_id: str,
    consistency_markers: Optional[dict] = None,
    continuity_notes: Optional[List[str]] = None,
    consistency_guidelines: Optional[List[str]] = None,
    transition_notes: Optional[List[str]] = None,
    initial_reference_image: Optional[str] = None,  # Base reference image to start the chain (e.g., scene's reference image for start/end frames)
    cancellation_check: Optional[callable] = None,
    scene_offset: int = 0,  # Offset for scene numbering in filenames (e.g., if generating single images per scene in a loop)
) -> List[str]:
    """
    Generate multiple images sequentially, using each previous image as reference for the next.
    
    This ensures visual consistency across all generated images by:
    1. Generating the first image with enhanced prompts (consistency markers + continuity notes + guidelines)
       - If initial_reference_image is provided, use it as the base reference for the first image
       - Otherwise, generate the first image without a reference
    2. Using the first image as reference for the second image
    3. Using the second image as reference for the third image
    4. And so on...
    
    Args:
        prompts: List of base prompts, one per image (should be detailed image_generation_prompt from LLM)
        output_dir: Directory to save generated images
        generation_id: Generation ID for logging
        consistency_markers: Optional dict with style markers for consistency
        continuity_notes: Optional list of continuity notes for each scene (how it relates to previous scenes)
        consistency_guidelines: Optional list of per-scene visual consistency guidelines
        transition_notes: Optional list of scene transition notes
        initial_reference_image: Optional base reference image to start the chain (e.g., scene's reference image for start/end frames)
        cancellation_check: Optional function to check if generation should be cancelled
        scene_offset: Offset for scene numbering in filenames (CRITICAL for start/end images generated one at a time in a loop)
    
    Returns:
        List[str]: List of paths to generated images (in order)
    
    Example:
        prompts = [
            "A person jogging in a park",
            "The same person checking their phone",
            "The same person at a gym"
        ]
        # Image 1 will use initial_reference_image (if provided) or no reference
        # Image 2 will use Image 1 as reference
        # Image 3 will use Image 2 as reference
        # All share the same consistency markers and enhanced with continuity notes
        
    Note on scene_offset:
        When generating start/end images for multiple scenes (one at a time in a loop):
        - Scene 1 start: scene_offset=0 → filename: {gen_id}_scene_1.png
        - Scene 2 start: scene_offset=1 → filename: {gen_id}_scene_2.png
        - Scene 3 start: scene_offset=2 → filename: {gen_id}_scene_3.png
        Without scene_offset, all would be named _scene_1.png and overwrite each other!
    """
    if not prompts:
        return []
    
    image_paths = []
    previous_image_path = initial_reference_image  # Start with initial reference if provided
    
    for idx, prompt in enumerate(prompts, start=1):
        # Check cancellation
        if cancellation_check and cancellation_check():
            raise RuntimeError("Image generation cancelled by user")
        
        logger.info(f"[{generation_id}] Generating image {idx}/{len(prompts)}")
        logger.debug(f"Base prompt: {prompt[:80]}...")
        
        # Determine which reference image to use
        reference_to_use = None
        if previous_image_path:
            # Check if the file exists before using it
            ref_path = Path(previous_image_path)
            if ref_path.exists():
                reference_to_use = previous_image_path
                if idx == 1 and previous_image_path == initial_reference_image:
                    logger.info(f"[{generation_id}] Using initial reference image as base for visual consistency: {previous_image_path}")
                else:
                    logger.info(f"[{generation_id}] Using previous generated image as reference for visual consistency: {previous_image_path}")
            else:
                logger.warning(f"[{generation_id}] Reference image not found: {previous_image_path}, generating without reference")
                reference_to_use = None
        
        # Build enhanced prompt with all consistency information
        enhanced_prompt = _build_enhanced_image_prompt(
            base_prompt=prompt,
            consistency_markers=consistency_markers,
            continuity_note=continuity_notes[idx - 1] if continuity_notes and idx - 1 < len(continuity_notes) else None,
            consistency_guideline=consistency_guidelines[idx - 1] if consistency_guidelines and idx - 1 < len(consistency_guidelines) else None,
            transition_note=transition_notes[idx - 1] if transition_notes and idx - 1 < len(transition_notes) else None,
            scene_number=idx,
        )
        
        logger.debug(f"[{generation_id}] Enhanced prompt length: {len(enhanced_prompt)} characters")
        
        # Generate image with:
        # - Enhanced prompt (base + markers + continuity notes + guidelines + explicit coherence instructions)
        # - Previous image as reference (visual consistency chain)
        # 
        # Coherence Chain:
        # - Scene 1: Uses user's initial reference image (if provided) OR no reference
        # - Scene 2: Uses Scene 1's reference image as reference
        # - Scene 3: Uses Scene 2's reference image as reference
        # - Scene 4: Uses Scene 3's reference image as reference
        # This creates a visual chain where each scene maintains consistency with the previous one
        image_path = await generate_image(
            prompt=enhanced_prompt,
            output_dir=output_dir,
            generation_id=generation_id,
            scene_number=scene_offset + idx,  # Use scene_offset to ensure correct filename numbering
            consistency_markers=None,  # Already included in enhanced_prompt
            reference_image_path=reference_to_use,  # Use previous image as reference (creates visual chain)
            cancellation_check=cancellation_check,
        )
        
        image_paths.append(image_path)
        # Update previous_image_path to the newly generated image for next iteration
        # This creates the sequential chain: Image 1 -> Image 2 -> Image 3 -> Image 4
        previous_image_path = image_path  # Use this image as reference for next
        
        logger.info(f"[{generation_id}] Image {idx} generated: {image_path}")
    
    logger.info(f"[{generation_id}] ✅ All {len(image_paths)} images generated with sequential references")
    return image_paths

