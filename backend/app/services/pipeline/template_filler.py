"""
Template Filler Service - Stage 1 of Fill-in-the-Blank System

This service takes a structured template with __FILL__ placeholders
and uses LLM to fill every field based on the user prompt.
"""

import json
import logging
from typing import Dict, Any, Optional

import openai

from app.core.config import settings
from app.services.pipeline.fill_in_templates import get_fill_in_template

logger = logging.getLogger(__name__)


def get_template_filler_prompt(template: Dict[str, Any], user_prompt: str) -> str:
    """Generate system prompt for filling template fields."""
    
    template_name = template["template_name"]
    beats = template["beats"]
    
    return f"""You are a professional advertisement content creator. Your job is to fill in a structured template with specific, detailed information.

USER PROMPT: "{user_prompt}"

SELECTED TEMPLATE: {template_name}
STORY BEATS: {', '.join(beats)}

YOUR TASK:
You will receive a structured template with fields marked as "__FILL__". You must replace EVERY "__FILL__" with appropriate, specific content based on the user prompt.

CRITICAL RULES:

1. **BE SPECIFIC, NOT GENERIC**
   - ❌ BAD: "brown hair" 
   - ✅ GOOD: "chestnut brown"
   
   - ❌ BAD: "woman in her 30s"
   - ✅ GOOD: "32"
   
   - ❌ BAD: "kitchen"
   - ✅ GOOD: "modern minimalist kitchen with white marble counters"

2. **CHARACTER FIELDS - POLICE DESCRIPTION LEVEL**
   If character is present:
   - age_exact: Specific number (e.g., "32", not "early 30s")
   - height_feet and height_inches: Exact measurements (e.g., "5" and "6")
   - hair.color: Specific shade (e.g., "chestnut brown", not "brown")
   - hair.length: Precise (e.g., "mid-back length", not "long")
   - eye.color: Specific (e.g., "emerald green", not "green")
   - skin.fitzpatrick_type: Must be "Type I", "Type II", "Type III", "Type IV", "Type V", or "Type VI"
   - distinguishing_features.marks_or_scars: Specific location (e.g., "small beauty mark near left eye, above cheekbone")

3. **PRODUCT FIELDS - EXACT SPECIFICATIONS**
   If product is present:
   - dimensions: Numbers only (e.g., "4", not "about 4")
   - colors: Specific shades (e.g., "pure white", "matte black", "rose gold")
   - material: Precise (e.g., "white ceramic with matte finish", not "ceramic")
   - unique_features: Detailed (e.g., "thin gold rim at top edge, exactly 2mm width")

4. **SCENE FIELDS - CINEMATOGRAPHIC DETAIL**
   For each scene:
   - environment.background_description: Detailed visual description (e.g., "large window with soft white semi-sheer curtains, morning light filtering through")
   - camera.angle: Specific (e.g., "eye-level", "low angle looking up 30 degrees", "overhead bird's eye")
   - lighting.primary_light_source: Exact (e.g., "natural window light", "overhead pendant lamp with warm bulb")
   - character_details.action: Precise action (e.g., "reaching towards coffee mug with both hands, fingers approaching handle")

5. **CONSISTENCY ACROSS SCENES**
   - Character fields: MUST be identical in all scenes (same age, same hair, same eyes, etc.)
   - Product fields: MUST be identical in all scenes (same dimensions, same colors, etc.)
   - Only scene-specific fields should vary (camera angle, lighting, action, position)

6. **BOOLEAN FIELDS**
   - Use "true" or "false" (not "yes"/"no", not "True"/"False")

7. **DURATION FIELDS**
   - Must be between 3 and 7 (seconds)
   - Total of all scene durations should equal target duration

8. **NO PLACEHOLDERS LEFT**
   - Every "__FILL__" must be replaced
   - No field should contain "__FILL__" in your response
   - If uncertain, make a reasonable specific choice based on the user prompt

RESPONSE FORMAT:
Return the complete template with ALL "__FILL__" replaced with specific values. Return as valid JSON.

EXAMPLE OF GOOD FILLS:
```json
{{
  "character": {{
    "age_exact": "32",
    "height_feet": "5",
    "height_inches": "6",
    "hair": {{
      "color": "chestnut brown with subtle auburn highlights",
      "length": "mid-back length, approximately 20 inches",
      "style": "natural loose waves with middle part"
    }}
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "environment": {{
        "background_description": "large floor-to-ceiling window with sheer white linen curtains, soft diffused morning light creating gentle shadows on white textured walls"
      }},
      "camera": {{
        "angle": "eye-level from slightly above, approximately 10 degrees down"
      }}
    }}
  ]
}}
```

Now fill the template below based on the user prompt: "{user_prompt}"
"""


async def fill_template_with_llm(
    template_id: str,
    user_prompt: str,
    target_duration: int = 15,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Fill template with LLM based on user prompt.
    
    Args:
        template_id: ID of template to fill
        user_prompt: User's advertisement prompt
        target_duration: Target total duration in seconds
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Completely filled template with all __FILL__ replaced
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    # Load template
    template = get_fill_in_template(template_id)
    if not template:
        raise ValueError(f"Invalid template ID: {template_id}")
    
    model = "gpt-4o"  # Best model for following complex instructions
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = get_template_filler_prompt(template, user_prompt)
    
    # Prepare template structure for filling
    template_structure = template["structure"].copy()
    
    # Add target duration context to scenes
    num_scenes = len(template["beats"])
    avg_duration = target_duration // num_scenes
    
    user_message = f"""Fill this template completely. Replace ALL "__FILL__" placeholders with specific, detailed content.

Target duration: {target_duration} seconds total
Number of scenes: {num_scenes}
Suggested duration per scene: {avg_duration} seconds (adjust between 3-7 seconds as needed)

Template to fill:
```json
{json.dumps(template_structure, indent=2)}
```

Remember:
- Be SPECIFIC (not generic)
- Character/product details must be IDENTICAL across all scenes
- Replace EVERY "__FILL__" - no placeholders should remain
- Return valid JSON"""
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Template Filler] Filling {template_id} template, attempt {attempt}/{max_retries}")
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=8000,  # Large token budget for detailed fills
                )
                
                if not response.choices or not response.choices[0].message:
                    error_msg = "Empty response from OpenAI API"
                    logger.error(f"[Template Filler Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                content = response.choices[0].message.content
                if not content:
                    error_msg = "Response content is None"
                    logger.error(f"[Template Filler Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Parse JSON
                try:
                    filled_template = json.loads(content)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON: {e}. Content preview: {content[:500]}"
                    logger.warning(f"[Template Filler Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Validate: Check if any __FILL__ remain
                template_str = json.dumps(filled_template)
                remaining_fills = template_str.count("__FILL__")
                
                if remaining_fills > 0:
                    logger.warning(f"[Template Filler] Found {remaining_fills} unfilled placeholders")
                    if attempt < max_retries:
                        logger.info(f"[Template Filler] Retrying to fill remaining placeholders...")
                        last_error = f"{remaining_fills} unfilled placeholders remain"
                        continue
                    else:
                        logger.warning(f"[Template Filler] Proceeding with {remaining_fills} unfilled placeholders after {max_retries} attempts")
                
                logger.info(f"✅ Template filled successfully")
                logger.info(f"   Template: {template_id}")
                logger.info(f"   Story: {filled_template.get('story', {}).get('title', 'N/A')}")
                
                # Add metadata
                filled_template["_metadata"] = {
                    "template_id": template_id,
                    "template_name": template["template_name"],
                    "user_prompt": user_prompt,
                    "target_duration": target_duration,
                    "model_used": model,
                    "unfilled_placeholders": remaining_fills
                }
                
                return filled_template
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Template Filler Error] Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 15))
                    continue
        
        raise RuntimeError(f"Template filling failed after {max_retries} attempts: {last_error}")
    
    finally:
        await async_client.close()


def validate_filled_template(filled_template: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate that template is completely filled and follows rules.
    
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for remaining __FILL__ placeholders
    template_str = json.dumps(filled_template)
    if "__FILL__" in template_str:
        count = template_str.count("__FILL__")
        errors.append(f"{count} unfilled placeholders remain")
    
    # Validate character fields if present
    if filled_template.get("character", {}).get("present") == "true":
        char = filled_template["character"]
        
        # Check age is numeric
        age = char.get("demographics", {}).get("age_exact", "")
        if age and not age.isdigit():
            errors.append(f"age_exact must be numeric, got: {age}")
        
        # Check Fitzpatrick type format
        fitz = char.get("skin", {}).get("fitzpatrick_type", "")
        if fitz and not fitz.startswith("Type "):
            errors.append(f"fitzpatrick_type must be 'Type I-VI', got: {fitz}")
        
        # Check boolean fields
        if char.get("present") not in ["true", "false"]:
            errors.append(f"character.present must be 'true' or 'false', got: {char.get('present')}")
    
    # Validate product fields if present
    if filled_template.get("product", {}).get("present") == "true":
        prod = filled_template["product"]
        
        # Check dimensions are numeric
        dims = prod.get("dimensions", {})
        for dim_field in ["height_inches", "width_inches", "depth_inches"]:
            val = dims.get(dim_field, "")
            if val and not val.replace(".", "").isdigit():
                errors.append(f"product.dimensions.{dim_field} must be numeric, got: {val}")
    
    # Validate scene durations
    scenes = filled_template.get("scenes", [])
    for scene in scenes:
        duration = scene.get("duration_seconds", "")
        if duration:
            try:
                dur_num = int(duration)
                if dur_num < 3 or dur_num > 7:
                    errors.append(f"Scene {scene.get('scene_number')} duration must be 3-7 seconds, got: {dur_num}")
            except ValueError:
                errors.append(f"Scene {scene.get('scene_number')} duration must be numeric, got: {duration}")
    
    is_valid = len(errors) == 0
    return is_valid, errors

