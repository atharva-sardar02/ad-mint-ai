"""
Scene Generator Orchestrator for Master Mode.

Coordinates Scene Writer, Scene Critic, and Scene Cohesor to produce detailed scenes.
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.services.master_mode.schemas import (
    ScenesGenerationResult,
    SceneData,
    CohesionAnalysis
)
from app.services.master_mode.scene_writer import write_scene
from app.services.master_mode.scene_critic import critique_scene
from app.services.master_mode.scene_cohesor import check_cohesion

logger = logging.getLogger(__name__)


def _extract_scene_count_from_story(story: str) -> int:
    """Extract number of scenes from story Scene Breakdown section."""
    # Look for patterns like "### Scene 1:", "### Scene 2:", etc.
    scene_matches = re.findall(r'###\s*Scene\s+(\d+)', story, re.IGNORECASE)
    if scene_matches:
        return max(int(num) for num in scene_matches)
    
    # Fallback: count "Scene" mentions in Scene Breakdown section
    scene_breakdown_match = re.search(
        r'##\s*Scene Breakdown.*?(?=##|\Z)',
        story,
        re.DOTALL | re.IGNORECASE
    )
    if scene_breakdown_match:
        section = scene_breakdown_match.group(0)
        scene_count = len(re.findall(r'\bscene\s+\d+\b', section, re.IGNORECASE))
        if scene_count > 0:
            return scene_count
    
    # Default to 4 scenes (AIDA standard)
    logger.warning("Could not extract scene count from story, defaulting to 4")
    return 4


async def generate_scenes_from_story(
    story: str,
    max_iterations_per_scene: int = 3,
    max_cohesor_iterations: int = 2,
    trace_dir: Optional[Path] = None,
    expected_scene_count: Optional[int] = None
) -> ScenesGenerationResult:
    """
    Generate detailed scenes from a complete story.
    
    Workflow:
    1. For each scene: Writer → Critic → iterate (up to max_iterations_per_scene)
    2. After all scenes: Cohesor checks cohesion → Writer revises based on feedback
    
    Args:
        story: Complete story from Story Director
        max_iterations_per_scene: Max iterations per scene (default: 3)
        max_cohesor_iterations: Max cohesion review iterations (default: 2)
        trace_dir: Optional directory to save traces
        expected_scene_count: Expected number of scenes (from Story Director calculation)
        
    Returns:
        ScenesGenerationResult with all scenes and cohesion analysis
    """
    logger.info(f"Starting scene generation from story (max_iter={max_iterations_per_scene}, story_len={len(story)})")
    
    # Initialize trace directory
    if trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)
        (trace_dir / "story.md").write_text(story, encoding="utf-8")
    
    # Extract number of scenes from story
    extracted_count = _extract_scene_count_from_story(story)
    
    # Use expected scene count if provided (from Story Director), otherwise use extracted
    if expected_scene_count:
        total_scenes = expected_scene_count
        logger.info(f"Using expected scene count from Story Director: {total_scenes} scenes")
        if extracted_count != expected_scene_count:
            logger.warning(f"Extracted scene count ({extracted_count}) differs from expected ({expected_scene_count}). Using expected count.")
    else:
        total_scenes = extracted_count
        logger.info(f"Detected {total_scenes} scenes in story")
    
    completed_scenes: List[Dict[str, Any]] = []
    conversation_history: List[Dict[str, Any]] = []
    total_iterations = 0
    
    # Phase 1: Write each scene with critic feedback
    for scene_num in range(1, total_scenes + 1):
        logger.info(f"\n=== Processing Scene {scene_num}/{total_scenes} ===")
        
        iteration = 0
        approved = False
        current_feedback = None
        scene_content = None
        final_critique = None
        
        while iteration < max_iterations_per_scene and not approved:
            iteration += 1
            total_iterations += 1
            
            logger.info(f"[Scene {scene_num}] Iteration {iteration}/{max_iterations_per_scene}")
            
            # Scene Writer writes/revises
            scene_content = await write_scene(
                story=story,
                scene_number=scene_num,
                total_scenes=total_scenes,
                previous_scenes=completed_scenes,
                feedback=current_feedback
            )
            
            # Save to trace
            if trace_dir:
                (trace_dir / f"scene_{scene_num}_iteration_{iteration}_draft.md").write_text(
                    scene_content, encoding="utf-8"
                )
            
            # Scene Critic evaluates
            critique = await critique_scene(
                scene=scene_content,
                story_context=story,
                scene_number=scene_num,
                previous_scenes=completed_scenes
            )
            
            final_critique = critique
            
            # Save critique to trace
            if trace_dir:
                (trace_dir / f"scene_{scene_num}_iteration_{iteration}_critique.json").write_text(
                    json.dumps(critique.model_dump(), indent=2), encoding="utf-8"
                )
            
            logger.info(
                f"[Scene {scene_num}] Iteration {iteration} - "
                f"Status: {critique.approval_status}, Score: {critique.overall_score:.1f}/100"
            )
            
            # Record conversation
            conversation_history.append({
                "agent": "scene_writer",
                "scene_number": scene_num,
                "iteration": iteration,
                "content": scene_content,
                "timestamp": datetime.now().isoformat()
            })
            conversation_history.append({
                "agent": "scene_critic",
                "scene_number": scene_num,
                "iteration": iteration,
                "content": critique.model_dump(),
                "timestamp": datetime.now().isoformat()
            })
            
            # Check approval
            if critique.approval_status == "approved":
                approved = True
                logger.info(f"[Scene {scene_num}] Approved at iteration {iteration}")
            else:
                # Prepare feedback for next iteration
                current_feedback = (
                    f"Critique: {critique.critique}\n\n"
                    f"Improvements needed:\n" + "\n".join(f"- {imp}" for imp in critique.improvements) + "\n\n"
                    f"Priority fixes:\n" + "\n".join(f"- {fix}" for fix in critique.priority_fixes)
                )
        
        # Add completed scene
        scene_data = {
            "scene_number": scene_num,
            "content": scene_content,
            "iterations": iteration,
            "final_critique": final_critique,
            "approved": approved
        }
        completed_scenes.append(scene_data)
        
        logger.info(f"[Scene {scene_num}] Completed with {iteration} iterations (approved={approved})")
    
    # Phase 2: Cohesion review and revisions
    logger.info(f"\n=== Phase 2: Cohesion Review ===")
    
    cohesor_iteration = 0
    cohesion_approved = False
    final_cohesion_analysis = None
    
    while cohesor_iteration < max_cohesor_iterations and not cohesion_approved:
        cohesor_iteration += 1
        total_iterations += 1
        
        logger.info(f"[Cohesor] Iteration {cohesor_iteration}/{max_cohesor_iterations}")
        
        # Check cohesion
        cohesion_result = await check_cohesion(story, completed_scenes)
        final_cohesion_analysis = cohesion_result
        
        # Save to trace
        if trace_dir:
            (trace_dir / f"cohesion_iteration_{cohesor_iteration}_analysis.json").write_text(
                json.dumps(cohesion_result.model_dump(), indent=2), encoding="utf-8"
            )
        
        logger.info(f"[Cohesor] Cohesion score: {cohesion_result.overall_cohesion_score:.1f}/100")
        
        # Record conversation
        conversation_history.append({
            "agent": "scene_cohesor",
            "iteration": cohesor_iteration,
            "content": cohesion_result.model_dump(),
            "timestamp": datetime.now().isoformat()
        })
        
        # Check approval
        if cohesion_result.overall_cohesion_score >= 80:
            cohesion_approved = True
            logger.info(f"[Cohesor] Cohesion approved at iteration {cohesor_iteration}")
        else:
            # Revise scenes based on feedback
            logger.info(f"[Cohesor] Revising scenes based on feedback")
            
            for scene_num_str, feedback_list in cohesion_result.scene_specific_feedback.items():
                scene_num = int(scene_num_str)
                if feedback_list:
                    feedback_text = "\n".join(f"- {fb}" for fb in feedback_list)
                    
                    # Scene Writer revises
                    revised_scene = await write_scene(
                        story=story,
                        scene_number=scene_num,
                        total_scenes=total_scenes,
                        previous_scenes=completed_scenes,
                        feedback=f"Cohesion feedback:\n{feedback_text}"
                    )
                    
                    # Update scene
                    completed_scenes[scene_num - 1]["content"] = revised_scene
                    
                    if trace_dir:
                        (trace_dir / f"scene_{scene_num}_cohesor_revision_{cohesor_iteration}.md").write_text(
                            revised_scene, encoding="utf-8"
                        )
    
    # Create final result
    final_scenes = [
        SceneData(
            scene_number=s["scene_number"],
            content=s["content"],
            iterations=s["iterations"],
            final_critique=s["final_critique"],
            approved=s["approved"]
        )
        for s in completed_scenes
    ]
    
    # Save final scenes
    if trace_dir:
        final_scenes_text = "\n\n".join([s.content for s in final_scenes])
        (trace_dir / "final_scenes.md").write_text(final_scenes_text, encoding="utf-8")
        
        # Save summary
        summary = {
            "total_scenes": total_scenes,
            "total_iterations": total_iterations,
            "cohesion_score": final_cohesion_analysis.overall_cohesion_score if final_cohesion_analysis else 0,
            "timestamp": datetime.now().isoformat()
        }
        (trace_dir / "scene_generation_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    
    logger.info(f"\n=== Scene Generation Complete ===")
    logger.info(f"Total scenes: {total_scenes}")
    logger.info(f"Total iterations: {total_iterations}")
    logger.info(f"Final cohesion score: {final_cohesion_analysis.overall_cohesion_score if final_cohesion_analysis else 0:.1f}/100")
    
    result = ScenesGenerationResult(
        original_story=story,
        total_scenes=total_scenes,
        scenes=final_scenes,
        cohesion_score=final_cohesion_analysis.overall_cohesion_score if final_cohesion_analysis else 0,
        cohesion_analysis=final_cohesion_analysis or CohesionAnalysis(overall_cohesion_score=0),
        conversation_history=conversation_history,
        total_iterations=total_iterations
    )
    
    return result


