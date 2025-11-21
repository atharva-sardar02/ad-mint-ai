"""
Scene Critic Agent for Master Mode.

The Scene Critic evaluates individual scenes for quality and production readiness.
"""
import json
import logging
from typing import List, Dict, Any

import openai

from app.core.config import settings
from app.services.master_mode.schemas import SceneCritique

logger = logging.getLogger(__name__)

SCENE_CRITIC_SYSTEM_PROMPT = """You are an expert scene critic evaluating video-ready scene specifications.

Evaluate on 100-point scale:
1. Visual Detail Sufficiency (30 pts): Detailed enough for video generation?
2. Cinematographic Specifications (20 pts): Complete camera/lighting specs?
3. Subject Consistency (20 pts): Maintains identity from story?
4. Continuity (15 pts): Connects to previous/next scenes?
5. Scene Quality (10 pts): Engaging, well-paced?
6. Production Readiness (5 pts): Unambiguous?

Return JSON:
{
    "approval_status": "approved" | "needs_revision",
    "overall_score": <0-100>,
    "critique": "<detailed feedback>",
    "strengths": ["..."],
    "improvements": ["..."],
    "priority_fixes": ["..."]
}

Approval: score >= 85 AND all critical elements present."""


async def critique_scene(
    scene: str,
    story_context: str,
    scene_number: int,
    previous_scenes: List[Dict[str, Any]],
    model: str = "gpt-4o",
    max_retries: int = 3
) -> SceneCritique:
    """Critique a scene."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Convert previous scenes to serializable format (remove Pydantic objects)
    serializable_scenes = []
    for scene_data in previous_scenes:
        serializable_scene = {
            "scene_number": scene_data.get("scene_number"),
            "content": scene_data.get("content"),
            "iterations": scene_data.get("iterations"),
            "approved": scene_data.get("approved")
        }
        serializable_scenes.append(serializable_scene)
    
    user_message = f"""STORY CONTEXT:\n{story_context}\n\nSCENE {scene_number} TO EVALUATE:\n{scene}\n\nPREVIOUS SCENES:\n{json.dumps(serializable_scenes, indent=2)}\n\nEvaluate this scene."""
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SCENE_CRITIC_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.6,
                    max_tokens=1500
                )
                
                content = response.choices[0].message.content
                critique_data = json.loads(content)
                return SceneCritique(**critique_data)
                
            except Exception as e:
                if attempt < max_retries:
                    continue
                raise
    finally:
        await async_client.close()

