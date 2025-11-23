"""
Unit tests for image processor with Vision API integration.

Tests AC#4, AC#5 from Story 1.2
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.media.image_processor import ImageProcessor, get_image_processor
from app.schemas.unified_pipeline import ReferenceImageAnalysis


@pytest.fixture
def vision_api_response():
    """Mock successful Vision API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "character_description": "Young woman in her 20s, casual athletic wear",
                        "product_features": "Blue eco-friendly water bottle, 500ml capacity",
                        "colors": ["#1E90FF", "#FFFFFF", "#333333"],
                        "style": "photorealistic",
                        "environment": "outdoor park setting, natural sunlight"
                    })
                }
            }
        ]
    }


@pytest.fixture
def vision_api_response_with_markdown():
    """Mock Vision API response with markdown code block."""
    return {
        "choices": [
            {
                "message": {
                    "content": "```json\n" + json.dumps({
                        "character_description": "Athletic male, running gear",
                        "product_features": "Sports drink bottle",
                        "colors": ["#FF0000"],
                        "style": "illustrated",
                        "environment": "gym interior"
                    }) + "\n```"
                }
            }
        ]
    }


@pytest.fixture
def mock_httpx_client(vision_api_response):
    """Mock httpx async client."""
    with patch("app.services.media.image_processor.httpx.AsyncClient") as mock_client:
        # Create mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = vision_api_response

        # Create mock context manager
        mock_instance = MagicMock()
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value = mock_instance

        yield mock_instance


class TestImageProcessorInitialization:
    """Test image processor initialization."""

    def test_init_with_api_key(self):
        """Test processor initializes with API key from settings."""
        with patch("app.services.media.image_processor.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            processor = ImageProcessor()
            assert processor.api_key == "sk-test-key"
            assert processor.model == "gpt-4-vision-preview"

    def test_get_image_processor_singleton(self):
        """Test get_image_processor returns singleton instance."""
        processor1 = get_image_processor()
        processor2 = get_image_processor()
        assert processor1 is processor2


class TestVisionAnalysis:
    """Test AC#4: GPT-4 Vision analysis."""

    @pytest.mark.asyncio
    async def test_analyze_with_vision_success(self, mock_httpx_client, vision_api_response):
        """Test successful Vision analysis returns ReferenceImageAnalysis."""
        processor = ImageProcessor()
        processor.api_key = "sk-test-key"

        result = await processor.analyze_with_vision(
            image_url="https://example.com/image.jpg",
            image_type="product"
        )

        # Check result is ReferenceImageAnalysis
        assert isinstance(result, ReferenceImageAnalysis)

        # Check all fields populated
        assert result.character_description == "Young woman in her 20s, casual athletic wear"
        assert result.product_features == "Blue eco-friendly water bottle, 500ml capacity"
        assert result.colors == ["#1E90FF", "#FFFFFF", "#333333"]
        assert result.style == "photorealistic"
        assert result.environment == "outdoor park setting, natural sunlight"

    @pytest.mark.asyncio
    async def test_analyze_with_vision_calls_api_correctly(self, mock_httpx_client):
        """Test Vision API called with correct payload."""
        processor = ImageProcessor()
        processor.api_key = "sk-test-key"

        await processor.analyze_with_vision(
            image_url="https://example.com/image.jpg",
            image_type="character"
        )

        # Check API was called
        assert mock_httpx_client.post.called

        # Check payload structure
        call_args = mock_httpx_client.post.call_args
        payload = call_args.kwargs["json"]

        assert payload["model"] == "gpt-4-vision-preview"
        assert len(payload["messages"]) == 1
        assert len(payload["messages"][0]["content"]) == 2  # Text + image_url

    @pytest.mark.asyncio
    async def test_analyze_with_vision_handles_markdown_response(self, vision_api_response_with_markdown):
        """Test Vision API response with markdown code blocks."""
        with patch("app.services.media.image_processor.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = vision_api_response_with_markdown

            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance

            processor = ImageProcessor()
            processor.api_key = "sk-test-key"

            result = await processor.analyze_with_vision(
                image_url="https://example.com/image.jpg",
                image_type="product"
            )

            # Should successfully parse despite markdown
            assert result.character_description == "Athletic male, running gear"
            assert result.product_features == "Sports drink bottle"
            assert result.colors == ["#FF0000"]


class TestVisionAnalysisErrorHandling:
    """Test Vision API error handling and retries."""

    @pytest.mark.asyncio
    async def test_analyze_with_vision_retries_on_500(self):
        """Test Vision API retries on transient 5xx errors."""
        with patch("app.services.media.image_processor.httpx.AsyncClient") as mock_client:
            # Mock response: first 2 calls fail, third succeeds
            mock_responses = [
                MagicMock(status_code=500),
                MagicMock(status_code=502),
                MagicMock(status_code=200, json=MagicMock(return_value={
                    "choices": [{"message": {"content": json.dumps({
                        "character_description": None,
                        "product_features": None,
                        "colors": ["#000000"],
                        "style": "test",
                        "environment": "test"
                    })}}]
                }))
            ]

            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(side_effect=mock_responses)
            mock_client.return_value.__aenter__.return_value = mock_instance

            processor = ImageProcessor()
            processor.api_key = "sk-test-key"

            result = await processor.analyze_with_vision(
                image_url="https://example.com/image.jpg",
                image_type="product"
            )

            # Should eventually succeed after retries
            assert result is not None
            assert mock_instance.post.call_count == 3

    @pytest.mark.asyncio
    async def test_analyze_with_vision_fails_on_4xx(self):
        """Test Vision API fails immediately on permanent 4xx errors."""
        with patch("app.services.media.image_processor.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock(
                status_code=400,
                json=MagicMock(return_value={"error": {"message": "Invalid request"}})
            )

            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance

            processor = ImageProcessor()
            processor.api_key = "sk-test-key"

            with pytest.raises(RuntimeError, match="Vision API error"):
                await processor.analyze_with_vision(
                    image_url="https://example.com/image.jpg",
                    image_type="product"
                )

            # Should not retry on 4xx
            assert mock_instance.post.call_count == 1


class TestVisionAnalysisPromptBuilder:
    """Test Vision analysis prompt construction."""

    def test_build_analysis_prompt_includes_image_type(self):
        """Test analysis prompt includes image type hint."""
        processor = ImageProcessor()
        prompt = processor._build_analysis_prompt("product")

        assert "product" in prompt.lower()

    def test_build_analysis_prompt_includes_all_fields(self):
        """Test analysis prompt requests all 5 characteristics."""
        processor = ImageProcessor()
        prompt = processor._build_analysis_prompt("character")

        assert "character" in prompt.lower() or "Character" in prompt
        assert "product" in prompt.lower() or "Product" in prompt
        assert "color" in prompt.lower() or "Color" in prompt
        assert "style" in prompt.lower() or "Style" in prompt or "visual" in prompt.lower()
        assert "environment" in prompt.lower() or "Environment" in prompt

    def test_build_analysis_prompt_requests_json_format(self):
        """Test analysis prompt requests JSON output."""
        processor = ImageProcessor()
        prompt = processor._build_analysis_prompt("environment")

        assert "JSON" in prompt or "json" in prompt


class TestVisionResponseParsing:
    """Test AC#5: Parse Vision API response into schema."""

    def test_parse_vision_response_success(self, vision_api_response):
        """Test successful parsing of Vision API response."""
        processor = ImageProcessor()
        result = processor._parse_vision_response(vision_api_response)

        assert isinstance(result, ReferenceImageAnalysis)
        assert result.character_description is not None
        assert result.colors is not None
        assert len(result.colors) > 0

    def test_parse_vision_response_handles_null_fields(self):
        """Test parsing handles null character/product fields."""
        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "character_description": None,
                            "product_features": None,
                            "colors": ["#FF0000"],
                            "style": "abstract",
                            "environment": "studio"
                        })
                    }
                }
            ]
        }

        processor = ImageProcessor()
        result = processor._parse_vision_response(response)

        assert result.character_description is None
        assert result.product_features is None
        assert result.colors == ["#FF0000"]

    def test_parse_vision_response_fallback_on_error(self):
        """Test parsing returns fallback analysis on error."""
        malformed_response = {"choices": [{"message": {"content": "Not JSON"}}]}

        processor = ImageProcessor()
        result = processor._parse_vision_response(malformed_response)

        # Should return fallback instead of crashing
        assert isinstance(result, ReferenceImageAnalysis)
        assert "Unable to analyze" in result.character_description
