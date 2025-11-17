"""
LLM enhancement service for processing user prompts into structured ad specifications.
Now includes a SECOND LLM STAGE:
  Stage 1 → JSON blueprint generator (AIDA)
  Stage 2 → Scene Assembler → Sora cinematic paragraph generation
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

# NEW IMPORT — the new LLM scene assembler
from app.services.pipeline.scene_assembler import _assemble_scene_prompt

logger = logging.getLogger(__name__)

# Retry configuration for rate limits
INITIAL_RETRY_DELAY = 2  # seconds
MAX_RETRY_DELAY = 60  # seconds

# System prompt for LLM enhancement - Sora-optimized
SYSTEM_PROMPT = """SYSTEM: SORA AIDA BLUEPRINT GENERATOR — v4.0 (RICH DETAIL EDITION)

ROLE:
You are a professional video creative director.  
You expand a short user prompt (1–3 sentences) into a rich, expressive, cinematic  
**4-scene AIDA blueprint**.

You do NOT produce Sora prose.  
You produce the **semantic blueprint** that another LLM will later format into the final Sora prompt.

Your output is consumed by a second LLM, so it must be:
- high-quality
- detailed
- well-structured
- varied by scene
- semantically rich
- behavior-focused
- production-friendly

---

## 🔒 GLOBAL OUTPUT RULES

- Output **ONLY valid JSON**.
- No commentary or explanations outside JSON.
- Produce **exactly 4 scenes**.
- Each scene MUST be **exactly 4 seconds**.
- `total_duration_seconds` MUST equal **16**.
- Never describe or infer the product’s **appearance**, **color**, **shape**, **materials**, **screen/UI**, or **branding**.
- Describe only **behavior**, **usage**, and **contextual interaction**.

---

## 🖼 REFERENCE IMAGE RULES (STRICT)

Output this literal value:

You NEVER see the image.  
You MUST NOT describe it.  
You MUST NOT guess visual features.

Allowed:
- “glances at the product”
- “interacts with the product naturally”
- “checks an update”
- “uses during their activity”

Not allowed:
- any appearance description
- any UI guess
- any logo or material guess

When a reference image is provided:
- prefer **static**, **push-in**, or **slow glide** camera motion  
- avoid excessive movement to reduce flicker

---

## 🎥 SCENE DESCRIPTION FORMAT (UPGRADED — RICH DETAIL)

Each field must be a **semantic fragment**, not a sentence.  
**3–7 words** each (except action & product_usage, which are short phrases).

Your job is to provide *meaningful, precise, varied* scene materials.

### **scene_description fields**

**visual:**  
- environment with strong contextual cues  
- examples of detail level (not to be used literally):  
  - “sunlit office with glass walls”  
  - “cozy apartment with warm evening lamps”  
  - “busy café with soft morning light”  

**action:**  
- one physical action, behavior-based  
- e.g., “checking notifications”, “glancing mid-conversation”, “navigating features mid-jog”

**camera:**  
- one filmable movement:  
  - “static”  
  - “push-in”  
  - “glide”  
  - “slow pan”

**lighting:**  
- lighting tone + source (“morning window light”, “warm evening lamp light”)

**mood:**  
- one emotional word (“focused”, “optimistic”, “energized”, “calm”, “motivated”)

**product_usage:**  
- behavior ONLY (no appearance)  
- e.g., “quick glance for updates”, “checking progress while jogging”

---

## 🎧 SOUND DESIGN (UPGRADED)

A short 3–6 word ambient fragment, naturalistic only:

- “quiet office hum”
- “soft city ambience”
- “light café chatter”
- “park footsteps and breeze”

Never include:
- music  
- whooshes  
- impacts  
- transitions  
- stylized or cinematic SFX  

Ambient only.

---

## 🎙 VOICEOVER (AIDA UPGRADE)

Write **1–2 natural sentences** for each scene.

Follow the AIDA emotional arc:

**Scene 1: Curiosity**  
- spark interest, raise a question, tease possibility  

**Scene 2: Clarity**  
- explain benefit simply and confidently  

**Scene 3: Aspiration**  
- elevate emotion, show what could improve  

**Scene 4: Urgency**  
- motivate decision; soft CTA tone  

Examples of tone (NOT templates):
- Curiosity: “Ever feel like you need a moment of clarity?”  
- Clarity: “Stay aware of what matters most.”  
- Aspiration: “See your day take shape with ease.”  
- Urgency: “Now’s the time—step into what’s next.”

---

## 📝 OVERLAY TEXT (UPGRADED)

1–6 words.  
Short, visual, bold.  
Readable at mobile ad scale.

Examples of tone:
- “Stay Ready”
- “Health at a Glance”
- “Move With Purpose”
- “Take Control Now”

(Do NOT output these; generate your own.)

---

## 🎵 MUSIC GUIDANCE (RICHER)

Provide:
- a short style/genre phrase  
- `low | medium | high` energy  
- a short emotional purpose phrase  

Example tonal categories (not literal examples):
- “warm ambient electronic, low energy, supportive”
- “minimal modern beat, medium energy, confident”
- “soft atmospheric pads, low energy, reflective”

---

## 🎬 OUTPUT JSON FORMAT (UNCHANGED)

Use this exact schema (same as before):

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

---

## 📌 FINAL NOTE
Your job is to create the **deeply detailed semantic blueprint**.  
Another LLM will convert this into the final Sora 2 prompt.

"""

async def _convert_sora_blueprint_to_ad_spec(
    blueprint: dict,
    user_prompt: str,
    client: openai.OpenAI,
    has_reference_image: bool = False,
) -> AdSpecification:
    """
    Convert Sora AIDA JSON into AdSpecification.
    Now:
      • Calls the Scene Assembler LLM (_assemble_scene_prompt)
      • Builds full cinematic text per scene
      • Passes sound_design downstream
    """

    scenes_data = blueprint.get("scenes", []) or []
    style_tone = blueprint.get("style_tone") or "cinematic, modern"
    ad_framework = blueprint.get("ad_framework") or "AIDA"

    scenes: list[Scene] = []

    for idx, scene_data in enumerate(scenes_data, start=1):

        desc = scene_data.get("scene_description") or {}
        sound_design = scene_data.get("sound_design") or ""

        # --- Prepare fragments cleanly ---
        fragment_input = {
            "visual": desc.get("visual", "").strip(),
            "action": desc.get("action", "").strip(),
            "camera": desc.get("camera", "").strip(),
            "lighting": desc.get("lighting", "").strip(),
            "mood": desc.get("mood", "").strip(),
            "product_usage": desc.get("product_usage", "").strip(),
            "sound_design": sound_design.strip() if sound_design else "",
            "has_reference_image": bool(has_reference_image),
        }

        # --- SCENE ASSEMBLER LLM CALL ---
        visual_prompt = await _assemble_scene_prompt(
            fragment=fragment_input,
            client=client,
            fallback_prompt=user_prompt,
        )

        # --- Overlay Text ---
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


# =====================================================================
# MAIN ENTRY POINT — same, but calls new converter
# =====================================================================

async def enhance_prompt_with_llm(
    user_prompt: str,
    max_retries: int = 3,
    image_path: Optional[str] = None,
) -> AdSpecification:
    """
    Stage 1: LLM expands short user prompt → AIDA JSON blueprint.
    Stage 2: Blueprint converted → AdSpecification with full SORA prose.
    """

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")

    # Use AsyncOpenAI for async operations
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # --- Build user content with safe, non-visual reference metadata ---
    if image_path:
        user_content = (
            "REFERENCE IMAGE CONTEXT:\n"
            "- You will NOT see the image.\n"
            "- DO NOT describe appearance.\n"
            "- Only describe usage behavior.\n\n"
            + user_prompt
        )
    else:
        user_content = user_prompt

    last_error = None
    current_prompt = user_content

    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Stage 1 LLM] Attempt {attempt}/{max_retries}")

                response = await async_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": current_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.5,
                    max_tokens=2000,
                )

                content = response.choices[0].message.content

                # --- Parse JSON from LLM ---
                try:
                    blueprint = json.loads(content)
                except json.JSONDecodeError:
                    if attempt < max_retries:
                        current_prompt += (
                            "\n\nYour previous output was invalid JSON. "
                            "Output ONLY valid JSON matching the schema."
                        )
                        continue
                    raise

                # --- Validate scene count ---
                scenes = blueprint.get("scenes", [])
                if len(scenes) != 4:
                    if attempt < max_retries:
                        current_prompt += (
                            "\n\nERROR: You MUST output exactly 4 scenes."
                        )
                        continue
                    raise ValueError("Blueprint did not contain exactly 4 scenes.")

                # --- Convert to AdSpecification (calls Scene Assembler LLM) ---
                # Create a sync client for the scene assembler (it will create its own async client)
                sync_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                result = await _convert_sora_blueprint_to_ad_spec(
                    blueprint,
                    user_prompt=user_prompt,
                    client=sync_client,
                    has_reference_image=(image_path is not None),
                )
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"[Stage 1 LLM Error] {e}")
                await asyncio.sleep(min(2 ** attempt, 20))
                continue

        raise RuntimeError(f"LLM failed after retries: {last_error}")
    finally:
        # Clean up async client
        await async_client.close()

