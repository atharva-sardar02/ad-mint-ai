"""
Unit tests for video generation service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.schemas.generation import Scene, TextOverlay
from app.services.pipeline.video_generation import (
    generate_video_clip,
    _generate_with_retry,
    _download_video,
    _validate_video
)


@pytest.fixture
def sample_scene():
    """Sample Scene for testing."""
    return Scene(
        scene_number=1,
        scene_type="Problem",
        visual_prompt="A person struggling with a problem",
        text_overlay=TextOverlay(
            text="Test Text",
            position="top",
            font_size=48,
            color="#FF0000",
            animation="fade_in"
        ),
        duration=5
    )


@pytest.fixture
def mock_replicate_client():
    """Mock Replicate client."""
    with patch('app.services.pipeline.video_generation.replicate.Client') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.mark.asyncio
async def test_generate_video_clip_success(sample_scene, mock_replicate_client, tmp_path):
    """Test successful video clip generation."""
    # Mock settings
    with patch('app.services.pipeline.video_generation.settings') as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock prediction
        prediction = MagicMock()
        prediction.status = "succeeded"
        prediction.output = "https://example.com/video.mp4"
        prediction.id = "pred-123"
        
        mock_replicate_client.predictions.create.return_value = prediction
        mock_replicate_client.predictions.get.return_value = prediction
        
        # Mock download
        with patch('app.services.pipeline.video_generation._download_video') as mock_download:
            with patch('app.services.pipeline.video_generation._validate_video') as mock_validate:
                output_dir = str(tmp_path)
                clip_path = await generate_video_clip(
                    scene=sample_scene,
                    output_dir=output_dir,
                    generation_id="test-gen-123",
                    scene_number=1
                )
                
                assert clip_path is not None
                assert "test-gen-123" in clip_path
                mock_download.assert_called_once()
                mock_validate.assert_called_once()


@pytest.mark.asyncio
async def test_generate_video_clip_cancellation(sample_scene, tmp_path):
    """Test video generation cancellation."""
    with patch('app.services.pipeline.video_generation.settings') as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        def cancellation_check():
            return True
        
        output_dir = str(tmp_path)
        
        with pytest.raises(RuntimeError, match="cancelled"):
            await generate_video_clip(
                scene=sample_scene,
                output_dir=output_dir,
                generation_id="test-gen-123",
                scene_number=1,
                cancellation_check=cancellation_check
            )


@pytest.mark.asyncio
async def test_generate_with_retry_success(mock_replicate_client):
    """Test retry logic with successful generation."""
    with patch('app.services.pipeline.video_generation.settings') as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        prediction = MagicMock()
        prediction.status = "succeeded"
        prediction.output = "https://example.com/video.mp4"
        prediction.id = "pred-123"
        
        mock_replicate_client.predictions.create.return_value = prediction
        mock_replicate_client.predictions.get.return_value = prediction
        
        video_url = await _generate_with_retry(
            model_name="minimax-ai/minimax-video-01",
            prompt="Test prompt",
            duration=5
        )
        
        assert video_url == "https://example.com/video.mp4"
        mock_replicate_client.predictions.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_with_retry_rate_limit(mock_replicate_client):
    """Test retry logic with rate limit error."""
    import replicate
    from app.services.pipeline.video_generation import REPLICATE_MODELS
    
    with patch('app.services.pipeline.video_generation.settings') as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # First attempt: rate limit
        # Second attempt: success
        prediction = MagicMock()
        prediction.status = "succeeded"
        prediction.output = "https://example.com/video.mp4"
        prediction.id = "pred-123"
        
        mock_replicate_client.predictions.create.side_effect = [
            replicate.exceptions.RateLimitError("Rate limit exceeded"),
            prediction
        ]
        mock_replicate_client.predictions.get.return_value = prediction
        
        video_url = await _generate_with_retry(
            model_name=REPLICATE_MODELS["primary"],
            prompt="Test prompt",
            duration=5
        )
        
        assert video_url == "https://example.com/video.mp4"
        assert mock_replicate_client.predictions.create.call_count == 2


@pytest.mark.asyncio
async def test_download_video_success(tmp_path):
    """Test video download."""
    import httpx
    
    video_url = "https://example.com/video.mp4"
    output_path = tmp_path / "test_video.mp4"
    
    # Create a mock video file content
    video_content = b"fake video content"
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.content = video_content
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.get.return_value = mock_response
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client.return_value = mock_client_instance
        
        await _download_video(video_url, output_path)
        
        assert output_path.exists()
        assert output_path.read_bytes() == video_content


@pytest.mark.asyncio
async def test_validate_video_success(tmp_path):
    """Test video validation."""
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b"fake video content")
    
    # Should not raise
    await _validate_video(video_path, expected_duration=5)


@pytest.mark.asyncio
async def test_validate_video_missing_file(tmp_path):
    """Test video validation with missing file."""
    video_path = tmp_path / "nonexistent.mp4"
    
    with pytest.raises(RuntimeError, match="not found"):
        await _validate_video(video_path, expected_duration=5)

