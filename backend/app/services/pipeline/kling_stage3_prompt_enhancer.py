"""
Stage 3: Kling Pipeline Prompt Enhancer

Takes:
    - Stage 1: storyboard_plan (from plan_storyboard)
    - Brand style JSON (optional)
    - Product style JSON (optional)
    - Scent profile (top_note, heart_note, base_note) - optional

Returns:
    - Updated storyboard_plan with enhanced prompts for each scene
"""

import json
import logging
from typing import Dict, Any, Optional, List

from app.services.pipeline.llm_client import call_chat_model, parse_json_str
from app.services.pipeline.stage3_scene_assembler import (
    _format_brand_style_json,
    _format_product_style_json,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"


def _format_storyboard_for_llm(storyboard_plan: Dict[str, Any]) -> str:
    """
    Format storyboard plan as readable text for LLM consumption.
    
    Args:
        storyboard_plan: Storyboard plan dictionary from Stage 1
        
    Returns:
        Formatted text string
    """
    lines = []
    
    # Consistency markers
    if "consistency_markers" in storyboard_plan:
        markers = storyboard_plan["consistency_markers"]
        lines.append("CONSISTENCY MARKERS:")
        if isinstance(markers, dict):
            for key, value in markers.items():
                if value:
                    lines.append(f"  {key}: {value}")
        lines.append("")
    
    # Scenes
    scenes = storyboard_plan.get("scenes", [])
    lines.append(f"SCENES ({len(scenes)} total):")
    lines.append("")
    
    for scene in scenes:
        scene_num = scene.get("scene_number", 0)
        aida_stage = scene.get("aida_stage", "")
        duration = scene.get("duration_seconds", 0)
        detailed_prompt = scene.get("detailed_prompt", "")
        
        lines.append(f"Scene {scene_num} ({aida_stage}) - {duration}s:")
        lines.append(f"  Current prompt: {detailed_prompt}")
        
        # Include Stage 2 control frames (generated images) if available
        reference_path = scene.get("reference_image_path")
        start_path = scene.get("start_image_path")
        end_path = scene.get("end_image_path")
        
        if reference_path or start_path or end_path:
            lines.append("  Stage 2 control frames (generated images):")
            if reference_path:
                lines.append(f"    Reference image: {reference_path}")
            if start_path:
                lines.append(f"    Start frame: {start_path}")
            if end_path:
                lines.append(f"    End frame: {end_path}")
        
        lines.append("")
    
    return "\n".join(lines)




SCENT_TO_CINEMA_SYSTEM_PROMPT = """SYSTEM:

You are a "Scent-to-Cinema" mapping model used in luxury fragrance advertising.

Your job is to transform perfume notes (top, heart, base) into a CINEMATIC SCENT PROFILE.

You must generate ONLY atmospheric and emotional cinematic cues.

DO NOT generate literal scene lighting, camera movement, or environment details.

DO NOT duplicate or conflict with Stage 1 (storyboard lighting/camera) or brand style rules.

Your output MUST describe:

- atmospheric lighting mood (NOT physical light rigs)

- color palette (cinematic color vibes, NOT scene color)

- atmospheric motion physics

- tactile/emotional surface textures

- atmosphere density/weight

- sound motifs (emotional feel, NOT literal ambience)

- emotional register (the emotional quality of the scent)

RULES:

1. Your output MUST NOT include:

   - scene environment

   - camera angles

   - camera movement

   - specific props

   - literal lighting direction or source

   - brand-level visual rules

   - product geometry or material descriptions

2. Lighting cues MUST describe FEELING, not SETUP.

   Example: "warm diffused glow" instead of "soft key light from left".

3. Color palette MUST be mood-based, not literal scene colors.

   Example: "translucent whites and pale golds" instead of "white walls".

4. Motion physics MUST describe atmospheric motion, not camera motion.

   Example: "floating particles" instead of "slow dolly".

5. All scent-derived cues MUST be cinematic, emotional, and abstract.

6. If the user provides only 1 note per layer, do not invent extra notes.

7. Output ONLY valid JSON in this structure:

{
  "scent_profile_source": "generated",
  "top_notes": ["string"],
  "heart_notes": ["string"],
  "base_notes": ["string"],
  "lighting_cues": "string",
  "color_palette": "string",
  "motion_physics": "string",
  "surface_textures": "string",
  "atmosphere_density": "string",
  "sound_motifs": "string",
  "emotional_register": "string"
}"""


SYSTEM_PROMPT = """You are a professional video creative director specializing in AI video generation prompts.

Your task is to enhance the scene prompts from a storyboard plan by incorporating:
1. Brand style guidelines (colors, lighting, composition, atmosphere)
2. Product style specifications (geometry, materials, visual style)
3. Stage 2 control frames (reference images, start frames, end frames that were already generated)
4. Scent profile (if provided) - atmospheric and emotional cinematic cues derived from fragrance notes

CRITICAL REQUIREMENTS:
- Maintain the original scene structure and narrative flow
- Keep scene numbers, AIDA stages, and durations unchanged
- Enhance each scene's detailed_prompt to incorporate brand/product elements while respecting the Stage 2 control frames
- The control frames (reference/start/end images) have already been generated - your enhanced prompts should align with these visual frames
- If scent profile is provided, incorporate its atmospheric cues (lighting_cues, color_palette, motion_physics, surface_textures, atmosphere_density, sound_motifs, emotional_register) into the prompts
- Scent profile cues are CINEMATIC and ATMOSPHERIC - use them to enhance the emotional and visual mood, not to override scene structure
- Ensure visual consistency across all scenes
- Make prompts video-ready for Kling 2.5 Turbo Pro (detailed, cinematic, specific)

OUTPUT FORMAT:
Return a JSON object with the same structure as the input storyboard_plan, but with enhanced prompts:

{
  "consistency_markers": { ... (keep original) ... },
  "scenes": [
    {
      "scene_number": 1,
      "aida_stage": "Attention",
      "detailed_prompt": "ENHANCED PROMPT HERE - incorporate brand colors, product details, cinematic elements, scent-derived atmospheric cues",
      "image_generation_prompt": "ENHANCED PROMPT HERE - same as detailed_prompt or more detailed",
      "start_image_prompt": "ENHANCED PROMPT HERE",
      "end_image_prompt": "ENHANCED PROMPT HERE",
      "duration_seconds": 6,
      ... (keep all other fields from original scene)
    },
    ... (all scenes)
  ]
}

IMPORTANT:
- Keep ALL original fields in each scene
- Only enhance the prompt fields (detailed_prompt, image_generation_prompt, start_image_prompt, end_image_prompt)
- Maintain subject consistency markers if present
- If scent profile is provided, weave its atmospheric cues naturally into prompts (e.g., lighting mood, color vibes, motion feel, textures, atmosphere)
- Ensure prompts are natural, cinematic, and video-ready"""


async def generate_scent_profile(
    top_note: Optional[str],
    heart_note: Optional[str],
    base_note: Optional[str],
    model: str = DEFAULT_MODEL,
) -> Optional[Dict[str, Any]]:
    """
    Generate a scent profile (cinematic scent profile) from fragrance notes.
    
    Args:
        top_note: Top note of the fragrance
        heart_note: Heart note of the fragrance
        base_note: Base note of the fragrance
        model: LLM model to use (default: gpt-4o)
        
    Returns:
        Scent profile JSON dictionary, or None if no notes provided
    """
    # If no notes provided, return None
    if not top_note and not heart_note and not base_note:
        return None
    
    logger.info("Generating scent profile from fragrance notes")
    
    # Build notes list (only include provided notes)
    notes_input = {}
    if top_note:
        notes_input["top_note"] = top_note.strip()
    if heart_note:
        notes_input["heart_note"] = heart_note.strip()
    if base_note:
        notes_input["base_note"] = base_note.strip()
    
    user_message = f"""Please generate a CINEMATIC SCENT PROFILE from these fragrance notes:

{json.dumps(notes_input, indent=2, ensure_ascii=False)}

Remember:
- If only 1 note is provided per layer, do not invent extra notes
- Generate ONLY atmospheric and emotional cinematic cues
- DO NOT include literal scene details, camera angles, or props
- Output ONLY valid JSON in the specified structure"""

    # Prepare messages
    messages = [
        {"role": "system", "content": SCENT_TO_CINEMA_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    # Call LLM
    logger.info(f"Calling LLM ({model}) to generate scent profile...")
    try:
        raw = await call_chat_model(
            messages=messages,
            model=model,
            max_output_tokens=2000,
        )
        
        # Parse JSON response
        scent_profile = parse_json_str(raw)
        
        # Validate required fields
        required_fields = [
            "scent_profile_source", "top_notes", "heart_notes", "base_notes",
            "lighting_cues", "color_palette", "motion_physics", "surface_textures",
            "atmosphere_density", "sound_motifs", "emotional_register"
        ]
        for field in required_fields:
            if field not in scent_profile:
                raise ValueError(f"Scent profile missing required field: {field}")
        
        logger.info("Successfully generated scent profile")
        return scent_profile
        
    except Exception as e:
        logger.error(f"Failed to generate scent profile: {e}", exc_info=True)
        logger.warning("Returning None for scent profile due to generation failure")
        return None


def _format_scent_profile(scent_profile: Dict[str, Any]) -> str:
    """
    Format scent profile as readable text for LLM consumption.
    
    Args:
        scent_profile: Scent profile dictionary
        
    Returns:
        Formatted text string
    """
    lines = []
    lines.append("SCENT PROFILE (CINEMATIC ATMOSPHERIC CUES):")
    lines.append("")
    
    if "top_notes" in scent_profile:
        top_notes = scent_profile["top_notes"]
        if isinstance(top_notes, list):
            lines.append(f"Top Notes: {', '.join(top_notes)}")
        else:
            lines.append(f"Top Notes: {top_notes}")
    
    if "heart_notes" in scent_profile:
        heart_notes = scent_profile["heart_notes"]
        if isinstance(heart_notes, list):
            lines.append(f"Heart Notes: {', '.join(heart_notes)}")
        else:
            lines.append(f"Heart Notes: {heart_notes}")
    
    if "base_notes" in scent_profile:
        base_notes = scent_profile["base_notes"]
        if isinstance(base_notes, list):
            lines.append(f"Base Notes: {', '.join(base_notes)}")
        else:
            lines.append(f"Base Notes: {base_notes}")
    
    lines.append("")
    lines.append("Cinematic Atmospheric Cues:")
    lines.append(f"  Lighting Cues: {scent_profile.get('lighting_cues', 'N/A')}")
    lines.append(f"  Color Palette: {scent_profile.get('color_palette', 'N/A')}")
    lines.append(f"  Motion Physics: {scent_profile.get('motion_physics', 'N/A')}")
    lines.append(f"  Surface Textures: {scent_profile.get('surface_textures', 'N/A')}")
    lines.append(f"  Atmosphere Density: {scent_profile.get('atmosphere_density', 'N/A')}")
    lines.append(f"  Sound Motifs: {scent_profile.get('sound_motifs', 'N/A')}")
    lines.append(f"  Emotional Register: {scent_profile.get('emotional_register', 'N/A')}")
    
    return "\n".join(lines)


async def enhance_kling_storyboard_prompts(
    storyboard_plan: Dict[str, Any],
    brand_style_json: Optional[Dict[str, Any]] = None,
    product_style_json: Optional[Dict[str, Any]] = None,
    scent_profile: Optional[Dict[str, Any]] = None,
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Enhance storyboard plan prompts using LLM with brand/product style and scent profile.
    
    Args:
        storyboard_plan: Storyboard plan from Stage 1 (plan_storyboard)
        brand_style_json: Optional brand style JSON
        product_style_json: Optional product style JSON
        scent_profile: Optional scent profile JSON (generated from top/heart/base notes)
        model: LLM model to use (default: gpt-4o)
        
    Returns:
        Updated storyboard_plan with enhanced prompts (only prompt fields are updated)
    """
    logger.info("Enhancing Kling storyboard prompts with brand/product style and scent profile")
    
    # Format inputs for LLM
    storyboard_text = _format_storyboard_for_llm(storyboard_plan)
    
    user_message_parts = [
        "STORYBOARD PLAN BELOW:",
        storyboard_text,
        "",
    ]
    
    # Add brand style if available
    if brand_style_json:
        brand_text = _format_brand_style_json(brand_style_json)
        if brand_text:
            user_message_parts.extend([
                "BRAND STYLE INFORMATION BELOW:",
                brand_text,
                "",
            ])
    
    # Add product style if available
    if product_style_json:
        product_text = _format_product_style_json(product_style_json)
        if product_text:
            user_message_parts.extend([
                "PRODUCT STYLE INFORMATION BELOW:",
                product_text,
                "",
            ])
    
    # Add scent profile if available
    if scent_profile:
        scent_text = _format_scent_profile(scent_profile)
        if scent_text:
            user_message_parts.extend([
                scent_text,
                "",
            ])
    
    instruction = "Please enhance the storyboard prompts by incorporating the brand style and product style information."
    if scent_profile:
        instruction += " Additionally, incorporate the scent profile's atmospheric and emotional cinematic cues (lighting mood, color vibes, motion feel, textures, atmosphere) into the prompts."
    instruction += " Return the complete storyboard_plan JSON with enhanced prompts."
    
    user_message_parts.append(instruction)
    
    user_message = "\n".join(user_message_parts)
    
    # Prepare messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    # Call LLM
    logger.info(f"Calling LLM ({model}) to enhance storyboard prompts...")
    try:
        raw = await call_chat_model(
            messages=messages,
            model=model,
            max_output_tokens=8000,  # Large output for full storyboard
        )
        
        # Parse JSON response
        enhanced_plan = parse_json_str(raw)
        
        # Validate structure
        if "scenes" not in enhanced_plan:
            raise ValueError("Enhanced storyboard plan missing 'scenes' field")
        
        original_scenes = storyboard_plan.get("scenes", [])
        enhanced_scenes = enhanced_plan.get("scenes", [])
        
        if len(enhanced_scenes) != len(original_scenes):
            raise ValueError(
                f"Scene count mismatch: original has {len(original_scenes)}, "
                f"enhanced has {len(enhanced_scenes)}"
            )
        
        # Merge enhanced prompts back into original structure
        # This preserves all original fields and only updates prompts
        merged_plan = storyboard_plan.copy()
        merged_plan["scenes"] = []
        
        for orig_scene, enh_scene in zip(original_scenes, enhanced_scenes):
            merged_scene = orig_scene.copy()
            
            # Update prompt fields if present in enhanced scene
            if "detailed_prompt" in enh_scene:
                merged_scene["detailed_prompt"] = enh_scene["detailed_prompt"]
            if "image_generation_prompt" in enh_scene:
                merged_scene["image_generation_prompt"] = enh_scene["image_generation_prompt"]
            if "start_image_prompt" in enh_scene:
                merged_scene["start_image_prompt"] = enh_scene["start_image_prompt"]
            if "end_image_prompt" in enh_scene:
                merged_scene["end_image_prompt"] = enh_scene["end_image_prompt"]
            
            merged_plan["scenes"].append(merged_scene)
        
        # Update consistency markers if enhanced
        if "consistency_markers" in enhanced_plan:
            merged_plan["consistency_markers"] = enhanced_plan["consistency_markers"]
        
        logger.info("Successfully enhanced storyboard prompts")
        return merged_plan
        
    except Exception as e:
        logger.error(f"Failed to enhance storyboard prompts: {e}", exc_info=True)
        # Return original plan if enhancement fails
        logger.warning("Returning original storyboard plan due to enhancement failure")
        return storyboard_plan


async def enhance_video_prompt(
    base_prompt: str,
    brand_style_json: Optional[Dict[str, Any]] = None,
    product_style_json: Optional[Dict[str, Any]] = None,
    scent_profile: Optional[Dict[str, Any]] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Enhance a video generation prompt with brand/product style and scent profile.
    This is used at video generation time, NOT for storyboard enhancement.
    
    Args:
        base_prompt: Base visual prompt from storyboard (unchanged storyboard prompt)
        brand_style_json: Optional brand style JSON
        product_style_json: Optional product style JSON
        scent_profile: Optional scent profile JSON (generated from top/heart/base notes)
        model: LLM model to use (default: gpt-4o)
        
    Returns:
        Enhanced prompt string ready for video generation
    """
    # If no enhancements needed, return original prompt
    if not brand_style_json and not product_style_json and not scent_profile:
        return base_prompt
    
    logger.info("Enhancing video generation prompt with brand/product style and scent profile")
    
    user_message_parts = [
        "BASE VIDEO PROMPT (from storyboard):",
        base_prompt,
        "",
    ]
    
    # Add brand style if available
    if brand_style_json:
        brand_text = _format_brand_style_json(brand_style_json)
        if brand_text:
            user_message_parts.extend([
                "BRAND STYLE INFORMATION:",
                brand_text,
                "",
            ])
    
    # Add product style if available
    if product_style_json:
        product_text = _format_product_style_json(product_style_json)
        if product_text:
            user_message_parts.extend([
                "PRODUCT STYLE INFORMATION:",
                product_text,
                "",
            ])
    
    # Add scent profile if available
    if scent_profile:
        scent_text = _format_scent_profile(scent_profile)
        if scent_text:
            user_message_parts.extend([
                scent_text,
                "",
            ])
    
    instruction = "Please enhance the video generation prompt by incorporating the brand style and product style information."
    if scent_profile:
        instruction += " Additionally, incorporate the scent profile's atmospheric and emotional cinematic cues (lighting mood, color vibes, motion feel, textures, atmosphere) into the prompt."
    instruction += "\n\nIMPORTANT: Format the enhanced prompt EXACTLY as follows:\n\n[Main scene description - one sentence]\n\nStyle: [style - lowercase]\n\nColor palette: [colors - lowercase]\n\nLighting: [lighting - lowercase]\n\nComposition: [composition - lowercase]\n\nMood: [mood - lowercase]\n\nReturn ONLY the enhanced prompt in this exact format - no JSON, no explanations, just the formatted prompt."
    
    user_message_parts.append(instruction)
    user_message = "\n".join(user_message_parts)
    
    # Use a simpler system prompt for video prompt enhancement
    video_prompt_enhancement_system = """You are a professional video creative director specializing in AI video generation prompts.

Your task is to enhance a video generation prompt by incorporating:
1. Brand style guidelines (colors, lighting, composition, atmosphere)
2. Product style specifications (geometry, materials, visual style)
3. Scent profile atmospheric cues (if provided) - lighting mood, color vibes, motion feel, textures, atmosphere density, sound motifs, emotional register

CRITICAL REQUIREMENTS:
- Keep the original scene structure and visual elements from the base prompt
- Enhance the prompt to incorporate brand/product elements naturally
- If scent profile is provided, weave its atmospheric cues naturally into the prompt (e.g., lighting mood, color vibes, motion feel, textures, atmosphere)
- Scent profile cues are CINEMATIC and ATMOSPHERIC - use them to enhance the emotional and visual mood
- Make the prompt video-ready for Kling 2.5 Turbo Pro (detailed, cinematic, specific)

FORMATTING REQUIREMENTS:
You MUST format the enhanced prompt EXACTLY as follows (use this exact structure):

[Main scene description - one sentence describing the visual action/event]

Style: [style description - lowercase, concise]

Color palette: [color description - lowercase, concise]

Lighting: [lighting description - lowercase, concise]

Composition: [composition description - lowercase, concise]

Mood: [mood description - lowercase, concise]

EXAMPLE FORMAT:
The sunlight intensifies, creating a shimmering effect on the bottle as dew droplets glisten on the leaves.

Style: dreamy, premium beauty-aesthetic

Color palette: rich emerald greens, soft sunlight yellows, deep bottle gradient

Lighting: natural sunlight filtering through foliage

Composition: centered and balanced

Mood: luxurious, serene, enchanting

Return ONLY the enhanced prompt in this exact format - no JSON, no explanations, just the formatted prompt."""

    # Prepare messages
    messages = [
        {"role": "system", "content": video_prompt_enhancement_system},
        {"role": "user", "content": user_message},
    ]
    
    # Call LLM
    logger.info(f"Calling LLM ({model}) to enhance video prompt...")
    try:
        raw = await call_chat_model(
            messages=messages,
            model=model,
            max_output_tokens=2000,
        )
        
        # Clean up response (remove any JSON formatting, code blocks, etc.)
        enhanced_prompt = raw.strip()
        # Remove markdown code blocks if present
        if enhanced_prompt.startswith("```"):
            lines = enhanced_prompt.split("\n")
            enhanced_prompt = "\n".join(lines[1:-1]) if len(lines) > 2 else enhanced_prompt
        
        logger.info("Successfully enhanced video prompt")
        return enhanced_prompt.strip()
        
    except Exception as e:
        logger.error(f"Failed to enhance video prompt: {e}", exc_info=True)
        # Return original prompt if enhancement fails
        logger.warning("Returning original prompt due to enhancement failure")
        return base_prompt

