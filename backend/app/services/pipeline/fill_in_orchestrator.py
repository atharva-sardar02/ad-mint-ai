"""
Fill-in-the-Blank Multi-Stage Pipeline Orchestrator

This orchestrator uses structured templates with explicit fields that the LLM fills.
Provides maximum control and consistency by converting the LLM into a form-filler.
"""

import logging
from typing import Dict, Any, Optional

from app.services.pipeline.template_selector import select_template_with_override
from app.services.pipeline.template_filler import fill_template_with_llm, validate_filled_template
from app.services.pipeline.prompt_generator_from_template import generate_storyboard_from_filled_template

logger = logging.getLogger(__name__)


async def generate_fill_in_storyboard(
    user_prompt: str,
    target_duration: int = 15,
    template_override: Optional[str] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Execute fill-in-the-blank storyboard generation.
    
    This approach uses structured templates with ~290 explicit fields that the LLM fills.
    Maximum control, zero ambiguity, perfect consistency.
    
    Args:
        user_prompt: User's advertisement prompt
        target_duration: Target total duration in seconds
        template_override: Optional manual template selection
        max_retries: Maximum retry attempts per stage
    
    Returns:
        dict: Complete storyboard with filled template and generated prompts
    """
    logger.info("=" * 80)
    logger.info("🎯 FILL-IN-THE-BLANK PIPELINE STARTED")
    logger.info(f"   User Prompt: {user_prompt}")
    logger.info(f"   Target Duration: {target_duration}s")
    logger.info(f"   Template Override: {template_override or 'None (AI will select)'}")
    logger.info("=" * 80)
    
    result = {
        "user_prompt": user_prompt,
        "target_duration": target_duration,
        "workflow": "fill_in_the_blank",
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
        # STAGE 1: Fill Template Fields
        # ========================================================================
        logger.info("")
        logger.info("📝 STAGE 1: Fill Template Fields (~290 fields)")
        logger.info("-" * 80)
        
        filled_template = await fill_template_with_llm(
            template_id=selected_template_id,
            user_prompt=user_prompt,
            target_duration=target_duration,
            max_retries=max_retries
        )
        
        story_title = filled_template.get("story", {}).get("title", "Untitled")
        unfilled_count = filled_template.get("_metadata", {}).get("unfilled_placeholders", 0)
        
        logger.info(f"✅ Template Filled: \"{story_title}\"")
        logger.info(f"   Unfilled placeholders: {unfilled_count}")
        
        # Validate filled template
        is_valid, errors = validate_filled_template(filled_template)
        if not is_valid:
            logger.warning(f"⚠️  Validation warnings: {len(errors)} issues")
            for error in errors[:5]:  # Show first 5
                logger.warning(f"   - {error}")
        else:
            logger.info("✅ Validation passed")
        
        result["stage_1_filled_template"] = filled_template
        result["stages"]["stage_1"] = {
            "name": "Fill Template Fields",
            "status": "completed",
            "story_title": story_title,
            "unfilled_count": unfilled_count,
            "validation_errors": errors if not is_valid else []
        }
        
        # ========================================================================
        # STAGE 2: Generate Prompts from Filled Fields
        # ========================================================================
        logger.info("")
        logger.info("🎨 STAGE 2: Generate Prompts (Concatenate Filled Fields)")
        logger.info("-" * 80)
        
        storyboard = generate_storyboard_from_filled_template(filled_template)
        
        num_scenes = len(storyboard.get("scenes", []))
        char_desc_len = len(storyboard.get("consistency_markers", {}).get("subject_description", ""))
        
        logger.info(f"✅ Storyboard Generated: {num_scenes} scenes")
        logger.info(f"   Character/Product description: {char_desc_len} characters")
        logger.info(f"   Ready for: Image Generation → Video Generation")
        
        result["stage_2_storyboard"] = storyboard
        result["stages"]["stage_2"] = {
            "name": "Generate Prompts",
            "status": "completed",
            "num_scenes": num_scenes,
            "subject_description_length": char_desc_len
        }
        
        # ========================================================================
        # Final Assembly
        # ========================================================================
        logger.info("")
        logger.info("🎯 FINAL: Storyboard Ready for Image/Video Generation")
        logger.info("-" * 80)
        
        result["final_storyboard"] = storyboard
        result["workflow_status"] = "completed"
        
        logger.info(f"✅ Complete Storyboard Generated:")
        logger.info(f"   - Template: {selected_template_id}")
        logger.info(f"   - Story: \"{story_title}\"")
        logger.info(f"   - Scenes: {num_scenes}")
        logger.info(f"   - Total Fields Filled: ~290")
        logger.info(f"   - Ready for: Image Generation → Video Generation")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("🎉 FILL-IN-THE-BLANK PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error(f"❌ FILL-IN-THE-BLANK PIPELINE FAILED: {e}")
        logger.error("=" * 80)
        
        result["workflow_status"] = "failed"
        result["error"] = str(e)
        
        raise

