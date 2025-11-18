"""
Unit tests for image prompt enhancement service with mocked OpenAI API.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import tempfile
import shutil

from app.services.pipeline.image_prompt_enhancement import (
    enhance_prompt_iterative,
    ImagePromptEnhancementResult,
    _cinematographer_enhance,
    _prompt_engineer_critique,
    _quick_score_prompt
)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch("app.services.pipeline.image_prompt_enhancement.openai.OpenAI") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_prompt():
    """Sample basic image prompt."""
    return "A cat in a city"


@pytest.fixture
def enhanced_prompt():
    """Sample enhanced prompt."""
    return "A sleek black cat sprinting across a rain-soaked neon city street at night. Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting with harsh neon glow, cinematic color grading, moody atmosphere, 16:9 aspect ratio"


@pytest.fixture
def critique_response():
    """Sample critique response from Prompt Engineer."""
    return {
        "scores": {
            "completeness": 85,
            "specificity": 82,
            "professionalism": 90,
            "cinematography": 88,
            "brand_alignment": 75,
            "overall": 84.0
        },
        "critique": "The prompt is well-structured with good cinematography details. Could benefit from more brand-specific elements.",
        "improvements": [
            "Add more specific brand colors or style keywords",
            "Include more detailed composition notes"
        ]
    }


@pytest.mark.asyncio
async def test_quick_score_prompt_basic():
    """Test quick scoring for a basic prompt."""
    prompt = "A cat"
    score = _quick_score_prompt(prompt)
    
    assert "completeness" in score
    assert "specificity" in score
    assert "professionalism" in score
    assert "cinematography" in score
    assert "brand_alignment" in score
    assert "overall" in score
    
    assert all(0 <= v <= 100 for v in score.values())


@pytest.mark.asyncio
async def test_quick_score_prompt_detailed():
    """Test quick scoring for a detailed prompt."""
    prompt = "A sleek black cat sprinting across a rain-soaked neon city street at night, Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting"
    score = _quick_score_prompt(prompt)
    
    # Detailed prompts should score higher
    assert score["overall"] > 50
    assert score["cinematography"] > 50  # Has camera details


@pytest.mark.asyncio
async def test_cinematographer_enhance(mock_openai_client, sample_prompt, enhanced_prompt):
    """Test Cinematographer agent enhancement."""
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = enhanced_prompt
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await _cinematographer_enhance(sample_prompt)
    
    assert result == enhanced_prompt
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_cinematographer_enhance_no_api_key():
    """Test Cinematographer enhancement fails without API key."""
    with patch("app.services.pipeline.image_prompt_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY not configured"):
            await _cinematographer_enhance("test prompt")


@pytest.mark.asyncio
async def test_prompt_engineer_critique(mock_openai_client, enhanced_prompt, critique_response):
    """Test Prompt Engineer critique and scoring."""
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(critique_response)
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await _prompt_engineer_critique(enhanced_prompt)
    
    assert "scores" in result
    assert "critique" in result
    assert "improvements" in result
    assert result["scores"]["overall"] == 84.0
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_prompt_engineer_critique_calculates_overall(mock_openai_client, enhanced_prompt):
    """Test Prompt Engineer calculates overall score if not provided."""
    critique_response = {
        "scores": {
            "completeness": 80,
            "specificity": 75,
            "professionalism": 85,
            "cinematography": 70,
            "brand_alignment": 65
        },
        "critique": "Good prompt",
        "improvements": []
    }
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(critique_response)
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await _prompt_engineer_critique(enhanced_prompt)
    
    # Should calculate overall score
    assert "overall" in result["scores"]
    expected_overall = (
        80 * 0.25 + 75 * 0.25 + 85 * 0.20 + 70 * 0.15 + 65 * 0.15
    )
    assert abs(result["scores"]["overall"] - expected_overall) < 0.1


@pytest.mark.asyncio
async def test_prompt_engineer_critique_invalid_structure(mock_openai_client, enhanced_prompt):
    """Test Prompt Engineer critique fails with invalid response structure."""
    invalid_response = {"scores": {}}  # Missing critique and improvements
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(invalid_response)
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    with pytest.raises(ValueError, match="Invalid critique response structure"):
        await _prompt_engineer_critique(enhanced_prompt)


@pytest.mark.asyncio
async def test_enhance_prompt_iterative_single_iteration(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test iterative enhancement with single iteration (threshold met)."""
    # Set threshold high so it stops after first iteration
    critique_response["scores"]["overall"] = 90.0
    
    # Mock Cinematographer response
    cinematographer_response = MagicMock()
    cinematographer_response.choices = [MagicMock()]
    cinematographer_response.choices[0].message.content = enhanced_prompt
    
    # Mock Prompt Engineer response
    engineer_response = MagicMock()
    engineer_response.choices = [MagicMock()]
    engineer_response.choices[0].message.content = json.dumps(critique_response)
    
    mock_openai_client.chat.completions.create.side_effect = [
        cinematographer_response,
        engineer_response
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir) / "traces"
        result = await enhance_prompt_iterative(
            user_prompt=sample_prompt,
            max_iterations=3,
            score_threshold=85.0,
            trace_dir=trace_dir
        )
        
        assert isinstance(result, ImagePromptEnhancementResult)
        assert result.original_prompt == sample_prompt
        assert result.final_prompt == enhanced_prompt
        assert result.total_iterations == 1
        assert result.final_score["overall"] == 90.0
        
        # Check trace files created
        assert (trace_dir / "00_original_prompt.txt").exists()
        assert (trace_dir / "01_agent1_iteration_1.txt").exists()
        assert (trace_dir / "02_agent2_iteration_1.txt").exists()
        assert (trace_dir / "05_final_enhanced_prompt.txt").exists()
        assert (trace_dir / "prompt_trace_summary.json").exists()


@pytest.mark.asyncio
async def test_enhance_prompt_iterative_max_iterations(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test iterative enhancement reaches max iterations."""
    # Set threshold low so it continues
    critique_response["scores"]["overall"] = 70.0
    
    # Mock responses for 3 iterations
    cinematographer_response = MagicMock()
    cinematographer_response.choices = [MagicMock()]
    cinematographer_response.choices[0].message.content = enhanced_prompt
    
    engineer_response = MagicMock()
    engineer_response.choices = [MagicMock()]
    engineer_response.choices[0].message.content = json.dumps(critique_response)
    
    # 3 iterations = 3 cinematographer + 3 engineer calls
    mock_openai_client.chat.completions.create.side_effect = [
        cinematographer_response, engineer_response,
        cinematographer_response, engineer_response,
        cinematographer_response, engineer_response
    ]
    
    result = await enhance_prompt_iterative(
        user_prompt=sample_prompt,
        max_iterations=3,
        score_threshold=90.0  # High threshold so it doesn't stop early
    )
    
    assert result.total_iterations == 3


@pytest.mark.asyncio
async def test_enhance_prompt_iterative_convergence(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test iterative enhancement stops on convergence (no improvement)."""
    # First iteration: score 70
    critique_response_1 = critique_response.copy()
    critique_response_1["scores"]["overall"] = 70.0
    
    # Second iteration: score 71 (improvement < 2 points = convergence)
    critique_response_2 = critique_response.copy()
    critique_response_2["scores"]["overall"] = 71.0
    
    cinematographer_response = MagicMock()
    cinematographer_response.choices = [MagicMock()]
    cinematographer_response.choices[0].message.content = enhanced_prompt
    
    engineer_response_1 = MagicMock()
    engineer_response_1.choices = [MagicMock()]
    engineer_response_1.choices[0].message.content = json.dumps(critique_response_1)
    
    engineer_response_2 = MagicMock()
    engineer_response_2.choices = [MagicMock()]
    engineer_response_2.choices[0].message.content = json.dumps(critique_response_2)
    
    mock_openai_client.chat.completions.create.side_effect = [
        cinematographer_response, engineer_response_1,
        cinematographer_response, engineer_response_2
    ]
    
    result = await enhance_prompt_iterative(
        user_prompt=sample_prompt,
        max_iterations=3,
        score_threshold=90.0
    )
    
    # Should stop after 2 iterations due to convergence
    assert result.total_iterations == 2


@pytest.mark.asyncio
async def test_enhance_prompt_iterative_high_initial_score(mock_openai_client, sample_prompt):
    """Test enhancement skips if initial score is already high."""
    # Create a detailed prompt that scores high
    detailed_prompt = "A sleek black cat sprinting across a rain-soaked neon city street at night, Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting with harsh neon glow, cinematic color grading, moody atmosphere, 16:9 aspect ratio, professional advertising quality"
    
    result = await enhance_prompt_iterative(
        user_prompt=detailed_prompt,
        max_iterations=3,
        score_threshold=85.0
    )
    
    # Should skip enhancement (total_iterations = 0)
    assert result.total_iterations == 0
    assert result.final_prompt == detailed_prompt
    # OpenAI should not be called
    mock_openai_client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_enhance_prompt_iterative_trace_files(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test trace files are created correctly."""
    critique_response["scores"]["overall"] = 90.0
    
    cinematographer_response = MagicMock()
    cinematographer_response.choices = [MagicMock()]
    cinematographer_response.choices[0].message.content = enhanced_prompt
    
    engineer_response = MagicMock()
    engineer_response.choices = [MagicMock()]
    engineer_response.choices[0].message.content = json.dumps(critique_response)
    
    mock_openai_client.chat.completions.create.side_effect = [
        cinematographer_response,
        engineer_response
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir) / "traces"
        result = await enhance_prompt_iterative(
            user_prompt=sample_prompt,
            max_iterations=3,
            score_threshold=85.0,
            trace_dir=trace_dir
        )
        
        # Check all trace files exist
        assert (trace_dir / "00_original_prompt.txt").exists()
        assert (trace_dir / "01_agent1_iteration_1.txt").exists()
        assert (trace_dir / "02_agent2_iteration_1.txt").exists()
        assert (trace_dir / "05_final_enhanced_prompt.txt").exists()
        assert (trace_dir / "prompt_trace_summary.json").exists()
        
        # Check content
        original = (trace_dir / "00_original_prompt.txt").read_text()
        assert original == sample_prompt
        
        final = (trace_dir / "05_final_enhanced_prompt.txt").read_text()
        assert final == enhanced_prompt
        
        # Check JSON summary
        summary = json.loads((trace_dir / "prompt_trace_summary.json").read_text())
        assert summary["original_prompt"] == sample_prompt
        assert summary["final_prompt"] == enhanced_prompt
        assert summary["total_iterations"] == 1
        assert "iterations" in summary
        assert len(summary["iterations"]) == 1


@pytest.mark.asyncio
async def test_enhance_prompt_iterative_no_trace_dir(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test enhancement works without trace directory."""
    critique_response["scores"]["overall"] = 90.0
    
    cinematographer_response = MagicMock()
    cinematographer_response.choices = [MagicMock()]
    cinematographer_response.choices[0].message.content = enhanced_prompt
    
    engineer_response = MagicMock()
    engineer_response.choices = [MagicMock()]
    engineer_response.choices[0].message.content = json.dumps(critique_response)
    
    mock_openai_client.chat.completions.create.side_effect = [
        cinematographer_response,
        engineer_response
    ]
    
    result = await enhance_prompt_iterative(
        user_prompt=sample_prompt,
        max_iterations=3,
        score_threshold=85.0,
        trace_dir=None
    )
    
    assert result.total_iterations == 1
    assert result.final_prompt == enhanced_prompt

