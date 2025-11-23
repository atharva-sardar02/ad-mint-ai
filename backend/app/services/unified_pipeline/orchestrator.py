"""
Unified Pipeline Orchestrator

Main coordinator that sequences all pipeline stages (story → references → scenes → videos).
Supports both interactive mode (waits for user approval) and automated mode (headless execution).
Consolidates 4 separate pipelines into 1 unified system.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

from app.schemas.unified_pipeline import (
    GenerationRequest,
    GenerationResponse,
    PipelineConfig,
    ReferenceImage,
    ReferenceImagesReadyMessage
)
from app.services.unified_pipeline.config_loader import load_pipeline_config
from app.services.unified_pipeline.reference_stage import ReferenceStage
from app.db.models.generation import Generation
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Main pipeline orchestrator coordinating all stages.

    Implements AC-1: Single orchestrator module that coordinates story → references → scenes → videos.
    """

    def __init__(self, db: Session):
        """
        Initialize orchestrator.

        Args:
            db: Database session for Generation record tracking
        """
        self.db = db

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Main pipeline execution entry point.

        This method implements the unified pipeline flow:
        1. Load configuration with Pydantic validation (AC-4)
        2. Create Generation database record (AC-7)
        3. Execute stages based on interactive/automated mode (AC-5)
        4. Track status progression (AC-7)

        Args:
            request: Generation request with prompt, framework, brand_assets, etc.

        Returns:
            GenerationResponse with generation_id, session_id, websocket_url, status
        """
        logger.info(f"Starting unified pipeline generation: interactive={request.interactive}")

        # Step 1: Load pipeline configuration with overrides
        try:
            config = load_pipeline_config(
                name="default",
                overrides=request.config
            )
            logger.info(f"✓ Pipeline configuration loaded: {config.pipeline_name}")
        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            raise ValueError(f"Invalid pipeline configuration: {e}")

        # Step 2: Create Generation database record (AC-7)
        generation_id = str(uuid4())
        session_id = request.session_id or str(uuid4())

        generation = Generation(
            id=generation_id,
            user_id="demo-user",  # TODO: Get from auth context
            prompt=request.prompt,
            framework=request.framework,
            status="pending",
            current_step="initialization",
            brand_assets=request.brand_assets.dict() if request.brand_assets else None,
            config=config.dict(),  # Store config snapshot (AC-7)
        )

        self.db.add(generation)
        self.db.commit()
        logger.info(f"✓ Generation record created: {generation_id}")

        # Step 3: Execute pipeline based on mode (AC-5)
        if request.interactive:
            logger.info("🔄 Starting INTERACTIVE mode pipeline")
            websocket_url = f"ws://localhost:8000/ws/{session_id}"
            # Interactive mode: stages will wait for user feedback
            # This will be implemented in Story 1.5
        else:
            logger.info("🚀 Starting AUTOMATED mode pipeline")
            websocket_url = None
            # Automated mode: run all stages without user interaction
            # This will be fully implemented with stage modules

        # For MVP/Story 1.1: Return immediate response, actual execution happens in background
        # Full stage execution will be implemented in subsequent stories

        response = GenerationResponse(
            generation_id=generation_id,
            session_id=session_id,
            websocket_url=websocket_url or "",
            status="pending",
            message="Generation started. Pipeline will execute all stages."
        )

        logger.info(f"✓ Generation response prepared: {generation_id}")
        return response

    async def execute_stage(
        self,
        stage_name: str,
        generation: Generation,
        config: PipelineConfig,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute individual pipeline stage.

        Args:
            stage_name: Stage name (story, references, scenes, videos)
            generation: Generation database record
            config: Pipeline configuration
            inputs: Stage-specific inputs

        Returns:
            Dict with stage outputs
        """
        logger.info(f"Executing stage: {stage_name}")

        # Update generation status
        generation.current_step = stage_name
        generation.status = stage_name
        self.db.commit()

        # Execute stage based on stage name
        if stage_name == "references":
            # Execute reference stage (Story 1.2)
            return await self._execute_reference_stage(generation, config, inputs)
        elif stage_name == "story":
            # Story stage implementation (Story 1.1, 1.5)
            return {"status": "not_implemented", "stage": stage_name}
        elif stage_name == "scenes":
            # Scene stage implementation (Story 1.1, 1.5)
            return {"status": "not_implemented", "stage": stage_name}
        elif stage_name == "videos":
            # Video stage implementation (Story 1.3)
            return {"status": "not_implemented", "stage": stage_name}
        else:
            logger.warning(f"Unknown stage: {stage_name}")
            return {"status": "unknown_stage", "stage": stage_name}

    async def _execute_reference_stage(
        self,
        generation: Generation,
        config: PipelineConfig,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute reference stage (Story 1.2).

        Args:
            generation: Generation database record
            config: Pipeline configuration
            inputs: Dict with 'story' text and optional 'session_id' for WebSocket

        Returns:
            Dict with reference_images and consistency_context
        """
        logger.info(f"Executing reference stage for generation {generation.id}")

        # Extract inputs
        story = inputs.get("story", generation.prompt)  # Use prompt if story not yet generated
        brand_assets = generation.brand_assets  # Already stored as dict
        session_id = inputs.get("session_id")  # For WebSocket notifications

        # Convert brand_assets dict to BrandAssets schema
        from app.schemas.unified_pipeline import BrandAssets
        brand_assets_obj = BrandAssets(**brand_assets) if brand_assets else None

        # Execute reference stage
        reference_stage = ReferenceStage(config)
        reference_images = await reference_stage.execute(
            story=story,
            brand_assets=brand_assets_obj,
            generation_id=generation.id
        )

        # Build consistency context
        consistency_context = reference_stage.build_consistency_context(reference_images)

        # Store reference images in database (AC#5 JSONB storage)
        generation.reference_images = [img.dict() for img in reference_images]
        self.db.commit()

        logger.info(f"✓ Reference stage complete: {len(reference_images)} images stored")

        # Send WebSocket message if session_id provided (AC#7 Interactive Display)
        if session_id:
            try:
                from app.api.routes.websocket import manager

                # Prepare reference images data for WebSocket payload
                images_payload = [
                    {
                        "url": img.url,
                        "type": img.type,
                        "analysis": img.analysis.dict()
                    }
                    for img in reference_images
                ]

                # Create WebSocket message
                ws_message = ReferenceImagesReadyMessage(
                    payload={
                        "images": images_payload,
                        "message": "Using these 3 reference images for visual consistency across all scenes",
                        "count": len(reference_images)
                    }
                )

                # Send to session
                await manager.send_message(session_id, ws_message.dict())
                logger.info(f"✓ WebSocket message sent to session {session_id}: reference_images_ready")

            except Exception as e:
                # Don't fail the stage if WebSocket fails (non-critical)
                logger.warning(f"Failed to send WebSocket message: {e}")

        return {
            "status": "complete",
            "stage": "references",
            "reference_images": reference_images,
            "consistency_context": consistency_context
        }


async def create_generation(request: GenerationRequest, db: Session) -> GenerationResponse:
    """
    Convenience function to create a new generation.

    Args:
        request: Generation request
        db: Database session

    Returns:
        GenerationResponse
    """
    orchestrator = PipelineOrchestrator(db)
    return await orchestrator.generate(request)
