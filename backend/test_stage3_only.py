#!/usr/bin/env python3
"""
Test script to generate Stage 3 using fresh Stage 1 and Stage 2.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pipeline.stage1_blueprint import run_stage1_blueprint
from app.services.pipeline.stage2_scent_profile import run_stage2_scent_profile
from app.services.pipeline.stage3_scene_assembler import run_stage3_scene_assembler


async def main():
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    
    print("=" * 80)
    print("GENERATING STAGE 1...")
    print("=" * 80)
    blueprint = await run_stage1_blueprint(user_prompt)
    print(f"✅ Stage 1: {blueprint.framework}, {len(blueprint.scenes)} scenes\n")
    
    print("=" * 80)
    print("GENERATING STAGE 2...")
    print("=" * 80)
    scent_profile = await run_stage2_scent_profile(user_prompt, blueprint)
    print(f"✅ Stage 2: {scent_profile.scent_profile_source}\n")
    
    print("=" * 80)
    print("GENERATING STAGE 3...")
    print("=" * 80)
    paragraphs = await run_stage3_scene_assembler(blueprint, scent_profile)
    
    print("\n" + "=" * 80)
    print("STAGE 3 OUTPUT - 5 CINEMATIC PARAGRAPHS:")
    print("=" * 80 + "\n")
    
    for i, paragraph in enumerate(paragraphs, start=1):
        print(f"SCENE {i}:")
        print("-" * 80)
        print(paragraph)
        print("-" * 80)
        print()


if __name__ == "__main__":
    asyncio.run(main())

