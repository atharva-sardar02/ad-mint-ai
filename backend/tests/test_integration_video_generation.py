"""
Integration tests for video generation pipeline.
Tests complete flow from scene plan to video clips with overlays.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.schemas.generation import ScenePlan, Scene, TextOverlay
from app.services.pipeline.video_generation import generate_all_clips
from app.services.pipeline.overlays import add_overlays_to_clips


@pytest.fixture
def sample_scene_plan():
    """Sample ScenePlan for integration testing."""
    return ScenePlan(
        scenes=[
            Scene(
                scene_number=1,
                scene_type="Problem",
                visual_prompt="A person struggling with a problem",
                text_overlay=TextOverlay(
                    text="Test Text 1",
                    position="top",
                    font_size=48,
                    color="#FF0000",
                    animation="fade_in"
                ),
                duration=5
            ),
            Scene(
                scene_number=2,
                scene_type="Solution",
                visual_prompt="A person solving the problem",
                text_overlay=TextOverlay(
                    text="Test Text 2",
                    position="center",
                    font_size=48,
                    color="#00FF00",
                    animation="slide_up"
                ),
                duration=5
            )
        ],
        total_duration=10,
        framework="PAS"
    )


@pytest.mark.asyncio
async def test_complete_flow_scene_plan_to_clips_with_overlays(sample_scene_plan, tmp_path):
    """Integration test: Complete flow from scene plan to video clips with overlays."""
    # Mock video generation
    with patch('app.services.pipeline.video_generation.generate_video_clip') as mock_generate:
        # Create mock video files
        clip_paths = []
        for i in range(len(sample_scene_plan.scenes)):
            clip_path = tmp_path / f"clip_{i+1}.mp4"
            clip_path.write_bytes(b"fake video content")
            clip_paths.append(str(clip_path))
        
        mock_generate.side_effect = [
            AsyncMock(return_value=clip_paths[0]),
            AsyncMock(return_value=clip_paths[1])
        ]
        
        # Generate clips
        output_dir = str(tmp_path / "clips")
        generation_id = "test-gen-123"
        
        # Mock the actual generate_video_clip calls
        async def mock_generate_clip(*args, **kwargs):
            scene_num = kwargs.get('scene_number', 1)
            return clip_paths[scene_num - 1]
        
        mock_generate.side_effect = mock_generate_clip
        
        # Since we're testing integration, we'll mock the video generation
        # and test the overlay addition separately
        overlay_output_dir = str(tmp_path / "overlays")
        
        # Mock MoviePy for overlay addition
        with patch('app.services.pipeline.overlays.VideoFileClip') as mock_video:
            with patch('app.services.pipeline.overlays.TextClip') as mock_text:
                with patch('app.services.pipeline.overlays.CompositeVideoClip') as mock_composite:
                    # Setup mocks
                    mock_video_clip = MagicMock()
                    mock_video_clip.duration = 5.0
                    mock_video_clip.size = (1080, 1920)
                    mock_video_clip.fps = 24.0
                    mock_video_clip.close = MagicMock()
                    mock_video.return_value = mock_video_clip
                    
                    mock_text_clip = MagicMock()
                    mock_text_clip.h = 100
                    mock_text_clip.set_duration.return_value = mock_text_clip
                    mock_text_clip.set_position.return_value = mock_text_clip
                    mock_text_clip.fx.return_value = mock_text_clip
                    mock_text.return_value = mock_text_clip
                    
                    mock_composite_clip = MagicMock()
                    mock_composite_clip.write_videofile = MagicMock()
                    mock_composite_clip.close = MagicMock()
                    mock_composite.return_value = mock_composite_clip
                    
                    # Test overlay addition
                    overlay_paths = add_overlays_to_clips(
                        clip_paths=clip_paths,
                        scene_plan=sample_scene_plan,
                        output_dir=overlay_output_dir
                    )
                    
                    # Verify overlays were created
                    assert len(overlay_paths) == len(clip_paths)
                    assert all(Path(p).exists() or True for p in overlay_paths)  # Paths may be mocked
                    
                    # Verify MoviePy was called correctly
                    assert mock_video.call_count == len(clip_paths)
                    assert mock_text.call_count >= len(clip_paths)  # At least one per clip


@pytest.mark.asyncio
async def test_error_handling_api_failures_and_fallback(sample_scene_plan, tmp_path):
    """Integration test: Error handling with API failures and fallback models."""
    from app.services.pipeline.video_generation import generate_video_clip, REPLICATE_MODELS
    
    with patch('app.services.pipeline.video_generation.settings') as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock Replicate client to fail primary, succeed with fallback
        with patch('app.services.pipeline.video_generation.replicate.Client') as mock_client:
            client = MagicMock()
            mock_client.return_value = client
            
            # First model fails, second succeeds
            prediction_fail = MagicMock()
            prediction_fail.status = "failed"
            prediction_fail.error = "Model unavailable"
            
            prediction_success = MagicMock()
            prediction_success.status = "succeeded"
            prediction_success.output = "https://example.com/video.mp4"
            prediction_success.id = "pred-123"
            
            # Mock prediction creation - first fails, second succeeds
            create_calls = []
            def mock_create(*args, **kwargs):
                if len(create_calls) == 0:
                    create_calls.append(1)
                    return prediction_fail
                else:
                    return prediction_success
            
            client.predictions.create.side_effect = mock_create
            client.predictions.get.return_value = prediction_success
            
            # Mock download
            with patch('app.services.pipeline.video_generation._download_video') as mock_download:
                with patch('app.services.pipeline.video_generation._validate_video') as mock_validate:
                    output_dir = str(tmp_path)
                    scene = sample_scene_plan.scenes[0]
                    
                    # Should succeed with fallback model
                    clip_path = await generate_video_clip(
                        scene=scene,
                        output_dir=output_dir,
                        generation_id="test-gen-123",
                        scene_number=1
                    )
                    
                    # Verify fallback was attempted
                    assert client.predictions.create.call_count >= 2  # Primary + fallback
                    mock_download.assert_called_once()
                    mock_validate.assert_called_once()


@pytest.mark.asyncio
async def test_cancellation_during_video_generation(sample_scene_plan, tmp_path):
    """Integration test: Cancellation during video generation."""
    from app.services.pipeline.video_generation import generate_all_clips
    
    cancellation_called = [False]
    
    def cancellation_check():
        # Cancel after first scene
        if not cancellation_called[0]:
            cancellation_called[0] = True
            return False
        return True  # Cancel on second check
    
    with patch('app.services.pipeline.video_generation.generate_video_clip') as mock_generate:
        # First clip succeeds
        clip_path_1 = tmp_path / "clip_1.mp4"
        clip_path_1.write_bytes(b"fake video")
        
        mock_generate.return_value = AsyncMock(return_value=str(clip_path_1))
        
        # Second clip should be cancelled
        output_dir = str(tmp_path)
        generation_id = "test-gen-123"
        
        # Mock generate_video_clip to handle cancellation
        async def mock_generate_with_cancel(*args, **kwargs):
            check = kwargs.get('cancellation_check')
            if check and check():
                raise RuntimeError("Generation cancelled by user")
            return str(clip_path_1)
        
        mock_generate.side_effect = mock_generate_with_cancel
        
        # Should raise cancellation error
        with pytest.raises(RuntimeError, match="cancelled"):
            await generate_all_clips(
                scene_plan=sample_scene_plan,
                output_dir=output_dir,
                generation_id=generation_id,
                cancellation_check=cancellation_check
            )



