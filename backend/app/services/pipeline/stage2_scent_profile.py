"""
Stage 2: Scent Profile Generator (Option C — Full Cinematic Mode)

Takes:
    - user_scent_notes (optional raw string)
    - Stage 1 blueprint (for moods / lighting / style_tone summary)

Returns:
    - ScentProfile (no strict word counts, full color + environment allowed)
"""

import json
from typing import Optional

from pydantic import ValidationError

from app.services.pipeline.llm_client import call_chat_model, parse_json_str
from app.services.pipeline.llm_schemas import ScentProfile, Stage1Blueprint
from app.services.pipeline.prompts import STAGE2_SCENT_PROFILE_PROMPT
from app.services.pipeline.text_converters import stage1_to_stage2_summary

DEFAULT_MODEL = "gpt-5"  # or "gpt-4.1" for cheaper runs


async def run_stage2_scent_profile(
    user_notes: Optional[str],
    stage1_blueprint: Stage1Blueprint,
    model: str = DEFAULT_MODEL,
) -> ScentProfile:
    """
    Stage 2 (Option C):
    - Build a compact summary from Stage 1.
    - Provide user notes + Stage-1 summary to the LLM.
    - Parse JSON into ScentProfile.
    """

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

    raw = await call_chat_model(
        messages=messages,
        model=model,
        max_output_tokens=4000,
    )

    data = parse_json_str(raw)

    try:
        return ScentProfile.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Stage 2 scent profile failed validation: {e}") from e