"""
Storyboard generator using OpenAI Vision API.
Creates a storyboard from user prompt + reference images.
"""
import base64
import json
import logging
from pathlib import Path
from typing import List, Optional

import openai
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.generation import AdSpecification, AdSpec, BrandGuidelines, Scene, TextOverlay

logger = logging.getLogger(__name__)

# System prompt for storyboard generation with vision
STORYBOARD_SYSTEM_PROMPT = """SYSTEM: STORYBOARD GENERATOR — v1.0 (VISION-ENABLED)

ROLE:
You are a professional video creative director and storyboard artist.
You analyze user prompts and reference images to create a detailed storyboard
for a 4-scene AIDA video advertisement.

You CAN see and analyze reference images provided by the user.
Use the visual information from images to inform your storyboard creation.

---

## 🔒 GLOBAL OUTPUT RULES

- Output **ONLY valid JSON**.
- No commentary or explanations outside JSON.
- Produce **exactly 4 scenes**.
- Each scene MUST be **exactly 4 seconds**.
- `total_duration_seconds` MUST equal **16**.

---

## 🖼 REFERENCE IMAGE ANALYSIS

When reference images are provided:
- Analyze the visual style, colors, composition, and key elements
- Note the product appearance, branding, and visual characteristics
- Use this information to create consistent scenes that match the reference
- Assign reference images to appropriate scenes (can reuse same image or use different ones)
- Describe scenes that align with the visual style of the reference images

---

## 🎥 SCENE DESCRIPTION FORMAT

Each scene should include:

**visual:**  
- Detailed environment description matching reference image style
- Specific visual elements, composition, and framing

**action:**  
- Clear physical action or behavior
- Product interaction if applicable

**camera:**  
- One of: "static", "push-in", "glide", "slow pan", "dolly", "tilt"

**lighting:**  
- Lighting description matching reference image style
- Time of day, light source, mood

**mood:**  
- Emotional tone: "focused", "optimistic", "energized", "calm", "motivated", etc.

**product_usage:**  
- How the product is used or featured in this scene
- Can reference visual elements from the reference image

---

## 🎙 VOICEOVER (AIDA)

Follow the AIDA emotional arc:

**Scene 1: Attention**  
- Hook the viewer, create curiosity

**Scene 2: Interest**  
- Explain benefit, build engagement

**Scene 3: Desire**  
- Elevate emotion, show aspiration

**Scene 4: Action**  
- Motivate decision, soft CTA

---

## 📝 OVERLAY TEXT

1–6 words. Short, visual, bold. Readable at mobile ad scale.

---

## 🎧 SOUND DESIGN

3–6 word ambient fragment, naturalistic only:
- "quiet office hum"
- "soft city ambience"
- "light café chatter"
- "park footsteps and breeze"

---

## 🎬 OUTPUT JSON FORMAT

{
  "ad_framework": "AIDA",
  "total_duration_seconds": 16,
  "reference_images": [
    {
      "scene_number": 1,
      "image_path": "path/to/image1.jpg",
      "description": "Brief description of how this image relates to the scene"
    },
    {
      "scene_number": 2,
      "image_path": "path/to/image2.jpg",
      "description": "Brief description"
    }
  ],
  "style_tone": "string",
  "scenes": [
    {
      "scene_number": 1,
      "aida_stage": "Attention",
      "duration_seconds": 4,
      "reference_image_path": "path/to/image1.jpg",
      "scene_description": {
        "visual": "string",
        "action": "string",
        "camera": "string",
        "lighting": "string",
        "mood": "string",
        "product_usage": "string"
      },
      "voiceover": "string",
      "overlay_text": "string",
      "sound_design": "string"
    },
    {
      "scene_number": 2,
      "aida_stage": "Interest",
      "duration_seconds": 4,
      "reference_image_path": "path/to/image2.jpg",
      "scene_description": {
        "visual": "string",
        "action": "string",
        "camera": "string",
        "lighting": "string",
        "mood": "string",
        "product_usage": "string"
      },
      "voiceover": "string",
      "overlay_text": "string",
      "sound_design": "string"
    },
    {
      "scene_number": 3,
      "aida_stage": "Desire",
      "duration_seconds": 4,
      "reference_image_path": "path/to/image3.jpg",
      "scene_description": {
        "visual": "string",
        "action": "string",
        "camera": "string",
        "lighting": "string",
        "mood": "string",
        "product_usage": "string"
      },
      "voiceover": "string",
      "overlay_text": "string",
      "sound_design": "string"
    },
    {
      "scene_number": 4,
      "aida_stage": "Action",
      "duration_seconds": 4,
      "reference_image_path": "path/to/image4.jpg",
      "scene_description": {
        "visual": "string",
        "action": "string",
        "camera": "string",
        "lighting": "string",
        "mood": "string",
        "product_usage": "string"
      },
      "voiceover": "string",
      "overlay_text": "string",
      "sound_design": "string"
    }
  ],
  "music": {
    "style": "string",
    "energy": "string",
    "notes": "string"
  }
}

---

## 📌 FINAL NOTE

Create a storyboard that:
- Uses reference images effectively
- Maintains visual consistency
- Follows AIDA framework
- Provides rich detail for video generation
"""


def _encode_image(image_path: str) -> str:
    """Encode image to base64 for OpenAI Vision API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def _prepare_image_messages(
    user_prompt: str,
    reference_image_paths: List[str]
) -> List[dict]:
    """Prepare messages with images for OpenAI Vision API."""
    messages = []
    
    # Add text prompt
    content = [{"type": "text", "text": user_prompt}]
    
    # Add reference images
    for image_path in reference_image_paths:
        if Path(image_path).exists():
            base64_image = _encode_image(image_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"  # High detail for better analysis
                }
            })
            logger.info(f"Added reference image to vision API: {image_path}")
        else:
            logger.warning(f"Reference image not found: {image_path}")
    
    messages.append({
        "role": "user",
        "content": content
    })
    
    return messages


async def generate_storyboard(
    user_prompt: str,
    reference_image_paths: Optional[List[str]] = None,
    max_retries: int = 3,
) -> AdSpecification:
    """
    Generate storyboard using OpenAI Vision API.
    
    Args:
        user_prompt: User's text prompt
        reference_image_paths: List of reference image paths (can be reused across scenes)
        max_retries: Maximum retry attempts
    
    Returns:
        AdSpecification with storyboard scenes including reference images
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    # Use best available OpenAI model with vision
    # gpt-4o is best, fallback to gpt-4-turbo
    model = "gpt-4o"  # Best model with vision capabilities
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    reference_image_paths = reference_image_paths or []
    
    # Prepare messages with images
    messages = _prepare_image_messages(user_prompt, reference_image_paths)
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Storyboard Generator] Attempt {attempt}/{max_retries} using {model}")
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
                        *messages
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,  # Slightly higher for creative storyboard generation
                    max_tokens=4000,  # More tokens for detailed storyboard
                )
                
                content = response.choices[0].message.content
                
                # Parse JSON
                try:
                    storyboard = json.loads(content)
                except json.JSONDecodeError:
                    if attempt < max_retries:
                        logger.warning(f"Invalid JSON response, retrying...")
                        continue
                    raise
                
                # Validate scene count
                scenes = storyboard.get("scenes", [])
                if len(scenes) != 4:
                    if attempt < max_retries:
                        logger.warning(f"Expected 4 scenes, got {len(scenes)}, retrying...")
                        continue
                    raise ValueError(f"Storyboard must contain exactly 4 scenes, got {len(scenes)}")
                
                # Convert storyboard to AdSpecification
                return _convert_storyboard_to_ad_spec(storyboard, user_prompt)
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Storyboard Generator Error] {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 20))
                    continue
        
        raise RuntimeError(f"Storyboard generation failed after retries: {last_error}")
    
    finally:
        await async_client.close()


def _convert_storyboard_to_ad_spec(
    storyboard: dict,
    user_prompt: str,
) -> AdSpecification:
    """Convert storyboard JSON to AdSpecification."""
    scenes_data = storyboard.get("scenes", []) or []
    style_tone = storyboard.get("style_tone") or "cinematic, modern"
    ad_framework = storyboard.get("ad_framework") or "AIDA"
    
    scenes: List[Scene] = []
    
    for idx, scene_data in enumerate(scenes_data, start=1):
        desc = scene_data.get("scene_description") or {}
        sound_design = scene_data.get("sound_design") or ""
        reference_image_path = scene_data.get("reference_image_path")
        
        # Build base visual prompt from scene description
        visual_parts = [
            desc.get("visual", ""),
            desc.get("action", ""),
            desc.get("camera", ""),
            desc.get("lighting", ""),
            desc.get("mood", ""),
            desc.get("product_usage", ""),
        ]
        visual_prompt = ", ".join([p for p in visual_parts if p])
        
        # Overlay text
        overlay_text_value = (scene_data.get("overlay_text") or "").strip()
        text_overlay = TextOverlay(
            text=overlay_text_value,
            position="center",
            font_size=48,
            color="#FFFFFF",
            animation="fade_in",
        )
        
        scenes.append(
            Scene(
                scene_number=scene_data.get("scene_number") or idx,
                scene_type=scene_data.get("aida_stage") or "Scene",
                visual_prompt=visual_prompt,
                model_prompts={},  # Will be populated by model-specific generator
                reference_image_path=reference_image_path,
                text_overlay=text_overlay,
                duration=int(scene_data.get("duration_seconds") or 4),
                sound_design=sound_design,
            )
        )
    
    call_to_action = scenes[-1].text_overlay.text if scenes else ""
    
    return AdSpecification(
        product_description=user_prompt,
        brand_guidelines=BrandGuidelines(
            brand_name="Brand",
            brand_colors=["#FFFFFF"],
            visual_style_keywords=style_tone,
            mood=style_tone,
        ),
        ad_specifications=AdSpec(
            target_audience="general audience",
            call_to_action=call_to_action or "Learn more",
            tone=style_tone,
        ),
        framework=ad_framework,
        scenes=scenes,
    )

