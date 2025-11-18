"""
Unit tests for image generation service with mocked Replicate API.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import shutil
import asyncio

from app.services.pipeline.image_generation import (
    generate_images,
    ImageGenerationResult,
    _generate_with_retry,
    _download_image,
    ASPECT_RATIOS,
    MODEL_COSTS
)


@pytest.fixture
def mock_replicate_client():
    """Mock Replicate client."""
    with patch("app.services.pipeline.image_generation.replicate.Client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for image downloads."""
    with patch("app.services.pipeline.image_generation.httpx.AsyncClient") as mock:
        mock_client = AsyncMock()
        mock.return_value.__aenter__.return_value = mock_client
        mock.return_value.__aexit__.return_value = None
        yield mock_client


@pytest.fixture
def sample_prompt():
    """Sample image prompt."""
    return "A beautiful sunset over mountains with dramatic clouds"


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_generate_images_success(mock_replicate_client, sample_prompt, temp_output_dir):
    """Test successful image generation."""
    # Mock prediction object
    mock_prediction = MagicMock()
    mock_prediction.status = "succeeded"
    mock_prediction.output = "https://example.com/image.png"
    mock_prediction.id = "test-prediction-id"
    
    # Mock client methods
    mock_replicate_client.predictions.create.return_value = mock_prediction
    mock_replicate_client.predictions.get.return_value = mock_prediction
    
    # Mock image download
    with patch("app.services.pipeline.image_generation._download_image") as mock_download:
        mock_download.return_value = str(temp_output_dir / "image_001.png")
        
        results = await generate_images(
            prompt=sample_prompt,
            num_variations=4,
            aspect_ratio="16:9",
            output_dir=temp_output_dir
        )
        
        assert len(results) == 4
        assert all(isinstance(r, ImageGenerationResult) for r in results)
        assert all(r.prompt == sample_prompt for r in results)
        assert all(r.aspect_ratio == "16:9" for r in results)
        assert mock_replicate_client.predictions.create.call_count == 4


@pytest.mark.asyncio
async def test_generate_images_with_seed(mock_replicate_client, sample_prompt, temp_output_dir):
    """Test image generation with seed for reproducibility."""
    mock_prediction = MagicMock()
    mock_prediction.status = "succeeded"
    mock_prediction.output = "https://example.com/image.png"
    mock_prediction.id = "test-prediction-id"
    
    mock_replicate_client.predictions.create.return_value = mock_prediction
    mock_replicate_client.predictions.get.return_value = mock_prediction
    
    with patch("app.services.pipeline.image_generation._download_image") as mock_download:
        mock_download.return_value = str(temp_output_dir / "image_001.png")
        
        seed = 12345
        results = await generate_images(
            prompt=sample_prompt,
            num_variations=4,
            seed=seed,
            output_dir=temp_output_dir
        )
        
        assert len(results) == 4
        # Check that seed was passed to API
        calls = mock_replicate_client.predictions.create.call_args_list
        assert all("seed" in call.kwargs["input"] for call in calls)
        assert all(call.kwargs["input"]["seed"] == seed for call in calls)


@pytest.mark.asyncio
async def test_generate_images_invalid_num_variations(sample_prompt):
    """Test that invalid num_variations raises ValueError."""
    with pytest.raises(ValueError, match="num_variations must be between 1 and 8"):
        await generate_images(
            prompt=sample_prompt,
            num_variations=10  # Invalid
        )


@pytest.mark.asyncio
async def test_generate_images_invalid_aspect_ratio(sample_prompt):
    """Test that invalid aspect_ratio raises ValueError."""
    with pytest.raises(ValueError, match="aspect_ratio must be one of"):
        await generate_images(
            prompt=sample_prompt,
            aspect_ratio="21:9"  # Invalid
        )


@pytest.mark.asyncio
async def test_generate_images_missing_api_token(sample_prompt):
    """Test that missing API token raises ValueError."""
    with patch("app.services.pipeline.image_generation.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = None
        
        with pytest.raises(ValueError, match="Replicate API token is not configured"):
            await generate_images(prompt=sample_prompt)


@pytest.mark.asyncio
async def test_generate_with_retry_success(mock_replicate_client):
    """Test successful generation with retry logic."""
    mock_prediction = MagicMock()
    mock_prediction.status = "succeeded"
    mock_prediction.output = "https://example.com/image.png"
    mock_prediction.id = "test-prediction-id"
    
    mock_replicate_client.predictions.create.return_value = mock_prediction
    mock_replicate_client.predictions.get.return_value = mock_prediction
    
    with patch("app.services.pipeline.image_generation.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        url = await _generate_with_retry(
            model_name="stability-ai/sdxl",
            prompt="test prompt",
            width=1344,
            height=768
        )
        
        assert url == "https://example.com/image.png"
        assert mock_replicate_client.predictions.create.called


@pytest.mark.asyncio
async def test_generate_with_retry_rate_limit(mock_replicate_client):
    """Test retry logic with rate limit error."""
    mock_prediction = MagicMock()
    mock_prediction.status = "processing"
    mock_prediction.id = "test-prediction-id"
    
    # First call: rate limit error
    # Second call: success
    mock_replicate_client.predictions.create.side_effect = [
        Exception("429 Rate limit exceeded"),
        mock_prediction
    ]
    mock_replicate_client.predictions.get.side_effect = [
        mock_prediction,
        MagicMock(status="succeeded", output="https://example.com/image.png")
    ]
    
    with patch("app.services.pipeline.image_generation.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        with patch("asyncio.sleep"):  # Speed up test
            url = await _generate_with_retry(
                model_name="stability-ai/sdxl",
                prompt="test prompt",
                width=1344,
                height=768
            )
            
            assert url == "https://example.com/image.png"
            assert mock_replicate_client.predictions.create.call_count == 2


@pytest.mark.asyncio
async def test_download_image_success(mock_httpx_client, temp_output_dir):
    """Test successful image download."""
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "image/png"}
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b"fake image data"
    
    mock_httpx_client.get = AsyncMock(return_value=mock_response)
    
    image_path = await _download_image(
        image_url="https://example.com/image.png",
        output_dir=temp_output_dir,
        index=1
    )
    
    assert image_path.endswith("image_001.png")
    assert Path(image_path).exists()
    assert Path(image_path).read_bytes() == b"fake image data"


@pytest.mark.asyncio
async def test_download_image_http_error(mock_httpx_client, temp_output_dir):
    """Test image download with HTTP error."""
    import httpx
    
    mock_httpx_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection error"))
    
    with pytest.raises(RuntimeError, match="Image download failed"):
        await _download_image(
            image_url="https://example.com/image.png",
            output_dir=temp_output_dir,
            index=1
        )


def test_aspect_ratios_defined():
    """Test that all required aspect ratios are defined."""
    required_ratios = ["1:1", "4:3", "16:9", "9:16"]
    for ratio in required_ratios:
        assert ratio in ASPECT_RATIOS
        width, height = ASPECT_RATIOS[ratio]
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0 and height > 0


def test_model_costs_defined():
    """Test that model costs are defined for default model."""
    assert "stability-ai/sdxl" in MODEL_COSTS
    assert MODEL_COSTS["stability-ai/sdxl"] > 0

