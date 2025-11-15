"""
Unit tests for LLM enhancement service with mocked OpenAI API.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
import openai
from pydantic import ValidationError

from app.services.pipeline.llm_enhancement import enhance_prompt_with_llm
from app.schemas.generation import AdSpecification, BrandGuidelines, AdSpec, Scene, TextOverlay


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch("app.services.pipeline.llm_enhancement.openai.OpenAI") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def valid_llm_response():
    """Valid LLM response JSON."""
    return {
        "product_description": "A premium coffee maker",
        "brand_guidelines": {
            "brand_name": "CoffeePro",
            "brand_colors": ["#8B4513", "#D2691E"],
            "visual_style_keywords": "luxury, modern, elegant",
            "mood": "sophisticated"
        },
        "ad_specifications": {
            "target_audience": "Coffee enthusiasts",
            "call_to_action": "Order now",
            "tone": "premium"
        },
        "framework": "PAS",
        "scenes": [
            {
                "scene_number": 1,
                "scene_type": "Problem",
                "visual_prompt": "Show someone struggling with a cheap coffee maker",
                "text_overlay": {
                    "text": "Tired of bad coffee?",
                    "position": "top",
                    "font_size": 48,
                    "color": "#8B4513",
                    "animation": "fade_in"
                },
                "duration": 5
            },
            {
                "scene_number": 2,
                "scene_type": "Agitation",
                "visual_prompt": "Show the frustration of inconsistent coffee",
                "text_overlay": {
                    "text": "Every cup is different",
                    "position": "center",
                    "font_size": 48,
                    "color": "#8B4513",
                    "animation": "slide_up"
                },
                "duration": 5
            },
            {
                "scene_number": 3,
                "scene_type": "Solution",
                "visual_prompt": "Show CoffeePro making perfect espresso",
                "text_overlay": {
                    "text": "CoffeePro - Perfect every time",
                    "position": "bottom",
                    "font_size": 48,
                    "color": "#D2691E",
                    "animation": "fade_in"
                },
                "duration": 5
            }
        ]
    }


@pytest.mark.asyncio
async def test_enhance_prompt_success(mock_openai_client, valid_llm_response):
    """Test successful LLM enhancement with valid response."""
    # Mock OpenAI API response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(valid_llm_response)
    mock_openai_client.chat.completions.create.return_value = mock_response

    with patch("app.services.pipeline.llm_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"

        result = await enhance_prompt_with_llm("Create a luxury coffee maker ad")

        assert isinstance(result, AdSpecification)
        assert result.framework == "PAS"
        assert len(result.scenes) == 3
        assert result.product_description == "A premium coffee maker"
        assert result.brand_guidelines.brand_name == "CoffeePro"


@pytest.mark.asyncio
async def test_enhance_prompt_invalid_json(mock_openai_client):
    """Test LLM enhancement with invalid JSON response."""
    # Mock OpenAI API response with invalid JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is not valid JSON {"
    mock_openai_client.chat.completions.create.return_value = mock_response

    with patch("app.services.pipeline.llm_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"

        with pytest.raises(ValueError, match="LLM returned invalid JSON"):
            await enhance_prompt_with_llm("Create a luxury coffee maker ad")


@pytest.mark.asyncio
async def test_enhance_prompt_pydantic_validation_failure(mock_openai_client):
    """Test LLM enhancement with response that fails Pydantic validation."""
    # Mock OpenAI API response with invalid structure (missing required fields)
    invalid_response = {
        "product_description": "A premium coffee maker",
        # Missing brand_guidelines, ad_specifications, framework, scenes
    }
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_openai_client.chat.completions.create.return_value = mock_response

    with patch("app.services.pipeline.llm_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"

        with pytest.raises(ValueError, match="doesn't match schema"):
            await enhance_prompt_with_llm("Create a luxury coffee maker ad")


@pytest.mark.asyncio
async def test_enhance_prompt_api_error_retry(mock_openai_client):
    """Test LLM enhancement with API error and retry logic."""
    # Mock OpenAI API to fail twice, then succeed
    valid_response = {
        "product_description": "A premium coffee maker",
        "brand_guidelines": {
            "brand_name": "CoffeePro",
            "brand_colors": ["#8B4513"],
            "visual_style_keywords": "luxury",
            "mood": "sophisticated"
        },
        "ad_specifications": {
            "target_audience": "Coffee enthusiasts",
            "call_to_action": "Order now",
            "tone": "premium"
        },
        "framework": "PAS",
        "scenes": [
            {
                "scene_number": 1,
                "scene_type": "Problem",
                "visual_prompt": "Show someone struggling",
                "text_overlay": {
                    "text": "Tired of bad coffee?",
                    "position": "top",
                    "font_size": 48,
                    "color": "#8B4513",
                    "animation": "fade_in"
                },
                "duration": 5
            },
            {
                "scene_number": 2,
                "scene_type": "Agitation",
                "visual_prompt": "Show frustration",
                "text_overlay": {
                    "text": "Every cup is different",
                    "position": "center",
                    "font_size": 48,
                    "color": "#8B4513",
                    "animation": "slide_up"
                },
                "duration": 5
            },
            {
                "scene_number": 3,
                "scene_type": "Solution",
                "visual_prompt": "Show CoffeePro",
                "text_overlay": {
                    "text": "CoffeePro - Perfect every time",
                    "position": "bottom",
                    "font_size": 48,
                    "color": "#8B4513",
                    "animation": "fade_in"
                },
                "duration": 5
            }
        ]
    }

    # Fail twice, then succeed
    mock_openai_client.chat.completions.create.side_effect = [
        openai.APIError(message="API error", request=None, body=None),
        openai.APIError(message="API error", request=None, body=None),
        MagicMock(choices=[MagicMock(message=MagicMock(content=json.dumps(valid_response)))]),
    ]

    with patch("app.services.pipeline.llm_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"

        result = await enhance_prompt_with_llm("Create a luxury coffee maker ad")

        assert isinstance(result, AdSpecification)
        assert result.framework == "PAS"
        # Verify it retried (called 3 times)
        assert mock_openai_client.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_enhance_prompt_api_error_max_retries(mock_openai_client):
    """Test LLM enhancement fails after max retries."""
    # Mock OpenAI API to always fail
    mock_openai_client.chat.completions.create.side_effect = openai.APIError(
        message="API error",
        request=None,
        body=None
    )

    with patch("app.services.pipeline.llm_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"

        with pytest.raises(openai.APIError):
            await enhance_prompt_with_llm("Create a luxury coffee maker ad")

        # Verify it retried max_retries times (3)
        assert mock_openai_client.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_enhance_prompt_missing_api_key():
    """Test LLM enhancement fails when API key is missing."""
    with patch("app.services.pipeline.llm_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None

        with pytest.raises(ValueError, match="OpenAI API key is not configured"):
            await enhance_prompt_with_llm("Create a luxury coffee maker ad")


@pytest.mark.asyncio
async def test_enhance_prompt_validates_framework(mock_openai_client):
    """Test LLM enhancement validates framework is one of PAS, BAB, or AIDA."""
    invalid_response = {
        "product_description": "A premium coffee maker",
        "brand_guidelines": {
            "brand_name": "CoffeePro",
            "brand_colors": ["#8B4513"],
            "visual_style_keywords": "luxury",
            "mood": "sophisticated"
        },
        "ad_specifications": {
            "target_audience": "Coffee enthusiasts",
            "call_to_action": "Order now",
            "tone": "premium"
        },
        "framework": "INVALID",  # Invalid framework
        "scenes": [
            {
                "scene_number": 1,
                "scene_type": "Problem",
                "visual_prompt": "Show someone struggling",
                "text_overlay": {
                    "text": "Tired of bad coffee?",
                    "position": "top",
                    "font_size": 48,
                    "color": "#8B4513",
                    "animation": "fade_in"
                },
                "duration": 5
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_openai_client.chat.completions.create.return_value = mock_response

    with patch("app.services.pipeline.llm_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = "test-key"

        with pytest.raises(ValueError, match="doesn't match schema"):
            await enhance_prompt_with_llm("Create a luxury coffee maker ad")

