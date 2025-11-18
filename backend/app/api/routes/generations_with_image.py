"""
Additional generation endpoints that support reference image upload.
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.generation import Generation
from app.db.session import get_db
from app.schemas.generation import GenerateResponse
from app.services.coherence_settings import apply_defaults
from app.services.pipeline.progress_tracking import update_generation_progress
from app.api.routes.generations import process_generation  # reuse existing pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generations"])


@router.post("/generate-with-image", status_code=status.HTTP_202_ACCEPTED)
async def create_generation_with_image(
    request: Request,
    prompt: str = Form(..., min_length=10, max_length=2000),  # Match /api/generate endpoint
    image: UploadFile = File(...),
    model: Optional[str] = Form(None),
    target_duration: Optional[int] = Form(None, ge=9, le=60),  # Target total video duration in seconds (default: 15). LLM will decide number of scenes and duration per scene (max 7s per scene)
    refinement_instructions: Optional[str] = Form(None),  # JSON string of refinement instructions
    brand_name: Optional[str] = Form(None, max_length=50),  # Optional brand name
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerateResponse:
    """
    Start a new video generation from a user prompt and a reference image.

    This endpoint mirrors /api/generate but accepts multipart/form-data with:
    - prompt: text prompt
    - image: JPG/PNG reference image (max 10MB)

    It reuses the standard process_generation pipeline and only passes the
    reference image path into the LLM stage for additional context.
    """
    # Basic content-type validation
    if image.content_type not in ("image/jpeg", "image/jpg", "image/png"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_IMAGE_TYPE",
                    "message": "Only JPG and PNG images are allowed",
                }
            },
        )

    contents = await image.read()
    max_size_bytes = 10 * 1024 * 1024  # 10 MB
    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "IMAGE_TOO_LARGE",
                    "message": "Image size must be less than 10MB",
                }
            },
        )

    # Apply default coherence settings (match /api/generate behavior)
    coherence_settings = apply_defaults(None)
    coherence_settings_dict = coherence_settings.model_dump()

    # Create Generation record
    generation = Generation(
        user_id=current_user.id,
        title=None,
        prompt=prompt,
        status="pending",
        progress=0,
        current_step="Initializing",
        coherence_settings=coherence_settings_dict,
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)

    generation_id = generation.id

    # Save image to temp directory
    image_dir = Path("output") / "temp" / "images" / generation_id
    image_dir.mkdir(parents=True, exist_ok=True)
    ext = ".jpg" if image.content_type in ("image/jpeg", "image/jpg") else ".png"
    image_path = image_dir / f"reference_image{ext}"
    image_path.write_bytes(contents)

    # Kick off standard pipeline but with image_path passed into LLM stage
    # Pass model if specified (e.g., "openai/sora-2" for Sora-2)
    if model:
        logger.info(f"[{generation_id}] Using specified model: {model}")
    else:
        logger.info(f"[{generation_id}] No model specified, will use default fallback chain")
    
    # Parse refinement_instructions if provided (JSON string)
    refinement_instructions_dict = None
    if refinement_instructions:
        try:
            import json
            refinement_instructions_dict = json.loads(refinement_instructions)
        except json.JSONDecodeError:
            logger.warning(f"[{generation_id}] Invalid JSON in refinement_instructions, ignoring")
    
    background_tasks.add_task(
        process_generation,
        generation_id,
        prompt,
        model,  # Pass the selected model (e.g., "openai/sora-2")
        target_duration,  # Pass target_duration if specified
        True,   # use_llm
        str(image_path),
        refinement_instructions_dict,  # Pass refinement instructions
        brand_name,  # Pass brand name if provided
    )

    # Initial status update
    update_generation_progress(
        db=db,
        generation_id=generation_id,
        progress=0,
        current_step="Initializing with reference image",
        status="pending",
    )

    return GenerateResponse(
        generation_id=generation_id,
        status="pending",
        message="Video generation with reference image started",
    )


