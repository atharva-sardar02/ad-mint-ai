"""
Multi-Stage Story-Driven Pipeline Orchestrator

Orchestrates the complete 4-stage workflow:
- Stage 0: Template Selection (AI-powered)
- Stage 1: Story Generation (narrative & script)
- Stage 2: Scene Division (timing & details)
- Stage 3: Visual Specification (image generation prompts)
"""

import logging
from typing import Dict, Any, Optional

from app.services.pipeline.template_selector import select_template_with_override
from app.services.pipeline.story_generator import generate_story
from app.services.pipeline.scene_divider import divide_into_scenes
from app.services.pipeline.storyboard_planner import plan_storyboard_from_scenes

logger = logging.getLogger(__name__)


async def generate_multi_stage_storyboard(
    user_prompt: str,
    target_duration: int = 15,
    template_override: Optional[str] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Execute complete 4-stage story-driven storyboard generation.
    
    This is the NEW multi-stage approach that generates better narratives
    through structured storytelling.
    
    Args:
        user_prompt: User's advertisement prompt
        target_duration: Target total duration in seconds
        template_override: Optional manual template selection (overrides AI)
        max_retries: Maximum retry attempts per stage
    
    Returns:
        dict: Complete storyboard with all stage outputs
            {
                "stage_0_template_selection": {...},
                "stage_1_story": {...},
                "stage_2_scenes": {...},
                "stage_3_storyboard": {...},
                "final_storyboard": {...}  // Ready for image/video generation
            }
    """
    logger.info("=" * 80)
    logger.info("🚀 MULTI-STAGE STORY-DRIVEN PIPELINE STARTED")
    logger.info(f"   User Prompt: {user_prompt}")
    logger.info(f"   Target Duration: {target_duration}s")
    logger.info(f"   Template Override: {template_override or 'None (AI will select)'}")
    logger.info("=" * 80)
    
    result = {
        "user_prompt": user_prompt,
        "target_duration": target_duration,
        "workflow": "multi_stage_story_driven",
        "stages": {}
    }
    
    try:
        # ========================================================================
        # STAGE 0: Template Selection
        # ========================================================================
        logger.info("")
        logger.info("📋 STAGE 0: Template Selection")
        logger.info("-" * 80)
        
        template_selection = await select_template_with_override(
            user_prompt=user_prompt,
            template_override=template_override,
            max_retries=max_retries
        )
        
        selected_template_id = template_selection["selected_template"]
        confidence = template_selection.get("confidence", "N/A")
        reasoning = template_selection.get("reasoning", "N/A")
        
        logger.info(f"✅ Template Selected: {selected_template_id}")
        logger.info(f"   Confidence: {confidence}")
        logger.info(f"   Reasoning: {reasoning}")
        
        result["stage_0_template_selection"] = template_selection
        result["stages"]["stage_0"] = {
            "name": "Template Selection",
            "status": "completed",
            "selected_template": selected_template_id,
            "confidence": confidence
        }
        
        # ========================================================================
        # STAGE 1: Story Generation
        # ========================================================================
        logger.info("")
        logger.info("📖 STAGE 1: Story Generation")
        logger.info("-" * 80)
        
        story = await generate_story(
            user_prompt=user_prompt,
            template_id=selected_template_id,
            target_duration=target_duration,
            max_retries=max_retries
        )
        
        story_title = story.get("story_title", "Untitled")
        logline = story.get("narrative", {}).get("logline", "N/A")
        
        logger.info(f"✅ Story Generated: \"{story_title}\"")
        logger.info(f"   Logline: {logline}")
        
        result["stage_1_story"] = story
        result["stages"]["stage_1"] = {
            "name": "Story Generation",
            "status": "completed",
            "story_title": story_title,
            "template_used": selected_template_id
        }
        
        # ========================================================================
        # STAGE 2: Scene Division
        # ========================================================================
        logger.info("")
        logger.info("🎬 STAGE 2: Scene Division")
        logger.info("-" * 80)
        
        scenes_data = await divide_into_scenes(
            story=story,
            template_id=selected_template_id,
            target_duration=target_duration,
            max_retries=max_retries
        )
        
        num_scenes = scenes_data.get("number_of_scenes", len(scenes_data.get("scenes", [])))
        total_duration = scenes_data.get("total_duration", 0)
        
        logger.info(f"✅ Scenes Divided: {num_scenes} scenes")
        logger.info(f"   Total Duration: {total_duration}s (target: {target_duration}s)")
        
        result["stage_2_scenes"] = scenes_data
        result["stages"]["stage_2"] = {
            "name": "Scene Division",
            "status": "completed",
            "num_scenes": num_scenes,
            "total_duration": total_duration
        }
        
        # ========================================================================
        # STAGE 3: Visual Specification
        # ========================================================================
        logger.info("")
        logger.info("🎨 STAGE 3: Visual Specification")
        logger.info("-" * 80)
        
        storyboard = await plan_storyboard_from_scenes(
            story=story,
            scenes_data=scenes_data,
            target_duration=target_duration,
            max_retries=max_retries
        )
        
        num_storyboard_scenes = len(storyboard.get("scenes", []))
        
        logger.info(f"✅ Visual Storyboard Generated: {num_storyboard_scenes} scenes with detailed prompts")
        logger.info(f"   - image_generation_prompt: Main reference image")
        logger.info(f"   - start_image_prompt: First frame")
        logger.info(f"   - end_image_prompt: Last frame")
        
        result["stage_3_storyboard"] = storyboard
        result["stages"]["stage_3"] = {
            "name": "Visual Specification",
            "status": "completed",
            "num_scenes": num_storyboard_scenes
        }
        
        # ========================================================================
        # Final Assembly
        # ========================================================================
        logger.info("")
        logger.info("🎯 FINAL: Storyboard Ready for Image/Video Generation")
        logger.info("-" * 80)
        
        # The final storyboard is ready for image generation and video generation
        result["final_storyboard"] = storyboard
        result["workflow_status"] = "completed"
        
        logger.info(f"✅ Complete Storyboard Generated:")
        logger.info(f"   - Template: {selected_template_id}")
        logger.info(f"   - Story: \"{story_title}\"")
        logger.info(f"   - Scenes: {num_scenes}")
        logger.info(f"   - Duration: {total_duration}s")
        logger.info(f"   - Ready for: Image Generation → Video Generation")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("🎉 MULTI-STAGE STORY-DRIVEN PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error(f"❌ MULTI-STAGE PIPELINE FAILED: {e}")
        logger.error("=" * 80)
        
        # Mark as failed
        result["workflow_status"] = "failed"
        result["error"] = str(e)
        
        raise


async def generate_storyboard_legacy(
    user_prompt: str,
    reference_image_path: Optional[str] = None,
    target_duration: int = 15,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Execute legacy single-stage storyboard generation (for backward compatibility).
    
    This is the OLD approach that does everything in one LLM call.
    Use generate_multi_stage_storyboard() for better results.
    
    Args:
        user_prompt: User's advertisement prompt
        reference_image_path: Optional reference image
        target_duration: Target total duration in seconds
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Storyboard plan (legacy format)
    """
    from app.services.pipeline.storyboard_planner import plan_storyboard
    
    logger.info("⚠️  Using LEGACY single-stage storyboard generation")
    logger.info("   (Consider using multi-stage workflow for better narratives)")
    
    storyboard = await plan_storyboard(
        user_prompt=user_prompt,
        reference_image_path=reference_image_path,
        target_duration=target_duration,
        max_retries=max_retries
    )
    
    return {
        "workflow": "legacy_single_stage",
        "final_storyboard": storyboard,
        "workflow_status": "completed"
    }

