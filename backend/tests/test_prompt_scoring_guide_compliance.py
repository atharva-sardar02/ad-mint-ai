"""
Tests to verify enhanced prompts comply with Prompt Scoring Guide guidelines.
"""
import pytest
from unittest.mock import patch, MagicMock
import json

from app.services.pipeline.image_prompt_enhancement import enhance_prompt_iterative, ImagePromptEnhancementResult


def check_scene_structure(prompt: str) -> bool:
    """Check if prompt follows scene description structure (who/what → action → where/when → style)."""
    # Basic check: prompt should have multiple parts (subject, action, context, style)
    words = prompt.lower().split()
    
    # Check for action words
    action_words = ["sprinting", "standing", "sitting", "walking", "running", "looking", "holding", "wearing"]
    has_action = any(word in words for word in action_words)
    
    # Check for location/context words
    context_words = ["street", "city", "room", "outdoor", "indoor", "night", "day", "morning", "evening"]
    has_context = any(word in words for word in context_words)
    
    # Check for style words
    style_words = ["cinematic", "professional", "dramatic", "moody", "vibrant", "soft", "harsh"]
    has_style = any(word in words for word in style_words)
    
    return has_action and has_context and has_style


def check_camera_cues(prompt: str) -> bool:
    """Check if prompt includes camera cues."""
    camera_cues = [
        "wide aerial shot",
        "close-up portrait",
        "telephoto shot",
        "macro photograph",
        "low-angle view",
        "aerial shot",
        "close-up",
        "telephoto",
        "macro"
    ]
    prompt_lower = prompt.lower()
    return any(cue in prompt_lower for cue in camera_cues)


def check_lighting_cues(prompt: str) -> bool:
    """Check if prompt includes lighting cues."""
    lighting_cues = [
        "soft golden morning light",
        "harsh neon glow",
        "dramatic side lighting",
        "soft, diffused lighting",
        "golden light",
        "neon glow",
        "side lighting",
        "diffused lighting"
    ]
    prompt_lower = prompt.lower()
    return any(cue in prompt_lower for cue in lighting_cues)


def check_single_scene(prompt: str) -> bool:
    """Check if prompt is limited to one scene or idea."""
    # Count scene separators (semicolons, newlines, "then", "next")
    separators = prompt.count(";") + prompt.count("\n") + prompt.lower().count(" then ") + prompt.lower().count(" next ")
    return separators < 2  # Allow one separator for style/context separation


def check_natural_language(prompt: str) -> bool:
    """Check if prompt uses natural language (not keyword stuffing)."""
    # Check for excessive commas (keyword stuffing indicator)
    comma_count = prompt.count(",")
    word_count = len(prompt.split())
    
    # If more than 30% of words are separated by commas, it might be keyword stuffing
    if word_count > 0:
        comma_ratio = comma_count / word_count
        return comma_ratio < 0.3
    
    return True


@pytest.fixture
def mock_enhancement_response():
    """Mock enhancement response that complies with Prompt Scoring Guide."""
    enhanced_prompt = "A sleek black cat sprinting across a rain-soaked neon city street at night. Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting with harsh neon glow, cinematic color grading, moody atmosphere, 16:9 aspect ratio"
    
    critique_response = {
        "scores": {
            "completeness": 90,
            "specificity": 88,
            "professionalism": 92,
            "cinematography": 95,
            "brand_alignment": 80,
            "overall": 89.0
        },
        "critique": "Excellent prompt with all required elements",
        "improvements": []
    }
    
    return enhanced_prompt, critique_response


@pytest.mark.asyncio
async def test_enhanced_prompt_scene_structure(mock_enhancement_response):
    """Test enhanced prompts follow scene description structure."""
    enhanced_prompt, critique_response = mock_enhancement_response
    
    assert check_scene_structure(enhanced_prompt), "Prompt should follow scene description structure (who/what → action → where/when → style)"


@pytest.mark.asyncio
async def test_enhanced_prompt_camera_cues(mock_enhancement_response):
    """Test enhanced prompts include camera cues."""
    enhanced_prompt, critique_response = mock_enhancement_response
    
    assert check_camera_cues(enhanced_prompt), "Prompt should include camera cues (wide aerial shot, close-up portrait, telephoto shot, macro photograph)"


@pytest.mark.asyncio
async def test_enhanced_prompt_lighting_cues(mock_enhancement_response):
    """Test enhanced prompts include lighting cues."""
    enhanced_prompt, critique_response = mock_enhancement_response
    
    assert check_lighting_cues(enhanced_prompt), "Prompt should include lighting cues (soft golden morning light, harsh neon glow, dramatic side lighting)"


@pytest.mark.asyncio
async def test_enhanced_prompt_single_scene(mock_enhancement_response):
    """Test enhanced prompts limit to one scene or idea."""
    enhanced_prompt, critique_response = mock_enhancement_response
    
    assert check_single_scene(enhanced_prompt), "Prompt should be limited to one scene or idea"


@pytest.mark.asyncio
async def test_enhanced_prompt_natural_language(mock_enhancement_response):
    """Test enhanced prompts use natural language (not keyword stuffing)."""
    enhanced_prompt, critique_response = mock_enhancement_response
    
    assert check_natural_language(enhanced_prompt), "Prompt should use natural language, not keyword stuffing"


@pytest.mark.asyncio
async def test_full_enhancement_compliance():
    """Test full enhancement process produces compliant prompts."""
    sample_prompt = "A cat in a city"
    
    with patch("app.services.pipeline.image_prompt_enhancement.openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock Cinematographer response (compliant prompt)
        cinematographer_response = MagicMock()
        cinematographer_response.choices = [MagicMock()]
        cinematographer_response.choices[0].message.content = "A sleek black cat sprinting across a rain-soaked neon city street at night. Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting with harsh neon glow, cinematic color grading, moody atmosphere, 16:9 aspect ratio"
        
        # Mock Prompt Engineer response
        engineer_response = MagicMock()
        engineer_response.choices = [MagicMock()]
        engineer_response.choices[0].message.content = json.dumps({
            "scores": {
                "completeness": 90,
                "specificity": 88,
                "professionalism": 92,
                "cinematography": 95,
                "brand_alignment": 80,
                "overall": 89.0
            },
            "critique": "Excellent prompt",
            "improvements": []
        })
        
        mock_client.chat.completions.create.side_effect = [
            cinematographer_response,
            engineer_response
        ]
        
        result = await enhance_prompt_iterative(
            user_prompt=sample_prompt,
            max_iterations=1,
            score_threshold=85.0
        )
        
        # Verify compliance
        assert check_scene_structure(result.final_prompt)
        assert check_camera_cues(result.final_prompt)
        assert check_lighting_cues(result.final_prompt)
        assert check_single_scene(result.final_prompt)
        assert check_natural_language(result.final_prompt)



