"""
Option C: Full Cinematic TikTok-Style Perfume Pipeline

Single coherent file:

- Prompts

- Pydantic schemas

- LLM client wrapper

- Text converters

- Stage 1 / Stage 2 / Stage 3

- Orchestrator

"""

import json
import logging
import re
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError, field_validator

# --------------------------------------------------------------------------------------
# LLM CLIENT
# --------------------------------------------------------------------------------------

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured.")
        self.client = AsyncOpenAI(api_key=api_key)

    async def call_chat_model(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3,
        max_output_tokens: int = 1500,
        stream: bool = False,
    ) -> str:
        """
        Unified chat wrapper.

        - Uses chat.completions for GPT-4 and GPT-5 family.

        - For gpt-5, omits temperature and uses max_completion_tokens.

        - If gpt-5 returns empty content, retries once with gpt-4.

        """

        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty list.")

        for i, msg in enumerate(messages):
            if "role" not in msg or "content" not in msg:
                raise ValueError(f"Message #{i} missing 'role' or 'content'.")
            if msg["role"] not in ("system", "user", "assistant"):
                raise ValueError(f"Invalid role in message #{i}: {msg['role']}")
            if not isinstance(msg["content"], str):
                raise TypeError(f"Message #{i} content must be string.")

        MODELS_USE_COMPLETION_TOKENS = {"gpt-5", "gpt-5-turbo", "gpt-5o"}
        MODELS_TEMPERATURE_RESTRICTED = {"gpt-5", "gpt-5-turbo", "gpt-5o"}

        request_params: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if model not in MODELS_TEMPERATURE_RESTRICTED:
            request_params["temperature"] = temperature

        if model in MODELS_USE_COMPLETION_TOKENS:
            request_params["max_completion_tokens"] = max_output_tokens
        else:
            request_params["max_tokens"] = max_output_tokens

        async def _once(model_name: str) -> str:
            request_params["model"] = model_name
            import asyncio
            from openai import APIError, APIConnectionError, APITimeoutError
            
            try:
                resp = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        **request_params,
                        stream=False,
                    ),
                    timeout=120.0  # 2 minute timeout per API call
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"{model_name} API call timed out after 120 seconds")
            except APIConnectionError as e:
                logger.error(f"[LLM][{model_name}] Connection error: {e}")
                raise ConnectionError(f"Network error connecting to OpenAI API: {e}. Please check your internet connection and try again.")
            except APITimeoutError as e:
                logger.error(f"[LLM][{model_name}] Timeout error: {e}")
                raise TimeoutError(f"OpenAI API request timed out: {e}. Please try again.")
            except APIError as e:
                logger.error(f"[LLM][{model_name}] API error: {e}")
                raise ValueError(f"OpenAI API error: {e}. Please check your API key and account status.")
            except Exception as e:
                logger.error(f"[LLM][{model_name}] Unexpected error: {type(e).__name__}: {e}")
                raise
            
            if not resp.choices:
                raise ValueError(f"{model_name} returned no choices.")
            text = resp.choices[0].message.content
            if not text:
                raise ValueError(f"{model_name} returned empty content.")
            # usage may not always be present, so guard it
            usage = getattr(resp, "usage", None)
            if usage:
                logger.info(
                    f"[LLM][{model_name}] Tokens: prompt={getattr(usage, 'prompt_tokens', None)}, "
                    f"completion={getattr(usage, 'completion_tokens', None)}"
                )
            return text

        try:
            try:
                return await _once(model)
            except (ConnectionError, TimeoutError) as network_err:
                # Don't retry on network errors - raise immediately
                logger.error(f"[LLM][{model}] Network/timeout error: {network_err}")
                raise
            except ValueError as inner_err:
                # If gpt-5 failed, fallback to gpt-4 once
                if model in MODELS_USE_COMPLETION_TOKENS:
                    logger.warning(
                        f"[LLM][{model}] returned empty/invalid content, "
                        "retrying once with gpt-4..."
                    )
                    try:
                        return await _once("gpt-4")
                    except (ConnectionError, TimeoutError) as retry_err:
                        # Network error on retry - raise immediately
                        logger.error(f"[LLM][gpt-4] Network error on retry: {retry_err}")
                        raise
                raise inner_err
        except Exception as e:
            logger.exception(f"[LLM ERROR][{model}] {e}")
            raise


def parse_json_str(raw: str) -> Dict[str, Any]:
    """Strict JSON parser with helpful errors."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from model: {e}\nRaw:\n{raw}") from e


# --------------------------------------------------------------------------------------
# PROMPTS (Option C)
# --------------------------------------------------------------------------------------

STAGE1_BLUEPRINT_PROMPT = """SYSTEM: STAGE 1 — PERFUME BLUEPRINT GENERATOR (Option C — Cinematic, TikTok-Ready)

ROLE:

You expand a short user prompt (and optionally scent notes) into a
5-scene perfume ad blueprint for Sora/TikTok.

OUTPUT:

A JSON object with:

- 5 scenes

- each scene 3–4 seconds

- clearly cinematic, concrete, ad-like

Scene Framework:

1. "First Impression" – hook, first sight of bottle or wearer

2. "Evolving Aura" – scent expanding into the environment

3. "Wearer's World" – lifestyle / context shot

4. "Intimate Close" – close, emotional moment

5. "Final Signature" – iconic product or brand shot

------------------------------------------------------------
GENERAL RULES
------------------------------------------------------------

• You MAY use real environments (streets, cafes, rooftops, beaches, apartments).

• You MAY show characters, wardrobe, props, real lighting, lenses, color.

• You MAY use time-of-day, weather, ambiance.

• You MAY show the bottle in scenes 1 and 5 only.

• Scenes 2–4 should minimize bottle usage.

• Style: TikTok-ready, visually bold, emotionally legible.

• No explicit sexual content.

------------------------------------------------------------
SCENE FIELDS
------------------------------------------------------------

For EACH of the 5 scenes, you MUST return:

- scene_number: 1–5

- stage: one of:
    "First Impression", "Evolving Aura", "Wearer's World",
    "Intimate Close", "Final Signature"

- duration_seconds: 3 or 4

- scene_description:
    - visual   (5–12 words; environment + subject + composition)
    - action   (5–12 words; what the character or camera does)
    - camera   (static | handheld | slow dolly | slow pan | glide | push in)
    - lighting (5–12 words; time of day + lighting quality + color)
    - mood     (one or two words)
    - product_usage (3–8 words; how scent is felt or noticed)

- sound_design: 5–12 words (ambience + general sound energy)

- voiceover: "" (empty string)

- overlay_text: "" (empty string)

Bottle rules:

- Scene 1: MAY show bottle in hand, on surface, etc.

- Scenes 2–4: Focus on wearer & world, minimal bottle presence.

- Scene 5: MUST show bottle clearly in a striking composition.

------------------------------------------------------------
OUTPUT FORMAT
------------------------------------------------------------

Return ONLY valid JSON:

{
  "framework": "Perfume-5-Scene",
  "total_duration_seconds": 20,
  "reference_image_path": "{{REFERENCE_IMAGE_PATH}}",
  "reference_image_usage": "inspiration for mood and composition",
  "style_tone": "cinematic, TikTok-ready, emotionally vivid",
  "scenes": [...],
  "music": {
    "style": "",
    "energy": "",
    "notes": ""
  }
}
"""

STAGE2_SCENT_PROFILE_PROMPT = """SYSTEM: STAGE 2 — SCENT-TO-CINEMATIC PROFILE (Option C — Full Color, Full Environment)

ROLE:

You take:

• user_scent_notes  (top/heart/base notes in loose text)

• stage1_summary    (moods + lighting + style_tone from Stage 1)

You output a SCENT PROFILE that maps perfume notes into cinematic language:

- what kinds of light fit this scent

- what colors fit it

- how motion and atmosphere should feel

- what sound design & emotional register match

------------------------------------------------------------
NOTE RULES
------------------------------------------------------------

• top_notes, heart_notes, base_notes: arrays of ingredient names (e.g., "lemon", "bergamot", "neroli", "vetiver").

• If the user provided these explicitly, use them (normalized).

• You MAY infer missing heart/base notes, but keep them realistic (no vibes like "freshness", "energy").

• Do NOT use generic categories like "citrus" or "floral" as notes; use ingredients.

------------------------------------------------------------
CINEMATIC FIELDS
------------------------------------------------------------

Each MUST be a single descriptive sentence (10–24 words):

- lighting_cues: how the light behaves across the ad.

- color_palette: overall chroma + accent colors.

- motion_physics: style of camera movement and on-screen motion.

- surface_textures: reflections, materials, fabric, skin, glass, liquids.

- atmosphere_density: air quality, haze vs clarity, depth.

- sound_motifs: ambience + musical texture (no specific songs/artists).

- emotional_register: emotional arc over all 5 scenes.

You MAY mention:

• environments indirectly (city lights, cafe warmth, rooftop wind, ocean air, etc.).

• time of day.

• color words freely (golden, neon, teal, blush, amber, etc.).

------------------------------------------------------------
OUTPUT FORMAT
------------------------------------------------------------

Return ONLY valid JSON:

{
  "scent_profile_source": "user_provided" | "inferred" | "hybrid",

  "top_notes": [...],
  "heart_notes": [...],
  "base_notes": [...],

  "lighting_cues": "string (10–24 words)",
  "color_palette": "string (10–24 words)",
  "motion_physics": "string (10–24 words)",
  "surface_textures": "string (10–24 words)",
  "atmosphere_density": "string (10–24 words)",
  "sound_motifs": "string (10–24 words)",
  "emotional_register": "string (10–24 words)"
}
"""

STAGE3_SCENE_ASSEMBLER_PROMPT = """SYSTEM: STAGE 3 — CINEMATIC SCENE ASSEMBLER (Option C — Full Cinematic, TikTok-Style)

ROLE:

You receive:

1. STAGE 1 BLUEPRINT (5 scenes with: visual, action, camera, lighting, mood, product_usage)

2. STAGE 2 CINEMATIC PROFILE (lighting_cues, color_palette, motion_physics, surface_textures, atmosphere_density, sound_motifs, emotional_register)

You must turn this into 5 cinematic paragraphs, one per scene, video-ready.

Each paragraph:

• describes a 3–4 second shot

• includes:
    - environment / setting
    - subject (wearer, bottle, or both)
    - camera motion
    - lighting & color inspired by Stage 2
    - an emotional micro-beat

• references the perfume subtly through visuals, atmosphere, or reactions.

STYLE:

• Cinematic, vivid, but concise (3–5 sentences per scene).

• Clear enough that a video model can "see" the shot.

• You MAY mention environments (city street, cafe, rooftop, bedroom, metro platform, beach, etc.).

• You MAY use color (golden hour, neon pink, deep teal shadows, etc.).

• You MAY show the bottle explicitly in scenes 1 and 5; optional cameo in others.

• No explicit sex, no hard performance claims.

SOUND REQUIREMENTS:

• ONLY ambient/environmental sounds (city traffic, wind, water, footsteps, fabric rustling, glass clinking, etc.).

• NO voiceovers, NO speech, NO dialogue, NO narration, NO talking, NO words spoken.

• NO music descriptions (music will be added separately if needed).

• When mentioning sound, describe ONLY natural ambient sounds from the environment.

MAPPING RULES:

• Use Stage-1 fragments as the backbone:
    - location and composition from "visual"
    - key movement from "action"
    - camera move from "camera"
    - lighting from "lighting"
    - mood from "mood"
    - how scent is felt from "product_usage"
  You may freely rewrite the fragments into fluent sentences, as long as you keep their meaning.

• Use Stage-2 to "flavor" each scene:
    - lighting_cues → how light shifts or behaves in that scene
    - color_palette → key colors in the shot
    - motion_physics → feel of camera and character movement
    - surface_textures → skin, fabric, glass, environment surfaces
    - atmosphere_density → haze/clarity, depth
    - sound_motifs → describe ONLY ambient/environmental sounds (no voice, no music)
    - emotional_register → emotional undertone of the moment

OUTPUT FORMAT:

Write the 5 scenes in order:

Scene 1: {Stage-1 scene title}
{3–5 sentence cinematic description}

Scene 2: {Stage-1 scene title}
{3–5 sentence cinematic description}

Scene 3: {Stage-1 scene title}
{3–5 sentence cinematic description}

Scene 4: {Stage-1 scene title}
{3–5 sentence cinematic description}

Scene 5: {Stage-1 scene title}
{3–5 sentence cinematic description}

No analysis, no JSON, no code fences — just the labeled scenes.
"""


# --------------------------------------------------------------------------------------
# Pydantic Schemas
# --------------------------------------------------------------------------------------

class SceneDescription(BaseModel):
    visual: str
    action: str
    camera: str
    lighting: str
    mood: str
    product_usage: str


class BlueprintScene(BaseModel):
    scene_number: int
    stage: str
    duration_seconds: int
    scene_description: SceneDescription
    sound_design: str
    voiceover: str
    overlay_text: str


class Stage1Blueprint(BaseModel):
    framework: str
    total_duration_seconds: int
    reference_image_path: str
    reference_image_usage: str
    style_tone: str
    scenes: List[BlueprintScene]
    music: Dict[str, str]


class ScentProfile(BaseModel):
    """
    Stage 2 output: olfactory + cinematic profile (Option C).
    No word-count constraints or color policing at schema level.
    """
    scent_profile_source: str = Field(..., pattern="^(inferred|user_provided|hybrid)$")

    top_notes: List[str]
    heart_notes: List[str]
    base_notes: List[str]

    lighting_cues: str
    color_palette: str
    motion_physics: str
    surface_textures: str
    atmosphere_density: str
    sound_motifs: str
    emotional_register: str

    @field_validator("top_notes", "heart_notes", "base_notes", mode="after")
    @classmethod
    def validate_notes(cls, notes):
        # Light sanity check: ingredients, not pure vibe words.
        forbidden_categories = ["citrus", "floral", "woody", "ambery", "green"]
        for n in notes:
            if n.lower() in forbidden_categories:
                raise ValueError(
                    f"Invalid note '{n}'. Use specific ingredients, not broad categories."
                )
        return notes


# --------------------------------------------------------------------------------------
# Text Converters
# --------------------------------------------------------------------------------------

def stage1_to_text(stage1: Stage1Blueprint) -> str:
    lines = ["STAGE 1 BLUEPRINT"]
    for scene in stage1.scenes:
        lines.append(f"\nScene {scene.scene_number}: {scene.stage}")
        lines.append(f"visual: {scene.scene_description.visual}")
        lines.append(f"action: {scene.scene_description.action}")
        lines.append(f"camera: {scene.scene_description.camera}")
        lines.append(f"lighting: {scene.scene_description.lighting}")
        lines.append(f"mood: {scene.scene_description.mood}")
        lines.append(f"product_usage: {scene.scene_description.product_usage}")
    return "\n".join(lines)


def stage2_to_text(stage2: ScentProfile) -> str:
    return (
        "STAGE 2 CINEMATIC PHYSICS\n"
        f"lighting_cues: {stage2.lighting_cues}\n"
        f"color_palette: {stage2.color_palette}\n"
        f"motion_physics: {stage2.motion_physics}\n"
        f"surface_textures: {stage2.surface_textures}\n"
        f"atmosphere_density: {stage2.atmosphere_density}\n"
        f"sound_motifs: {stage2.sound_motifs}\n"
        f"emotional_register: {stage2.emotional_register}\n"
    )


def stage1_to_stage2_summary(stage1: Stage1Blueprint) -> dict:
    moods = [s.scene_description.mood for s in stage1.scenes]
    lightings = [s.scene_description.lighting for s in stage1.scenes]
    return {
        "moods": moods,
        "lightings": lightings,
        "style_tone": stage1.style_tone,
    }


# --------------------------------------------------------------------------------------
# Stage 1 / Stage 2 / Stage 3
# --------------------------------------------------------------------------------------

# Use valid OpenAI model names
# Options: "gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"
DEFAULT_STAGE1_MODEL = "gpt-4"  # Standard GPT-4 model
DEFAULT_STAGE2_MODEL = "gpt-4"  # Standard GPT-4 model
DEFAULT_STAGE3_MODEL = "gpt-4"  # Standard GPT-4 model


async def run_stage1_blueprint(
    llm: LLMClient,
    user_prompt: str,
    reference_image_path: str = "{{REFERENCE_IMAGE_PATH}}",
    reference_image_usage: str = "inspiration for mood and composition",
    style_tone: str = "cinematic, TikTok-ready, emotionally vivid",
    model: str = DEFAULT_STAGE1_MODEL,
) -> Stage1Blueprint:
    payload = json.dumps(
        {
            "user_input": user_prompt,
            "reference_image_path": reference_image_path,
            "reference_image_usage": reference_image_usage,
            "style_tone": style_tone,
        },
        ensure_ascii=False,
    )

    messages = [
        {"role": "system", "content": STAGE1_BLUEPRINT_PROMPT},
        {"role": "user", "content": payload},
    ]

    raw = await llm.call_chat_model(messages=messages, model=model, max_output_tokens=3000)
    data = parse_json_str(raw)

    data.setdefault("reference_image_path", reference_image_path)
    data.setdefault("reference_image_usage", reference_image_usage)
    data.setdefault("style_tone", style_tone)

    if "music" not in data:
        data["music"] = {"style": "", "energy": "", "notes": ""}
    else:
        data["music"] = {"style": "", "energy": "", "notes": ""}

    if "scenes" in data:
        for scene in data["scenes"]:
            scene.setdefault("voiceover", "")
            scene.setdefault("overlay_text", "")

    try:
        return Stage1Blueprint.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Stage 1 blueprint failed validation: {e}") from e


async def run_stage2_scent_profile(
    llm: LLMClient,
    user_notes: Optional[str],
    stage1_blueprint: Stage1Blueprint,
    model: str = DEFAULT_STAGE2_MODEL,
) -> ScentProfile:
    stage1_summary = stage1_to_stage2_summary(stage1_blueprint)
    payload = json.dumps(
        {
            "user_scent_notes": user_notes or "",
            "stage1_summary": stage1_summary,
        },
        ensure_ascii=False,
    )

    messages = [
        {"role": "system", "content": STAGE2_SCENT_PROFILE_PROMPT},
        {"role": "user", "content": payload},
    ]

    raw = await llm.call_chat_model(messages=messages, model=model, max_output_tokens=3000)
    data = parse_json_str(raw)

    try:
        return ScentProfile.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Stage 2 scent profile failed validation: {e}") from e


def _split_scenes(raw: str) -> List[str]:
    lines = raw.splitlines()
    scenes: List[str] = []
    current: List[str] = []

    for line in lines:
        if re.match(r"^\s*Scene\s+\d+:", line):
            if current:
                scenes.append("\n".join(current).strip())
                current = []
            current.append(line)
        else:
            current.append(line)

    if current:
        scenes.append("\n".join(current).strip())

    scenes = [s for s in scenes if s]
    if len(scenes) == 5:
        return scenes

    fallback = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    return fallback


async def run_stage3_scene_assembler(
    llm: LLMClient,
    stage1_blueprint: Stage1Blueprint,
    scent_profile: ScentProfile,
    model: str = DEFAULT_STAGE3_MODEL,
) -> List[str]:
    if len(stage1_blueprint.scenes) != 5:
        raise ValueError(f"Stage 1 must contain exactly 5 scenes, got {len(stage1_blueprint.scenes)}")

    stage1_text = stage1_to_text(stage1_blueprint)
    stage2_text = stage2_to_text(scent_profile)

    messages = [
        {"role": "system", "content": STAGE3_SCENE_ASSEMBLER_PROMPT},
        {"role": "user", "content": stage1_text},
        {"role": "user", "content": stage2_text},
    ]

    raw = await llm.call_chat_model(messages=messages, model=model, max_output_tokens=4000)
    raw = raw.strip()

    paragraphs = _split_scenes(raw)

    if len(paragraphs) != 5:
        raise ValueError(
            f"Stage 3 expected 5 scenes, got {len(paragraphs)}.\n\nRaw output:\n{raw}"
        )

    return paragraphs


# --------------------------------------------------------------------------------------
# Orchestrator
# --------------------------------------------------------------------------------------

async def generate_sora_prompt_option_c(
    api_key: str,
    user_prompt: str,
    user_scent_notes: Optional[str] = None,
    reference_image_path: str = "{{REFERENCE_IMAGE_PATH}}",
    reference_image_usage: str = "inspiration for mood and composition",
    style_tone: str = "cinematic, TikTok-ready, emotionally vivid",
) -> Dict[str, Any]:
    """
    One-shot orchestrator:

    - Stage 1 (gpt-4) → blueprint

    - Stage 2 (gpt-4) → scent profile

    - Stage 3 (gpt-4 with fallback) → 5 cinematic paragraphs

    """

    llm = LLMClient(api_key=api_key)

    stage1 = await run_stage1_blueprint(
        llm=llm,
        user_prompt=user_prompt,
        reference_image_path=reference_image_path,
        reference_image_usage=reference_image_usage,
        style_tone=style_tone,
        model=DEFAULT_STAGE1_MODEL,
    )

    stage2 = await run_stage2_scent_profile(
        llm=llm,
        user_notes=user_scent_notes,
        stage1_blueprint=stage1,
        model=DEFAULT_STAGE2_MODEL,
    )

    stage3 = await run_stage3_scene_assembler(
        llm=llm,
        stage1_blueprint=stage1,
        scent_profile=stage2,
        model=DEFAULT_STAGE3_MODEL,
    )

    return {
        "stage1_blueprint": stage1.model_dump(),
        "stage2_scent_profile": stage2.model_dump(),
        "stage3_scenes": stage3,
    }

