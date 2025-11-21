"""
Tests for Inpainting Service (Story 4: Advanced Image Editing)

Tests cover:
- Mask decoding from base64
- PIL Image conversion
- Replicate API integration (mocked)
- Image download and save
- Error handling
"""

import asyncio
import base64
import io
import pytest
from pathlib import Path
from PIL import Image
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from app.services.pipeline.inpainting_service import (
    inpaint_image,
    _decode_mask,
    _inpaint_with_retry,
    _download_image,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def sample_mask_base64():
    """Create a sample mask as base64."""
    # Create 100x100 binary mask (all white = replace all)
    mask_data = bytes([255] * (100 * 100))
    return base64.b64encode(mask_data).decode("utf-8")


@pytest.fixture
def sample_mask_image():
    """Create a sample mask as PIL Image."""
    return Image.new("L", (100, 100), 255)  # White = replace


@pytest.fixture
def mock_replicate_client():
    """Mock Replicate client with successful prediction."""
    mock_client = Mock()
    mock_prediction = Mock()
    mock_prediction.id = "pred_123"
    mock_prediction.status = "succeeded"
    mock_prediction.output = ["http://example.com/edited_image.png"]

    mock_client.predictions.create.return_value = mock_prediction
    mock_client.predictions.get.return_value = mock_prediction

    return mock_client


# ============================================================================
# Mask Decoding Tests (AC #2, #3)
# ============================================================================

def test_decode_mask_raw_bytes(sample_mask_base64):
    """Test decoding raw binary mask from base64."""
    mask_image = _decode_mask(sample_mask_base64, (100, 100))

    assert mask_image.mode == "L"  # Grayscale
    assert mask_image.size == (100, 100)

    # Check all pixels are 255 (white)
    pixels = list(mask_image.getdata())
    assert all(p == 255 for p in pixels)


def test_decode_mask_png_image(tmp_path):
    """Test decoding mask provided as PNG image."""
    # Create PNG mask
    mask = Image.new("L", (100, 100), 128)
    mask_buffer = io.BytesIO()
    mask.save(mask_buffer, format="PNG")
    mask_buffer.seek(0)

    # Encode as base64
    mask_base64 = base64.b64encode(mask_buffer.getvalue()).decode("utf-8")

    # Decode
    decoded = _decode_mask(mask_base64, (100, 100))

    assert decoded.mode == "L"
    assert decoded.size == (100, 100)


def test_decode_mask_binary_threshold():
    """Test raw binary mask is converted to binary (0 or 255)."""
    # Create raw binary mask with various grayscale values (not PNG)
    # Simulate grayscale values above/below threshold
    mask_data = bytes([0, 50, 100, 127, 128, 129, 200, 255] * 1250)  # 10000 bytes for 100x100
    mask_base64 = base64.b64encode(mask_data).decode("utf-8")

    # Decode
    decoded = _decode_mask(mask_base64, (100, 100))

    # Check all pixels are either 0 or 255 (threshold = 128)
    decoded_pixels = list(decoded.getdata())
    for i, p in enumerate(decoded_pixels):
        original_value = mask_data[i]
        if original_value > 128:
            assert p == 255, f"Pixel {i}: original={original_value}, decoded={p}"
        else:
            assert p == 0, f"Pixel {i}: original={original_value}, decoded={p}"


def test_decode_mask_invalid_base64():
    """Test error handling for invalid base64."""
    with pytest.raises(ValueError, match="Invalid base64"):
        _decode_mask("not_valid_base64!!!", (100, 100))


def test_decode_mask_wrong_size():
    """Test error handling for wrong mask size."""
    # Create mask with wrong size
    mask_data = bytes([255] * (50 * 50))  # 50x50 instead of 100x100
    mask_base64 = base64.b64encode(mask_data).decode("utf-8")

    with pytest.raises(ValueError, match="Invalid mask size"):
        _decode_mask(mask_base64, (100, 100))


# ============================================================================
# Inpainting Service Tests (AC #5)
# ============================================================================

@pytest.mark.asyncio
@patch("app.services.pipeline.inpainting_service.replicate.Client")
@patch("app.services.pipeline.inpainting_service._download_image")
async def test_inpaint_with_retry_success(mock_download, mock_client_class, sample_mask_image, mock_replicate_client):
    """Test successful inpainting with Replicate API."""
    mock_client_class.return_value = mock_replicate_client
    mock_download.return_value = None

    # Create sample image
    original = Image.new("RGB", (100, 100), "red")

    # Run inpainting
    result_url = await _inpaint_with_retry(
        original_image=original,
        mask_image=sample_mask_image,
        prompt="blue background",
        negative_prompt="blurry"
    )

    assert result_url == "http://example.com/edited_image.png"
    assert mock_replicate_client.predictions.create.called

    # Verify input parameters
    call_args = mock_replicate_client.predictions.create.call_args
    assert call_args[1]["input"]["prompt"] == "blue background"
    assert call_args[1]["input"]["negative_prompt"] == "blurry"


@pytest.mark.asyncio
@patch("app.services.pipeline.inpainting_service.replicate.Client")
async def test_inpaint_with_retry_failure(mock_client_class):
    """Test inpainting failure handling."""
    mock_client = Mock()
    mock_prediction = Mock()
    mock_prediction.id = "pred_fail"
    mock_prediction.status = "failed"
    mock_prediction.error = "Model error"

    mock_client.predictions.create.return_value = mock_prediction
    mock_client.predictions.get.return_value = mock_prediction
    mock_client_class.return_value = mock_client

    original = Image.new("RGB", (100, 100), "red")
    mask = Image.new("L", (100, 100), 255)

    with pytest.raises(RuntimeError, match="Inpainting failed"):
        await _inpaint_with_retry(
            original_image=original,
            mask_image=mask,
            prompt="test",
            negative_prompt=""
        )


@pytest.mark.asyncio
@patch("app.services.pipeline.inpainting_service.replicate.Client")
async def test_inpaint_with_retry_timeout(mock_client_class):
    """Test inpainting timeout handling."""
    mock_client = Mock()
    mock_prediction = Mock()
    mock_prediction.id = "pred_timeout"
    mock_prediction.status = "processing"  # Never completes

    mock_client.predictions.create.return_value = mock_prediction
    mock_client.predictions.get.return_value = mock_prediction
    mock_client.predictions.cancel = Mock()
    mock_client_class.return_value = mock_client

    original = Image.new("RGB", (100, 100), "red")
    mask = Image.new("L", (100, 100), 255)

    # Patch MAX_POLLING_TIME to speed up test
    with patch("app.services.pipeline.inpainting_service.MAX_POLLING_TIME", 0.1):
        with pytest.raises(RuntimeError, match="Inpainting timeout"):
            await _inpaint_with_retry(
                original_image=original,
                mask_image=mask,
                prompt="test",
                negative_prompt=""
            )

    # Verify cancel was called
    mock_client.predictions.cancel.assert_called_once()


# ============================================================================
# Full Inpainting Flow Tests (AC #5, #7, #8)
# ============================================================================

@pytest.mark.asyncio
@patch("app.services.pipeline.inpainting_service._inpaint_with_retry")
async def test_inpaint_image_success(mock_inpaint, sample_image, sample_mask_base64, tmp_path):
    """Test full inpainting flow."""
    # Mock inpainting to return a URL
    mock_inpaint.return_value = "http://example.com/edited.png"

    # Mock image download
    with patch("app.services.pipeline.inpainting_service._download_image") as mock_download:
        mock_download.return_value = None

        result = await inpaint_image(
            image_path=sample_image,
            mask_base64=sample_mask_base64,
            prompt="test prompt",
            negative_prompt="test negative",
            output_dir=str(tmp_path),
            image_id=0
        )

    # Verify result path
    assert result.endswith(".png")
    assert "edited" in result

    # Verify inpaint was called with correct args
    mock_inpaint.assert_called_once()
    call_args = mock_inpaint.call_args[1]
    assert call_args["prompt"] == "test prompt"
    assert call_args["negative_prompt"] == "test negative"


@pytest.mark.asyncio
async def test_inpaint_image_missing_file():
    """Test error when image file doesn't exist."""
    with pytest.raises(ValueError, match="Image not found"):
        await inpaint_image(
            image_path="/nonexistent/image.png",
            mask_base64="base64data",
            prompt="test",
            negative_prompt=""
        )


@pytest.mark.asyncio
async def test_inpaint_image_empty_prompt(sample_image, sample_mask_base64):
    """Test error when prompt is empty."""
    with pytest.raises(ValueError, match="Prompt is required"):
        await inpaint_image(
            image_path=sample_image,
            mask_base64=sample_mask_base64,
            prompt="",
            negative_prompt=""
        )


@pytest.mark.asyncio
async def test_inpaint_image_missing_mask(sample_image):
    """Test error when mask is missing."""
    with pytest.raises(ValueError, match="Mask data is required"):
        await inpaint_image(
            image_path=sample_image,
            mask_base64="",
            prompt="test",
            negative_prompt=""
        )


# ============================================================================
# Image Download Tests
# ============================================================================

@pytest.mark.asyncio
async def test_download_image(tmp_path):
    """Test image download from URL."""
    # Mock httpx response
    mock_response = Mock()
    mock_response.content = b"fake_image_data"
    mock_response.raise_for_status = Mock()

    with patch("app.services.pipeline.inpainting_service.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        output_path = tmp_path / "downloaded.png"
        await _download_image("http://example.com/image.png", output_path)

    # Verify file was written
    assert output_path.exists()
    assert output_path.read_bytes() == b"fake_image_data"


@pytest.mark.asyncio
async def test_download_image_http_error(tmp_path):
    """Test error handling for failed download."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 404")

    with patch("app.services.pipeline.inpainting_service.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        output_path = tmp_path / "failed.png"

        with pytest.raises(Exception, match="HTTP 404"):
            await _download_image("http://example.com/missing.png", output_path)
