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
    trace_dir: Optional[Path] = None,
    enhance_prompts: bool = True
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
        
    Returns:
        List of Veo 3.1 video generation parameters for each scene
    """
    logger.info(f"Converting {len(scenes)} scenes to Veo 3.1 video parameters")
    
    # Create trace directory if provided
    if trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Enhance scenes with LLM for ultra-detailed prompts
    if enhance_prompts:
        logger.info("[Scene→Video] Step 1: Enhancing scenes with LLM for Veo 3.1 optimization")
        enhanced_scenes = await enhance_all_scenes_for_video(
            scenes=scenes,
            reference_image_descriptions=None  # Could pass vision analysis here
        )
        
        # Step 1.5: Align enhanced scenes for cohesion (NEW LAYER)
        logger.info("[Scene→Video] Step 1.5: Aligning enhanced scenes for visual consistency")
        enhanced_scenes = await align_enhanced_scenes(enhanced_scenes)
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
    
    return video_params_list

