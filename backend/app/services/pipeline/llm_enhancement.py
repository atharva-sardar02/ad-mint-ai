"""
LLM enhancement service for processing user prompts into structured ad specifications.
"""
import asyncio
import json
import logging
from typing import Optional

import openai
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.generation import (
    AdSpecification,
    AdSpec,
    BrandGuidelines,
    Scene,
    TextOverlay,
)

logger = logging.getLogger(__name__)

# Retry configuration for rate limits
INITIAL_RETRY_DELAY = 2  # seconds
MAX_RETRY_DELAY = 60  # seconds

# System prompt for LLM enhancement - Sora-optimized
SYSTEM_PROMPT = """ 
SYSTEM: SORA AIDA BLUEPRINT GENERATOR v3.0
ROLE: 
You expand a short user prompt (1–3 sentences) into a valid JSON blueprint 
for a 4-scene AIDA advertisement.

OUTPUT RULES:
• Output ONLY valid JSON.
• No commentary, no sentences outside JSON.
• EXACTLY 4 scenes.
• Each scene MUST be exactly 4 seconds.
• total_duration_seconds MUST equal 16.

REFERENCE IMAGE:
• Output literal string "{{REFERENCE_IMAGE_PATH}}".
• You NEVER see the image. 
• Do NOT describe or infer product appearance.
• Only describe how the product is *used*, not how it looks.

SCENE DESCRIPTION FORMAT (STRICT):
Each field MUST be a 3–7 word fragment (no sentences):
  "visual":        3–7 words
  "action":        1 action verb phrase
  "camera":        simple motion ("static", "glide", "push-in")
  "lighting":      1 phrase ("soft daylight", "warm indoor")
  "mood":          1 emotional word
  "product_usage": 1 behavioral phrase (no appearance)

VOICEOVER:
• 1–2 short sentences.
• AIDA emotional beats:
    Scene 1: curiosity
    Scene 2: clarity
    Scene 3: aspiration
    Scene 4: urgency

OVERLAY TEXT:
• 1–6 punchy words.

SOUND DESIGN:
• 3–6 word ambient fragment only.
• Allowed: “quiet office hum”, “city street murmur”.
• Not allowed: whooshes, impacts, music, transitions.

MUSIC (POST-PRODUCTION):
style: short phrase
energy: low | medium | high
notes: short emotional purpose

JSON SCHEMA:
{
  "ad_framework": "AIDA",
  "total_duration_seconds": 16,

  "reference_image_path": "{{REFERENCE_IMAGE_PATH}}",
  "reference_image_usage": "string",
  "style_tone": "string",

  "scenes": [
    {
      "scene_number": 1,
      "aida_stage": "Attention",
      "duration_seconds": 4,
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
"""


def _build_sora_scene_prompt(
    scene_description: dict,
    sound_design: Optional[str],
    fallback_prompt: str,
) -> str:
    """
    Build a compact Sora-optimized scene prompt.
    Fields are 3–7 word fragments.
    No punctuation, no sentences, no labels.
    Just newline-separated fragments.
    """

    if not scene_description:
        return fallback_prompt

    lines: list[str] = []

    order = ["visual", "action", "camera", "lighting", "mood", "product_usage"]

    for key in order:
        value = scene_description.get(key)
        if value:
            fragment = str(value).strip()
            # No punctuation allowed
            fragment = fragment.replace(".", "").replace(",", "")
            if fragment:
                lines.append(fragment)

    # Ambient sound fragment (3–6 words)
    if sound_design:
        sd = str(sound_design).strip()
        sd = sd.replace(".", "").replace(",", "")
        if sd:
            lines.append(f"Ambient sound: {sd}")

    # If nothing valid, fallback to entire user prompt
    if not lines:
        return fallback_prompt

    # Join fragments line-by-line for Sora
    return "\n".join(lines)

def _convert_sora_blueprint_to_ad_spec(blueprint: dict, user_prompt: str) -> AdSpecification:
    """
    Convert a Sora-3.0 AIDA compact-fragment blueprint into
    the internal AdSpecification format.
    """

    scenes_data = blueprint.get("scenes", []) or []
    style_tone = blueprint.get("style_tone") or "cinematic, modern"
    ad_framework = blueprint.get("ad_framework") or "AIDA"

    scenes: list[Scene] = []

    for idx, scene_data in enumerate(scenes_data, start=1):

        desc = scene_data.get("scene_description") or {}
        sound_design = scene_data.get("sound_design")

        # Build compact Sora-friendly text block
        visual_prompt = _build_sora_scene_prompt(
            scene_description=desc,
            sound_design=sound_design,
            fallback_prompt=user_prompt,
        )

        # Overlay text extraction (1–6 words)
        overlay_text_value = scene_data.get("overlay_text") or ""
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
                text_overlay=text_overlay,
                duration=int(scene_data.get("duration_seconds") or 4),
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


async def enhance_prompt_with_llm(
    user_prompt: str,
    max_retries: int = 3,
    image_path: Optional[str] = None,
) -> AdSpecification:
    """
    Generate a Sora-3.0 AIDA blueprint using GPT-4-Turbo (compact fragment style),
    then convert it into AdSpecification for the video pipeline.
    """

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")

    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    # ----------- Build user content (non-visual reference image metadata) ------------
    if image_path:
        user_content = (
            "REFERENCE IMAGE CONTEXT:\n"
            "- A reference image will be provided directly to Sora.\n"
            "- You NEVER see the image.\n"
            "- Do NOT describe its appearance.\n"
            "- Only describe how the product is USED, not how it looks.\n\n"
            + user_prompt
        )
    else:
        user_content = user_prompt

    # -------------------------- Retry Loop -----------------------------------------
    last_error = None
    current_prompt = user_content

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[LLM] Attempt {attempt}/{max_retries}")

            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": current_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=1600,
            )

            content = response.choices[0].message.content
            logger.info("[LLM RAW JSON OUTPUT]")
            logger.info(content)

            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON: {e}")
                if attempt < max_retries:
                    current_prompt = (
                        user_content
                        + "\n\nYour previous output was INVALID JSON. Output ONLY valid JSON."
                    )
                    continue
                raise

            # Validate scene count
            scenes = data.get("scenes", [])
            if len(scenes) != 4:
                logger.warning(f"Expected 4 scenes, got {len(scenes)}")
                if attempt < max_retries:
                    current_prompt = (
                        user_content
                        + "\n\nERROR: You must output EXACTLY 4 scenes."
                    )
                    continue
                raise ValueError("LLM did not output exactly 4 scenes.")

            # Validate scene durations
            bad = [s for s in scenes if s.get("duration_seconds") != 4]
            if bad:
                if attempt < max_retries:
                    current_prompt = (
                        user_content
                        + "\n\nERROR: Each scene MUST have exactly 4 seconds."
                    )
                    continue
                raise ValueError("Incorrect scene durations.")

            # Convert blueprint → AdSpecification
            return _convert_sora_blueprint_to_ad_spec(data, user_prompt)

        except Exception as e:
            last_error = e
            logger.warning(f"LLM error: {e}")
            await asyncio.sleep(min(2 ** attempt, 20))
            continue

    raise RuntimeError(f"LLM failed after {max_retries} attempts: {last_error}")

