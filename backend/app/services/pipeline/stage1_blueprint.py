"""
Stage 1: Blueprint Generator (Option C — Cinematic, TikTok-Ready)
Converts user prompt -> 5-scene blueprint with concrete, ad-like fragments.
"""

import json
from typing import Optional

from pydantic import ValidationError

from app.services.pipeline.llm_client import call_chat_model, parse_json_str
from app.services.pipeline.llm_schemas import Stage1Blueprint
from app.services.pipeline.prompts import STAGE1_BLUEPRINT_PROMPT

DEFAULT_MODEL = "gpt-4.1"


async def run_stage1_blueprint(
    user_prompt: str,
    reference_image_path: str = "{{REFERENCE_IMAGE_PATH}}",
    reference_image_usage: str = "inspiration for mood and composition",
    style_tone: str = "cinematic, TikTok-ready, emotionally vivid",
    model: str = DEFAULT_MODEL,
) -> Stage1Blueprint:
    """
    Stage 1 (Option C): Takes a short user prompt and produces
    a 5-scene cinematic TikTok-style perfume blueprint.
    """

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

    raw = await call_chat_model(messages=messages, model=model)
    data = parse_json_str(raw)

    # Ensure reference + style fields exist
    data.setdefault("reference_image_path", reference_image_path)
    data.setdefault("reference_image_usage", reference_image_usage)
    data.setdefault("style_tone", style_tone)

    # Ensure framework + total_duration_seconds sane defaults if missing
    data.setdefault("framework", "Perfume-5-Scene")
    if "total_duration_seconds" not in data:
        # fall back to sum of durations if present, else 20
        total = 0
        for s in data.get("scenes", []):
            try:
                total += int(s.get("duration_seconds", 4))
            except Exception:
                total += 4
        data["total_duration_seconds"] = total or 20

    # Ensure music exists and is empty
    if "music" not in data:
        data["music"] = {"style": "", "energy": "", "notes": ""}
    else:
        data["music"] = {
            "style": "",
            "energy": "",
            "notes": "",
        }

    # Ensure scene stages exist & match Option C labels
    option_c_titles = [
        "First Impression",
        "Evolving Aura",
        "Wearer's World",
        "Intimate Close",
        "Final Signature",
    ]

    if "scenes" in data:
        for i, scene in enumerate(data["scenes"]):
            scene_num = scene.get("scene_number", i + 1)
            if "stage" not in scene:
                if 1 <= scene_num <= 5:
                    scene["stage"] = option_c_titles[scene_num - 1]
            # Ensure voiceover and overlay_text exist
            scene.setdefault("voiceover", "")
            scene.setdefault("overlay_text", "")

    # Pydantic validation
    try:
        blueprint = Stage1Blueprint.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Stage 1 blueprint failed validation: {e}") from e

    return blueprint