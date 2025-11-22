"""
Option A: Abstract Cinematic Perfume Pipeline

Single coherent file:

- LLM client wrapper

- Prompts (Option A: abstract, environment-free)

- Pydantic schemas

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

        - Uses chat.completions for GPT-4 / GPT-4.1 / GPT-5 family.

        - For GPT-5 family, omits temperature and uses max_completion_tokens.

        - If GPT-5 returns empty/invalid content, retries once with gpt-4.
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
                    timeout=120.0,  # 2 minute timeout per API call
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"{model_name} API call timed out after 120 seconds")
            except APIConnectionError as e:
                logger.error(f"[LLM][{model_name}] Connection error: {e}")
                raise ConnectionError(
                    f"Network error connecting to OpenAI API: {e}. "
                    f"Please check your internet connection and try again."
                )
            except APITimeoutError as e:
                logger.error(f"[LLM][{model_name}] Timeout error: {e}")
                raise TimeoutError(
                    f"OpenAI API request timed out: {e}. Please try again."
                )
            except APIError as e:
                logger.error(f"[LLM][{model_name}] API error: {e}")
                raise ValueError(
                    f"OpenAI API error: {e}. "
                    f"Please check your API key and account status."
                )
            except Exception as e:
                logger.error(f"[LLM][{model_name}] Unexpected error: {type(e).__name__}: {e}")
                raise

            if not resp.choices:
                raise ValueError(f"{model_name} returned no choices.")

            text = resp.choices[0].message.content
            if not text:
                raise ValueError(f"{model_name} returned empty content.")

            usage = getattr(resp, "usage", None)
            if usage:
                logger.info(
                    f"[LLM][{model_name}] Tokens: "
                    f"prompt={getattr(usage, 'prompt_tokens', None)}, "
                    f"completion={getattr(usage, 'completion_tokens', None)}"
                )
            return text

        try:
            try:
                return await _once(model)
            except (ConnectionError, TimeoutError) as network_err:
                logger.error(f"[LLM][{model}] Network/timeout error: {network_err}")
                raise
            except ValueError as inner_err:
                # If a GPT-5 family model failed, retry once with gpt-4
                if model in MODELS_USE_COMPLETION_TOKENS:
                    logger.warning(
                        f"[LLM][{model}] returned empty/invalid content, "
                        "retrying once with gpt-4..."
                    )
                    try:
                        return await _once("gpt-4")
                    except (ConnectionError, TimeoutError) as retry_err:
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
# PROMPTS — OPTION A (ABSTRACT, ENVIRONMENT-FREE)
# --------------------------------------------------------------------------------------

STAGE1_BLUEPRINT_PROMPT = """SYSTEM: STAGE 1 — BLUEPRINT GENERATOR (STRICT ABSTRACT FRAGMENTS, Option A)

ROLE:

You convert the user's short input into a 5-scene perfume-style blueprint.

Your output MUST be:

• fully abstract

• cinematic

• environment-free

• ingredient-free

• strictly fragmented

• fully compliant with the schema

------------------------------------------------------------
ABSOLUTE PROHIBITIONS (MUST NEVER APPEAR)
------------------------------------------------------------

You MUST NOT include:

• any nature (trees, groves, beaches, water, flowers, skies, clouds, sunlight)

• any environments (rooms, streets, rooftops, hallways, windows, interiors)

• any time-of-day (morning, sunrise, noon, sunset, night, dusk, dawn)

• any concrete locations (city, cafe, studio, apartment, rooftop, corridor)

• any weather or seasons (rain, fog, wind, snow, summer, winter)

• any ingredient or scent language (citrus, lemon, bergamot, floral, woody)

• any food or fruit

• any storytelling or character actions beyond abstract motion

------------------------------------------------------------
ALLOWED VISUAL FRAGMENTS (USE ONLY THESE STYLES)
------------------------------------------------------------

Use ONLY abstract, non-representational fragments like:

• "narrow geometric frame"

• "clean modern silhouette"

• "soft reflective plane"

• "minimalist abstract form"

• "subtle layered gradient"

• "dim diffused backdrop"

• "floating abstract contours"

• "soft radiant halo"

• "stacked translucent planes"

NO landscapes. NO interiors. NO objects except the word "bottle" in scenes 1 and 5.

------------------------------------------------------------
PRODUCT USAGE FIELD (STRICT RULE)
------------------------------------------------------------

product_usage MUST be:

• 2–5 word abstract sensory metaphor

• no ingredients

• no category words like "citrus", "floral", "woody"

• no explicit emotions like "happy", "sad"

Allowed examples:

• "bright airy lift"

• "cool luminous drift"

• "soft radiant pulse"

• "gentle vibrant clarity"

------------------------------------------------------------
SCENE TITLES (FIXED — MUST MATCH EXACTLY)
------------------------------------------------------------

Scene 1: "First Impression"

Scene 2: "Awakening"

Scene 3: "Radiance"

Scene 4: "Momentum"

Scene 5: "Lasting Impression"

------------------------------------------------------------
FRAGMENT LENGTH RULES
------------------------------------------------------------

Each scene MUST have:

scene_number: 1–5

stage: exact title above

duration_seconds: 4

scene_description:
  visual: 3–7 abstract words
  action: 3–7 abstract motion words
  camera: one of: "static", "slow pan", "slow dolly", "glide"
  lighting: 3–7 abstract lighting words
  mood: 1 word (e.g., "calm", "vital", "buoyant")
  product_usage: 2–5 abstract metaphor words

sound_design: 1–6 abstract ambient words (e.g., "soft shimmering hush")

voiceover: "" (empty string)

overlay_text: "" (empty string)

------------------------------------------------------------
OBJECT RULES
------------------------------------------------------------

Only scenes 1 and 5 may include the word "bottle" inside visual or action.

Scenes 2–4 MUST NOT reference any object.

------------------------------------------------------------
OUTPUT FORMAT (STRICT)
------------------------------------------------------------

Return ONLY valid JSON:

{
  "framework": "Perfume-5-Scene",
  "total_duration_seconds": 20,
  "reference_image_path": "{{REFERENCE_IMAGE_PATH}}",
  "reference_image_usage": "inspiration for mood and composition",
  "style_tone": "cinematic, intimate, perfume-focused",
  "scenes": [
    {
      "scene_number": 1,
      "stage": "First Impression",
      "duration_seconds": 4,
      "scene_description": {
        "visual": "",
        "action": "",
        "camera": "",
        "lighting": "",
        "mood": "",
        "product_usage": ""
      },
      "sound_design": "",
      "voiceover": "",
      "overlay_text": ""
    }
    ... scenes 2–5 with identical structure ...
  ],
  "music": {
    "style": "",
    "energy": "",
    "notes": ""
  }
}

CRITICAL:

• Return ONLY JSON

• No explanations

• No extra text

• No prose outside the JSON
"""

STAGE2_SCENT_PROFILE_PROMPT = """SYSTEM: STAGE 2 — OLFACTORY INTELLIGENCE ENGINE (Option A — Abstract Cinematic Physics)

ROLE:

You receive:

• user_scent_notes   (user's ingredient notes in loose text, may be empty)

• stage1_summary     (mood words + lighting fragments + style_tone from Stage 1)

You output a structured CINEMATIC SCENT PROFILE that maps fragrance notes into:

• lighting behavior

• motion physics

• atmospheric qualities

• surface textures

• sound textures

• emotional register

All cinematic fields MUST remain ABSTRACT and ENVIRONMENT-FREE.

------------------------------------------------------------
NOTE EXTRACTION RULES (STRICT)
------------------------------------------------------------

1. If the user specifies ingredients, use them exactly (normalized to singular where appropriate).

2. If the user does NOT specify heart/base notes:

   - infer realistic ingredient notes only (e.g., "orange blossom", "neroli", "green tea", "vetiver", "musk")

   - NEVER infer vague vibes or adjectives as notes.

3. NEVER use generic categories in note arrays (citrus, floral, woody, green, ambery).

4. NEVER use emotions or vibe words as notes.

------------------------------------------------------------
CINEMATIC ATTRIBUTE RULES (ABSTRACT ONLY)
------------------------------------------------------------

Each cinematic field MUST be:

• a single descriptive sentence

• roughly 12–24 words (no need to count perfectly, just stay in that range)

• about PHYSICAL cinematography ONLY

You MUST NOT describe:

• environments (city, cafe, room, rooftop, street, forest, sky, ocean, window)

• locations (indoors, outdoors)

• objects (table, chair, glass, trees, leaves, buildings, faces)

• characters or actions

• time of day or weather

• explicit scent / smell words ("lemon", "citrus", "fragrance", "aroma")

Allowed topics:

• light behavior (gradients, highlights, diffusion, glow, halo, contour)

• airflow and motion (currents, oscillations, pulses, drift)

• optical diffusion (haze, clarity, softness)

• material responses (reflection, translucency, sheen, shimmer)

• color in an abstract sense (pale, luminous, saturated, muted) WITHOUT naming concrete environments

------------------------------------------------------------
OUTPUT FORMAT
------------------------------------------------------------

Return ONLY valid JSON:

{
  "scent_profile_source": "user_provided" | "inferred" | "hybrid",

  "top_notes": [...],
  "heart_notes": [...],
  "base_notes": [...],

  "lighting_cues": "abstract string",
  "color_palette": "abstract string",
  "motion_physics": "abstract string",
  "surface_textures": "abstract string",
  "atmosphere_density": "abstract string",
  "sound_motifs": "abstract string",
  "emotional_register": "abstract string"
}
"""

STAGE3_SCENE_ASSEMBLER_PROMPT = """SYSTEM: STAGE 3 — ABSTRACT CINEMATIC SCENE ASSEMBLER (Option A)

ROLE:

You receive:

1. STAGE 1 BLUEPRINT (5 abstract scenes with: visual, action, camera, lighting, mood, product_usage)

2. STAGE 2 CINEMATIC PHYSICS (lighting_cues, color_palette, motion_physics, surface_textures, atmosphere_density, sound_motifs, emotional_register)

You must turn BOTH into 5 abstract cinematic paragraphs, one per scene.

These paragraphs are STILL ABSTRACT:

• NO environments

• NO characters

• NO ingredients

• NO concrete objects (except the word "bottle" is allowed ONLY if present in Stage 1 for Scenes 1 or 5)

------------------------------------------------------------
CORE RULES
------------------------------------------------------------

• You MUST stay fully abstract and environment-free.

• DO NOT introduce rooms, cities, nature, bodies, faces, or props.

• Describe only:

  - fields of light

  - motion

  - contours

  - gradients

  - pulses

  - textures

  - densities

  - sound textures

Stage 1 usage:

• For each scene, use the meaning of:

  - visual

  - action

  - camera

  - lighting

  - mood

  - product_usage

• You may lightly rephrase fragments into fluent sentences, but KEEP them abstract and aligned.

Stage 2 usage:

• Weave lighting_cues, color_palette, motion_physics, surface_textures, atmosphere_density, sound_motifs, emotional_register THROUGH each scene.

• Do NOT copy Stage-2 sentences verbatim; instead integrate their ideas and vocabulary.

------------------------------------------------------------
SOUND REQUIREMENTS
------------------------------------------------------------

• ONLY ambient/environmental sounds (abstract sound textures like "soft shimmering hush", "gentle oscillating pulse", "subtle resonant hum").

• NO voiceovers, NO speech, NO dialogue, NO narration, NO talking, NO words spoken.

• NO music descriptions (music will be added separately if needed).

• When mentioning sound, describe ONLY abstract ambient sound textures.

------------------------------------------------------------
STRUCTURE
------------------------------------------------------------

For EACH of the 5 scenes, produce:

Scene X: {Stage-1 scene title}

{3–5 sentence abstract cinematic description}

• 3–5 sentences per scene.

• No bullet points.

• No JSON.

• No headings beyond "Scene X: ...".

All five scenes MUST remain mutually coherent, like five moments in the same abstract visual universe.
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
    Stage 2 output: olfactory + abstract cinematic physics profile (Option A).

    We keep schema light: only enforce ingredient vs category on notes.
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
DEFAULT_STAGE1_MODEL = "gpt-4"  # Standard GPT-4 model
DEFAULT_STAGE2_MODEL = "gpt-4"  # Standard GPT-4 model
DEFAULT_STAGE3_MODEL = "gpt-4"  # Standard GPT-4 model


async def run_stage1_blueprint(
    llm: LLMClient,
    user_prompt: str,
    reference_image_path: str = "{{REFERENCE_IMAGE_PATH}}",
    reference_image_usage: str = "inspiration for mood and composition",
    style_tone: str = "cinematic, intimate, perfume-focused",
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

    raw = await llm.call_chat_model(
        messages=messages,
        model=model,
        max_output_tokens=2000,
    )

    data = parse_json_str(raw)

    data.setdefault("reference_image_path", reference_image_path)
    data.setdefault("reference_image_usage", reference_image_usage)
    data.setdefault("style_tone", style_tone)

    # Ensure music exists and is empty
    if "music" not in data:
        data["music"] = {"style": "", "energy": "", "notes": ""}
    else:
        data["music"] = {"style": "", "energy": "", "notes": ""}

    # Ensure voiceover and overlay_text exist for each scene
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

    raw = await llm.call_chat_model(
        messages=messages,
        model=model,
        max_output_tokens=2000,
    )

    data = parse_json_str(raw)

    try:
        return ScentProfile.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Stage 2 scent profile failed validation: {e}") from e


def _split_scenes(raw: str) -> List[str]:
    """
    Robust scene splitting:

    1) Try grouping lines starting with 'Scene X:'

    2) Fallback to splitting on double newlines.
    """
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
        raise ValueError(
            f"Stage 1 must contain exactly 5 scenes, got {len(stage1_blueprint.scenes)}"
        )

    stage1_text = stage1_to_text(stage1_blueprint)
    stage2_text = stage2_to_text(scent_profile)

    messages = [
        {"role": "system", "content": STAGE3_SCENE_ASSEMBLER_PROMPT},
        {"role": "user", "content": stage1_text},
        {"role": "user", "content": stage2_text},
    ]

    raw = await llm.call_chat_model(
        messages=messages,
        model=model,
        max_output_tokens=3000,
    )

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

async def generate_sora_prompt_option_a(
    api_key: str,
    user_prompt: str,
    user_scent_notes: Optional[str] = None,
    reference_image_path: str = "{{REFERENCE_IMAGE_PATH}}",
    reference_image_usage: str = "inspiration for mood and composition",
    style_tone: str = "cinematic, intimate, perfume-focused",
) -> Dict[str, Any]:
    """
    One-shot orchestrator (Option A: abstract, environment-free):

    - Stage 1 (gpt-4) → abstract 5-scene blueprint

    - Stage 2 (gpt-4) → abstract scent physics profile

    - Stage 3 (gpt-4) → 5 abstract cinematic paragraphs
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

