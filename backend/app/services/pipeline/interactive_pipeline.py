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

    # ========================================================================
    # Stage Generation Methods
    # ========================================================================

    async def _generate_story_stage(
        self,
        session_id: str,
        modifications: Optional[Dict[str, Any]] = None
    ):
        """Generate story for the session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

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
            reference_images = []

            for i in range(3):  # Generate 3 variations
                try:
                    image_path = await generate_image(
                        prompt=enhanced_prompt_result.get("enhanced_prompt", prompt_to_use),
                        output_dir=output_dir,
                        generation_id=f"{session_id}_ref",
                        scene_number=i + 1
                    )

                    # Score image quality
                    quality_score = None
                    try:
                        from app.services.pipeline.image_quality_scoring import score_image
                        scores = await score_image(image_path, enhanced_prompt_result.get("enhanced_prompt", prompt_to_use))
                        quality_score = scores.get("overall", None)
                    except Exception as e:
                        logger.warning(f"Quality scoring failed for image {i+1}: {e}")

                    reference_images.append({
                        "index": i + 1,
                        "path": image_path,
                        "url": f"/api/v1/outputs/interactive/{session_id}/reference_images/{Path(image_path).name}",
                        "prompt": enhanced_prompt_result.get("enhanced_prompt", prompt_to_use),
                        "quality_score": quality_score
                    })

                    logger.info(f"✅ Reference image {i + 1}/3 generated")

                except Exception as e:
                    logger.error(f"Failed to generate reference image {i + 1}: {e}")
                    # Continue with remaining images

            if not reference_images:
                raise RuntimeError("Failed to generate any reference images")

            # Save outputs
            session.outputs["reference_image"] = {
                "images": reference_images,
                "prompt_used": enhanced_prompt_result.get("enhanced_prompt", prompt_to_use),
                "modifications_applied": modifications or {}
            }
            session.stage_data["reference_image_iterations"] = session.stage_data.get("reference_image_iterations", 0) + 1
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
            storyboard_clips = []

            scenes = storyboard_payload.get("scenes", [])
            for i, scene in enumerate(scenes):
                clip_index = i + 1

                # Skip clips not in affected_indices if regenerating specific ones
                if affected_indices and clip_index not in affected_indices:
                    # Reuse existing clip if available
                    existing_clips = session.outputs.get("storyboard", {}).get("clips", [])
                    existing_clip = next((c for c in existing_clips if c["clip_number"] == clip_index), None)
                    if existing_clip:
                        storyboard_clips.append(existing_clip)
                        logger.info(f"Reusing existing clip {clip_index}")
                        continue

                try:
                    # Generate start and end frame images for each clip
                    scene_prompt = scene.get("visual_prompt", "")

                    logger.info(f"Generating images for clip {clip_index}...")

                    # Generate start frame
                    start_frame_path = await generate_image(
                        prompt=f"{scene_prompt} (start frame)",
                        output_dir=output_dir,
                        generation_id=f"{session_id}_clip_{clip_index:03d}",
                        scene_number=None
                    )

                    # Generate end frame
                    end_frame_path = await generate_image(
                        prompt=f"{scene_prompt} (end frame)",
                        output_dir=output_dir,
                        generation_id=f"{session_id}_clip_{clip_index:03d}_end",
                        scene_number=None
                    )

                    # Score clip quality (using start frame)
                    quality_score = None
                    try:
                        from app.services.pipeline.image_quality_scoring import score_image
                        scores = await score_image(start_frame_path, scene.get("visual", ""))
                        quality_score = scores.get("overall", None)
                    except Exception as e:
                        logger.warning(f"Quality scoring failed for clip {clip_index}: {e}")

                    storyboard_clips.append({
                        "clip_number": clip_index,
                        "scene": scene,
                        "start_frame": {
                            "path": start_frame_path,
                            "url": f"/api/v1/outputs/interactive/{session_id}/storyboard/{Path(start_frame_path).name}"
                        },
                        "end_frame": {
                            "path": end_frame_path,
                            "url": f"/api/v1/outputs/interactive/{session_id}/storyboard/{Path(end_frame_path).name}"
                        },
                        "duration": scene.get("duration", 4),
                        "voiceover": scene.get("scene_type", ""),
                        "quality_score": quality_score
                    })

                    logger.info(f"✅ Clip {clip_index}/{len(scenes)} generated")

                except Exception as e:
                    logger.error(f"Failed to generate storyboard clip {clip_index}: {e}")
                    # Continue with remaining clips

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

        try:
            logger.info(f"🎥 Generating final video for session {session_id} with Veo 3")
            video_output_dir = f"{settings.OUTPUT_BASE_DIR}/interactive/{session_id}/video"
            Path(video_output_dir).mkdir(parents=True, exist_ok=True)

            generated_clips = []
            for clip in clips:
                clip_number = clip.get("clip_number")
                scene_data = clip.get("scene", {}) or {}
                visual_prompt = (
                    scene_data.get("visual_prompt")
                    or scene_data.get("visual")
                    or storyboard.get("storyboard_spec", {}).get("visual_prompt")
                    or ""
                )

                scene_payload = Scene(
                    scene_number=clip_number or len(generated_clips) + 1,
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

                generated_clips.append(
                    {
                        "clip_number": scene_payload.scene_number,
                        "path": clip_path,
                        "model": model_used,
                    }
                )

            session.outputs["video"] = {
                "clips": generated_clips,
                "model": "google/veo-3",
                "status": "completed",
            }
            session.status = "complete"
            session.current_stage = "Complete"
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
