import json
import logging
import re

import openai
from app.core.config import settings

logger = logging.getLogger(__name__)

SCENE_ASSEMBLER_SYSTEM_PROMPT = """
SYSTEM: SORA SCENE ASSEMBLER — v4.0 (STRICT SHOT LANGUAGE)

ROLE:
You convert a compact JSON fragment into ONE short cinematic description
for a single 4-second Sora video shot.

The user sends:
{
  "visual": "string",
  "action": "string",
  "camera": "string",
  "lighting": "string",
  "mood": "string",
  "product_usage": "string",
  "sound_design": "string",
  "has_reference_image": true/false
}

INTERPRETATION RULES:
• The fragment already contains everything you need.
• You MUST NOT invent extra locations, props, or characters.
• You MUST NOT invent brand names, UI, logos, or on-screen text.
• You NEVER describe what the product looks like; only how it is used.

SHOT GRAMMAR (MANDATORY):
Describe ONE continuous, real-time, 4-second shot with:
• ONE clear setting from "visual"
• ONE visible subject or group
• ONE simple physical action from "action" / "product_usage"
• ONE camera behavior from "camera"
• ONE lighting description from "lighting"
• Optional ambient detail from "sound_design"

CAMERA:
Allowed camera values (case-insensitive):
• "static"   → camera does not move
• "push-in"  → slow push-in toward subject
• "glide"    → slow sideways movement
• "slow pan" → slow horizontal pan

You must:
• Follow the camera field exactly if it is one of these.
• If it is missing or unknown, default to a steady static mid-shot.
• Never describe cuts, edits, angle changes, or multiple shots.

REFERENCE IMAGE:
If has_reference_image is true:
• Prefer a steady or very slow camera.
• Avoid large body movements or complex choreography.
• Emphasize stability and clarity of the moment.
• NEVER describe any visual details of the product from the image.

PRODUCT USAGE:
• ONLY describe behavior, not appearance.
• Good: “briefly checks their watch for an update”.
• Bad: “sleek black watch”, “colorful interface”, “branded display”.

MOOD, STYLE, TONE:
• Express mood through concrete visual cues and behavior.
• DO NOT use meta phrases like “the mood is…”, “the overall visual style feels…”.
• Avoid vague brand adjectives like: “aspirational”, “premium”, “luxurious”,
  “professional”, “modern”, “stylish”, “elevated”, “dynamic”.
• Do NOT mention “mood”, “style”, or “tone” explicitly in your output.

SOUND:
• Use "sound_design" only as light ambient context:
  e.g. “with faint city ambience in the background”.
• Do NOT describe music, impacts, transitions, or stylized SFX.

OUTPUT REQUIREMENTS (VERY IMPORTANT):
• Output ONLY 1–2 sentences of natural prose.
• 20–45 words total.
• Describe ONE continuous 4-second moment.
• No lists, no labels, no JSON, no quotes around the text.
• Never repeat a product description or feature list.
"""


client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


def _simplify_clause(text: str, max_words: int) -> str:
    """
    Take the first simple clause and trim to max_words.
    Helps prevent drifting into long product blurbs.
    """
    if not text:
        return ""
    # Cut at strong separators
    for sep in [".", ";", " but ", " and then ", " while "]:
        if sep in text:
            text = text.split(sep)[0]
    words = text.strip().split()
    if len(words) > max_words:
        words = words[:max_words]
    return " ".join(words).strip()


def _sanitize_fragment(fragment: dict) -> dict:
    """
    Clamp fragment fields into Sora-friendly ranges:
      - short, concrete clauses
      - safe camera values
    """
    camera = (fragment.get("camera") or "").strip().lower()
    allowed_cameras = {"static", "push-in", "glide", "slow pan"}
    if camera not in allowed_cameras:
        camera = "static"

    return {
        "visual": _simplify_clause(fragment.get("visual", ""), 10),
        "action": _simplify_clause(fragment.get("action", ""), 10),
        "camera": camera,
        "lighting": _simplify_clause(fragment.get("lighting", ""), 8),
        "mood": _simplify_clause(fragment.get("mood", ""), 5),
        "product_usage": _simplify_clause(fragment.get("product_usage", ""), 10),
        "sound_design": _simplify_clause(fragment.get("sound_design", ""), 8),
        "has_reference_image": bool(fragment.get("has_reference_image", False)),
    }


def _postprocess_sora_text(text: str) -> str:
    """
    Enforce:
      - 1–2 sentences max
      - <= 45 words
      - remove extra whitespace
    """
    if not text:
        return text

    # Normalize whitespace
    text = " ".join(text.split())

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return ""

    # Keep at most 2 sentences
    sentences = sentences[:2]
    text = " ".join(sentences)

    # Cap at 45 words
    words = text.split()
    if len(words) > 45:
        words = words[:45]
        if not words[-1].endswith((".", "!", "?")):
            words[-1] = words[-1].rstrip(",;") + "."
        text = " ".join(words)

    return text.strip()


async def _assemble_scene_prompt(
    fragment: dict,
    client: openai.OpenAI,
    fallback_prompt: str,
) -> str:
    """
    Stage 2: Convert fragments → final Sora prose.

    Guarantees (as much as possible):
      • Single, simple, filmable shot
      • Short 1–2 sentence output
      • No meta mood/style lines
    """
    if not fragment:
        return fallback_prompt

    sanitized = _sanitize_fragment(fragment)

    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": SCENE_ASSEMBLER_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(sanitized, ensure_ascii=False)},
            ],
            temperature=0.15,
            max_tokens=220,
        )
        raw_text = (response.choices[0].message.content or "").strip()
        final_text = _postprocess_sora_text(raw_text)
        return final_text or fallback_prompt
    except Exception as e:
        logger.warning(f"[Scene Assembler] Falling back due to error: {e}")
        return fallback_prompt