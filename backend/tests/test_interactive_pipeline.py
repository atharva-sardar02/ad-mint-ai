"""
Tests for InteractivePipelineOrchestrator image stages.

Tests cover:
- Reference image stage generation
- Storyboard stage generation
- Selective clip regeneration
- Session state management
- Stage transitions
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.pipeline.interactive_pipeline import InteractivePipelineOrchestrator
from app.schemas.interactive import PipelineSessionState
from app.core.config import Settings


class TestReferenceImageStage:
    """Test suite for reference image generation stage."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return InteractivePipelineOrchestrator(session_ttl_hours=1)

    @pytest.fixture
    def mock_session(self):
        """Create mock session with story output."""
        return PipelineSessionState(
            session_id="test_session_123",
            user_id="user_123",
            status="reference_image",
            current_stage="Reference Image Generation",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            prompt="Create a modern tech startup office",
            target_duration=15,
            mode="interactive",
            title=None,
            outputs={"story": {"narrative": "A tech startup story"}},
            conversation_history=[],
            stage_data={},
            error=None,
            error_count=0
        )

    @pytest.mark.asyncio
    async def test_generate_reference_image_stage_creates_3_images(
        self, orchestrator, mock_session
    ):
        """Test that reference image stage generates 3 image variations."""
        with patch.object(orchestrator, 'get_session', return_value=mock_session), \
             patch.object(orchestrator, '_save_session', new_callable=AsyncMock), \
             patch.object(orchestrator, '_notify_stage_complete', new_callable=AsyncMock), \
             patch('app.services.pipeline.image_generation.generate_image', new_callable=AsyncMock) as mock_gen_image, \
             patch('app.services.pipeline.image_prompt_enhancement.enhance_image_prompt', new_callable=AsyncMock) as mock_enhance, \
             patch('app.core.config.settings.OUTPUT_BASE_DIR', '/tmp/test_output'):

            # Mock image generation
            mock_enhance.return_value = {"enhanced_prompt": "Enhanced test prompt"}
            mock_gen_image.side_effect = [
                "/output/image_1.png",
                "/output/image_2.png",
                "/output/image_3.png"
            ]

            await orchestrator._generate_reference_image_stage("test_session_123")

            # Verify 3 images were generated
            assert mock_gen_image.call_count == 3

            # Verify session was saved
            assert orchestrator._save_session.called

            # Verify notification was sent
            assert orchestrator._notify_stage_complete.called

    @pytest.mark.asyncio
    async def test_generate_reference_image_stage_with_modifications(
        self, orchestrator, mock_session
    ):
        """Test reference image generation with feedback modifications."""
        modifications = {
            "feedback_text": "Make it brighter",
            "brightness": "increase"
        }

        with patch.object(orchestrator, 'get_session', return_value=mock_session), \
             patch.object(orchestrator, '_save_session', new_callable=AsyncMock), \
             patch.object(orchestrator, '_notify_stage_complete', new_callable=AsyncMock), \
             patch('app.services.pipeline.image_generation.generate_image', new_callable=AsyncMock) as mock_gen_image, \
             patch('app.services.pipeline.image_prompt_enhancement.enhance_image_prompt', new_callable=AsyncMock) as mock_enhance, \
             patch('app.core.config.settings.OUTPUT_BASE_DIR', '/tmp/test_output'):

            mock_enhance.return_value = {"enhanced_prompt": "Enhanced test prompt"}
            mock_gen_image.side_effect = ["/output/image_1.png", "/output/image_2.png", "/output/image_3.png"]

            await orchestrator._generate_reference_image_stage(
                "test_session_123",
                modifications=modifications
            )

            # Verify modifications were applied in prompt enhancement
            enhance_call_args = mock_enhance.call_args
            assert "Make it brighter" in enhance_call_args[1]["base_prompt"]

    @pytest.mark.asyncio
    async def test_generate_reference_image_stage_saves_to_session(
        self, orchestrator, mock_session
    ):
        """Test that generated images are saved to session outputs."""
        with patch.object(orchestrator, 'get_session', return_value=mock_session), \
             patch.object(orchestrator, '_save_session', new_callable=AsyncMock) as mock_save, \
             patch.object(orchestrator, '_notify_stage_complete', new_callable=AsyncMock), \
             patch('app.services.pipeline.image_generation.generate_image', new_callable=AsyncMock) as mock_gen_image, \
             patch('app.services.pipeline.image_prompt_enhancement.enhance_image_prompt', new_callable=AsyncMock) as mock_enhance, \
             patch('app.core.config.settings.OUTPUT_BASE_DIR', '/tmp/test_output'):

            mock_enhance.return_value = {"enhanced_prompt": "Enhanced test prompt"}
            mock_gen_image.side_effect = ["/output/image_1.png", "/output/image_2.png", "/output/image_3.png"]

            await orchestrator._generate_reference_image_stage("test_session_123")

            # Verify session was saved with image data
            assert mock_save.called
            saved_session = mock_save.call_args[0][0]
            assert "reference_image" in saved_session.outputs
            assert "images" in saved_session.outputs["reference_image"]
            assert len(saved_session.outputs["reference_image"]["images"]) == 3

    @pytest.mark.asyncio
    async def test_generate_reference_image_stage_error_handling(
        self, orchestrator, mock_session
    ):
        """Test error handling when image generation fails."""
        with patch.object(orchestrator, 'get_session', return_value=mock_session), \
             patch.object(orchestrator, '_save_session', new_callable=AsyncMock) as mock_save, \
             patch('app.services.pipeline.image_generation.generate_image', new_callable=AsyncMock) as mock_gen_image, \
             patch('app.services.pipeline.image_prompt_enhancement.enhance_image_prompt', new_callable=AsyncMock) as mock_enhance, \
             patch('app.core.config.settings.OUTPUT_BASE_DIR', '/tmp/test_output'):

            mock_enhance.return_value = {"enhanced_prompt": "Enhanced test prompt"}
            mock_gen_image.side_effect = RuntimeError("Image generation failed")

            with pytest.raises(RuntimeError):
                await orchestrator._generate_reference_image_stage("test_session_123")

            # Verify error was logged to session
            assert mock_save.called
            saved_session = mock_save.call_args[0][0]
            assert saved_session.error is not None
            assert saved_session.error_count > 0


class TestStoryboardStage:
    """Test suite for storyboard generation stage."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return InteractivePipelineOrchestrator(session_ttl_hours=1)

    @pytest.fixture
    def mock_session_with_images(self):
        """Create mock session with reference images."""
        return PipelineSessionState(
            session_id="test_session_123",
            user_id="user_123",
            status="storyboard",
            current_stage="Storyboard Generation",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            prompt="Create a modern tech startup office",
            target_duration=15,
            mode="interactive",
            title=None,
            outputs={
                "story": {"narrative": "A tech startup story"},
                "reference_image": {
                    "images": [
                        {"index": 1, "path": "/output/ref_1.png"},
                        {"index": 2, "path": "/output/ref_2.png"}
                    ]
                }
            },
            conversation_history=[],
            stage_data={},
            error=None,
            error_count=0
        )

    @pytest.mark.asyncio
    async def test_generate_storyboard_stage_creates_clips(
        self, orchestrator, mock_session_with_images
    ):
        """Test that storyboard stage generates clips with start/end frames."""
        mock_storyboard = {
            "scenes": [
                {"visual": "Office entrance", "action": "Person walking in", "duration_seconds": 4},
                {"visual": "Desk area", "action": "Working on laptop", "duration_seconds": 4}
            ]
        }

        with patch.object(orchestrator, 'get_session', return_value=mock_session_with_images), \
             patch.object(orchestrator, '_save_session', new_callable=AsyncMock) as mock_save, \
             patch.object(orchestrator, '_notify_stage_complete', new_callable=AsyncMock), \
             patch('app.services.pipeline.storyboard_service.generate_storyboard', new_callable=AsyncMock) as mock_gen_sb, \
             patch('app.services.pipeline.image_generation.generate_image', new_callable=AsyncMock) as mock_gen_image, \
             patch('app.core.config.settings.OUTPUT_BASE_DIR', '/tmp/test_output'):

            mock_gen_sb.return_value = mock_storyboard
            # Mock start and end frame generation for each clip
            mock_gen_image.side_effect = [
                "/output/clip_1_start.png", "/output/clip_1_end.png",
                "/output/clip_2_start.png", "/output/clip_2_end.png"
            ]

            await orchestrator._generate_storyboard_stage("test_session_123")

            # Verify storyboard was generated
            assert mock_gen_sb.called

            # Verify start/end frames were generated (2 scenes × 2 frames each = 4 images)
            assert mock_gen_image.call_count == 4

            # Verify session was saved with clip data
            assert mock_save.called
            saved_session = mock_save.call_args[0][0]
            assert "storyboard" in saved_session.outputs
            assert "clips" in saved_session.outputs["storyboard"]
            assert len(saved_session.outputs["storyboard"]["clips"]) == 2

    @pytest.mark.asyncio
    async def test_generate_storyboard_stage_selective_regeneration(
        self, orchestrator, mock_session_with_images
    ):
        """Test selective clip regeneration using affected_indices."""
        # Set up existing clips in session
        mock_session_with_images.outputs["storyboard"] = {
            "clips": [
                {"clip_number": 1, "start_frame": {"path": "/old_clip_1_start.png"}},
                {"clip_number": 2, "start_frame": {"path": "/old_clip_2_start.png"}},
                {"clip_number": 3, "start_frame": {"path": "/old_clip_3_start.png"}}
            ]
        }

        mock_storyboard = {
            "scenes": [
                {"visual": "Scene 1", "action": "Action 1", "duration_seconds": 4},
                {"visual": "Scene 2", "action": "Action 2", "duration_seconds": 4},
                {"visual": "Scene 3", "action": "Action 3", "duration_seconds": 4}
            ]
        }

        modifications = {"affected_indices": [2]}  # Only regenerate clip 2

        with patch.object(orchestrator, 'get_session', return_value=mock_session_with_images), \
             patch.object(orchestrator, '_save_session', new_callable=AsyncMock) as mock_save, \
             patch.object(orchestrator, '_notify_stage_complete', new_callable=AsyncMock), \
             patch('app.services.pipeline.storyboard_service.generate_storyboard', new_callable=AsyncMock) as mock_gen_sb, \
             patch('app.services.pipeline.image_generation.generate_image', new_callable=AsyncMock) as mock_gen_image, \
             patch('app.core.config.settings.OUTPUT_BASE_DIR', '/tmp/test_output'):

            mock_gen_sb.return_value = mock_storyboard
            # Only 2 images should be generated (start/end for clip 2)
            mock_gen_image.side_effect = [
                "/output/clip_2_start_new.png",
                "/output/clip_2_end_new.png"
            ]

            await orchestrator._generate_storyboard_stage(
                "test_session_123",
                modifications=modifications
            )

            # Verify only affected clip was regenerated (2 frames)
            assert mock_gen_image.call_count == 2

            # Verify existing clips were reused
            saved_session = mock_save.call_args[0][0]
            clips = saved_session.outputs["storyboard"]["clips"]
            assert len(clips) == 3  # All 3 clips present
            # Clip 1 and 3 should be reused (old paths)
            assert clips[0]["start_frame"]["path"] == "/old_clip_1_start.png"
            assert clips[2]["start_frame"]["path"] == "/old_clip_3_start.png"

    @pytest.mark.asyncio
    async def test_generate_storyboard_stage_with_reference_images(
        self, orchestrator, mock_session_with_images
    ):
        """Test that storyboard generation uses reference images."""
        mock_storyboard = {
            "scenes": [
                {"visual": "Office", "action": "Working", "duration_seconds": 4}
            ]
        }

        with patch.object(orchestrator, 'get_session', return_value=mock_session_with_images), \
             patch.object(orchestrator, '_save_session', new_callable=AsyncMock), \
             patch.object(orchestrator, '_notify_stage_complete', new_callable=AsyncMock), \
             patch('app.services.pipeline.storyboard_service.generate_storyboard', new_callable=AsyncMock) as mock_gen_sb, \
             patch('app.services.pipeline.image_generation.generate_image', new_callable=AsyncMock) as mock_gen_image, \
             patch('app.core.config.settings.OUTPUT_BASE_DIR', '/tmp/test_output'):

            mock_gen_sb.return_value = mock_storyboard
            mock_gen_image.side_effect = ["/output/clip_1_start.png", "/output/clip_1_end.png"]

            await orchestrator._generate_storyboard_stage("test_session_123")

            # Verify storyboard generation received reference image paths
            gen_sb_call_args = mock_gen_sb.call_args
            assert "reference_image_paths" in gen_sb_call_args[1]
            ref_paths = gen_sb_call_args[1]["reference_image_paths"]
            assert len(ref_paths) == 2
            assert "/output/ref_1.png" in ref_paths
            assert "/output/ref_2.png" in ref_paths


class TestSessionManagement:
    """Test suite for session state management."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return InteractivePipelineOrchestrator(session_ttl_hours=1)

    @pytest.mark.asyncio
    async def test_session_stage_iteration_tracking(self, orchestrator):
        """Test that stage iterations are tracked in stage_data."""
        mock_session = PipelineSessionState(
            session_id="test_session_123",
            user_id="user_123",
            status="reference_image",
            current_stage="Reference Image Generation",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            prompt="Test prompt",
            target_duration=15,
            mode="interactive",
            title=None,
            outputs={"story": {"narrative": "Story"}},
            conversation_history=[],
            stage_data={},
            error=None,
            error_count=0
        )

        with patch.object(orchestrator, 'get_session', return_value=mock_session), \
             patch.object(orchestrator, '_save_session', new_callable=AsyncMock) as mock_save, \
             patch.object(orchestrator, '_notify_stage_complete', new_callable=AsyncMock), \
             patch('app.services.pipeline.image_generation.generate_image', new_callable=AsyncMock) as mock_gen_image, \
             patch('app.services.pipeline.image_prompt_enhancement.enhance_image_prompt', new_callable=AsyncMock) as mock_enhance, \
             patch('app.core.config.settings.OUTPUT_BASE_DIR', '/tmp/test_output'):

            mock_enhance.return_value = {"enhanced_prompt": "Enhanced"}
            mock_gen_image.side_effect = ["/img1.png", "/img2.png", "/img3.png"]

            # First generation
            await orchestrator._generate_reference_image_stage("test_session_123")
            saved_session = mock_save.call_args[0][0]
            assert saved_session.stage_data.get("reference_image_iterations") == 1

            # Regenerate with feedback
            mock_save.reset_mock()
            await orchestrator._generate_reference_image_stage("test_session_123")
            saved_session = mock_save.call_args[0][0]
            assert saved_session.stage_data.get("reference_image_iterations") == 2
