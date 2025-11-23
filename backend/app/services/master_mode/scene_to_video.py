"""
Scene to Video Parameter Builder for Master Mode.

Converts detailed scene descriptions into Veo 3.1 video generation parameters.
ENHANCES scenes with LLM to create ultra-detailed 300-500 word prompts optimized for Veo 3.1.
"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.services.master_mode.scene_enhancer import enhance_all_scenes_for_video, align_enhanced_scenes
from app.services.master_mode.appearance_sanitizer import sanitize_all_video_params

logger = logging.getLogger(__name__)


def extract_scene_metadata(scene_content: str) -> Dict[str, Any]:
    """
    Extract metadata from scene content (duration, camera movement, etc.).
    
    Args:
        scene_content: The detailed scene description (Markdown)
        
    Returns:
        Dict with duration, camera_movement, subject_present
    """
    # Default values
    metadata = {
        "duration": 6,  # Default 6 seconds
        "camera_movement": "static",
        "subject_present": True
    }
    
    content_lower = scene_content.lower()
    
    # Extract duration from scene header (e.g., "Scene 1: Attention (6 seconds)")
    import re
    duration_match = re.search(r'\((\d+)\s*seconds?\)', content_lower)
    if duration_match:
        duration = int(duration_match.group(1))
        # Veo 3.1 only supports 4, 6, or 8 seconds
        if duration <= 4:
            metadata["duration"] = 4
        elif duration <= 6:
            metadata["duration"] = 6
        else:
            metadata["duration"] = 8
    
    # Detect camera movement
    if any(word in content_lower for word in ["push-in", "push in", "dolly in"]):
        metadata["camera_movement"] = "push-in"
    elif any(word in content_lower for word in ["pull-out", "pull out", "dolly out"]):
        metadata["camera_movement"] = "pull-out"
    elif any(word in content_lower for word in ["pan left", "panning left"]):
        metadata["camera_movement"] = "pan-left"
    elif any(word in content_lower for word in ["pan right", "panning right"]):
        metadata["camera_movement"] = "pan-right"
    elif any(word in content_lower for word in ["tilt up"]):
        metadata["camera_movement"] = "tilt-up"
    elif any(word in content_lower for word in ["tilt down"]):
        metadata["camera_movement"] = "tilt-down"
    
    # Detect if subject is present
    if "subject does not appear" in content_lower or "no subject" in content_lower:
        metadata["subject_present"] = False
    
    return metadata


async def convert_scenes_to_video_prompts(
    scenes: List[Dict[str, Any]],
    story: str,
    reference_image_paths: Optional[List[str]] = None,
    vision_analysis: Optional[Dict[str, str]] = None,  # NEW: Vision analysis for consistency
    trace_dir: Optional[Path] = None,
    enhance_prompts: bool = True,
    generation_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convert all scenes to Veo 3.1 video generation parameters.
    ENHANCES scenes with LLM to expand from 150-250 words to 300-500 words with
    ultra-detailed cinematography, lighting, and technical specifications.
    
    Args:
        scenes: List of scene data (scene_number, content)
        story: Complete story for context
        reference_image_paths: User-provided reference images
        trace_dir: Optional directory to save trace files
        enhance_prompts: Whether to use LLM to enhance prompts (default: True)
        generation_id: Optional generation ID for streaming progress
        
    Returns:
        List of Veo 3.1 video generation parameters for each scene
    """
    logger.info(f"Converting {len(scenes)} scenes to Veo 3.1 video parameters")
    
    # Import send_llm_interaction for streaming
    from app.api.routes.master_mode_progress import send_llm_interaction
    
    # Create trace directory if provided
    if trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Enhance scenes with LLM for ultra-detailed prompts
    if enhance_prompts:
        logger.info("[Scene→Video] Step 1: Enhancing scenes with LLM for Veo 3.1 optimization")
        
        # Stream enhancer start
        if generation_id:
            await send_llm_interaction(
                generation_id=generation_id,
                agent="Scene Enhancer",
                interaction_type="prompt",
                content=f"Enhancing {len(scenes)} scenes for ultra-detailed Veo 3.1 prompts...",
                metadata={"num_scenes": len(scenes)}
            )
        
        # Build reference image descriptions from vision analysis
        reference_image_descriptions = None
        if vision_analysis:
            desc_parts = []
            if "character" in vision_analysis:
                desc_parts.append(f"**CHARACTER (maintain EXACT appearance):**\n{vision_analysis['character']}")
            if "product" in vision_analysis:
                desc_parts.append(f"**PRODUCT (maintain EXACT appearance):**\n{vision_analysis['product']}")
            if desc_parts:
                reference_image_descriptions = "\n\n".join(desc_parts)
                logger.info(f"[Scene→Video] Using vision analysis for character/product consistency ({len(reference_image_descriptions)} chars)")
        
        enhanced_scenes = await enhance_all_scenes_for_video(
            scenes=scenes,
            reference_image_descriptions=reference_image_descriptions  # Pass vision analysis
        )
        
        # Stream enhancer results
        if generation_id:
            total_original_length = sum(len(s["content"]) for s in scenes)
            total_enhanced_length = sum(len(s.get("enhanced_content", s["content"])) for s in enhanced_scenes)
            expansion_percent = ((total_enhanced_length - total_original_length) / total_original_length) * 100
            
            await send_llm_interaction(
                generation_id=generation_id,
                agent="Scene Enhancer",
                interaction_type="response",
                content=f"""✅ **Enhanced {len(scenes)} scenes**

**Expansion:**
- Original: {total_original_length:,} chars
- Enhanced: {total_enhanced_length:,} chars
- Growth: +{expansion_percent:.1f}%

All scenes now include ultra-detailed cinematography, lighting specifications, and technical parameters optimized for Veo 3.1.""",
                metadata={
                    "num_scenes": len(scenes),
                    "original_length": total_original_length,
                    "enhanced_length": total_enhanced_length,
                    "expansion_percent": expansion_percent
                }
            )
        
        # Step 1.5: Align enhanced scenes for cohesion (NEW LAYER)
        logger.info("[Scene→Video] Step 1.5: Aligning enhanced scenes for visual consistency")
        
        # Stream aligner start
        if generation_id:
            await send_llm_interaction(
                generation_id=generation_id,
                agent="Scene Aligner",
                interaction_type="prompt",
                content=f"Aligning {len(enhanced_scenes)} enhanced scenes for visual consistency across all scenes...",
                metadata={"num_scenes": len(enhanced_scenes)}
            )
        
        enhanced_scenes = await align_enhanced_scenes(enhanced_scenes)
        
        # Stream aligner results
        if generation_id:
            await send_llm_interaction(
                generation_id=generation_id,
                agent="Scene Aligner",
                interaction_type="response",
                content=f"""✅ **Aligned {len(enhanced_scenes)} scenes for consistency**

**Visual Cohesion Enforced:**
- ✓ People appear identical across all scenes
- ✓ Products maintain exact specifications
- ✓ Lighting style harmonized
- ✓ Camera feel unified
- ✓ Audio flow continuous

All scenes now have forensic-level visual consistency.""",
                metadata={
                    "num_scenes": len(enhanced_scenes)
                }
            )
    else:
        logger.info("[Scene→Video] Step 1: Using original scene content (enhancement disabled)")
        enhanced_scenes = scenes
    
    # Step 2: Build video generation parameters for each scene
    logger.info("[Scene→Video] Step 2: Building Veo 3.1 parameters")
    video_params_list = []
    
    for idx, scene in enumerate(enhanced_scenes):
        scene_number = scene["scene_number"]
        original_content = scene["content"]
        
        # Use enhanced content if available, otherwise use original
        if enhance_prompts and "enhanced_content" in scene:
            prompt_content = scene["enhanced_content"]
            logger.info(f"[Scene→Video] Scene {scene_number}: Using enhanced prompt ({len(prompt_content)} chars)")
        else:
            prompt_content = original_content
            logger.info(f"[Scene→Video] Scene {scene_number}: Using original prompt ({len(prompt_content)} chars)")
        
        # Extract metadata from original scene content (for duration, etc.)
        metadata = extract_scene_metadata(original_content)
        
        # Build Veo 3.1 parameters
        veo_params = {
            "scene_number": scene_number,
            "prompt": prompt_content,  # Enhanced ultra-detailed prompt (300-500 words)
            "negative_prompt": (
                "blurry, low quality, distorted, deformed, disfigured, bad anatomy, "
                "extra limbs, missing limbs, floating limbs, text, watermarks, logos, "
                "signatures, low resolution, pixelated, grainy, amateur, unrealistic, "
                "cartoon, animated, CGI, fake, artificial, poor lighting, overexposed, "
                "underexposed, motion blur, compression artifacts, noise, glitches"
            ),
            "duration": metadata["duration"],
            "aspect_ratio": "16:9",  # Default, can be made configurable
            "resolution": "1080p",  # High quality for ultra-realistic results
            "generate_audio": True,
            "seed": None,  # Let Veo generate random seed
        }
        
        # Add reference images if subject is present and images are provided
        if metadata["subject_present"] and reference_image_paths:
            # For Veo 3.1 R2V mode with reference images
            veo_params["reference_images"] = reference_image_paths
            # Note: When using reference_images, duration must be 8s and aspect_ratio 16:9
            veo_params["duration"] = 8
            veo_params["aspect_ratio"] = "16:9"
            logger.info(f"[Scene→Video] Scene {scene_number}: R2V mode with {len(reference_image_paths)} reference images")
        else:
            # Use start/end frame mode (will be populated later with generated images)
            veo_params["image"] = None  # Will be set to start frame path
            veo_params["last_frame"] = None  # Will be set to end frame path
            logger.info(f"[Scene→Video] Scene {scene_number}: Start/end frame mode")
        
        # Add metadata
        veo_params["metadata"] = {
            "scene_number": scene_number,
            "camera_movement": metadata["camera_movement"],
            "subject_present": metadata["subject_present"],
            "original_scene_length": len(original_content)
        }
        
        video_params_list.append(veo_params)
        
        # Save to trace
        if trace_dir:
            trace_file = trace_dir / f"scene_{scene_number}_video_params.json"
            trace_file.write_text(json.dumps(veo_params, indent=2), encoding="utf-8")
    
    logger.info(f"Successfully created {len(video_params_list)} Veo 3.1 parameter sets")
    logger.info(f"Total prompt length: {sum(len(p['prompt']) for p in video_params_list)} characters")
    
    # Step 3: Sanitize appearance descriptions from prompts (NEW)
    # This ensures reference images are the SOLE source of truth for character appearance
    logger.info("[Scene→Video] Step 3: Sanitizing appearance descriptions from prompts")
    
    # Stream sanitizer start
    if generation_id:
        await send_llm_interaction(
            generation_id=generation_id,
            agent="Appearance Sanitizer",
            interaction_type="prompt",
            content=f"Removing all physical appearance descriptions (face, hair, race, body) from {len(video_params_list)} video prompts to let reference images be the sole source of truth...",
            metadata={"num_scenes": len(video_params_list)}
        )
    
    video_params_list = sanitize_all_video_params(video_params_list)
    
    # Stream sanitizer results
    if generation_id:
        total_removed = sum(
            p["metadata"].get("original_prompt_length", 0) - p["metadata"].get("sanitized_prompt_length", 0)
            for p in video_params_list
        )
        total_original = sum(p["metadata"].get("original_prompt_length", 0) for p in video_params_list)
        removal_percent = (total_removed / total_original) * 100 if total_original > 0 else 0
        
        await send_llm_interaction(
            generation_id=generation_id,
            agent="Appearance Sanitizer",
            interaction_type="response",
            content=f"""✅ **Sanitized {len(video_params_list)} prompts**

**Removed Appearance Descriptions:**
- Total removed: {total_removed:,} chars ({removal_percent:.1f}%)
- Categories: face features, hair, skin tone, race, body type, age descriptors

**Kept:**
- ✓ Reference phrases ("exact same person from Reference Image 1")
- ✓ Actions, emotions, wardrobe
- ✓ Environment, lighting, camera specs

**Result:** Reference images are now the SOLE source of character appearance. This eliminates text/image "fighting" that causes inconsistency.""",
            metadata={
                "num_scenes": len(video_params_list),
                "total_removed": total_removed,
                "removal_percent": removal_percent
            }
        )
    
    logger.info(f"[Scene→Video] ✅ Prompts sanitized - reference images are now sole source of appearance")
    
    return video_params_list

