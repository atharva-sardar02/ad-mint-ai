"""
Option A-Hybrid: Abstract Perfume Ad Pipeline (Single File)

Stages:
  Stage 1  -> Abstract 5-scene blueprint (no environments, no ingredients)
  Stage 2  -> Abstract cinematic physics profile (no environments)
  Stage 3  -> 5 video-ready abstract cinematic paragraphs with a clear emotional arc

Use:
  from option_a_hybrid_pipeline import generate_sora_prompt_option_a_hybrid

  result = await generate_sora_prompt_option_a_hybrid(
      api_key=OPENAI_API_KEY,
      user_prompt="Fresh, bright citrus perfume with a clean, modern vibe.",
      user_scent_notes="lemon, bergamot, neroli, vetiver"
  )

  result["stage3_scenes"]  # -> list[str], one paragraph per scene, video-ready
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

# ======================================================================================
# LLM CLIENT
# ======================================================================================


class LLMClient:
    """
    Async wrapper around OpenAI chat.completions with:
      - GPT-4.x / GPT-5 support
      - sane defaults
      - timeout
      - optional GPT-5 -> GPT-4 fallback on empty/invalid content
    """

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
    ) -> str:
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

        base_params: Dict[str, Any] = {
            "messages": messages,
            "model": model,
        }

        if model not in MODELS_TEMPERATURE_RESTRICTED:
            base_params["temperature"] = temperature

        if model in MODELS_USE_COMPLETION_TOKENS:
            base_params["max_completion_tokens"] = max_output_tokens
        else:
            base_params["max_tokens"] = max_output_tokens

        async def _once(model_name: str) -> str:
            import asyncio
            from openai import APIError, APIConnectionError, APITimeoutError

            params = dict(base_params)
            params["model"] = model_name

            try:
                resp = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        **params,
                        stream=False,
                    ),
                    timeout=90.0,
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"{model_name} API call timed out after 90 seconds")
            except APIConnectionError as e:
                logger.error(f"[LLM][{model_name}] Connection error: {e}")
                raise ConnectionError(f"Network error connecting to OpenAI API: {e}")
            except APITimeoutError as e:
                logger.error(f"[LLM][{model_name}] Timeout error: {e}")
                raise TimeoutError(f"OpenAI API request timed out: {e}")
            except APIError as e:
                logger.error(f"[LLM][{model_name}] API error: {e}")
                raise ValueError(f"OpenAI API error: {e}")
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
                    f"[LLM][{model_name}] Tokens: prompt={getattr(usage, 'prompt_tokens', None)}, "
                    f"completion={getattr(usage, 'completion_tokens', None)}"
                )
            return text

        try:
            try:
                return await _once(model)
            except ValueError as e:
                # Fallback path: if GPT-5 misbehaves, retry once with GPT-4.x
                if model in MODELS_USE_COMPLETION_TOKENS:
                    logger.warning(
                        f"[LLM][{model}] invalid/empty content, retrying once with gpt-4.1..."
                    )
                    return await _once("gpt-4.1")
                raise e
        except Exception as e:
            logger.exception(f"[LLM ERROR][{model}] {e}")
            raise


def parse_json_str(raw: str) -> Dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from model: {e}\nRaw:\n{raw}") from e


# ======================================================================================
# PROMPTS — OPTION A-HYBRID
# ======================================================================================

STAGE1_BLUEPRINT_PROMPT = """
SYSTEM: STAGE 1 — ABSTRACT PERFUME BLUEPRINT (Option A-Hybrid)

ROLE:
You convert a short user prompt (and optional scent notes) into a 5-scene ABSTRACT
perfume blueprint. The output is used by later stages and MUST be:

• environment-free
• ingredient-free
• character-free
• purely abstract geometry / light / motion / mood
• structured as a 5-scene emotional arc

EMOTIONAL ARC (ABSTRACT NARRATIVE SPINE):
1. First Impression  → initial spark, clean arrival, bright tension
2. Awakening        → expansion, lift, awakening of energy
3. Radiance         → peak luminosity, open presence
4. Momentum         → sustained motion, rhythmic flow
5. Lasting Impression → soft echo, lingering after-image

------------------------------------------------------------
ABSOLUTE PROHIBITIONS (MUST NOT APPEAR)
------------------------------------------------------------
You MUST NOT mention:
• environments: city, street, cafe, kitchen, room, rooftop, window, sky, sea, forest, grove, garden, park
• nature: trees, leaves, flowers, waves, sun, clouds, mountains, river, sand
• bodies / people: woman, hand, face, eyes, skin, hair, wrist, fingers, friends, crowd
• ingredients & scent words: citrus, lemon, bergamot, jasmine, amber, wood, floral, musk, perfume, fragrance, scent
• food & drink: slice, fruit, tea, coffee, drink, meal, breakfast
• time-of-day & weather: morning, noon, sunset, night, rain, fog, snow, wind, summer, winter
• literal locations: apartment, studio, train, street, cafe, office, balcony, bedroom, terrace

The blueprint is like an abstract motion-graphics ad: shapes, halos, gradients, pulses.

------------------------------------------------------------
ALLOWED VISUAL / MOTION STYLES
------------------------------------------------------------
Use ONLY abstract fragments like:
• "narrow geometric frame"
• "minimalist abstract halo"
• "soft reflective plane"
• "clean modern silhouette"
• "floating layered contours"
• "subtle light gradient"
• "dim diffused backdrop"
• "pulsing concentric rings"

You MAY invent similar abstract phrases, but they MUST NOT become real objects or places.

------------------------------------------------------------
PRODUCT_USAGE FIELD (ABSTRACT METAPHOR)
------------------------------------------------------------
product_usage MUST be a 2–5 word abstract sensory metaphor:
• allowed examples:
  - "bright airy lift"
  - "soft radiant pulse"
  - "cool luminous drift"
  - "gentle vibrant clarity"
• NO ingredients, NO environments, NO people.

------------------------------------------------------------
SCENE TITLES (FIXED)
------------------------------------------------------------
Scene 1: "First Impression"
Scene 2: "Awakening"
Scene 3: "Radiance"
Scene 4: "Momentum"
Scene 5: "Lasting Impression"

------------------------------------------------------------
FIELD LENGTH RULES
------------------------------------------------------------
scene_description fields:
• visual:        3–8 abstract words
• action:        3–8 abstract motion words
• camera:        one of: "static", "slow pan", "slow dolly", "glide"
• lighting:      3–8 abstract lighting words
• mood:          1 word only (e.g. "fresh", "calm", "charged", "serene")
• product_usage: 2–5 words (abstract metaphor, as defined above)

sound_design:    1–6 abstract ambient words (e.g. "soft hum", "distant shimmer")

voiceover:       ""  (empty string)
overlay_text:    ""  (empty string)

OBJECT RULE:
• Only Scene 1 and Scene 5 MAY use the word "bottle".
  They must keep it abstract: "bottle silhouette", "bottle outline in halo".
• Scenes 2–4 MUST NOT mention "bottle" or any other concrete object.

------------------------------------------------------------
OUTPUT FORMAT
------------------------------------------------------------
Return ONLY valid JSON:

{
  "framework": "Perfume-5-Scene",
  "total_duration_seconds": 20,
  "reference_image_path": "{{REFERENCE_IMAGE_PATH}}",
  "reference_image_usage": "inspiration for abstract motion and light",
  "style_tone": "cinematic, intimate, abstract perfume-focused",
  "scenes": [...],
  "music": {
    "style": "",
    "energy": "",
    "notes": ""
  }
}
"""

STAGE2_SCENT_PROFILE_PROMPT = """
SYSTEM: STAGE 2 — ABSTRACT SCENT PHYSICS PROFILE (Option A-Hybrid)

ROLE:
You receive:
• user_scent_notes: loose text with possible ingredients
• stage1_summary: moods + product_usage metaphors + style_tone

You output an ABSTRACT SCENT PHYSICS PROFILE that never leaves the abstract domain.
It describes how light, color fields, motion, texture, atmosphere and sound SHOULD BE
animated for the ad.

------------------------------------------------------------
NOTE RULES
------------------------------------------------------------
• top_notes, heart_notes, base_notes are arrays of INGREDIENT NAMES
  (e.g. "lemon", "bergamot", "neroli", "vetiver").
• You MAY infer plausible heart/base ingredients if missing.
• You MUST NOT use vague categories like "citrus", "floral", "woody" as notes.
  Use concrete ingredients instead.
• You MUST NOT use pure vibes like "freshness", "energy" as notes.

------------------------------------------------------------
CINEMATIC FIELDS (ABSTRACT-ONLY)
------------------------------------------------------------
Each cinematic field is a single sentence (10–22 words),
describing ONLY abstract behavior of light / color / motion / texture / atmosphere / sound / emotion.

They MUST:
• stay environment-free (no city, room, sky, horizon, window, street, grove, ocean, table, etc.)
• be character-free (no person, hand, face, skin, eyes, hair)
• be ingredient-free in these fields (no lemon, citrus, jasmine, etc.)
• focus on:
  - halos, gradients, pulses, contours
  - light intensity, direction, diffusion
  - color fields & transitions (not painted onto objects)
  - motion rhythms, oscillations, flows
  - texture qualities (matte, glossy, granular, translucent)
  - sound textures (hums, chimes, distant shimmer)
  - emotional tone as an abstract field (e.g. "buoyant calm", "charged clarity")

Fields:
• lighting_cues
• color_palette
• motion_physics
• surface_textures
• atmosphere_density
• sound_motifs
• emotional_register

------------------------------------------------------------
OUTPUT FORMAT
------------------------------------------------------------
Return ONLY valid JSON:

{
  "scent_profile_source": "user_provided" | "inferred" | "hybrid",

  "top_notes": [...],
  "heart_notes": [...],
  "base_notes": [...],

  "lighting_cues": "string (10–22 words, abstract, environment-free)",
  "color_palette": "string (10–22 words, abstract, environment-free)",
  "motion_physics": "string (10–22 words, abstract, environment-free)",
  "surface_textures": "string (10–22 words, abstract, environment-free)",
  "atmosphere_density": "string (10–22 words, abstract, environment-free)",
  "sound_motifs": "string (10–22 words, abstract, environment-free)",
  "emotional_register": "string (10–22 words, abstract, environment-free)"
}
"""

STAGE3_SCENE_ASSEMBLER_PROMPT = """
SYSTEM: STAGE 3 — ABSTRACT CINEMATIC SCENE ASSEMBLER (Option A-Hybrid)

ROLE:
You receive:
1. STAGE 1 BLUEPRINT
   - 5 scenes: abstract visual/action/camera/lighting/mood/product_usage fragments
2. STAGE 2 SCENT PHYSICS
   - lighting_cues, color_palette, motion_physics, surface_textures,
     atmosphere_density, sound_motifs, emotional_register

You must output 5 ABSTRACT CINEMATIC PARAGRAPHS, one per scene, video-ready.

HYBRID GOAL:
• Keep the visuals fully abstract (Option A).
• Maintain a CLEAR EMOTIONAL & RHYTHMIC PROGRESSION across the 5 scenes (narrative spine).

------------------------------------------------------------
HARD CONTENT RULES
------------------------------------------------------------
Across ALL 5 paragraphs you MUST NOT mention:
• environments or places: city, street, cafe, room, rooftop, forest, grove, beach, sea, sky, window, table, skyline
• bodies / people: woman, hand, face, eyes, hair, skin, wrist, fingers, friends, crowd, character
• literal objects: glass, table, chair, car, building, tree, flower, leaf
• scent/ingredient words: citrus, lemon, bergamot, jasmine, amber, vanilla, musk, perfume, fragrance, cologne, scent
• time-of-day & weather: morning, dusk, night, rain, snow, fog, storm, season names

Allowed:
• abstract forms: silhouettes, halos, frames, contours, gradients, pulses, rings, planes, volumes, fields
• abstract motion: drift, pulse, oscillation, orbit, spiral, sweep, flicker, swell, ripple
• abstract light: radiant, diffused, sharp, soft, layered, concentric, luminous, dim, saturated
• abstract sound: hum, hush, echo, shimmer, distant chime, subtle resonance

Bottle rule:
• Only Scene 1 and Scene 5 MAY mention "bottle" or "bottle silhouette".
  They must remain abstract (no table, no hand, no room).

------------------------------------------------------------
MAPPING RULES
------------------------------------------------------------
For EACH scene:
• Use Stage-1 fragments as the backbone:
  - visual          → shapes / layout
  - action          → how forms move
  - camera          → how the viewpoint moves
  - lighting        → intensity / style of illumination
  - mood            → emotional tone of the beat
  - product_usage   → subtle abstract "effect" field

• Use Stage-2 physics to FLAVOR each paragraph:
  - lighting_cues       → how light evolves in that scene
  - color_palette       → color fields and transitions
  - motion_physics      → rhythm & style of motion
  - surface_textures    → qualities of the abstract forms' surfaces
  - atmosphere_density  → feel of the surrounding field
  - sound_motifs        → abstract sound texture only (no speech, no music)
  - emotional_register  → felt emotional quality of the beat

You may rephrase fragments into fluent sentences, but MUST preserve their meaning
and MUST stay in the abstract domain.

------------------------------------------------------------
STRUCTURE & LENGTH
------------------------------------------------------------
For each scene:

Scene X: {Stage-1 scene title}
{3–5 sentences of abstract, coherent cinematic description}

• Sentences should be 15–35 words each (not micro-snippets, not novels).
• The 5 scenes together should feel like one continuous evolution of the same abstract "world":
  - Scene 1: introduction of motif & mood
  - Scene 2: expansion / awakening
  - Scene 3: radiant peak
  - Scene 4: pulsing sustained motion
  - Scene 5: soft, lingering after-image

------------------------------------------------------------
OUTPUT
------------------------------------------------------------
Write exactly:

Scene 1: {Title}
{paragraph}

Scene 2: {Title}
{paragraph}

Scene 3: {Title}
{paragraph}

Scene 4: {Title}
{paragraph}

Scene 5: {Title}
{paragraph}

No JSON, no code fences, no extra commentary.
"""


# ======================================================================================
# Pydantic Schemas
# ======================================================================================

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
    Stage 2 output: abstract scent-physics profile.
    No word-count constraints enforced here; we rely on the prompt.
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


# ======================================================================================
# TEXT CONVERTERS
# ======================================================================================

def stage1_to_text(stage1: Stage1Blueprint) -> str:
    lines = ["STAGE 1 BLUEPRINT (ABSTRACT)"]
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
        "STAGE 2 ABSTRACT SCENT PHYSICS\n"
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
    product_usage = [s.scene_description.product_usage for s in stage1.scenes]
    return {
        "moods": moods,
        "product_usage": product_usage,
        "style_tone": stage1.style_tone,
    }


# ======================================================================================
# STAGES
# ======================================================================================

DEFAULT_STAGE1_MODEL = "gpt-4.1"
DEFAULT_STAGE2_MODEL = "gpt-4.1"
DEFAULT_STAGE3_MODEL = "gpt-4.1"


async def run_stage1_blueprint(
    llm: LLMClient,
    user_prompt: str,
    reference_image_path: str = "{{REFERENCE_IMAGE_PATH}}",
    reference_image_usage: str = "inspiration for abstract motion and light",
    style_tone: str = "cinematic, intimate, abstract perfume-focused",
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

    raw = await llm.call_chat_model(messages=messages, model=model, max_output_tokens=2200)
    data = parse_json_str(raw)

    data.setdefault("framework", "Perfume-5-Scene")
    data.setdefault("total_duration_seconds", 20)
    data.setdefault("reference_image_path", reference_image_path)
    data.setdefault("reference_image_usage", reference_image_usage)
    data.setdefault("style_tone", style_tone)

    if "music" not in data:
        data["music"] = {"style": "", "energy": "", "notes": ""}
    else:
        data["music"] = {"style": "", "energy": "", "notes": ""}

    # Normalize scenes: handle scene_title -> stage, ensure scene_number and duration_seconds
    if "scenes" in data:
        stage_mapping = {
            "First Impression": "First Impression",
            "Awakening": "Awakening",
            "Radiance": "Radiance",
            "Momentum": "Momentum",
            "Lasting Impression": "Lasting Impression",
        }
        
        for i, scene in enumerate(data["scenes"], start=1):
            # Normalize scene_title to stage if present
            if "scene_title" in scene and "stage" not in scene:
                scene["stage"] = scene.pop("scene_title")
            
            # Ensure scene_number
            if "scene_number" not in scene:
                scene["scene_number"] = i
            
            # Ensure stage matches expected values
            if "stage" in scene:
                stage_val = scene["stage"]
                # Try to match to expected stage names
                for key, value in stage_mapping.items():
                    if key.lower() in stage_val.lower() or stage_val.lower() in key.lower():
                        scene["stage"] = value
                        break
                # If no match, use the first 5 expected stages in order
                if scene["stage"] not in stage_mapping.values():
                    stages_list = list(stage_mapping.values())
                    if i <= len(stages_list):
                        scene["stage"] = stages_list[i - 1]
            
            # Ensure duration_seconds
            if "duration_seconds" not in scene:
                scene["duration_seconds"] = 4
            
            # Ensure voiceover/overlay_text
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

    raw = await llm.call_chat_model(messages=messages, model=model, max_output_tokens=2000)
    data = parse_json_str(raw)

    try:
        return ScentProfile.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Stage 2 scent profile failed validation: {e}") from e


def _split_scenes(raw: str) -> List[str]:
    # Prefer "Scene X:" grouping; fallback to double-newline.
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

    raw = await llm.call_chat_model(messages=messages, model=model, max_output_tokens=2500)
    raw = raw.strip()

    paragraphs = _split_scenes(raw)

    if len(paragraphs) != 5:
        raise ValueError(
            f"Stage 3 expected 5 scenes, got {len(paragraphs)}.\n\nRaw output:\n{raw}"
        )

    return paragraphs


# ======================================================================================
# ORCHESTRATOR
# ======================================================================================

async def generate_sora_prompt_option_a_hybrid(
    api_key: str,
    user_prompt: str,
    user_scent_notes: Optional[str] = None,
    reference_image_path: str = "{{REFERENCE_IMAGE_PATH}}",
    reference_image_usage: str = "inspiration for abstract motion and light",
    style_tone: str = "cinematic, intimate, abstract perfume-focused",
) -> Dict[str, Any]:
    """
    One-shot A-Hybrid pipeline:

      Stage 1 (abstract blueprint)  -> gpt-4.1
      Stage 2 (abstract physics)    -> gpt-4.1
      Stage 3 (abstract paragraphs) -> gpt-4.1 (with internal gpt-5 option if you change defaults)

    Returns:
      {
        "stage1_blueprint": ...dict...,
        "stage2_scent_profile": ...dict...,
        "stage3_scenes": [str, str, str, str, str]
      }
    """

    llm = LLMClient(api_key=api_key)

    logger.info("=== STAGE 1 (Option A-Hybrid): Abstract 5-scene blueprint ===")
    stage1 = await run_stage1_blueprint(
        llm=llm,
        user_prompt=user_prompt,
        reference_image_path=reference_image_path,
        reference_image_usage=reference_image_usage,
        style_tone=style_tone,
        model=DEFAULT_STAGE1_MODEL,
    )

    logger.info("=== STAGE 2 (Option A-Hybrid): Abstract scent physics ===")
    stage2 = await run_stage2_scent_profile(
        llm=llm,
        user_notes=user_scent_notes,
        stage1_blueprint=stage1,
        model=DEFAULT_STAGE2_MODEL,
    )

    logger.info("=== STAGE 3 (Option A-Hybrid): Abstract cinematic assembly ===")
    stage3 = await run_stage3_scene_assembler(
        llm=llm,
        stage1_blueprint=stage1,
        scent_profile=stage2,
        model=DEFAULT_STAGE3_MODEL,
    )

    logger.info("=== PIPELINE COMPLETE (Option A-Hybrid) ===")

    return {
        "stage1_blueprint": stage1.model_dump(),
        "stage2_scent_profile": stage2.model_dump(),
        "stage3_scenes": stage3,
    }