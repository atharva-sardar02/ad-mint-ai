#!/usr/bin/env python3
"""
Test Stage 2 scent profile generation using Stage 1 output.
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
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    user_scent_notes = "lemon, bergamot"
    
    print("=" * 80)
    print("STAGE 1: Generating 5-scene blueprint")
    print("=" * 80)
    print(f"User Prompt: {user_prompt}")
    print("=" * 80)
    print("\n")
    
    try:
        # Generate Stage 1
        stage1_blueprint = await run_stage1_blueprint(
            user_prompt=user_prompt,
            model="gpt-4.1",
        )
        
        print("✓ Stage 1 complete!")
        print(f"  Framework: {stage1_blueprint.framework}")
        print(f"  Scenes: {len(stage1_blueprint.scenes)}")
        print("\n")
        
        # Generate Stage 2
        print("=" * 80)
        print("STAGE 2: Generating scent physics profile")
        print("=" * 80)
        print(f"User Scent Notes: {user_scent_notes}")
        print("=" * 80)
        print("\n")
        
        stage2_scent_profile = await run_stage2_scent_profile(
            user_notes=user_scent_notes,
            stage1_blueprint=stage1_blueprint,
            model="gpt-5",
        )
        
        print("=" * 80)
        print("STAGE 2 OUTPUT - SCENT PROFILE:")
        print("=" * 80)
        print("\n")
        
        # Pretty print the scent profile
        profile_dict = stage2_scent_profile.model_dump()
        print(json.dumps(profile_dict, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Scent Profile Source: {stage2_scent_profile.scent_profile_source}")
        print(f"\nNotes:")
        print(f"  Top Notes: {', '.join(stage2_scent_profile.top_notes)}")
        print(f"  Heart Notes: {', '.join(stage2_scent_profile.heart_notes)}")
        print(f"  Base Notes: {', '.join(stage2_scent_profile.base_notes)}")
        print(f"\nCinematic Physics:")
        print(f"  Lighting Cues: {stage2_scent_profile.lighting_cues}")
        print(f"  Color Palette: {stage2_scent_profile.color_palette}")
        print(f"  Motion Physics: {stage2_scent_profile.motion_physics}")
        print(f"  Surface Textures: {stage2_scent_profile.surface_textures}")
        print(f"  Atmosphere Density: {stage2_scent_profile.atmosphere_density}")
        print(f"  Sound Motifs: {stage2_scent_profile.sound_motifs}")
        print(f"  Emotional Register: {stage2_scent_profile.emotional_register}")
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

