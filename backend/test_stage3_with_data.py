#!/usr/bin/env python3
"""
Generate Stage 3 using provided Stage 2 data.
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
    user_prompt = "A fresh citrus perfume that energizes your day with vibrant lemon and bergamot."
    
    print("=" * 80)
    print("GENERATING STAGE 1...")
    print("=" * 80)
    blueprint = await run_stage1_blueprint(user_prompt)
    print(f"✅ Stage 1 Complete: {blueprint.framework}, {len(blueprint.scenes)} scenes\n")
    
    # Use the provided Stage 2 data
    stage2_data = {
        "scent_profile_source": "hybrid",
        "top_notes": ["lemon", "bergamot"],
        "heart_notes": ["neroli", "jasmine", "petitgrain", "ginger"],
        "base_notes": ["vetiver", "cedarwood", "white musk", "ambroxan"],
        "lighting_cues": "Crisp linear highlights accelerate, diffused radiant glow breathes, sharp luminous streaks cross, soft layered brilliance accumulates, subtle radiant contour steadies transitions.",
        "color_palette": "Vivid cool luminosity edging toward gentle warmth, translucent whites blend with pale golds, quick silver sheens, restrained saturated accents punctuate clarity.",
        "motion_physics": "Diagonal sweeps accelerate then taper, micro-vibrations brighten edges, buoyant lift cycles upward, controlled inertia settles, repeat pulses synchronize, trajectories remain precise.",
        "surface_textures": "Microfaceted sheens glide over matte diffusion, fine-grain specular ribbons cohere, semi-translucent layers deepen, subtle anisotropic shimmer aligns, clean edges maintain definition.",
        "atmosphere_density": "Light particulate suspension with gentle compression, low turbulence corridors, breathable clarity expanding, crisp gradients forming, controlled diffusion halos, permeable intervals restoring openness.",
        "sound_motifs": "Subtle crystalline chime introduces delicate ascending shimmer; quick bright tonal sweeps follow; gentle resonant hum underpins; soft sustained shimmer lingers with overtones.",
        "emotional_register": "Invigorating, vital, dynamic, clear and uplifting; cinematic intimacy frames sensations; cool lucidity brightens edges, restrained warmth gathers softly, confidence rises without harshness."
    }
    
    print("=" * 80)
    print("USING PROVIDED STAGE 2 DATA:")
    print("=" * 80)
    print(f"Top Notes: {', '.join(stage2_data['top_notes'])}")
    print(f"Heart Notes: {', '.join(stage2_data['heart_notes'])}")
    print(f"Base Notes: {', '.join(stage2_data['base_notes'])}")
    print("✅ Stage 2 Data Validated\n")
    
    # Validate and create ScentProfile
    scent_profile = ScentProfile.model_validate(stage2_data)
    
    print("=" * 80)
    print("GENERATING STAGE 3 SCENE ASSEMBLER (GPT-5)...")
    print("=" * 80)
    print()
    
    paragraphs = await run_stage3_scene_assembler(blueprint, scent_profile)
    
    print("=" * 80)
    print("STAGE 3 OUTPUT - 5 CINEMATIC PARAGRAPHS:")
    print("=" * 80)
    print()
    
    for i, paragraph in enumerate(paragraphs, start=1):
        print(f"SCENE {i}:")
        print("-" * 80)
        print(paragraph)
        print("-" * 80)
        print()
    
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

