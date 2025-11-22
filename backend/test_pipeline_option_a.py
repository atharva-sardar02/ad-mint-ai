#!/usr/bin/env python3
"""
Test Option A (Abstract) pipeline to generate video prompts.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.pipeline.pipeline_option_a import (
    LLMClient,
    run_stage1_blueprint,
    run_stage2_scent_profile,
    run_stage3_scene_assembler,
)


async def main():
    if not settings.OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not configured in settings.")
        sys.exit(1)

    # Initialize LLM client
    llm = LLMClient(api_key=settings.OPENAI_API_KEY)

    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    user_scent_notes = "lemon, bergamot"

    print("=" * 80)
    print("GENERATING VIDEO PROMPTS WITH OPTION A (ABSTRACT)")
    print("=" * 80)
    print(f"User Prompt: {user_prompt}")
    print(f"User Scent Notes: {user_scent_notes}")
    print("=" * 80)
    print("\n")

    try:
        # STAGE 1: Generate abstract blueprint
        print("=" * 80)
        print("STAGE 1: Generating abstract 5-scene blueprint")
        print("=" * 80)
        print("\n")

        stage1_blueprint = await run_stage1_blueprint(
            llm=llm,
            user_prompt=user_prompt,
            model="gpt-4",
        )

        print("✓ Stage 1 complete!")
        print(f"  Framework: {stage1_blueprint.framework}")
        print(f"  Total Duration: {stage1_blueprint.total_duration_seconds}s")
        print(f"  Scenes: {len(stage1_blueprint.scenes)}")
        print("\n")
        print("Scene Titles:")
        for scene in stage1_blueprint.scenes:
            print(f"  Scene {scene.scene_number}: {scene.stage}")
            print(f"    Visual: {scene.scene_description.visual}")
            print(f"    Action: {scene.scene_description.action}")
        print("\n")

        # STAGE 2: Generate abstract scent profile
        print("=" * 80)
        print("STAGE 2: Generating abstract scent physics profile")
        print("=" * 80)
        print("\n")

        stage2_scent_profile = await run_stage2_scent_profile(
            llm=llm,
            user_notes=user_scent_notes,
            stage1_blueprint=stage1_blueprint,
            model="gpt-4",
        )

        print("✓ Stage 2 complete!")
        print(f"  Scent Profile Source: {stage2_scent_profile.scent_profile_source}")
        print(f"  Top Notes: {', '.join(stage2_scent_profile.top_notes)}")
        print(f"  Heart Notes: {', '.join(stage2_scent_profile.heart_notes)}")
        print(f"  Base Notes: {', '.join(stage2_scent_profile.base_notes)}")
        print("\n")

        # STAGE 3: Generate abstract video prompts
        print("=" * 80)
        print("STAGE 3: Assembling abstract video-ready prompts")
        print("=" * 80)
        print("\n")

        stage3_scenes = await run_stage3_scene_assembler(
            llm=llm,
            stage1_blueprint=stage1_blueprint,
            scent_profile=stage2_scent_profile,
            model="gpt-4",
        )

        print("=" * 80)
        print("VIDEO PROMPTS (OPTION A - ABSTRACT):")
        print("=" * 80)
        print("\n")

        for i, prompt in enumerate(stage3_scenes, start=1):
            print(f"SCENE {i}:")
            print("-" * 80)
            print(prompt)
            print("-" * 80)
            print()

        print("=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Total scenes: {len(stage3_scenes)}")
        for i, p in enumerate(stage3_scenes, start=1):
            sentences = p.count('.') + p.count('!') + p.count('?')
            words = len(p.split())
            print(f"Scene {i}: {sentences} sentences, {words} words")
        print("=" * 80)
        print("\n✓ All stages complete successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)

