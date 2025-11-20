#!/usr/bin/env python3
"""
Test the unified pipeline orchestrator to generate Stage 3 output.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pipeline.pipeline_orchestrator import generate_video_prompt


async def main():
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    user_scent_notes = "lemon, bergamot"  # Optional scent notes
    
    print("=" * 80)
    print("UNIFIED PIPELINE: Stage 1 → Stage 2 → Stage 3")
    print("=" * 80)
    print(f"User Prompt: {user_prompt}")
    print(f"User Scent Notes: {user_scent_notes}")
    print("=" * 80)
    print("\n")
    
    try:
        result = await generate_video_prompt(
            user_prompt=user_prompt,
            user_scent_notes=user_scent_notes,
        )
        
        print("=" * 80)
        print("STAGE 3 OUTPUT - 5 CINEMATIC PARAGRAPHS:")
        print("=" * 80)
        print("\n")
        
        for i, paragraph in enumerate(result["stage3_scenes"], start=1):
            print(f"SCENE {i}:")
            print("-" * 80)
            print(paragraph)
            print("-" * 80)
            print()
        
        print("=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Total scenes: {len(result['stage3_scenes'])}")
        for i, p in enumerate(result["stage3_scenes"], start=1):
            sentences = p.count('.') + p.count('!') + p.count('?')
            words = len(p.split())
            print(f"Scene {i}: {sentences} sentences, {words} words")
        print("=" * 80)
        
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

