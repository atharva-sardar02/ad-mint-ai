#!/usr/bin/env python3
"""
Test script to generate Stage 3 output from Stage 1 and Stage 2 data.
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
from app.services.pipeline.llm_schemas import ScentProfile


async def main():
    # User prompt
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    
    print("=" * 80)
    print("GENERATING STAGE 1 BLUEPRINT...")
    print("=" * 80)
    print("\n")
    sys.stdout.flush()
    
    # Generate Stage 1
    blueprint = await run_stage1_blueprint(user_prompt)
    
    # Use the provided Stage 2 data
    stage2_data = {
        "scent_profile_source": "hybrid",
        "top_notes": ["lemon", "bergamot"],
        "heart_notes": ["orange blossom"],
        "base_notes": ["musk"],
        "lighting_cues": "Bright natural illumination with crisp reflective highlights that soften into warmer diffused gradients shaped by subtle shifts in ambient light.",
        "color_palette": "Luminous yellows and soft greens blended with warm transitional tones that move gently across reflective and translucent surfaces.",
        "motion_physics": "Measured glide-like camera motion paired with subtle directional airflow that creates lightly drifting particles and gentle kinetic transitions.",
        "surface_textures": "Smooth reflective glass and polished metal interacting with shifting highlights and soft shadow gradients across clean material surfaces.",
        "atmosphere_density": "Clear open air with mild diffusion and soft luminosity that maintains consistent visual clarity while allowing gradual tonal transitions.",
        "sound_motifs": "Layered ambient textures with distant soft resonance, subtle tonal movement, and gentle dispersed sound activity without environment specificity.",
        "emotional_register": "Energized, bright, and uplifting with a tempered grounded calm that supports clarity, optimism, and a sense of refreshed openness."
    }
    
    print("=" * 80)
    print("USING PROVIDED STAGE 2 DATA:")
    print("=" * 80)
    print(json.dumps(stage2_data, indent=2))
    print("=" * 80)
    print("\n")
    
    # Validate and create ScentProfile
    scent_profile = ScentProfile.model_validate(stage2_data)
    
    print("=" * 80)
    print("GENERATING STAGE 3 SCENE ASSEMBLER OUTPUT...")
    print("=" * 80)
    print("\n")
    sys.stdout.flush()
    
    # Generate Stage 3
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

