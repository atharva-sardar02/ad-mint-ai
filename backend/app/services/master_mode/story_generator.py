"""
Master Mode Story Generator - Main Orchestrator.

Manages the iterative loop between Story Director and Story Critic agents.
Maintains conversation history and context throughout iterations.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.services.master_mode.schemas import (
    StoryGenerationResult,
    IterationData,
    ConversationEntry,
    CritiqueResult
)
from app.services.master_mode.story_director import generate_story_draft
from app.services.master_mode.story_critic import critique_story

logger = logging.getLogger(__name__)


async def generate_story_iterative(
    user_prompt: str,
    max_iterations: int = 3,
    reference_image_paths: Optional[List[str]] = None,
    brand_name: Optional[str] = None,
    trace_dir: Optional[Path] = None,
    director_model: str = "gpt-4o",
    critic_model: str = "gpt-4o"
) -> StoryGenerationResult:
    """
    Generate a story through iterative collaboration between Story Director and Story Critic.
    
    Args:
        user_prompt: The original user prompt describing the advertisement
        max_iterations: Maximum number of iteration rounds (default: 3)
        reference_image_paths: Optional list of paths to reference images (person, product, etc.)
        brand_name: Optional brand name to feature in the advertisement
        trace_dir: Optional directory to save trace files for debugging
        director_model: OpenAI model for Story Director (default: gpt-4o)
        critic_model: OpenAI model for Story Critic (default: gpt-4o)
        
    Returns:
        StoryGenerationResult with final story, iteration history, and metadata
    """
    logger.info(
        f"Starting iterative story generation "
        f"(max_iterations={max_iterations}, prompt_length={len(user_prompt)}, "
        f"reference_images={len(reference_image_paths) if reference_image_paths else 0}, "
        f"brand_name={brand_name or 'None'})"
    )
    
    # Initialize trace directory if provided
    if trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)
        (trace_dir / "00_original_prompt.txt").write_text(user_prompt, encoding="utf-8")
    
    # Initialize conversation history
    conversation_history: List[ConversationEntry] = []
    iteration_history: List[IterationData] = []
    
    # Track current story and feedback
    current_story = None
    current_feedback = None
    final_approval_status = "needs_revision"
    final_score = 0.0
    
    # Iterative loop
    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n=== Iteration {iteration}/{max_iterations} ===")
        
        # Step 1: Story Director generates/revises story
        logger.info("[Orchestrator] Calling Story Director...")
        
        # Prepare feedback for director (if not first iteration)
        feedback_text = None
        if current_feedback:
            feedback_parts = [
                f"Critique: {current_feedback.critique}",
                "\nStrengths to maintain:",
                *[f"- {s}" for s in current_feedback.strengths],
                "\nImprovements needed:",
                *[f"- {imp}" for imp in current_feedback.improvements],
                "\nPriority fixes:",
                *[f"- {fix}" for fix in current_feedback.priority_fixes]
            ]
            feedback_text = "\n".join(feedback_parts)
        
        # Convert conversation history to dict format for director/critic
        history_dict = [
            {
                "role": entry.role,
                "iteration": entry.iteration,
                "content": entry.content
            }
            for entry in conversation_history
        ]
        
        story_draft = await generate_story_draft(
            user_prompt=user_prompt,
            feedback=feedback_text,
            conversation_history=history_dict,
            reference_image_paths=reference_image_paths,
            brand_name=brand_name,
            model=director_model
        )
        
        current_story = story_draft
        
        # Save story draft to trace
        if trace_dir:
            (trace_dir / f"{iteration*2-1:02d}_director_iteration_{iteration}.md").write_text(
                story_draft, encoding="utf-8"
            )
        
        # Add to conversation history
        conversation_history.append(ConversationEntry(
            role="director",
            iteration=iteration,
            content={"story_draft": story_draft}
        ))
        
        logger.info(f"[Orchestrator] Story Director completed ({len(story_draft)} characters)")
        
        # Step 2: Story Critic evaluates the story
        logger.info("[Orchestrator] Calling Story Critic...")
        
        critique_result = await critique_story(
            story_draft=story_draft,
            user_prompt=user_prompt,
            conversation_history=history_dict,
            model=critic_model
        )
        
        current_feedback = critique_result
        final_score = critique_result.overall_score
        final_approval_status = critique_result.approval_status
        
        # Save critique to trace
        if trace_dir:
            critique_text = f"""APPROVAL STATUS: {critique_result.approval_status}
OVERALL SCORE: {critique_result.overall_score:.1f}/100

CRITIQUE:
{critique_result.critique}

STRENGTHS:
{chr(10).join('- ' + s for s in critique_result.strengths)}

IMPROVEMENTS NEEDED:
{chr(10).join('- ' + imp for imp in critique_result.improvements)}

PRIORITY FIXES:
{chr(10).join('- ' + fix for fix in critique_result.priority_fixes)}
"""
            (trace_dir / f"{iteration*2:02d}_critic_iteration_{iteration}.txt").write_text(
                critique_text, encoding="utf-8"
            )
        
        # Add to conversation history
        critique_dict = critique_result.model_dump()
        conversation_history.append(ConversationEntry(
            role="critic",
            iteration=iteration,
            content=critique_dict
        ))
        
        # Create iteration data
        iteration_data = IterationData(
            iteration=iteration,
            story_draft=story_draft,
            critique=critique_result
        )
        iteration_history.append(iteration_data)
        
        logger.info(
            f"[Orchestrator] Story Critic completed - "
            f"Status: {final_approval_status}, Score: {final_score:.1f}/100"
        )
        
        # Early stopping: If critic approves, we're done
        if critique_result.approval_status == "approved":
            logger.info(f"[Orchestrator] Story approved! Stopping early at iteration {iteration}")
            break
        
        # Prepare feedback for next iteration
        if iteration < max_iterations:
            logger.info(f"[Orchestrator] Preparing for next iteration...")
    
    # Determine final story (use last story draft)
    final_story = current_story if current_story else user_prompt
    
    # Save final story to trace
    if trace_dir:
        (trace_dir / "05_final_story.md").write_text(final_story, encoding="utf-8")
        
        # Save summary
        summary = {
            "original_prompt": user_prompt,
            "final_approval_status": final_approval_status,
            "final_score": final_score,
            "total_iterations": len(iteration_history),
            "iterations": [
                {
                    "iteration": it.iteration,
                    "score": it.critique.overall_score,
                    "approval_status": it.critique.approval_status
                }
                for it in iteration_history
            ],
            "timestamp": datetime.now().isoformat()
        }
        (trace_dir / "story_generation_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    
    logger.info(f"\n=== Story Generation Complete ===")
    logger.info(f"Final status: {final_approval_status}")
    logger.info(f"Final score: {final_score:.1f}/100")
    logger.info(f"Total iterations: {len(iteration_history)}")
    
    # Create and return result
    result = StoryGenerationResult(
        original_prompt=user_prompt,
        final_story=final_story,
        approval_status=final_approval_status,
        final_score=final_score,
        iterations=iteration_history,
        total_iterations=len(iteration_history),
        conversation_history=conversation_history
    )
    
    return result

