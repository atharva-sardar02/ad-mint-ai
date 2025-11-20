"""
Story Generator (Stage 1)
Generates complete narrative story and script based on selected template.
"""

import json
import logging
from typing import Dict, Any

import openai

from app.core.config import settings
from app.services.pipeline.story_templates import get_template

logger = logging.getLogger(__name__)


def get_story_generator_prompt(template: Dict[str, Any], target_duration: int) -> str:
    """Generate system prompt for story generation based on template."""
    
    template_name = template["name"]
    template_description = template["description"]
    narrative_guidance = template["narrative_guidance"]
    emotional_tone = template["emotional_tone"]
    beats = template["structure"]["beats"]
    
    beats_desc = "\n".join([
        f"{i+1}. **{beat['name']}** ({beat['duration_range'][0]}-{beat['duration_range'][1]}s)\n"
        f"   - Goal: {beat['goal']}\n"
        f"   - Visual Style: {beat['visual_style']}"
        for i, beat in enumerate(beats)
    ])
    
    return f"""You are an award-winning creative director and advertising copywriter. Your job is to craft a compelling narrative story and script for a {target_duration}-second advertisement.

SELECTED TEMPLATE: {template_name}
{template_description}

TEMPLATE STRUCTURE:
{beats_desc}

NARRATIVE GUIDANCE:
{narrative_guidance}

EMOTIONAL TONE: {emotional_tone}

Your task is to create a COMPLETE story with:
1. **Narrative Arc** - Full story with setup, development, and resolution
2. **Character/Subject Development** - If there's a character or product, develop them richly
3. **Emotional Beats** - Map emotions to each story beat
4. **Voice-Over Script** - Natural, compelling copy that enhances (not narrates) the visuals
5. **Key Visual Moments** - Describe the most important visual beats
6. **Brand Integration** - How the brand/product fits authentically into the story

CRITICAL REQUIREMENTS:

1. **Character Consistency** (if character is present):
   - Create ONE specific character with detailed identity
   - Describe them with "police description" level detail:
     * Exact age (e.g., "32 years old")
     * Height (e.g., "5 feet 6 inches")
     * Build (e.g., "medium build, approximately 130 pounds")
     * Hair: color, length, style, texture
     * Face: shape, features, eye color/shape
     * Skin tone: specific (use Fitzpatrick scale if relevant)
     * Distinguishing features: marks, scars, unique traits
     * Clothing: detailed description
   - This character must remain IDENTICAL throughout the story

2. **Product Consistency** (if product is present):
   - Describe product with EXTREME physical detail
   - Exact dimensions, colors, materials, textures, branding
   - This product must remain IDENTICAL throughout the story

3. **Story Cohesion**:
   - Story must flow naturally through all {len(beats)} beats
   - Each beat should transition smoothly to the next
   - Total duration should be approximately {target_duration} seconds

4. **Authenticity**:
   - Avoid clichés and generic descriptions
   - Create specific, memorable moments
   - Make it feel real and relatable

Return your story in this JSON format:

{{
  "template_used": "{template["template_id"]}",
  "story_title": "Catchy internal title for the story",
  "target_duration": {target_duration},
  
  "narrative": {{
    "logline": "One-sentence story summary (like a movie logline)",
    "setup": "Opening situation - establish world, character/product, context",
    "development": "Story progression - how situation develops through middle beats",
    "climax": "Peak moment - the key turning point or main message",
    "resolution": "Closing - how story concludes, final emotion/message"
  }},
  
  "character_subject": {{
    "type": "character" | "product" | "both" | "none",
    "character_description": "IF character present: DETAILED police-description level detail (age, height, build, hair, face, eyes, skin, features, expression, clothing). If no character, set to null.",
    "product_description": "IF product present: DETAILED physical description (dimensions, colors, materials, textures, branding, design). If no product, set to null.",
    "character_name": "Character's name (if applicable, can be generic like 'Sarah' or 'The Runner')",
    "character_backstory": "Brief backstory that informs their actions (2-3 sentences)",
    "character_goal": "What does the character want/need in this story?",
    "character_arc": "How does the character change from beginning to end?"
  }},
  
  "emotional_arc": [
    {{"beat": "Beat 1 name", "emotion": "Primary emotion in this beat", "intensity": "low/medium/high"}},
    {{"beat": "Beat 2 name", "emotion": "Primary emotion", "intensity": "low/medium/high"}},
    ...
  ],
  
  "voice_over_script": {{
    "style": "Describe voiceover style (e.g., 'warm conversational', 'bold declarative', 'soft introspective')",
    "lines": [
      {{
        "beat": "Beat 1 name",
        "text": "The actual voice-over text for this beat",
        "tone": "How it should be delivered (confident, gentle, excited, etc.)",
        "timing_note": "Any timing guidance (e.g., 'pause after first sentence', 'build energy')"
      }},
      ...
    ],
    "music_suggestion": "Type of music that would complement the story (e.g., 'uplifting piano', 'ambient electronic', 'warm acoustic guitar')"
  }},
  
  "key_visual_moments": [
    {{
      "beat": "Beat name",
      "moment_description": "Detailed description of this key visual moment",
      "why_important": "Why this moment matters to the story",
      "visual_style_note": "Any specific visual treatment (lighting, camera, composition)"
    }},
    ...
  ],
  
  "brand_integration": {{
    "brand_presence": "How brand/product appears in the story (subtle, prominent, hero)",
    "integration_approach": "How brand fits authentically (e.g., 'product solves character's problem', 'product is part of daily ritual')",
    "brand_message": "Core message about the brand this story conveys",
    "call_to_action": "Implicit or explicit call to action (e.g., 'try it yourself', 'join the community', 'discover more')"
  }},
  
  "production_notes": {{
    "overall_style": "Overall visual style for the ad (e.g., 'cinematic realism', 'vibrant stylized', 'intimate documentary')",
    "color_palette": "Suggested color palette (e.g., 'warm earth tones', 'cool blues and whites', 'vibrant primaries')",
    "lighting_approach": "Overall lighting strategy (e.g., 'natural soft morning light', 'dramatic studio lighting', 'golden hour warmth')",
    "pacing": "Overall pacing (e.g., 'slow and contemplative', 'energetic and dynamic', 'building momentum')",
    "special_notes": "Any other important creative direction"
  }}
}}

Remember:
- Be specific and detailed, especially with character/product descriptions
- Create a cohesive story that follows the template structure
- Make it memorable and emotionally resonant
- Ensure the story can realistically fit in {target_duration} seconds
- If there's a character, describe them forensically (police description level)
- If there's a product, describe it with extreme physical detail
- Follow the {template_name} template structure and emotional tone
"""


async def generate_story(
    user_prompt: str,
    template_id: str,
    target_duration: int = 15,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Generate complete narrative story based on user prompt and selected template.
    
    Args:
        user_prompt: User's advertisement prompt
        template_id: Selected template ID
        target_duration: Target total duration in seconds
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Complete story with narrative, script, and production notes
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    template = get_template(template_id)
    if not template:
        raise ValueError(f"Invalid template ID: {template_id}")
    
    model = "gpt-4o"  # Best model for creative writing
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = get_story_generator_prompt(template, target_duration)
    user_message = f"""Create a compelling {target_duration}-second advertisement story for this concept:

"{user_prompt}"

Follow the {template['name']} template structure. Be creative, specific, and emotionally engaging. Remember to provide forensic-level detail for any characters and extreme physical detail for any products."""
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Story Generator] Generating story with {template_id} template, attempt {attempt}/{max_retries}")
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.8,  # Higher temperature for creativity
                    max_tokens=4000,
                )
                
                if not response.choices or not response.choices[0].message:
                    error_msg = "Empty response from OpenAI API"
                    logger.error(f"[Story Generator Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                content = response.choices[0].message.content
                if not content:
                    error_msg = "Response content is None"
                    logger.error(f"[Story Generator Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Parse JSON
                try:
                    story = json.loads(content)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON: {e}. Content preview: {content[:500]}"
                    logger.warning(f"[Story Generator Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Validate structure
                required_fields = ["narrative", "character_subject", "emotional_arc", "voice_over_script"]
                missing_fields = [field for field in required_fields if field not in story]
                if missing_fields:
                    error_msg = f"Missing required fields: {missing_fields}"
                    logger.warning(f"[Story Generator Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                logger.info(f"✅ Story generated: \"{story.get('story_title', 'Untitled')}\"")
                logger.info(f"   Logline: {story.get('narrative', {}).get('logline', 'N/A')}")
                
                # Add metadata
                story["generation_metadata"] = {
                    "user_prompt": user_prompt,
                    "template_id": template_id,
                    "template_name": template["name"],
                    "model_used": model,
                    "target_duration": target_duration
                }
                
                return story
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Story Generator Error] Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 15))
                    continue
        
        raise RuntimeError(f"Story generation failed after {max_retries} attempts: {last_error}")
    
    finally:
        await async_client.close()

