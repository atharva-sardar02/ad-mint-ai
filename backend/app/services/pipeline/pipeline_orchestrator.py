"""
Unified orchestrator: Stage 1 → Stage 2 → Stage 3 (Option C)

Generates video-ready 5-scene cinematic paragraphs from:
- user_prompt
- optional user_scent_notes
- optional brand style JSON (from Story 10.2)
- optional product style JSON (from Story 10.2)
"""

import time
import logging
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.pipeline.pipeline_option_c import (
    LLMClient,
    run_stage1_blueprint,
    run_stage2_scent_profile,
)
from app.services.pipeline.stage3_scene_assembler import run_stage3_scene_assembler

logger = logging.getLogger(__name__)


async def generate_video_prompt(
    user_prompt: str,
    user_scent_notes: Optional[str] = None,
    product_image_id: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Optional[Session] = None,
    *,
    reference_image_path: str = "{{REFERENCE_IMAGE_PATH}}",
    reference_image_usage: str = "inspiration for mood and composition",
    style_tone: str = "cinematic, TikTok-ready, emotionally vivid",
) -> Dict[str, Any]:
    """
    Full 3-stage pipeline orchestrator (Option C):

    Stage 1: GPT-4 Blueprint (5-scene TikTok-style ad)
    Stage 2: GPT-4 Scent-to-Cinematic Profile
    Stage 3: GPT-4 Cinematic Scene Assembler (with optional brand/product style JSON)

    Args:
        user_prompt: User's text prompt for video generation
        user_scent_notes: Optional scent notes from user
        product_image_id: Optional product image ID if user selected a product image
        user_id: Optional user ID for loading brand style JSON (required if db is provided)
        db: Optional database session for loading brand/product style JSON
        reference_image_path: Reference image path for Stage 1
        reference_image_usage: How reference image should be used
        style_tone: Style tone for generation

    Returns:
        {
          "stage1_blueprint": ...,
          "stage2_scent_profile": ...,
          "stage3_scenes": [scene1_text, ..., scene5_text]
        }
    """

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured in settings.")

    # Initialize LLM client
    llm = LLMClient(api_key=settings.OPENAI_API_KEY)

    user_scent_notes = user_scent_notes or ""

    # Load brand style JSON if user_id and db are provided
    brand_style_json: Optional[Dict[str, Any]] = None
    if user_id and db:
        try:
            from app.db.models.brand_style import BrandStyleFolder
            brand_folder = db.query(BrandStyleFolder).filter(
                BrandStyleFolder.user_id == user_id
            ).first()
            if brand_folder and brand_folder.extracted_style_json:
                brand_style_json = brand_folder.extracted_style_json
                logger.info(f"Loaded brand style JSON for user {user_id}")
            else:
                logger.debug(f"No brand style JSON found for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to load brand style JSON for user {user_id}: {e}. Continuing without brand style.")

    # Load product style JSON if product_image_id and db are provided
    product_style_json: Optional[Dict[str, Any]] = None
    if product_image_id and db:
        try:
            from app.db.models.uploaded_image import UploadedImage
            product_image = db.query(UploadedImage).filter(
                UploadedImage.id == product_image_id,
                UploadedImage.folder_type == "product"
            ).first()
            if product_image and product_image.extracted_product_style_json:
                product_style_json = product_image.extracted_product_style_json
                logger.info(f"Loaded product style JSON for product image {product_image_id}")
            else:
                logger.debug(f"No product style JSON found for product image {product_image_id}")
        except Exception as e:
            logger.warning(f"Failed to load product style JSON for product image {product_image_id}: {e}. Continuing without product style.")

    # STAGE 1
    logger.info("=== STAGE 1: Generating 5-scene blueprint ===")
    t0 = time.monotonic()
    try:
        stage1_blueprint = await run_stage1_blueprint(
            llm=llm,
            user_prompt=user_prompt,
            reference_image_path=reference_image_path,
            reference_image_usage=reference_image_usage,
            style_tone=style_tone,
            model="gpt-4",  # Standard GPT-4 model
        )
    except (ConnectionError, TimeoutError) as network_err:
        logger.error(f"Stage 1 network error: {network_err}")
        return {"error": "stage1_failed", "details": str(network_err)}
    except Exception as e:
        logger.exception("Stage 1 failed.")
        return {"error": "stage1_failed", "details": str(e)}
    logger.info(f"Stage 1 complete in {time.monotonic() - t0:.2f}s")

    # STAGE 2
    logger.info("=== STAGE 2: Generating scent profile ===")
    t0 = time.monotonic()
    try:
        stage2_scent_profile = await run_stage2_scent_profile(
            llm=llm,
            user_notes=user_scent_notes,
            stage1_blueprint=stage1_blueprint,
            model="gpt-4",  # Standard GPT-4 model
        )
    except (ConnectionError, TimeoutError) as network_err:
        logger.error(f"Stage 2 network error: {network_err}")
        return {"error": "stage2_failed", "details": str(network_err)}
    except Exception as e:
        logger.exception("Stage 2 failed.")
        return {"error": "stage2_failed", "details": str(e)}
    logger.info(f"Stage 2 complete in {time.monotonic() - t0:.2f}s")

    # STAGE 3
    logger.info("=== STAGE 3: Assembling final video paragraphs ===")
    if brand_style_json:
        logger.info("Brand style JSON will be incorporated into scene generation")
    if product_style_json:
        logger.info("Product style JSON will be incorporated into scene generation")
    t0 = time.monotonic()
    try:
        stage3_scenes = await run_stage3_scene_assembler(
            stage1_blueprint=stage1_blueprint,
            scent_profile=stage2_scent_profile,
            brand_style_json=brand_style_json,
            product_style_json=product_style_json,
            model="gpt-4",  # Standard GPT-4 model
        )
        if brand_style_json:
            logger.info("Brand style JSON successfully applied to scene generation")
        if product_style_json:
            logger.info("Product style JSON successfully applied to scene generation")
    except (ConnectionError, TimeoutError) as network_err:
        logger.error(f"Stage 3 network error: {network_err}")
        return {"error": "stage3_failed", "details": str(network_err)}
    except Exception as e:
        logger.exception("Stage 3 failed.")
        return {"error": "stage3_failed", "details": str(e)}
    logger.info(f"Stage 3 complete in {time.monotonic() - t0:.2f}s")

    logger.info("=== PIPELINE COMPLETE ===")

    return {
        "stage1_blueprint": stage1_blueprint.model_dump(),
        "stage2_scent_profile": stage2_scent_profile.model_dump(),
        "stage3_scenes": stage3_scenes,
    }