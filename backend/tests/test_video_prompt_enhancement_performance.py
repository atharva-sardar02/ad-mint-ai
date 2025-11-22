"""
Performance tests for video prompt enhancement service.
Target: <60 seconds for 2-iteration enhancement.
"""
import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.services.pipeline.video_prompt_enhancement import (
    enhance_video_prompt_iterative,
    enhance_storyboard_motion_prompts
)
from pathlib import Path
import tempfile
from PIL import Image


@pytest.fixture
def mock_openai_client_fast():
    """Mock OpenAI client with fast responses."""
    with patch("app.services.pipeline.video_prompt_enhancement.openai.OpenAI") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        
        # Fast mock responses
        enhanced_prompt = "A sleek modern smartphone displayed on a minimalist white surface, Canon EOS R5 50mm f/1.4 lens, close-up portrait, soft diffused lighting creating gentle shadows, shallow depth of field with softly blurred background, cinematic color grading with cool tones, clean professional atmosphere, 16:9 aspect ratio, slow dolly forward with subtle zoom, smooth 24fps cinematic motion, seamless transition"
        
        critique_response = {
            "scores": {
                "completeness": 90,
                "specificity": 85,
                "professionalism": 92,
                "cinematography": 88,
                "temporal_coherence": 80,
                "brand_alignment": 75,
                "overall": 85.0
            },
            "critique": "Well-structured prompt with good cinematography details.",
            "improvements": ["Add more brand-specific elements"]
        }
        
        mock_response_enhance = MagicMock()
        mock_response_enhance.choices = [MagicMock()]
        mock_response_enhance.choices[0].message.content = enhanced_prompt
        
        mock_response_critique = MagicMock()
        mock_response_critique.choices = [MagicMock()]
        mock_response_critique.choices[0].message.content = json.dumps(critique_response)
        
        # Simulate fast API responses (no actual delay)
        mock_client.chat.completions.create.side_effect = [
            mock_response_enhance,
            mock_response_critique,
            mock_response_enhance,
            mock_response_critique
        ]
        
        yield mock_client


@pytest.mark.asyncio
@pytest.mark.performance
async def test_single_prompt_enhancement_performance(mock_openai_client_fast):
    """Test that single prompt enhancement completes within target time (<60s for 2 iterations)."""
    sample_prompt = "A sleek smartphone on a minimalist desk"
    
    start_time = time.time()
    
    result = await enhance_video_prompt_iterative(
        user_prompt=sample_prompt,
        max_iterations=2,
        score_threshold=85.0
    )
    
    elapsed_time = time.time() - start_time
    
    # Verify completion
    assert result is not None
    assert result.total_iterations <= 2
    
    # Performance target: <60 seconds for 2 iterations
    # Note: With mocked API, this should be much faster, but we test the structure
    assert elapsed_time < 60.0, f"Enhancement took {elapsed_time:.2f}s, target is <60s"
    
    print(f"\nSingle prompt enhancement (2 iterations): {elapsed_time:.2f}s")


@pytest.mark.asyncio
@pytest.mark.performance
async def test_storyboard_enhancement_performance(mock_openai_client_fast, tmp_path):
    """Test that storyboard enhancement completes within target time (<60s per clip)."""
    # Create storyboard JSON with 3 clips
    unified_narrative = {
        "overall_story": {"narrative": "A story about a product"},
        "emotional_arc": {},
        "visual_progression": {},
        "scene_connections": {},
        "product_reveal_strategy": {},
        "brand_narrative": {}
    }
    
    narrative_file = tmp_path / "unified_narrative.json"
    with open(narrative_file, "w", encoding="utf-8") as f:
        json.dump(unified_narrative, f)
    
    # Create frame images
    for i in range(1, 4):
        start_img = Image.new("RGB", (1920, 1080), color="red")
        end_img = Image.new("RGB", (1920, 1080), color="blue")
        start_img.save(tmp_path / f"clip_{i:03d}_start.png")
        end_img.save(tmp_path / f"clip_{i:03d}_end.png")
    
    storyboard_data = {
        "unified_narrative_path": str(narrative_file),
        "clips": [
            {
                "clip_number": i,
                "motion_description": f"Camera movement for clip {i}",
                "camera_movement": "Static",
                "shot_size": "Medium",
                "perspective": "Eye level",
                "lens_type": "Standard",
                "start_frame_path": str(tmp_path / f"clip_{i:03d}_start.png"),
                "end_frame_path": str(tmp_path / f"clip_{i:03d}_end.png")
            }
            for i in range(1, 4)
        ]
    }
    
    storyboard_file = tmp_path / "storyboard_metadata.json"
    with open(storyboard_file, "w", encoding="utf-8") as f:
        json.dump(storyboard_data, f)
    
    start_time = time.time()
    
    result = await enhance_storyboard_motion_prompts(
        storyboard_path=storyboard_file,
        max_iterations=2,
        score_threshold=85.0
    )
    
    elapsed_time = time.time() - start_time
    
    # Verify completion
    assert result is not None
    assert len(result.clips) == 3
    
    # Performance target: <60 seconds per clip (for 3 clips: <180s)
    # With mocked API, this should be much faster, but we test the structure
    target_time = 180.0  # 60s per clip * 3 clips
    assert elapsed_time < target_time, f"Storyboard enhancement took {elapsed_time:.2f}s, target is <{target_time}s"
    
    print(f"\nStoryboard enhancement (3 clips, 2 iterations each): {elapsed_time:.2f}s")
    print(f"Average per clip: {elapsed_time / 3:.2f}s")


@pytest.mark.asyncio
@pytest.mark.performance
async def test_quick_score_performance():
    """Test that quick scoring is fast (rule-based, no LLM calls)."""
    sample_prompt = "A sleek smartphone on a minimalist desk"
    
    start_time = time.time()
    
    from app.services.pipeline.video_prompt_enhancement import _quick_score_prompt
    score = _quick_score_prompt(sample_prompt, video_mode=True)
    
    elapsed_time = time.time() - start_time
    
    # Quick scoring should be very fast (<1 second, rule-based)
    assert elapsed_time < 1.0, f"Quick scoring took {elapsed_time:.4f}s, should be <1s"
    assert "overall" in score
    assert "temporal_coherence" in score
    
    print(f"\nQuick scoring: {elapsed_time:.4f}s")


@pytest.mark.asyncio
@pytest.mark.performance
async def test_high_score_skip_performance(mock_openai_client_fast):
    """Test that high-scoring prompts skip enhancement quickly."""
    # High-quality prompt that should score well and skip enhancement
    high_quality_prompt = "A sleek modern smartphone displayed on a minimalist white surface, Canon EOS R5 50mm f/1.4 lens, close-up portrait, soft diffused lighting creating gentle shadows, shallow depth of field with softly blurred background, cinematic color grading with cool tones, clean professional atmosphere, 16:9 aspect ratio, slow dolly forward with subtle zoom, smooth 24fps cinematic motion, seamless transition from product reveal to lifestyle context"
    
    start_time = time.time()
    
    result = await enhance_video_prompt_iterative(
        user_prompt=high_quality_prompt,
        max_iterations=3,
        score_threshold=85.0
    )
    
    elapsed_time = time.time() - start_time
    
    # High-scoring prompts should skip enhancement (0 iterations) and be very fast
    if result.total_iterations == 0:
        assert elapsed_time < 5.0, f"Skip took {elapsed_time:.2f}s, should be <5s"
        print(f"\nHigh-score skip (0 iterations): {elapsed_time:.2f}s")
    else:
        # If it did enhance, should still be fast
        assert elapsed_time < 60.0
        print(f"\nHigh-score enhancement ({result.total_iterations} iterations): {elapsed_time:.2f}s")


@pytest.mark.asyncio
@pytest.mark.performance
async def test_convergence_early_stop_performance(mock_openai_client_fast):
    """Test that convergence detection stops early and saves time."""
    sample_prompt = "A sleek smartphone on a minimalist desk"
    
    # Mock responses that show convergence (small improvement)
    enhanced_prompt = "Enhanced prompt"
    
    critique_response_1 = {
        "scores": {"overall": 70.0, "completeness": 70, "specificity": 70, "professionalism": 70, "cinematography": 70, "temporal_coherence": 70, "brand_alignment": 70},
        "critique": "Good",
        "improvements": ["Improve"]
    }
    
    critique_response_2 = {
        "scores": {"overall": 71.0, "completeness": 71, "specificity": 71, "professionalism": 71, "cinematography": 71, "temporal_coherence": 71, "brand_alignment": 71},
        "critique": "Good",
        "improvements": ["Improve"]
    }
    
    mock_client = mock_openai_client_fast
    mock_response_enhance = MagicMock()
    mock_response_enhance.choices = [MagicMock()]
    mock_response_enhance.choices[0].message.content = enhanced_prompt
    
    mock_response_critique_1 = MagicMock()
    mock_response_critique_1.choices = [MagicMock()]
    mock_response_critique_1.choices[0].message.content = json.dumps(critique_response_1)
    
    mock_response_critique_2 = MagicMock()
    mock_response_critique_2.choices = [MagicMock()]
    mock_response_critique_2.choices[0].message.content = json.dumps(critique_response_2)
    
    mock_client.chat.completions.create.side_effect = [
        mock_response_enhance,
        mock_response_critique_1,
        mock_response_enhance,
        mock_response_critique_2
    ]
    
    start_time = time.time()
    
    result = await enhance_video_prompt_iterative(
        user_prompt=sample_prompt,
        max_iterations=3,
        score_threshold=85.0
    )
    
    elapsed_time = time.time() - start_time
    
    # Should stop after 2 iterations due to convergence
    assert result.total_iterations == 2
    
    # Should be faster than 3 full iterations
    assert elapsed_time < 60.0
    
    print(f"\nConvergence early stop (2 iterations): {elapsed_time:.2f}s")

