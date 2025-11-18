"""
Simple prompt generator with consistency markers.
Uses OpenAI to generate prompts and extract consistency markers for cohesive video/image generation.
"""
import logging
from typing import Optional

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a creative director generating prompts for video and image generation.

Given a user's prompt, create:
1. A detailed, cinematic prompt optimized for video/image generation
2. Consistency markers that will be used across all scenes/images to maintain visual cohesion

CONSISTENCY MARKERS should include:
- style: Visual style (e.g., "cinematic", "modern minimalist", "warm documentary")
- color_palette: Color scheme (e.g., "warm earth tones", "cool blues and grays", "vibrant primary colors")
- lighting: Lighting description (e.g., "soft natural window light", "dramatic side lighting", "even studio lighting")
- composition: Composition style (e.g., "rule of thirds", "centered framing", "dynamic angles")
- mood: Emotional tone (e.g., "energetic", "calm professional", "optimistic")

Output format (JSON):
{
  "prompt": "Detailed cinematic prompt for the scene",
  "consistency_markers": {
    "style": "string",
    "color_palette": "string",
    "lighting": "string",
    "composition": "string",
    "mood": "string"
  }
}

Keep prompts concise but descriptive (1-2 sentences, 20-50 words).
Markers should be short phrases (2-5 words each).
"""


async def generate_prompt_with_markers(
    user_prompt: str,
    scene_description: Optional[str] = None,
    max_retries: int = 3,
) -> tuple[str, dict]:
    """
    Generate an optimized prompt and consistency markers from user input.
    
    Args:
        user_prompt: User's original prompt
        scene_description: Optional scene-specific description
        max_retries: Maximum retry attempts
    
    Returns:
        tuple: (optimized_prompt, consistency_markers_dict)
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    # Use best available OpenAI model
    model = "gpt-4o"  # Best model for prompt generation
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Build user message
    if scene_description:
        user_content = f"User prompt: {user_prompt}\n\nScene: {scene_description}"
    else:
        user_content = f"User prompt: {user_prompt}"
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Prompt Generator] Attempt {attempt}/{max_retries}")
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=500,
                )
                
                content = response.choices[0].message.content
                
                # Parse JSON
                import json
                try:
                    result = json.loads(content)
                except json.JSONDecodeError as e:
                    if attempt < max_retries:
                        logger.warning(f"Invalid JSON response, retrying... {e}")
                        continue
                    raise
                
                # Extract prompt and markers
                optimized_prompt = result.get("prompt", user_prompt)
                consistency_markers = result.get("consistency_markers", {})
                
                logger.info(f"Generated prompt: {optimized_prompt[:80]}...")
                logger.debug(f"Consistency markers: {consistency_markers}")
                
                return optimized_prompt, consistency_markers
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Prompt Generator Error] {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 20))
                    continue
        
        raise RuntimeError(f"Prompt generation failed after retries: {last_error}")
    
    finally:
        await async_client.close()


async def generate_scene_prompts_with_markers(
    user_prompt: str,
    num_scenes: int = 4,
    max_retries: int = 3,
) -> list[tuple[str, dict]]:
    """
    Generate prompts and markers for multiple scenes.
    
    Args:
        user_prompt: User's original prompt
        num_scenes: Number of scenes to generate
        max_retries: Maximum retry attempts
    
    Returns:
        list: List of (prompt, consistency_markers) tuples, one per scene
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    model = "gpt-4o"
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = """You are a creative director generating prompts for a multi-scene video.

Given a user's prompt, create {num_scenes} scene prompts that:
1. Follow an AIDA structure (Attention, Interest, Desire, Action)
2. Share the SAME consistency markers across all scenes for visual cohesion
3. Each scene has a unique prompt but maintains the same visual style

Output format (JSON):
{{
  "consistency_markers": {{
    "style": "string",
    "color_palette": "string",
    "lighting": "string",
    "composition": "string",
    "mood": "string"
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "aida_stage": "Attention",
      "prompt": "Detailed prompt for scene 1"
    }},
    ...
  ]
}}
""".format(num_scenes=num_scenes)
    
    user_content = f"User prompt: {user_prompt}\n\nGenerate {num_scenes} scene prompts with shared consistency markers."
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Multi-Scene Prompt Generator] Attempt {attempt}/{max_retries}")
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=2000,
                )
                
                content = response.choices[0].message.content
                
                import json
                try:
                    result = json.loads(content)
                except json.JSONDecodeError as e:
                    if attempt < max_retries:
                        logger.warning(f"Invalid JSON response, retrying... {e}")
                        continue
                    raise
                
                # Extract shared markers and scene prompts
                consistency_markers = result.get("consistency_markers", {})
                scenes = result.get("scenes", [])
                
                if len(scenes) != num_scenes:
                    if attempt < max_retries:
                        logger.warning(f"Expected {num_scenes} scenes, got {len(scenes)}, retrying...")
                        continue
                    raise ValueError(f"Expected {num_scenes} scenes, got {len(scenes)}")
                
                # Return list of (prompt, markers) tuples
                scene_prompts = [
                    (scene.get("prompt", ""), consistency_markers)
                    for scene in sorted(scenes, key=lambda x: x.get("scene_number", 0))
                ]
                
                logger.info(f"Generated {len(scene_prompts)} scene prompts with shared markers")
                
                return scene_prompts
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Multi-Scene Prompt Generator Error] {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 20))
                    continue
        
        raise RuntimeError(f"Multi-scene prompt generation failed after retries: {last_error}")
    
    finally:
        await async_client.close()

