"""
Scene Divider (Stage 2)
Divides the complete story into specific scenes with timing and details.
"""

import json
import logging
from typing import Dict, Any

import openai

from app.core.config import settings
from app.services.pipeline.story_templates import get_template

logger = logging.getLogger(__name__)


def get_scene_divider_prompt(template: Dict[str, Any], story: Dict[str, Any], target_duration: int) -> str:
    """Generate system prompt for scene division."""
    
    template_name = template["name"]
    beats = template["structure"]["beats"]
    
    beats_desc = "\n".join([
        f"{i+1}. **{beat['name']}** ({beat['duration_range'][0]}-{beat['duration_range'][1]}s)\n"
        f"   - Goal: {beat['goal']}\n"
        f"   - Visual Style: {beat['visual_style']}"
        for i, beat in enumerate(beats)
    ])
    
    story_narrative = story.get("narrative", {})
    character_subject = story.get("character_subject", {})
    emotional_arc = story.get("emotional_arc", [])
    voiceover = story.get("voice_over_script", {})
    production = story.get("production_notes", {})
    
    return f"""You are an expert film director and video editor. Your job is to take a complete story and divide it into specific scenes with precise timing and detailed descriptions.

TEMPLATE STRUCTURE: {template_name}
{beats_desc}

TARGET TOTAL DURATION: {target_duration} seconds

STORY CONTEXT:
Logline: {story_narrative.get('logline', 'N/A')}
Setup: {story_narrative.get('setup', 'N/A')}
Development: {story_narrative.get('development', 'N/A')}
Climax: {story_narrative.get('climax', 'N/A')}
Resolution: {story_narrative.get('resolution', 'N/A')}

CHARACTER/SUBJECT:
Type: {character_subject.get('type', 'unknown')}
Character Description: {character_subject.get('character_description', 'N/A')}
Product Description: {character_subject.get('product_description', 'N/A')}

EMOTIONAL ARC:
{json.dumps(emotional_arc, indent=2)}

VOICE-OVER SCRIPT:
{json.dumps(voiceover.get('lines', []), indent=2)}

PRODUCTION STYLE:
Style: {production.get('overall_style', 'N/A')}
Colors: {production.get('color_palette', 'N/A')}
Lighting: {production.get('lighting_approach', 'N/A')}
Pacing: {production.get('pacing', 'N/A')}

Your task is to divide this story into {len(beats)} specific scenes, each corresponding to one story beat. For each scene, you must provide:

1. **Scene Number** and **Story Beat** - Which beat this scene represents
2. **Duration** - Exact duration in seconds (MUST be between 3-7 seconds, total should equal {target_duration}s)
3. **Action Description** - What specifically happens in this scene (detailed, specific actions)
4. **Character/Subject Presence** - Is the main character/product visible? Throughout or partial?
5. **Camera Work** - Specific camera angles, movements, framing
6. **Composition** - How the frame is composed (rule of thirds, symmetry, depth, etc.)
7. **Lighting** - Specific lighting setup for this scene
8. **Emotional Tone** - Primary emotion being conveyed
9. **Visual Transitions** - How this scene connects to the next (if applicable)
10. **Voice-Over Timing** - Which voice-over line(s) play during this scene
11. **Key Props/Elements** - Important visual elements that must be present

CRITICAL RULES:

1. **Duration Constraints**:
   - Each scene MUST be between 3-7 seconds (MINIMUM 3, MAXIMUM 7)
   - Total duration of all scenes must equal approximately {target_duration} seconds
   - Distribute duration according to template beat ranges

2. **Subject Consistency**:
   - IF there's a character: They must be IDENTICAL in every scene they appear
   - Use the EXACT character description from the story
   - IF there's a product: It must be IDENTICAL in every scene it appears
   - Use the EXACT product description from the story

3. **Scene Flow**:
   - Each scene must flow naturally into the next
   - Consider visual transitions and continuity
   - Match emotional progression from the story

4. **Specificity**:
   - Be extremely specific about actions, not generic
   - Instead of "woman drinks coffee", say "woman brings white ceramic mug to lips, eyes close as she takes first sip, subtle smile forms"
   - Instead of "product shown", say "perfume bottle centered on marble surface, camera slowly orbits clockwise, morning light creates soft shadows"

Return your scene breakdown in this JSON format:

{{
  "total_duration": {target_duration},
  "number_of_scenes": {len(beats)},
  "template_beats_used": {json.dumps([beat['name'] for beat in beats])},
  
  "scenes": [
    {{
      "scene_number": 1,
      "story_beat": "Beat name from template",
      "duration_seconds": 4,  // MUST be 3-7
      
      "action_description": "Extremely detailed description of what happens. Be specific about every action, movement, gesture. Describe it like you're briefing a cinematographer who needs to capture this exactly.",
      
      "character_subject_presence": {{
        "character_visible": true/false,
        "character_presence_timing": "full_scene" | "enters_at_Xs" | "exits_at_Xs" | "partial",
        "product_visible": true/false,
        "product_presence_timing": "full_scene" | "appears_at_Xs" | "disappears_at_Xs" | "partial"
      }},
      
      "camera_work": {{
        "angle": "Specific angle (e.g., 'eye-level', 'low angle looking up', 'overhead bird's eye', 'dutch tilt')",
        "movement": "Camera movement (e.g., 'static', 'slow dolly in', 'handheld walk with subject', 'slow orbit clockwise')",
        "framing": "Shot size (e.g., 'close-up on face', 'medium shot waist up', 'wide establishing shot', 'extreme close-up on hands')",
        "lens_note": "Any lens characteristics (e.g., 'shallow depth of field', 'wide angle distortion', 'telephoto compression')"
      }},
      
      "composition": {{
        "layout": "How frame is composed (e.g., 'rule of thirds - subject right, negative space left', 'centered symmetrical', 'diagonal leading lines')",
        "depth": "Depth strategy (e.g., 'foreground product sharp, background soft bokeh', 'deep focus throughout', 'layered depth')",
        "visual_balance": "Balance and weight (e.g., 'heavy bottom light top', 'balanced left-right', 'asymmetrical tension')"
      }},
      
      "lighting": {{
        "setup": "Detailed lighting description (e.g., 'soft window light from left, white bounce right, backlight for rim', 'overhead practical pendant, ambient fill')",
        "mood": "Lighting mood (e.g., 'soft and intimate', 'dramatic high contrast', 'bright and airy')",
        "color_temperature": "Light color (e.g., 'warm 3200K', 'neutral 5600K', 'cool blue 7000K', 'mixed warm practicals cool ambience')"
      }},
      
      "emotional_tone": "Primary emotion this scene conveys (from emotional arc)",
      "emotional_intensity": "low" | "medium" | "high",
      
      "visual_transition": {{
        "from_previous": "How this scene connects FROM previous scene (N/A for scene 1)",
        "to_next": "How this scene transitions TO next scene (N/A for last scene)",
        "transition_type": "cut" | "dissolve" | "fade" | "match_cut" | "other"
      }},
      
      "voice_over": {{
        "has_voiceover": true/false,
        "text": "Voice-over text if applicable",
        "timing": "When VO starts/stops within scene"
      }},
      
      "key_props_elements": [
        "List of important visual elements that must be present in this scene"
      ],
      
      "special_notes": "Any other important details for this scene"
    }},
    // ... repeat for all scenes
  ],
  
  "continuity_notes": {{
    "character_consistency": "Reminder of how character must remain identical across all scenes they appear",
    "product_consistency": "Reminder of how product must remain identical across all scenes it appears",
    "visual_consistency": "Overall visual consistency requirements",
    "style_consistency": "Style and tone consistency reminders"
  }}
}}

Remember:
- Be extremely specific and detailed for each scene
- Each scene duration must be 3-7 seconds
- Total must equal {target_duration} seconds
- Follow the template beat structure
- Maintain absolute character/product consistency
- Describe actions cinematically, not generically
"""


async def divide_into_scenes(
    story: Dict[str, Any],
    template_id: str,
    target_duration: int = 15,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Divide complete story into specific scenes with timing and details.
    
    Args:
        story: Complete story from story generator
        template_id: Template ID used for story
        target_duration: Target total duration in seconds
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Scene breakdown with detailed specifications
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Invalid template ID: {template_id}")
    
    model = "gpt-4o"  # Best model for detailed planning
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = get_scene_divider_prompt(template, story, target_duration)
    user_message = f"""Divide the provided story into {len(template['structure']['beats'])} specific, detailed scenes with precise timing.

Follow the {template['name']} template structure. Be extremely specific about actions, camera work, and visual details. Remember that the character/product must remain IDENTICAL across all scenes where they appear.

Total duration must be approximately {target_duration} seconds, with each scene between 3-7 seconds."""
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Scene Divider] Dividing story into scenes, attempt {attempt}/{max_retries}")
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=5000,
                )
                
                if not response.choices or not response.choices[0].message:
                    error_msg = "Empty response from OpenAI API"
                    logger.error(f"[Scene Divider Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                content = response.choices[0].message.content
                if not content:
                    error_msg = "Response content is None"
                    logger.error(f"[Scene Divider Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Parse JSON
                try:
                    scenes_data = json.loads(content)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON: {e}. Content preview: {content[:500]}"
                    logger.warning(f"[Scene Divider Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Validate structure
                scenes = scenes_data.get("scenes", [])
                if len(scenes) < 1:
                    error_msg = f"Expected at least 1 scene, got {len(scenes)}"
                    logger.warning(f"[Scene Divider Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Validate scene durations
                total_duration = 0
                for scene in scenes:
                    duration = scene.get("duration_seconds", 4)
                    if duration < 3 or duration > 7:
                        error_msg = f"Scene {scene.get('scene_number')} has invalid duration {duration}s (must be 3-7s)"
                        logger.warning(f"[Scene Divider Error] {error_msg}")
                        if attempt < max_retries:
                            last_error = error_msg
                            continue
                        raise ValueError(error_msg)
                    total_duration += duration
                
                logger.info(f"✅ Story divided into {len(scenes)} scenes")
                logger.info(f"   Total duration: {total_duration}s (target: {target_duration}s)")
                
                # Add metadata
                scenes_data["generation_metadata"] = {
                    "template_id": template_id,
                    "template_name": template["name"],
                    "model_used": model,
                    "target_duration": target_duration,
                    "actual_duration": total_duration,
                    "story_title": story.get("story_title", "Untitled")
                }
                
                return scenes_data
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Scene Divider Error] Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 15))
                    continue
        
        raise RuntimeError(f"Scene division failed after {max_retries} attempts: {last_error}")
    
    finally:
        await async_client.close()

