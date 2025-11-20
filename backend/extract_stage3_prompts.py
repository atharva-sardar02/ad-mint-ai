#!/usr/bin/env python3
"""
Extract and display only the Stage 3 Sora 2 prompts from the hybrid pipeline.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.pipeline.pipeline_option_hybrid import (
    LLMClient,
    run_stage1_blueprint,
    run_stage2_scent_profile,
    run_stage3_scene_assembler,
)


async def main():
    if not settings.OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not configured.")
        sys.exit(1)

    llm = LLMClient(api_key=settings.OPENAI_API_KEY)
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    user_scent_notes = "lemon, bergamot"

    # Run all stages
    stage1 = await run_stage1_blueprint(llm=llm, user_prompt=user_prompt, model="gpt-4")
    stage2 = await run_stage2_scent_profile(llm=llm, user_notes=user_scent_notes, stage1_blueprint=stage1, model="gpt-4")
    stage3 = await run_stage3_scene_assembler(llm=llm, stage1_blueprint=stage1, scent_profile=stage2, model="gpt-4")

    # Output only the Stage 3 prompts
    print("=" * 80)
    print("EXACT STAGE 3 PROMPTS (SORA 2 READY):")
    print("=" * 80)
    print()
    
    for i, prompt in enumerate(stage3, start=1):
        print(f"PROMPT {i}:")
        print("-" * 80)
        print(prompt.strip())
        print("-" * 80)
        print()


if __name__ == "__main__":
    asyncio.run(main())

