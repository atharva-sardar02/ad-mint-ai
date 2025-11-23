"""
Wrapper for Master Mode story generation with SSE progress streaming.
"""
import logging
from typing import List, Optional
from app.services.master_mode.story_generator import generate_story_iterative as _generate_story_iterative
from app.services.master_mode.scene_generator import generate_scenes_from_story as _generate_scenes_from_story
from app.services.master_mode.schemas import StoryGenerationResult, ScenesGenerationResult
from app.api.routes.master_mode_progress import send_llm_interaction

logger = logging.getLogger(__name__)


async def generate_story_iterative_with_streaming(
    user_prompt: str,
    generation_id: str,
    max_iterations: int = 3,
    reference_image_paths: Optional[List[str]] = None,
    brand_name: Optional[str] = None,
    target_duration: Optional[int] = None
) -> StoryGenerationResult:
    """
    Wrapper around story generation that streams LLM interactions to SSE.
    """
    logger.info(f"[Streaming] Starting story generation with streaming for {generation_id}")
    
    # Call the original function
    result = await _generate_story_iterative(
        user_prompt=user_prompt,
        max_iterations=max_iterations,
        reference_image_paths=reference_image_paths,
        brand_name=brand_name,
        target_duration=target_duration
    )
    
    # Stream the conversation history retroactively
    # (In production, you'd integrate streaming directly into the agents)
    for entry in result.conversation_history:
        # Convert to dict if it's a Pydantic model
        if hasattr(entry, 'model_dump'):
            entry_dict = entry.model_dump()
        else:
            entry_dict = entry
            
        agent_name = "Story Director" if entry_dict["role"] == "director" else "Story Critic"
        content = entry_dict["content"]
        
        if entry_dict["role"] == "director":
            # Director sends story draft
            await send_llm_interaction(
                generation_id=generation_id,
                agent=agent_name,
                interaction_type="response",
                content=content.get("story_draft", ""),
                metadata={
                    "iteration": entry_dict["iteration"],
                    "word_count": len(content.get("story_draft", "").split())
                }
            )
        else:
            # Critic sends critique
            critique_text = f"""**Score: {content['overall_score']}/100**
**Status: {content['approval_status']}**

**Critique:**
{content['critique']}

**Strengths:**
{chr(10).join('- ' + s for s in content.get('strengths', []))}

**Improvements Needed:**
{chr(10).join('- ' + i for i in content.get('improvements', []))}

**Priority Fixes:**
{chr(10).join('- ' + f for f in content.get('priority_fixes', []))}
"""
            await send_llm_interaction(
                generation_id=generation_id,
                agent=agent_name,
                interaction_type="response",
                content=critique_text,
                metadata={
                    "iteration": entry_dict["iteration"],
                    "score": content['overall_score'],
                    "status": content['approval_status']
                }
            )
    
    return result


async def generate_scenes_with_streaming(
    story: str,
    generation_id: str,
    max_iterations_per_scene: int = 3,
    max_cohesor_iterations: int = 2,
    expected_scene_count: Optional[int] = None
) -> ScenesGenerationResult:
    """
    Wrapper around scene generation that streams LLM interactions to SSE.
    """
    logger.info(f"[Streaming] Starting scene generation with streaming for {generation_id}")
    
    # Call the original function
    result = await _generate_scenes_from_story(
        story=story,
        max_iterations_per_scene=max_iterations_per_scene,
        max_cohesor_iterations=max_cohesor_iterations,
        expected_scene_count=expected_scene_count
    )
    
    # Stream the conversation history
    for entry in result.conversation_history:
        # Convert to dict if it's a Pydantic model
        if hasattr(entry, 'model_dump'):
            entry_dict = entry.model_dump()
        else:
            entry_dict = entry
            
        agent_name = entry_dict["agent"].replace("_", " ").title()
        content = entry_dict["content"]
        
        if entry_dict["agent"] == "writer":
            # Scene Writer sends scene draft
            await send_llm_interaction(
                generation_id=generation_id,
                agent=f"{agent_name} (Scene {entry_dict.get('scene_number', '?')})",
                interaction_type="response",
                content=content.get("scene_content", content.get("content", "")),
                metadata={
                    "scene_number": entry_dict.get("scene_number"),
                    "iteration": entry_dict["iteration"]
                }
            )
        elif entry_dict["agent"] == "critic":
            # Scene Critic sends critique
            critique_text = f"""**Score: {content.get('overall_score', 'N/A')}/100**
**Status: {content.get('approval_status', 'N/A')}**

**Critique:**
{content.get('critique', '')}

**Strengths:**
{chr(10).join('- ' + s for s in content.get('strengths', []))}

**Improvements:**
{chr(10).join('- ' + i for i in content.get('improvements', []))}
"""
            await send_llm_interaction(
                generation_id=generation_id,
                agent=f"{agent_name} (Scene {entry_dict.get('scene_number', '?')})",
                interaction_type="response",
                content=critique_text,
                metadata={
                    "scene_number": entry_dict.get("scene_number"),
                    "iteration": entry_dict["iteration"],
                    "score": content.get('overall_score')
                }
            )
        elif entry_dict["agent"] == "cohesor":
            # Scene Cohesor sends cohesion analysis
            cohesion_text = f"""**Overall Cohesion Score: {content.get('overall_cohesion_score', 'N/A')}/100**

**Global Issues:**
{chr(10).join('- ' + issue for issue in content.get('global_issues', []))}

**Overall Recommendations:**
{chr(10).join('- ' + rec for rec in content.get('overall_recommendations', []))}

**Pairwise Transitions:**
"""
            for pair in content.get('pair_wise_analysis', []):
                cohesion_text += f"\n- Scene {pair['from_scene']} → {pair['to_scene']}: {pair['transition_score']}/100"
            
            await send_llm_interaction(
                generation_id=generation_id,
                agent=agent_name,
                interaction_type="response",
                content=cohesion_text,
                metadata={
                    "iteration": entry_dict["iteration"],
                    "overall_score": content.get('overall_cohesion_score')
                }
            )
    
    return result

