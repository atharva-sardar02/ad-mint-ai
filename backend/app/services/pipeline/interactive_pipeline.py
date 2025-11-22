"""
Interactive Pipeline Orchestrator with Pause Points

Extends the multi-stage pipeline with pause/resume functionality,
allowing users to review and refine outputs at each stage before
committing API credits to the next stage.

Key features:
- Session state persistence (Redis/PostgreSQL)
- WebSocket notifications for stage completion
- Conversational refinement at each stage
- User approval required before proceeding
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.config import settings
from app.schemas.interactive import (
    ChatMessage,
    PipelineSessionState,
)
from app.schemas.generation import Scene
from app.services.pipeline.story_generator import generate_story
from app.services.pipeline.template_selector import select_template_with_override
from app.services.pipeline.session_storage import get_session_storage
from app.services.pipeline.video_generation import generate_video_clip
from app.services.pipeline.stitching import stitch_video_clips

logger = logging.getLogger(__name__)


class InteractivePipelineOrchestrator:
    """
    Orchestrates interactive multi-stage pipeline with pause points.

    The pipeline executes stages sequentially:
    1. Story generation → pause for review → approve → continue
    2. Reference image generation → pause → approve → continue
    3. Storyboard generation → pause → approve → continue
    4. Video generation → complete

    Each pause point allows user to:
    - Review the output
    - Provide conversational feedback
    - Request regeneration with modifications
    - Approve and proceed to next stage
    """

    def __init__(self, session_ttl_hours: int = 1):
        """
        Initialize the orchestrator.

        Args:
            session_ttl_hours: Session time-to-live in hours (default: 1)
        """
        self.session_ttl_hours = session_ttl_hours
        self.storage = get_session_storage()
        self._connection_manager = None  # Lazily loaded to avoid circular imports
        logger.info(f"InteractivePipelineOrchestrator initialized (TTL: {session_ttl_hours}h)")

    async def start_pipeline(
        self,
        user_id: str,
        prompt: str,
        target_duration: int = 15,
        mode: str = "interactive",
        title: Optional[str] = None
    ) -> PipelineSessionState:
        """
        Start a new interactive pipeline session.

        Args:
            user_id: User identifier
            prompt: User's video generation prompt
            target_duration: Target video duration in seconds
            mode: Pipeline mode ('interactive' or 'auto')
            title: Optional video title

        Returns:
            PipelineSessionState: Initial session state
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.session_ttl_hours)

        session = PipelineSessionState(
            session_id=session_id,
            user_id=user_id,
            status="story",
            current_stage="Story Generation",
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            prompt=prompt,
            target_duration=target_duration,
            mode=mode,
            title=title,
            outputs={},
            conversation_history=[],
            stage_data={},
            error=None,
            error_count=0
        )

        # Save session
        await self._save_session(session)

        logger.info(f"✨ Pipeline session started: {session_id}")
        logger.info(f"   User: {user_id}")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Prompt: {prompt[:100]}...")

        # Start first stage (story generation) in background
        # In production, this would be a background task
        if mode == "auto":
            # Auto mode: run all stages without pausing
            logger.info("Auto mode: running all stages...")
            await self._run_auto_pipeline(session_id)
        else:
            # Interactive mode: generate story and wait for review
            await self._generate_story_stage(session_id)

        return session

    async def get_session(self, session_id: str) -> Optional[PipelineSessionState]:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            PipelineSessionState if found, None otherwise
        """
        session = await self._load_session(session_id)

        if session and session.expires_at < datetime.utcnow():
            logger.warning(f"Session {session_id} has expired")
            await self._delete_session(session_id)
            return None

        return session

    async def approve_stage(
        self,
        session_id: str,
        stage: str,
        notes: Optional[str] = None,
        selected_indices: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Approve current stage and transition to next stage.

        Args:
            session_id: Session identifier
            stage: Stage being approved
            notes: Optional approval notes

        Returns:
            dict: Approval result with next stage info
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != stage:
            raise ValueError(
                f"Cannot approve stage '{stage}' - current stage is '{session.status}'"
            )

        logger.info(f"✅ Stage approved: {stage} (session: {session_id})")
        if notes:
            logger.info(f"   Notes: {notes}")

        # Add approval message to conversation
        approval_msg = ChatMessage(
            type="system",
            content=f"Stage '{stage}' approved by user" + (f": {notes}" if notes else ""),
            timestamp=datetime.utcnow()
        )
        session.conversation_history.append(approval_msg)
        manual_images = None
        if stage == "story":
            manual_images = session.stage_data.pop("manual_reference_images", None)

        # Determine next stage
        stage_transitions = {
            "story": "reference_image",
            "reference_image": "storyboard",
            "storyboard": "video"
        }

        next_stage = stage_transitions.get(stage)
        if not next_stage:
            # Final stage approved - mark as complete
            session.status = "complete"
            session.current_stage = "Complete"
            await self._save_session(session)

            return {
                "session_id": session_id,
                "approved_stage": stage,
                "next_stage": "complete",
                "message": "Pipeline complete! Your video is ready."
            }

        if manual_images:
            logger.info("Manual reference images supplied; skipping automatic reference generation.")
            await self._complete_manual_reference_stage(session, manual_images)
            await self._generate_storyboard_stage(session_id)

            return {
                "session_id": session_id,
                "approved_stage": stage,
                "next_stage": "storyboard",
                "message": "Stage 'story' approved! Using your reference images to generate a storyboard..."
            }

        # Persist reference image selections if applicable
        if stage == "reference_image":
            if not selected_indices:
                images = session.outputs.get("reference_image", {}).get("images", [])
                if images:
                    selected_indices = [images[0]["index"]]
            if selected_indices:
                session.stage_data["reference_image_selected_indices"] = selected_indices
                logger.info(f"Reference image selections saved: {selected_indices}")

        # Transition to next stage
        session.status = next_stage
        session.current_stage = self._get_stage_name(next_stage)
        session.updated_at = datetime.utcnow()
        session.conversation_history = []  # Reset conversation for new stage

        await self._save_session(session)

        # Start next stage generation
        if next_stage == "reference_image":
            await self._generate_reference_image_stage(session_id)
        elif next_stage == "storyboard":
            await self._generate_storyboard_stage(session_id)
        elif next_stage == "video":
            await self._generate_video_stage(session_id)

        return {
            "session_id": session_id,
            "approved_stage": stage,
            "next_stage": next_stage,
            "message": f"Stage '{stage}' approved! {self._get_stage_message(next_stage)}"
        }

    async def regenerate_stage(
        self,
        session_id: str,
        stage: str,
        feedback: Optional[str] = None,
        modifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Regenerate current stage with user feedback.

        Args:
            session_id: Session identifier
            stage: Stage to regenerate
            feedback: User feedback text
            modifications: Structured modifications to apply

        Returns:
            dict: Regeneration result
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        if session.status != stage:
            raise ValueError(
                f"Cannot regenerate stage '{stage}' - current stage is '{session.status}'"
            )

        logger.info(f"🔄 Regenerating stage: {stage} (session: {session_id})")
        if feedback:
            logger.info(f"   Feedback: {feedback[:100]}...")
        if modifications:
            logger.info(f"   Modifications: {modifications}")

        # Add feedback to conversation
        if feedback:
            feedback_msg = ChatMessage(
                type="user",
                content=feedback,
                timestamp=datetime.utcnow(),
                metadata={"action": "regenerate_request"}
            )
            session.conversation_history.append(feedback_msg)

        # Regenerate based on stage
        if stage == "story":
            await self._generate_story_stage(session_id, modifications)
        elif stage == "reference_image":
            await self._generate_reference_image_stage(session_id, modifications)
        elif stage == "storyboard":
            await self._generate_storyboard_stage(session_id, modifications)

        session.updated_at = datetime.utcnow()
        await self._save_session(session)

        return {
            "session_id": session_id,
            "stage": stage,
            "message": f"Regenerated {stage} with your feedback",
            "regenerated": True
        }

    async def add_message(
        self,
        session_id: str,
        message: str,
        message_type: str = "user"
    ) -> ChatMessage:
        """
        Add a message to the conversation history.

        Args:
            session_id: Session identifier
            message: Message content
            message_type: Message type ('user', 'assistant', 'system')

        Returns:
            ChatMessage: Created message
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        chat_msg = ChatMessage(
            type=message_type,
            content=message,
            timestamp=datetime.utcnow()
        )

        session.conversation_history.append(chat_msg)
        session.updated_at = datetime.utcnow()
        await self._save_session(session)

        return chat_msg

    async def register_manual_reference_images(
        self,
        session_id: str,
        images: List[Dict[str, Any]],
    ) -> PipelineSessionState:
        """
        Persist user-provided reference images for later reuse.

        Args:
            session_id: Session identifier
            images: List of reference image metadata dictionaries
        """
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Normalize indexes to keep downstream UI predictable
        for idx, img in enumerate(images, start=1):
            img.setdefault("index", idx)
            img.setdefault("source", "manual")

        session.stage_data["manual_reference_images"] = images
        session.stage_data["reference_image_selected_indices"] = [img["index"] for img in images]
        session.updated_at = datetime.utcnow()

        await self._save_session(session)
        logger.info(
            "🖼️ Manual reference images registered for session %s (count=%s)",
            session_id,
            len(images),
        )
        return session

    # ========================================================================
    # Stage Generation Methods
    # ========================================================================

    async def _complete_manual_reference_stage(
        self,
        session: PipelineSessionState,
        manual_images: List[Dict[str, Any]],
    ):
        """Finalize reference image stage when user uploads their own assets."""
        session.stage_data.pop("manual_reference_images", None)
        session.stage_data["reference_image_manual"] = True
        session.stage_data["reference_image_selected_indices"] = [
            img.get("index") for img in manual_images if img.get("index") is not None
        ]

        session.outputs["reference_image"] = {
            "images": manual_images,
            "prompt_used": manual_images[0].get("prompt") if manual_images else session.prompt,
            "modifications_applied": {},
            "manual_upload": True,
        }

        session.status = "storyboard"
        session.current_stage = self._get_stage_name("storyboard")
        session.conversation_history = []
        session.updated_at = datetime.utcnow()

        await self._save_session(session)
        await self._notify_stage_complete(session.session_id, "reference_image", session.outputs["reference_image"])

    async def _generate_story_stage(
        self,
        session_id: str,
        modifications: Optional[Dict[str, Any]] = None
    ):
        """Generate story for the session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        stage_start = datetime.utcnow()
        try:
            logger.info(f"📖 Generating story for session {session_id}...")

            # Determine prompt with applied modifications
            prompt_to_use = session.prompt
            if modifications:
                prompt_to_use = self._build_story_prompt(session.prompt, modifications)

            # Select template (Stage 0)
            template_selection = await select_template_with_override(
                user_prompt=prompt_to_use,
                template_override=modifications.get("template") if modifications else None
            )

            template_id = template_selection["selected_template"]

            # Generate story (Stage 1)
            story_result = await generate_story(
                user_prompt=prompt_to_use,
                template_id=template_id,
                target_duration=session.target_duration
            )

            # Save outputs
            session.outputs["story"] = story_result
            session.outputs["template"] = template_selection
            session.stage_data["story_iterations"] = session.stage_data.get("story_iterations", 0) + 1
            if modifications:
                session.stage_data["story_last_modifications"] = modifications
                session.prompt = prompt_to_use
            duration_seconds = (datetime.utcnow() - stage_start).total_seconds()
            session.stage_data["story_last_duration_seconds"] = duration_seconds
            if isinstance(session.outputs["story"], dict):
                session.outputs["story"]["duration_seconds"] = duration_seconds
            session.updated_at = datetime.utcnow()

            await self._save_session(session)

            logger.info(f"✅ Story generated for session {session_id}")

            # Send WebSocket notification
            await self._notify_stage_complete(session_id, "story", story_result)

        except Exception as e:
            logger.error(f"❌ Story generation failed: {e}")
            session.error = str(e)
            session.error_count += 1
            await self._save_session(session)
            raise

    async def _generate_reference_image_stage(
        self,
        session_id: str,
        modifications: Optional[Dict[str, Any]] = None
    ):
        """Generate reference images for the session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        stage_start = datetime.utcnow()
        try:
            logger.info(f"🎨 Generating reference images for session {session_id}...")

            # Import here to avoid circular dependencies
            from app.services.pipeline.image_generation import generate_image
            from app.services.pipeline.image_prompt_enhancement import enhance_image_prompt

            story = session.outputs.get("story", {})
            user_prompt = session.prompt

            # Apply modifications from feedback if provided
            prompt_to_use = user_prompt
            effective_modifications = modifications or session.stage_data.get("story_last_modifications")
            if effective_modifications:
                prompt_to_use = self._build_story_prompt(user_prompt, effective_modifications)

            # Enhance the image prompt
            logger.info("Enhancing reference image prompt...")
            enhanced_prompt_result = await enhance_image_prompt(
                base_prompt=prompt_to_use,
                story_context=story.get("narrative", ""),
                target_style="cinematic"
            )

            # Generate 2-3 reference images for user to choose from
            output_dir = f"{settings.OUTPUT_BASE_DIR}/interactive/{session_id}/reference_images"
            enhanced_prompt_text = enhanced_prompt_result.get("enhanced_prompt", prompt_to_use)

            try:
                from app.services.pipeline.image_quality_scoring import score_image as score_image_fn
            except Exception:
                score_image_fn = None

            async def generate_and_score(index: int) -> Optional[Dict[str, Any]]:
                scene_number = index + 1
                try:
                    image_path = await generate_image(
                        prompt=enhanced_prompt_text,
                        output_dir=output_dir,
                        generation_id=f"{session_id}_ref",
                        scene_number=scene_number
                    )

                    quality_score = None
                    quality_metrics = None
                    if score_image_fn:
                        try:
                            scores = await score_image_fn(image_path, enhanced_prompt_text)
                            quality_metrics = scores
                            quality_score = scores.get("overall", None)
                        except Exception as score_err:
                            logger.warning(f"Quality scoring failed for image {scene_number}: {score_err}")

                    logger.info(f"✅ Reference image {scene_number}/3 generated")
                    return {
                        "index": scene_number,
                        "path": image_path,
                        "url": f"/api/v1/outputs/interactive/{session_id}/reference_images/{Path(image_path).name}",
                        "prompt": enhanced_prompt_text,
                        "quality_score": quality_score,
                        "quality_metrics": quality_metrics,
                        "source": "auto",
                    }
                except Exception as gen_err:
                    logger.error(f"Failed to generate reference image {scene_number}: {gen_err}")
                    return None

            tasks = [asyncio.create_task(generate_and_score(i)) for i in range(3)]
            results = await asyncio.gather(*tasks)
            reference_images = [img for img in results if img]

            if not reference_images:
                raise RuntimeError("Failed to generate any reference images")

            # Save outputs
            session.outputs["reference_image"] = {
                "images": reference_images,
                "prompt_used": enhanced_prompt_result.get("enhanced_prompt", prompt_to_use),
                "modifications_applied": modifications or {},
            }
            session.stage_data["reference_image_iterations"] = session.stage_data.get("reference_image_iterations", 0) + 1
            duration_seconds = (datetime.utcnow() - stage_start).total_seconds()
            session.stage_data["reference_image_last_duration_seconds"] = duration_seconds
            session.outputs["reference_image"]["duration_seconds"] = duration_seconds
            session.updated_at = datetime.utcnow()

            await self._save_session(session)

            logger.info(f"✅ Reference images generated for session {session_id}")

            # Send WebSocket notification
            await self._notify_stage_complete(session_id, "reference_image", session.outputs["reference_image"])

        except Exception as e:
            logger.error(f"❌ Reference image generation failed: {e}")
            session.error = str(e)
            session.error_count += 1
            await self._save_session(session)
            raise

    async def _generate_storyboard_stage(
        self,
        session_id: str,
        modifications: Optional[Dict[str, Any]] = None
    ):
        """Generate storyboard for the session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        stage_start = datetime.utcnow()
        try:
            logger.info(f"🎬 Generating storyboard for session {session_id}...")

            # Import here to avoid circular dependencies
            from app.services.pipeline.storyboard_generator import generate_storyboard
            from app.services.pipeline.image_generation import generate_image

            story = session.outputs.get("story", {})
            reference_images = session.outputs.get("reference_image", {}).get("images", [])
            selected_indices = session.stage_data.get("reference_image_selected_indices")
            if selected_indices:
                filtered_images = [img for img in reference_images if img.get("index") in selected_indices]
                if filtered_images:
                    reference_images = filtered_images
                else:
                    logger.warning(
                        f"Selected reference image indices {selected_indices} not found, using all images."
                    )
            user_prompt = session.prompt

            # Get reference image paths for storyboard generation
            reference_image_paths = [img["path"] for img in reference_images if img.get("path")]

            # Apply modifications if regenerating specific clips
            affected_indices = None
            if modifications and "affected_indices" in modifications:
                affected_indices = modifications["affected_indices"]
                logger.info(f"Regenerating specific clips: {affected_indices}")

            # Generate storyboard
            logger.info("Generating storyboard from story and reference images...")
            storyboard_prompt = user_prompt
            narrative_context = story.get("narrative")
            if narrative_context:
                narrative_text = narrative_context if isinstance(narrative_context, str) else json.dumps(narrative_context, ensure_ascii=False)
                storyboard_prompt = f"{user_prompt}\n\nStory context:\n{narrative_text}"
            if modifications:
                storyboard_prompt = f"{storyboard_prompt}\n\nApply these adjustments:\n{json.dumps(modifications, ensure_ascii=False)}"

            storyboard_result = await generate_storyboard(
                user_prompt=storyboard_prompt,
                reference_image_paths=reference_image_paths,
            )

            if hasattr(storyboard_result, "model_dump"):
                storyboard_payload = storyboard_result.model_dump()
            elif isinstance(storyboard_result, dict):
                storyboard_payload = storyboard_result
            else:
                storyboard_payload = json.loads(storyboard_result)

            # Generate images for each storyboard scene (clips)
            output_dir = f"{settings.OUTPUT_BASE_DIR}/interactive/{session_id}/storyboard"
            storyboard_clips: List[Dict[str, Any]] = []
            existing_clips = session.outputs.get("storyboard", {}).get("clips", [])
            existing_clip_map = {clip["clip_number"]: clip for clip in existing_clips}

            scenes = storyboard_payload.get("scenes", [])
            clip_results: Dict[int, Dict[str, Any]] = {}
            concurrency_limit = max(
                1, getattr(settings, "STORYBOARD_CLIP_CONCURRENCY", 3)
            )
            semaphore = asyncio.Semaphore(concurrency_limit)
            clip_tasks: List[asyncio.Task] = []

            async def process_clip(clip_index: int, scene: Dict[str, Any]):
                scene_prompt = scene.get("visual_prompt", "")
                logger.info(f"Generating images for clip {clip_index}...")

                async with semaphore:
                    start_task = asyncio.create_task(
                        generate_image(
                            prompt=f"{scene_prompt} (start frame)",
                            output_dir=output_dir,
                            generation_id=f"{session_id}_clip_{clip_index:03d}",
                            scene_number=None,
                        )
                    )
                    end_task = asyncio.create_task(
                        generate_image(
                            prompt=f"{scene_prompt} (end frame)",
                            output_dir=output_dir,
                            generation_id=f"{session_id}_clip_{clip_index:03d}_end",
                            scene_number=None,
                        )
                    )

                    start_frame_path, end_frame_path = await asyncio.gather(
                        start_task, end_task
                    )

                    quality_score = None
                    quality_metrics = None
                    try:
                        from app.services.pipeline.image_quality_scoring import score_image

                        scores = await score_image(start_frame_path, scene.get("visual", ""))
                        quality_metrics = scores
                        quality_score = scores.get("overall", None)
                    except Exception as e:
                        logger.warning(f"Quality scoring failed for clip {clip_index}: {e}")

                    logger.info(f"✅ Clip {clip_index}/{len(scenes)} generated")
                    return (
                        clip_index,
                        {
                            "clip_number": clip_index,
                            "scene": scene,
                            "start_frame": {
                                "path": start_frame_path,
                                "url": f"/api/v1/outputs/interactive/{session_id}/storyboard/{Path(start_frame_path).name}",
                            },
                            "end_frame": {
                                "path": end_frame_path,
                                "url": f"/api/v1/outputs/interactive/{session_id}/storyboard/{Path(end_frame_path).name}",
                            },
                            "duration": scene.get("duration", 4),
                            "voiceover": scene.get("scene_type", ""),
                            "quality_score": quality_score,
                            "quality_metrics": quality_metrics,
                        },
                    )

            for i, scene in enumerate(scenes):
                clip_index = i + 1

                # Skip clips not in affected_indices if regenerating specific ones
                if affected_indices and clip_index not in affected_indices:
                    existing_clip = existing_clip_map.get(clip_index)
                    if existing_clip:
                        clip_results[clip_index] = existing_clip
                        logger.info(f"Reusing existing clip {clip_index}")
                        continue

                clip_tasks.append(asyncio.create_task(process_clip(clip_index, scene)))

            for result in await asyncio.gather(*clip_tasks, return_exceptions=True):
                if isinstance(result, Exception):
                    logger.error(f"Storyboard clip generation task failed: {result}")
                    continue
                if result:
                    clip_index, clip_payload = result
                    clip_results[clip_index] = clip_payload

            storyboard_clips = [clip_results[idx] for idx in sorted(clip_results.keys()) if clip_results.get(idx)]

            if not storyboard_clips:
                raise RuntimeError("Failed to generate any storyboard clips")

            # Save outputs
            session.outputs["storyboard"] = {
                "clips": storyboard_clips,
                "total_clips": len(storyboard_clips),
                "storyboard_spec": storyboard_payload,
                "modifications_applied": modifications or {}
            }
            session.stage_data["storyboard_iterations"] = session.stage_data.get("storyboard_iterations", 0) + 1
            duration_seconds = (datetime.utcnow() - stage_start).total_seconds()
            session.stage_data["storyboard_last_duration_seconds"] = duration_seconds
            session.outputs["storyboard"]["duration_seconds"] = duration_seconds
            session.updated_at = datetime.utcnow()

            await self._save_session(session)

            logger.info(f"✅ Storyboard generated for session {session_id}")

            # Send WebSocket notification
            await self._notify_stage_complete(session_id, "storyboard", session.outputs["storyboard"])

        except Exception as e:
            logger.error(f"❌ Storyboard generation failed: {e}")
            session.error = str(e)
            session.error_count += 1
            await self._save_session(session)
            raise

    async def _generate_video_stage(
        self,
        session_id: str,
        modifications: Optional[Dict[str, Any]] = None
    ):
        """Generate final video for the session using Veo 3."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        storyboard = session.outputs.get("storyboard", {})
        clips = storyboard.get("clips", [])
        if not clips:
            raise RuntimeError("Cannot generate video without storyboard clips")

        stage_start = datetime.utcnow()
        try:
            logger.info(f"🎥 Generating final video for session {session_id} with Veo 3")
            video_output_dir = f"{settings.OUTPUT_BASE_DIR}/interactive/{session_id}/video"
            Path(video_output_dir).mkdir(parents=True, exist_ok=True)

            concurrency_limit = max(1, getattr(settings, "VIDEO_CLIP_CONCURRENCY", 2))
            semaphore = asyncio.Semaphore(concurrency_limit)
            clip_tasks: List[asyncio.Task] = []

            async def process_video_clip(clip: Dict[str, Any], default_index: int) -> Optional[Dict[str, Any]]:
                clip_number = clip.get("clip_number") or default_index
                scene_data = clip.get("scene", {}) or {}
                visual_prompt = (
                    scene_data.get("visual_prompt")
                    or scene_data.get("visual")
                    or storyboard.get("storyboard_spec", {}).get("visual_prompt")
                    or ""
                )

                scene_payload = Scene(
                    scene_number=clip_number or 0,
                    scene_type=scene_data.get("scene_type", "Scene"),
                    visual_prompt=visual_prompt,
                    model_prompts=scene_data.get("model_prompts", {}),
                    reference_image_path=scene_data.get("reference_image_path"),
                    text_overlay=None,
                    duration=int(clip.get("duration", 4)),
                    sound_design=scene_data.get("sound_design"),
                    transition_to_next=scene_data.get("transition_to_next", "crossfade"),
                )

                start_reference = clip.get("start_frame", {}).get("path")
                reference_images = []
                if start_reference:
                    reference_images.append(start_reference)

                async with semaphore:
                    clip_path, model_used = await generate_video_clip(
                        scene=scene_payload,
                        output_dir=video_output_dir,
                        generation_id=f"{session_id}_video",
                        scene_number=scene_payload.scene_number,
                        preferred_model="google/veo-3",
                        reference_image_path=start_reference,
                        reference_images=reference_images if reference_images else None,
                        resolution="1080p",
                        generate_audio=True,
                    )

                return {
                    "clip_number": scene_payload.scene_number,
                    "path": clip_path,
                    "url": f"/api/v1/outputs/interactive/{session_id}/video/{Path(clip_path).name}",
                    "model": model_used,
                }

            for clip in clips:
                default_index = clip.get("clip_number") or (len(clip_tasks) + 1)
                clip_tasks.append(asyncio.create_task(process_video_clip(clip, default_index)))

            clip_results: List[Dict[str, Any]] = []
            for result in await asyncio.gather(*clip_tasks, return_exceptions=True):
                if isinstance(result, Exception):
                    logger.error(f"Video clip generation failed: {result}")
                    continue
                if result:
                    clip_results.append(result)

            if not clip_results:
                raise RuntimeError("Video generation produced no clips")

            clip_results.sort(key=lambda c: c.get("clip_number") or 0)

            final_video_path = None
            final_video_url = None
            try:
                stitched_filename = f"{session_id}_final.mp4"
                stitched_path = Path(video_output_dir) / stitched_filename
                stitched_result = stitch_video_clips(
                    clip_paths=[clip["path"] for clip in clip_results],
                    output_path=str(stitched_path),
                )
                final_video_path = stitched_result
                final_video_url = f"/api/v1/outputs/interactive/{session_id}/video/{Path(stitched_result).name}"
            except Exception as stitch_err:
                logger.error(f"Video stitching failed for session {session_id}: {stitch_err}")

            duration_seconds = (datetime.utcnow() - stage_start).total_seconds()

            session.outputs["video"] = {
                "clips": clip_results,
                "model": "google/veo-3",
                "status": "completed",
                "duration_seconds": duration_seconds,
            }
            if final_video_path:
                session.outputs["video"]["final_video"] = {
                    "path": final_video_path,
                    "url": final_video_url,
                }

            session.status = "complete"
            session.current_stage = "Complete"
            session.stage_data["video_last_duration_seconds"] = duration_seconds
            session.updated_at = datetime.utcnow()
            await self._save_session(session)

            await self._notify_stage_complete(session_id, "video", session.outputs["video"])
            logger.info(f"✅ Video generation completed for session {session_id}")

        except Exception as e:
            logger.error(f"❌ Video generation failed: {e}")
            session.error = str(e)
            session.error_count += 1
            await self._save_session(session)
            raise

    async def _run_auto_pipeline(self, session_id: str):
        """Run all stages automatically without pausing (auto mode)."""
        await self._generate_story_stage(session_id)
        # Auto-approve and continue
        await self.approve_stage(session_id, "story")
        # Subsequent stages will be triggered by approve_stage

    # ========================================================================
    # Session Storage (Redis/PostgreSQL/In-Memory)
    # ========================================================================

    async def _save_session(self, session: PipelineSessionState):
        """Save session to storage (Redis/PostgreSQL/in-memory)."""
        await self.storage.save(session)
        logger.debug(f"Session saved: {session.session_id}")

    async def _load_session(self, session_id: str) -> Optional[PipelineSessionState]:
        """Load session from storage (Redis/PostgreSQL/in-memory)."""
        return await self.storage.load(session_id)

    async def _delete_session(self, session_id: str):
        """Delete session from storage (Redis/PostgreSQL/in-memory)."""
        await self.storage.delete(session_id)
        logger.debug(f"Session deleted: {session_id}")

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _get_stage_name(self, stage: str) -> str:
        """Get human-readable stage name."""
        stage_names = {
            "story": "Story Generation",
            "reference_image": "Reference Image Generation",
            "storyboard": "Storyboard Generation",
            "video": "Video Generation",
            "complete": "Complete"
        }
        return stage_names.get(stage, stage)

    def _get_stage_message(self, stage: str) -> str:
        """Get message for stage transition."""
        messages = {
            "reference_image": "Generating reference images...",
            "storyboard": "Generating storyboard...",
            "video": "Generating video...",
            "complete": "Pipeline complete!"
        }
        return messages.get(stage, f"Starting {stage}...")

    def _build_story_prompt(self, base_prompt: str, modifications: Optional[Dict[str, Any]]) -> str:
        """Merge user feedback into the story prompt."""
        if not modifications:
            return base_prompt

        parts = []
        feedback_text = modifications.get("feedback_text")
        if feedback_text:
            parts.append(f"User feedback: {feedback_text}")

        for key, value in modifications.items():
            if key == "feedback_text" or value in (None, "", []):
                continue
            parts.append(f"{key}: {value}")

        if not parts:
            return base_prompt

        modifications_text = "\n".join(str(p) for p in parts)
        return f"{base_prompt}\n\nPlease incorporate the following creative guidance:\n{modifications_text}"

    async def _notify_stage_complete(self, session_id: str, stage: str, data: Any):
        """
        Send WebSocket notification when stage completes.

        Args:
            session_id: Session ID
            stage: Stage name (story, reference_image, storyboard, video)
            data: Stage output data
        """
        if self._connection_manager is None:
            # Lazy import to avoid circular dependency
            try:
                from app.api.routes.websocket import manager
                self._connection_manager = manager
            except Exception as e:
                logger.warning(f"Could not load connection manager: {e}")
                return

        try:
            from app.schemas.interactive import WSStageCompleteMessage

            message = WSStageCompleteMessage(
                stage=stage,
                data=data
            )

            await self._connection_manager.send_message(
                session_id,
                message.model_dump()
            )

            logger.info(f"📤 Sent stage complete notification: session={session_id}, stage={stage}")

        except Exception as e:
            logger.error(f"Failed to send stage complete notification: {e}")


# Global orchestrator instance
_orchestrator: Optional[InteractivePipelineOrchestrator] = None


def get_orchestrator() -> InteractivePipelineOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = InteractivePipelineOrchestrator()
    return _orchestrator
