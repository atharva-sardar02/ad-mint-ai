"""
Unit tests for brand style extractor service with mocked Replicate API.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import shutil
import json

from app.services.pipeline.brand_style_extractor import (
    extract_brand_style,
    extract_product_style,
    VISION_MODEL_COST_PER_IMAGE,
    VISION_MODEL,
)
from app.services.pipeline.llm_schemas import BrandStyleJSON, ProductStyleJSON


@pytest.fixture
def mock_replicate_client():
    """Mock Replicate client."""
    with patch("app.services.pipeline.brand_style_extractor.replicate.Client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_brand_style_json():
    """Sample brand style JSON response."""
    return {
        "color_palette": {
            "primary_colors": ["#FF5733", "#33FF57"],
            "secondary_colors": ["#3357FF"],
            "accent_colors": ["#FF33F5"]
        },
        "visual_style": {
            "aesthetic": "modern",
            "mood": "sophisticated",
            "composition_style": "centered"
        },
        "typography": {
            "style": "sans-serif",
            "weight": "bold",
            "usage_patterns": "headlines"
        },
        "lighting_cues": "natural",
        "texture_surfaces": "matte",
        "atmosphere_density": "airier",
        "brand_markers": ["logo_placement_style", "iconography_patterns"]
    }


@pytest.fixture
def sample_product_style_json():
    """Sample product style JSON response."""
    return {
        "product_characteristics": {
            "form_factor": "bottle",
            "material_appearance": "glass",
            "surface_quality": "reflective"
        },
        "visual_style": {
            "composition": "centered",
            "background_treatment": "white",
            "perspective": "eye_level"
        },
        "color_profile": {
            "dominant_colors": ["#FFFFFF", "#000000"],
            "contrast_level": "high"
        },
        "product_usage_context": "luxury product in lifestyle imagery"
    }


@pytest.fixture
def temp_image_dir():
    """Create temporary directory with test images."""
    temp_dir = tempfile.mkdtemp()
    image_dir = Path(temp_dir)
    
    # Create dummy image files
    for i in range(3):
        image_path = image_dir / f"test_image_{i}.jpg"
        image_path.write_bytes(b"fake image data")
    
    yield image_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def single_image_path(temp_image_dir):
    """Single image path for product style extraction."""
    return temp_image_dir / "test_image_0.jpg"


@pytest.mark.asyncio
async def test_extract_brand_style_success(mock_replicate_client, temp_image_dir, sample_brand_style_json):
    """Test successful brand style extraction with multiple images."""
    # Mock settings
    with patch("app.services.pipeline.brand_style_extractor.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock Replicate API response
        json_response = json.dumps(sample_brand_style_json)
        mock_replicate_client.run.return_value = json_response
        
        # Get image paths
        image_paths = list(temp_image_dir.glob("*.jpg"))
        
        # Extract brand style
        result = await extract_brand_style(image_paths)
        
        # Verify result
        assert isinstance(result, BrandStyleJSON)
        assert result.color_palette.primary_colors == sample_brand_style_json["color_palette"]["primary_colors"]
        assert result.visual_style.aesthetic == sample_brand_style_json["visual_style"]["aesthetic"]
        assert result.typography.style == sample_brand_style_json["typography"]["style"]
        assert result.lighting_cues == sample_brand_style_json["lighting_cues"]
        assert len(result.brand_markers) == 2
        
        # Verify API was called
        mock_replicate_client.run.assert_called_once()


@pytest.mark.asyncio
async def test_extract_brand_style_with_markdown_code_block(mock_replicate_client, temp_image_dir, sample_brand_style_json):
    """Test brand style extraction when response includes markdown code blocks."""
    with patch("app.services.pipeline.brand_style_extractor.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock response with markdown code block
        json_response = f"```json\n{json.dumps(sample_brand_style_json)}\n```"
        mock_replicate_client.run.return_value = json_response
        
        image_paths = list(temp_image_dir.glob("*.jpg"))
        result = await extract_brand_style(image_paths)
        
        assert isinstance(result, BrandStyleJSON)
        assert result.color_palette.primary_colors == sample_brand_style_json["color_palette"]["primary_colors"]


@pytest.mark.asyncio
async def test_extract_product_style_success(mock_replicate_client, single_image_path, sample_product_style_json):
    """Test successful product style extraction."""
    with patch("app.services.pipeline.brand_style_extractor.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock Replicate API response
        json_response = json.dumps(sample_product_style_json)
        mock_replicate_client.run.return_value = json_response
        
        # Extract product style
        result = await extract_product_style(single_image_path)
        
        # Verify result
        assert isinstance(result, ProductStyleJSON)
        assert result.product_characteristics.form_factor == sample_product_style_json["product_characteristics"]["form_factor"]
        assert result.visual_style.composition == sample_product_style_json["visual_style"]["composition"]
        assert result.color_profile.dominant_colors == sample_product_style_json["color_profile"]["dominant_colors"]
        assert result.color_profile.contrast_level == sample_product_style_json["color_profile"]["contrast_level"]
        
        # Verify API was called
        mock_replicate_client.run.assert_called_once()


@pytest.mark.asyncio
async def test_extract_brand_style_no_images():
    """Test brand style extraction with no images raises ValueError."""
    with pytest.raises(ValueError, match="No images provided"):
        await extract_brand_style([])


@pytest.mark.asyncio
async def test_extract_brand_style_missing_image(temp_image_dir):
    """Test brand style extraction with missing image file."""
    missing_path = temp_image_dir / "nonexistent.jpg"
    
    with pytest.raises(ValueError, match="not found"):
        await extract_brand_style([missing_path])


@pytest.mark.asyncio
async def test_extract_product_style_missing_image():
    """Test product style extraction with missing image file."""
    missing_path = Path("/nonexistent/image.jpg")
    
    with pytest.raises(ValueError, match="not found"):
        await extract_product_style(missing_path)


@pytest.mark.asyncio
async def test_extract_brand_style_invalid_json(mock_replicate_client, temp_image_dir):
    """Test brand style extraction with invalid JSON response."""
    with patch("app.services.pipeline.brand_style_extractor.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock invalid JSON response
        mock_replicate_client.run.return_value = "This is not valid JSON"
        
        image_paths = list(temp_image_dir.glob("*.jpg"))
        
        with pytest.raises(ValueError, match="Invalid JSON response"):
            await extract_brand_style(image_paths)


@pytest.mark.asyncio
async def test_extract_brand_style_retry_on_error(mock_replicate_client, temp_image_dir, sample_brand_style_json):
    """Test brand style extraction retries on API errors."""
    with patch("app.services.pipeline.brand_style_extractor.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock ReplicateError on first call, success on second
        import replicate
        mock_replicate_client.run.side_effect = [
            replicate.exceptions.ReplicateError("Rate limit exceeded"),
            json.dumps(sample_brand_style_json)
        ]
        
        image_paths = list(temp_image_dir.glob("*.jpg"))
        
        # Should succeed after retry
        result = await extract_brand_style(image_paths)
        
        assert isinstance(result, BrandStyleJSON)
        assert mock_replicate_client.run.call_count == 2


@pytest.mark.asyncio
async def test_extract_brand_style_max_retries_exceeded(mock_replicate_client, temp_image_dir):
    """Test brand style extraction fails after max retries."""
    with patch("app.services.pipeline.brand_style_extractor.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock ReplicateError on all attempts
        import replicate
        mock_replicate_client.run.side_effect = replicate.exceptions.ReplicateError("API error")
        
        image_paths = list(temp_image_dir.glob("*.jpg"))
        
        with pytest.raises(RuntimeError, match="after 3 attempts"):
            await extract_brand_style(image_paths)
        
        # Should have tried 3 times
        assert mock_replicate_client.run.call_count == 3


@pytest.mark.asyncio
async def test_extract_brand_style_no_api_token(temp_image_dir):
    """Test brand style extraction fails when API token is missing."""
    with patch("app.services.pipeline.brand_style_extractor.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = None
        
        image_paths = list(temp_image_dir.glob("*.jpg"))
        
        with pytest.raises(ValueError, match="not configured"):
            await extract_brand_style(image_paths)


@pytest.mark.asyncio
async def test_extract_brand_style_validation_error(mock_replicate_client, temp_image_dir):
    """Test brand style extraction with invalid schema data."""
    with patch("app.services.pipeline.brand_style_extractor.settings") as mock_settings:
        mock_settings.REPLICATE_API_TOKEN = "test-token"
        
        # Mock response with invalid color format (not hex)
        invalid_json = {
            "color_palette": {
                "primary_colors": ["not-a-hex-color"],
                "secondary_colors": [],
                "accent_colors": []
            },
            "visual_style": {"aesthetic": "modern", "mood": "sophisticated", "composition_style": "centered"},
            "typography": {"style": "sans-serif", "weight": "bold", "usage_patterns": "headlines"},
            "lighting_cues": "natural",
            "texture_surfaces": "matte",
            "atmosphere_density": "airier",
            "brand_markers": []
        }
        
        mock_replicate_client.run.return_value = json.dumps(invalid_json)
        
        image_paths = list(temp_image_dir.glob("*.jpg"))
        
        with pytest.raises(ValueError, match="Invalid brand style data"):
            await extract_brand_style(image_paths)

