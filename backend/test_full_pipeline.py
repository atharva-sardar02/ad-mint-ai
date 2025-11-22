#!/usr/bin/env python3
"""
Test script to generate all 3 stages in sequence.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pipeline.stage1_blueprint import run_stage1_blueprint
from app.services.pipeline.stage2_scent_profile import run_stage2_scent_profile
from app.services.pipeline.stage3_scene_assembler import run_stage3_scene_assembler


async def main():
    # User prompt
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    
    print("=" * 80)
    print("USER PROMPT:")
    print("=" * 80)
    print(user_prompt)
    print("=" * 80)
    print("\n")
    
    # Stage 1
    print("=" * 80)
    print("STAGE 1: GENERATING BLUEPRINT (GPT-4.1)...")
    print("=" * 80)
    print("\n")
    sys.stdout.flush()
    
    blueprint = await run_stage1_blueprint(user_prompt)
    
    print("✅ Stage 1 Complete")
    print(f"   Framework: {blueprint.framework}")
    print(f"   Duration: {blueprint.total_duration_seconds}s")
    print(f"   Scenes: {len(blueprint.scenes)}")
    print("\n")
    
    # Stage 2
    print("=" * 80)
    print("STAGE 2: GENERATING SCENT PROFILE (GPT-5)...")
    print("=" * 80)
    print("\n")
    sys.stdout.flush()
    
    scent_profile = await run_stage2_scent_profile(user_prompt, blueprint)
    
    print("✅ Stage 2 Complete")
    print(f"   Source: {scent_profile.scent_profile_source}")
    print(f"   Top Notes: {', '.join(scent_profile.top_notes)}")
    print(f"   Heart Notes: {', '.join(scent_profile.heart_notes)}")
    print(f"   Base Notes: {', '.join(scent_profile.base_notes)}")
    print("\n")
    
    # Stage 3
    print("=" * 80)
    print("STAGE 3: GENERATING SCENE ASSEMBLER (GPT-5)...")
    print("=" * 80)
    print("\n")
    sys.stdout.flush()
    
    paragraphs = await run_stage3_scene_assembler(blueprint, scent_profile)
    
    print("=" * 80)
    print("STAGE 3 OUTPUT - 5 CINEMATIC PARAGRAPHS:")
    print("=" * 80)
    print("\n")
    
    for i, paragraph in enumerate(paragraphs, start=1):
        print(f"SCENE {i}:")
        print("-" * 80)
        print(paragraph)
        print("-" * 80)
        print("\n")
    
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total paragraphs: {len(paragraphs)}")
    for i, p in enumerate(paragraphs, start=1):
        sentences = p.count('.') + p.count('!') + p.count('?')
        words = len(p.split())
        print(f"Scene {i}: {sentences} sentences, {words} words")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

