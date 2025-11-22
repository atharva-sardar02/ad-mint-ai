#!/usr/bin/env python3
"""
Test script to generate SORA 2 prompts using the updated 3-stage pipeline.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.pipeline.llm_enhancement import generate_sora_script

async def main():
    # User prompt - you can change this
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    
    print("=" * 80)
    print("USER PROMPT:")
    print("=" * 80)
    print(user_prompt)
    print("=" * 80)
    print("\n")
    
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set in environment variables")
        return
    
    print("⏳ Running 3-stage pipeline (this may take 30-60 seconds)...")
    print("  Stage 1: Blueprint Generator")
    print("  Stage 2: Olfactory Intelligence Engine")
    print("  Stage 3: Sora Scene Assembler")
    print("=" * 80)
    print("\n")
    sys.stdout.flush()
    
    try:
        result = await generate_sora_script(
            user_prompt=user_prompt,
            reference_image_path="{{REFERENCE_IMAGE_PATH}}",
            reference_image_usage="inspiration for mood and composition",
            style_tone="cinematic, intimate, perfume-focused"
        )
        
        # Display Blueprint
        print("=" * 80)
        print("STAGE 1: BLUEPRINT (Semantic Fragments)")
        print("=" * 80)
        print(json.dumps(result["blueprint"], indent=2, ensure_ascii=False))
        print("\n")
        
        # Display Scent Profile
        print("=" * 80)
        print("STAGE 2: SCENT PROFILE (Olfactory Intelligence)")
        print("=" * 80)
        print(json.dumps(result["scent_profile"], indent=2, ensure_ascii=False))
        print("\n")
        
        # Display Final SORA 2 Prompts
        print("=" * 80)
        print("=" * 80)
        print("STAGE 3: FINAL SORA-2 PROMPTS (Cinematic Paragraphs)")
        print("=" * 80)
        print("=" * 80)
        print("\n")
        
        for i, prompt in enumerate(result["scenes_text"], start=1):
            print(f"{'=' * 80}")
            print(f"SCENE {i}:")
            print(f"{'=' * 80}")
            print(f"\n{prompt}\n")
            print(f"{'=' * 80}")
            print("\n")
        
        print("=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Total scenes: {len(result['scenes_text'])}")
        print(f"Framework: {result['blueprint'].get('framework', 'N/A')}")
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

