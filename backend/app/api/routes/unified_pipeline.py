"""
Unified Pipeline API Routes

Implements POST /api/v2/generate endpoint for unified pipeline.
Consolidates 4 separate pipeline endpoints into 1 unified system.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.unified_pipeline import GenerationRequest, GenerationResponse
from app.services.unified_pipeline.orchestrator import create_generation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2", tags=["unified-pipeline"])


@router.post("/generate", response_model=GenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_video(
    request: GenerationRequest,
    db: Session = Depends(get_db)
) -> GenerationResponse:
    """
    Unified pipeline generation endpoint (Story 1.1 AC-6).

    Consolidates Master Mode, Interactive, Original, and CLI pipelines into single endpoint.

    **Request Body:**
    - prompt: User prompt for video generation (10-5000 characters)
    - framework: Optional advertising framework (AIDA, PAS, FAB, custom)
    - brand_assets: Optional brand images (product_images, logo, character_images)
    - config: Optional configuration overrides
    - interactive: Interactive mode (waits for user feedback) or automated
    - session_id: Optional session ID for resuming
    - parallel_variants: Number of parallel variants for A/B testing

    **Response:**
    - generation_id: Unique generation ID
    - session_id: WebSocket session ID
    - websocket_url: WebSocket URL for real-time updates (if interactive)
    - status: Current status (pending, story, references, scenes, videos, completed, failed)
    - message: Human-readable status message

    **Examples:**

    Interactive mode with brand assets:
    ```json
    {
      "prompt": "Create a 30-second ad for eco-friendly water bottle",
      "framework": "AIDA",
      "brand_assets": {
        "product_images": ["s3://bucket/product1.jpg"],
        "logo": "s3://bucket/logo.png"
      },
      "interactive": true
    }
    ```

    Automated mode (CLI):
    ```json
    {
      "prompt": "Athletic shoe ad targeting runners",
      "framework": "PAS",
      "interactive": false
    }
    ```

    **Error Responses:**
    - 400 Bad Request: Invalid input (missing prompt, invalid framework)
    - 401 Unauthorized: Missing/invalid JWT token (TODO: add auth)
    - 429 Too Many Requests: Rate limit exceeded (10 generations/hour)
    - 500 Internal Server Error: Unexpected error

    **Status Codes:**
    - 202 Accepted: Generation started, processing asynchronously
    """
    try:
        logger.info(f"Received generation request: prompt_length={len(request.prompt)}, framework={request.framework}, interactive={request.interactive}")

        # TODO: Add authentication check (Story 1.1 focuses on core architecture)
        # TODO: Add rate limiting (10 generations/hour per user)

        # Create generation via orchestrator
        response = await create_generation(request, db)

        logger.info(f"✓ Generation created: {response.generation_id}")
        return response

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}
        )


@router.get("/generate/{generation_id}", response_model=dict)
async def get_generation_status(
    generation_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get generation status by ID.

    Args:
        generation_id: Generation UUID

    Returns:
        Generation status and outputs (if available)

    **Status Codes:**
    - 200 OK: Generation found
    - 404 Not Found: Generation ID not found
    """
    from app.db.models.generation import Generation

    generation = db.query(Generation).filter(Generation.id == generation_id).first()

    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Generation {generation_id} not found"}
        )

    return {
        "generation_id": generation.id,
        "status": generation.status,
        "current_step": generation.current_step,
        "prompt": generation.prompt,
        "framework": generation.framework,
        "brand_assets": generation.brand_assets,
        "reference_images": generation.reference_images,
        "scenes": generation.scenes,
        "video_clips": generation.video_clips,
        "video_url": generation.video_url,
        "config": generation.config,
        "created_at": generation.created_at.isoformat() if generation.created_at else None,
        "completed_at": generation.completed_at.isoformat() if generation.completed_at else None,
        "error_message": generation.error_message
    }
