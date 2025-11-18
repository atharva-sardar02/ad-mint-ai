#!/usr/bin/env python3
"""
Test script to show exact LLM response and Sora prompts for a given user prompt.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import openai
import json
from app.core.config import settings
from app.services.pipeline.llm_enhancement import enhance_prompt_with_llm, _build_sora_scene_prompt, SYSTEM_PROMPT
from app.services.pipeline.scene_planning import plan_scenes

async def main():
    user_prompt = "The Chronos Elite is a luxury smartwatch for busy professionals. It features a 7-day battery life and advanced health tracking, allowing users to stay connected and on top of their wellness goals without constant charging."
    
    print("=" * 80)
    print("USER PROMPT:")
    print("=" * 80)
    print(user_prompt)
    print("=" * 80)
    print("\n")
    
    # Step 1: Get LLM enhancement - capture raw response
    print("=" * 80)
    print("CALLING GPT-4 FOR LLM ENHANCEMENT...")
    print("=" * 80)
    print("\n")
    
    # Call OpenAI directly to get raw response
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=2000
    )
    
    raw_json = response.choices[0].message.content
    
    print("=" * 80)
    print("EXACT GPT-4 LLM RESPONSE (RAW JSON):")
    print("=" * 80)
    print(raw_json)
    print("=" * 80)
    print("\n")
    
    # Now get the processed version
    ad_spec = await enhance_prompt_with_llm(user_prompt)
    
    # The LLM response is logged, but let's also show the structured output
    print("=" * 80)
    print("LLM ENHANCED OUTPUT (AdSpecification):")
    print("=" * 80)
    print(json.dumps(ad_spec.model_dump(), indent=2))
    print("=" * 80)
    print("\n")
    
    # Step 2: Scene planning
    print("=" * 80)
    print("SCENE PLANNING...")
    print("=" * 80)
    print("\n")
    
    scene_plan = plan_scenes(ad_spec, target_duration=15)
    
    # Step 3: Show exact Sora prompts for each scene
    print("=" * 80)
    print("EXACT SORA-2 PROMPTS FOR EACH SCENE:")
    print("=" * 80)
    print("\n")
    
    for i, scene in enumerate(scene_plan.scenes, start=1):
        print(f"{'=' * 80}")
        print(f"SCENE {i} ({scene.scene_type}) - Duration: {scene.duration}s")
        print(f"{'=' * 80}")
        print(f"EXACT PROMPT TO BE SENT TO SORA-2:")
        print(f"{'-' * 80}")
        print(scene.visual_prompt)
        print(f"{'-' * 80}")
        print(f"Overlay Text: {scene.text_overlay.text if scene.text_overlay else 'None'}")
        print(f"{'=' * 80}")
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())

