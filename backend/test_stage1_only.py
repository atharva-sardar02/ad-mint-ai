#!/usr/bin/env python3
"""
Test Stage 1 blueprint generation only.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pipeline.stage1_blueprint import run_stage1_blueprint


async def main():
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    
    print("=" * 80)
    print("STAGE 1: Generating 5-scene blueprint")
    print("=" * 80)
    print(f"User Prompt: {user_prompt}")
    print("=" * 80)
    print("\n")
    
    try:
        stage1_blueprint = await run_stage1_blueprint(
            user_prompt=user_prompt,
            model="gpt-4.1",
        )
        
        print("=" * 80)
        print("STAGE 1 OUTPUT - BLUEPRINT:")
        print("=" * 80)
        print("\n")
        
        # Pretty print the blueprint
        blueprint_dict = stage1_blueprint.model_dump()
        print(json.dumps(blueprint_dict, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Framework: {stage1_blueprint.framework}")
        print(f"Total Duration: {stage1_blueprint.total_duration_seconds}s")
        print(f"Style/Tone: {stage1_blueprint.style_tone}")
        print(f"Number of scenes: {len(stage1_blueprint.scenes)}")
        print("\nScenes:")
        for scene in stage1_blueprint.scenes:
            print(f"  Scene {scene.scene_number}: {scene.stage} ({scene.duration_seconds}s)")
            print(f"    Visual: {scene.scene_description.visual}")
            print(f"    Action: {scene.scene_description.action}")
            print(f"    Camera: {scene.scene_description.camera}")
            print(f"    Lighting: {scene.scene_description.lighting}")
            print(f"    Mood: {scene.scene_description.mood}")
            print(f"    Product Usage: {scene.scene_description.product_usage}")
            print(f"    Sound Design: {scene.sound_design}")
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

