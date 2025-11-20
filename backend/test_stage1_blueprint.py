#!/usr/bin/env python3
"""
Test script to generate Stage 1 blueprint and Stage 2 scent profile for a user prompt.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pipeline.stage1_blueprint import run_stage1_blueprint
from app.services.pipeline.stage2_scent_profile import run_stage2_scent_profile


async def main():
    # User prompt
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    
    print("=" * 80)
    print("USER PROMPT:")
    print("=" * 80)
    print(user_prompt)
    print("=" * 80)
    print("\n")
    
    print("=" * 80)
    print("GENERATING STAGE 1 BLUEPRINT...")
    print("=" * 80)
    print("\n")
    sys.stdout.flush()
    
    try:
        blueprint = await run_stage1_blueprint(user_prompt)
        
        print("=" * 80)
        print("STAGE 1 BLUEPRINT OUTPUT:")
        print("=" * 80)
        print("\n")
        
        # Convert to dict for pretty printing
        blueprint_dict = blueprint.model_dump()
        print(json.dumps(blueprint_dict, indent=2, ensure_ascii=False))
        
        print("\n")
        print("=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Framework: {blueprint.framework}")
        print(f"Total Duration: {blueprint.total_duration_seconds} seconds")
        print(f"Number of Scenes: {len(blueprint.scenes)}")
        print(f"Reference Image Path: {blueprint.reference_image_path}")
        print(f"Reference Image Usage: {blueprint.reference_image_usage}")
        print(f"Style & Tone: {blueprint.style_tone}")
        print("=" * 80)
        
        # Now run Stage 2
        print("\n")
        print("=" * 80)
        print("GENERATING STAGE 2 SCENT PROFILE...")
        print("=" * 80)
        print("\n")
        sys.stdout.flush()
        
        scent_profile = await run_stage2_scent_profile(user_prompt, blueprint)
        
        print("=" * 80)
        print("STAGE 2 SCENT PROFILE OUTPUT:")
        print("=" * 80)
        print("\n")
        
        # Convert to dict for pretty printing
        scent_profile_dict = scent_profile.model_dump()
        print(json.dumps(scent_profile_dict, indent=2, ensure_ascii=False))
        
        print("\n")
        print("=" * 80)
        print("STAGE 2 SUMMARY:")
        print("=" * 80)
        print(f"Scent Profile Source: {scent_profile.scent_profile_source}")
        print(f"Top Notes: {', '.join(scent_profile.top_notes)}")
        print(f"Heart Notes: {', '.join(scent_profile.heart_notes)}")
        print(f"Base Notes: {', '.join(scent_profile.base_notes)}")
        print(f"Lighting Cues: {scent_profile.lighting_cues}")
        print(f"Color Palette: {scent_profile.color_palette}")
        print(f"Motion Physics: {scent_profile.motion_physics}")
        print(f"Surface Textures: {scent_profile.surface_textures}")
        print(f"Atmosphere Density: {scent_profile.atmosphere_density}")
        print(f"Sound Motifs: {scent_profile.sound_motifs}")
        print(f"Emotional Register: {scent_profile.emotional_register}")
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

