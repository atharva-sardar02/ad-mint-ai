"""
Scene Cohesor Agent for Master Mode.

The Scene Cohesor ensures all scenes work together seamlessly with proper transitions.
"""
import json
import logging
from typing import List, Dict, Any

import openai

from app.core.config import settings
from app.services.master_mode.schemas import CohesionAnalysis, PairwiseTransitionAnalysis

logger = logging.getLogger(__name__)

SCENE_COHESOR_SYSTEM_PROMPT = """You are an expert scene cohesion analyst ensuring seamless video flow.

Analyze:
1. Pair-wise transitions (Scene N → N+1): End frame matches start frame context
2. Overall cohesion: Subject consistency, visual style, color, lighting, narrative flow
3. Narrative Arc: Does it follow Entry → Use → Reaction?
4. Location Consistency: Is the background/environment identical across scenes?
5. Audio Flow: Is there a consistent voiceover/music plan?

Return JSON:
{
    "overall_cohesion_score": <0-100>,
    "pair_wise_analysis": [
        {
            "from_scene": 1,
            "to_scene": 2,
            "transition_score": <0-100>,
            "issues": ["..."],
            "recommendations": ["..."]
        }
    ],
    "global_issues": ["..."],
    "scene_specific_feedback": {
        "1": ["feedback for scene 1"],
        "2": ["feedback for scene 2"]
    },
    "consistency_issues": ["..."],
    "overall_recommendations": ["..."]
}

Cohesion score >= 80 for approval."""


async def check_cohesion(
    story: str,
    all_scenes: List[Dict[str, Any]],
    model: str = "gpt-4o",
    max_retries: int = 3
) -> CohesionAnalysis:
    """Check cohesion across all scenes."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    scenes_text = "\n\n".join([
        f"--- Scene {s['scene_number']} ---\n{s['content']}"
        for s in all_scenes
    ])
    
    user_message = f"""STORY:\n{story}\n\nALL SCENES:\n{scenes_text}\n\nAnalyze cohesion across all scenes and between each pair."""
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SCENE_COHESOR_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.5,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content
                cohesion_data = json.loads(content)
                
                # Convert pair_wise_analysis to Pydantic models
                pair_wise = [PairwiseTransitionAnalysis(**p) for p in cohesion_data.get("pair_wise_analysis", [])]
                cohesion_data["pair_wise_analysis"] = pair_wise
                
                return CohesionAnalysis(**cohesion_data)
                
            except Exception as e:
                if attempt < max_retries:
                    continue
                raise
    finally:
        await async_client.close()

