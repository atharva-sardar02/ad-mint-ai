#!/usr/bin/env python3
"""
Test script to show the JSON blueprint response from Stage 1 LLM.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import openai
from app.core.config import settings
from app.services.pipeline.llm_enhancement import SYSTEM_PROMPT

async def main():
    user_prompt = "The Chronos Elite is a luxury smartwatch for busy professionals. It features a 7-day battery life and advanced health tracking, allowing users to stay connected and on top of their wellness goals without constant charging."
    
    print("=" * 80)
    print("USER PROMPT:")
    print("=" * 80)
    print(user_prompt)
    print("=" * 80)
    print("\n")
    
    if not settings.OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set in environment variables")
        return
    
    print("⏳ Calling OpenAI API to generate JSON blueprint...")
    print("=" * 80)
    print("\n")
    sys.stdout.flush()
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = await async_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.5,
            max_tokens=2000,
        )
        
        raw_json = response.choices[0].message.content
        blueprint = json.loads(raw_json)
        
        print("=" * 80)
        print("JSON BLUEPRINT RESPONSE:")
        print("=" * 80)
        print(json.dumps(blueprint, indent=2, ensure_ascii=False))
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await async_client.close()

if __name__ == "__main__":
    asyncio.run(main())

