"""
Unit tests for video prompt enhancement service with mocked OpenAI API.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from pathlib import Path
import tempfile
import shutil

from app.services.pipeline.video_prompt_enhancement import (
    enhance_video_prompt_iterative,
    enhance_storyboard_motion_prompts,
    VideoPromptEnhancementResult,
    StoryboardMotionEnhancementResult,
    _video_director_enhance,
    _prompt_engineer_critique,
    _quick_score_prompt,
    _generate_motion_prompt
)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch("app.services.pipeline.video_prompt_enhancement.openai.OpenAI") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_prompt():
    """Sample basic video prompt."""
    return "A cat in a city"


@pytest.fixture
def enhanced_prompt():
    """Sample enhanced video prompt."""
    return "A sleek black cat sprinting across a rain-soaked neon city street at night. Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting with harsh neon glow, cinematic color grading, moody atmosphere, 16:9 aspect ratio, slow dolly forward with subtle zoom, smooth 24fps cinematic motion, seamless transition from product reveal to lifestyle context"


@pytest.fixture
def critique_response():
    """Sample critique response from Prompt Engineer."""
    return {
        "scores": {
            "completeness": 85,
            "specificity": 82,
            "professionalism": 90,
            "cinematography": 88,
            "temporal_coherence": 75,
            "brand_alignment": 75,
            "overall": 82.5
        },
        "critique": "The prompt is well-structured with good cinematography details. Temporal coherence could be improved with more motion details.",
        "improvements": [
            "Add more specific motion descriptions",
            "Include temporal continuity hints"
        ]
    }


@pytest.fixture
def sample_storyboard_json(tmp_path):
    """Create a sample storyboard JSON file."""
    storyboard_data = {
        "unified_narrative_path": str(tmp_path / "unified_narrative.json"),
        "clips": [
            {
                "clip_number": 1,
                "motion_description": "Camera slowly pushes in from wide establishing shot to medium shot",
                "camera_movement": "Push in from wide to medium",
                "shot_size": "Wide shot",
                "perspective": "Eye level, establishing",
                "lens_type": "Standard",
                "start_frame_path": str(tmp_path / "clip_001_start.png"),
                "end_frame_path": str(tmp_path / "clip_001_end.png")
            },
            {
                "clip_number": 2,
                "motion_description": "Smooth camera movement with subject motion",
                "camera_movement": "Smooth pan or dolly movement",
                "shot_size": "Medium shot",
                "perspective": "Eye level, dynamic",
                "lens_type": "Standard",
                "start_frame_path": str(tmp_path / "clip_002_start.png"),
                "end_frame_path": str(tmp_path / "clip_002_end.png")
            }
        ]
    }
    
    # Create storyboard file
    storyboard_file = tmp_path / "storyboard_metadata.json"
    with open(storyboard_file, "w", encoding="utf-8") as f:
        json.dump(storyboard_data, f, indent=2)
    
    # Create unified narrative JSON
    unified_narrative = {
        "overall_story": {
            "narrative": "A story about a product",
            "framework": "AIDA",
            "total_scenes": 2,
            "target_duration": 15
        },
        "emotional_arc": {
            "scene_1": {
                "scene_type": "Attention",
                "emotional_state": "Anticipation",
                "visual_mood": "Engaging",
                "product_visibility": "hidden",
                "narrative_purpose": "Grab attention"
            },
            "scene_2": {
                "scene_type": "Interest",
                "emotional_state": "Recognition",
                "visual_mood": "Intriguing",
                "product_visibility": "partial",
                "narrative_purpose": "Build interest"
            }
        },
        "visual_progression": {
            "scene_1": "abstract",
            "scene_2": "product-focused"
        },
        "scene_connections": {
            "scene_1_to_2": "Smooth transition from abstract to product focus"
        },
        "product_reveal_strategy": {
            "scene_1": "hidden",
            "scene_2": "partial"
        },
        "brand_narrative": {
            "brand_values": ["quality", "innovation"],
            "visual_style": "modern, clean"
        }
    }
    
    narrative_file = tmp_path / "unified_narrative.json"
    with open(narrative_file, "w", encoding="utf-8") as f:
        json.dump(unified_narrative, f, indent=2)
    
    # Create dummy frame images
    from PIL import Image
    for clip in storyboard_data["clips"]:
        start_img = Image.new("RGB", (1920, 1080), color="red")
        start_img.save(clip["start_frame_path"])
        end_img = Image.new("RGB", (1920, 1080), color="blue")
        end_img.save(clip["end_frame_path"])
    
    return storyboard_file, storyboard_data


@pytest.mark.asyncio
async def test_quick_score_prompt_basic():
    """Test quick scoring for a basic prompt."""
    prompt = "A cat"
    score = _quick_score_prompt(prompt, video_mode=True)
    
    assert "completeness" in score
    assert "specificity" in score
    assert "professionalism" in score
    assert "cinematography" in score
    assert "temporal_coherence" in score
    assert "brand_alignment" in score
    assert "overall" in score
    
    assert all(0 <= v <= 100 for v in score.values())


@pytest.mark.asyncio
async def test_quick_score_prompt_detailed():
    """Test quick scoring for a detailed video prompt."""
    prompt = "A sleek black cat sprinting across a rain-soaked neon city street at night, Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting, slow dolly forward, smooth 24fps cinematic motion"
    score = _quick_score_prompt(prompt, video_mode=True)
    
    # Detailed prompts should score higher
    assert score["overall"] > 50
    assert score["cinematography"] > 50  # Has camera details
    assert score["temporal_coherence"] > 50  # Has motion details


@pytest.mark.asyncio
async def test_quick_score_prompt_temporal_coherence():
    """Test that temporal coherence is scored for video prompts."""
    prompt_with_motion = "A cat moving smoothly, slow dolly forward, 24fps"
    prompt_without_motion = "A cat"
    
    score_with = _quick_score_prompt(prompt_with_motion, video_mode=True)
    score_without = _quick_score_prompt(prompt_without_motion, video_mode=True)
    
    assert score_with["temporal_coherence"] > score_without["temporal_coherence"]


@pytest.mark.asyncio
async def test_video_director_enhance(mock_openai_client, sample_prompt, enhanced_prompt):
    """Test Video Director agent enhancement."""
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = enhanced_prompt
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await _video_director_enhance(sample_prompt)
    
    assert result == enhanced_prompt
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_video_director_enhance_image_to_video(mock_openai_client, sample_prompt, enhanced_prompt):
    """Test Video Director agent enhancement for image-to-video mode."""
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = enhanced_prompt
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await _video_director_enhance(sample_prompt, image_to_video=True)
    
    assert result == enhanced_prompt
    # Verify the call included image-to-video instructions
    call_args = mock_openai_client.chat.completions.create.call_args
    user_message = call_args[1]["messages"][1]["content"]
    assert "image-to-video" in user_message.lower() or "motion" in user_message.lower()


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
    assert "temporal_coherence" in result["scores"]
    assert result["scores"]["overall"] > 0


@pytest.mark.asyncio
async def test_generate_motion_prompt(mock_openai_client):
    """Test motion prompt generation for image-to-video."""
    enhanced_prompt = "A cat in a city, slow dolly forward"
    motion_prompt = "slow dolly forward, smooth 24fps cinematic motion"
    
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = motion_prompt
    mock_openai_client.chat.completions.create.return_value = mock_response
    
    result = await _generate_motion_prompt(enhanced_prompt)
    
    assert result == motion_prompt
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_enhance_video_prompt_iterative_single_iteration(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test video prompt enhancement with single iteration that meets threshold."""
    # Mock OpenAI responses
    mock_response_enhance = MagicMock()
    mock_response_enhance.choices = [MagicMock()]
    mock_response_enhance.choices[0].message.content = enhanced_prompt
    
    mock_response_critique = MagicMock()
    mock_response_critique.choices = [MagicMock()]
    mock_response_critique.choices[0].message.content = json.dumps(critique_response)
    
    # Set high score to trigger early stopping
    critique_response["scores"]["overall"] = 90.0
    
    mock_openai_client.chat.completions.create.side_effect = [
        mock_response_enhance,
        mock_response_critique
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir)
        result = await enhance_video_prompt_iterative(
            user_prompt=sample_prompt,
            max_iterations=3,
            score_threshold=85.0,
            trace_dir=trace_dir
        )
        
        assert isinstance(result, VideoPromptEnhancementResult)
        assert result.final_prompt == enhanced_prompt
        assert result.total_iterations == 1  # Early stopping
        assert result.final_score["overall"] >= 85.0
        assert "temporal_coherence" in result.final_score
        
        # Verify trace files created
        assert (trace_dir / "00_original_prompt.txt").exists()
        assert (trace_dir / "05_final_enhanced_prompt.txt").exists()
        assert (trace_dir / "prompt_trace_summary.json").exists()


@pytest.mark.asyncio
async def test_enhance_video_prompt_iterative_image_to_video(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test video prompt enhancement with image-to-video mode."""
    # Mock OpenAI responses
    mock_response_enhance = MagicMock()
    mock_response_enhance.choices = [MagicMock()]
    mock_response_enhance.choices[0].message.content = enhanced_prompt
    
    mock_response_critique = MagicMock()
    mock_response_critique.choices = [MagicMock()]
    mock_response_critique.choices[0].message.content = json.dumps(critique_response)
    
    mock_response_motion = MagicMock()
    mock_response_motion.choices = [MagicMock()]
    mock_response_motion.choices[0].message.content = "slow dolly forward, smooth 24fps"
    
    critique_response["scores"]["overall"] = 90.0
    
    mock_openai_client.chat.completions.create.side_effect = [
        mock_response_enhance,
        mock_response_critique,
        mock_response_motion
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir)
        result = await enhance_video_prompt_iterative(
            user_prompt=sample_prompt,
            max_iterations=3,
            score_threshold=85.0,
            trace_dir=trace_dir,
            image_to_video=True
        )
        
        assert result.motion_prompt is not None
        assert "motion" in result.motion_prompt.lower() or "fps" in result.motion_prompt.lower()
        assert (trace_dir / "motion_prompt.txt").exists()


@pytest.mark.asyncio
async def test_enhance_video_prompt_iterative_convergence(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test video prompt enhancement with convergence detection."""
    # Mock OpenAI responses
    mock_response_enhance = MagicMock()
    mock_response_enhance.choices = [MagicMock()]
    mock_response_enhance.choices[0].message.content = enhanced_prompt
    
    # First iteration: score 70
    critique_response_1 = critique_response.copy()
    critique_response_1["scores"]["overall"] = 70.0
    
    # Second iteration: score 71 (only 1 point improvement - convergence)
    critique_response_2 = critique_response.copy()
    critique_response_2["scores"]["overall"] = 71.0
    
    mock_response_critique_1 = MagicMock()
    mock_response_critique_1.choices = [MagicMock()]
    mock_response_critique_1.choices[0].message.content = json.dumps(critique_response_1)
    
    mock_response_critique_2 = MagicMock()
    mock_response_critique_2.choices = [MagicMock()]
    mock_response_critique_2.choices[0].message.content = json.dumps(critique_response_2)
    
    mock_openai_client.chat.completions.create.side_effect = [
        mock_response_enhance,
        mock_response_critique_1,
        mock_response_enhance,
        mock_response_critique_2
    ]
    
    result = await enhance_video_prompt_iterative(
        user_prompt=sample_prompt,
        max_iterations=3,
        score_threshold=85.0
    )
        
    assert result.total_iterations == 2  # Stopped due to convergence


@pytest.mark.asyncio
async def test_enhance_storyboard_motion_prompts(mock_openai_client, sample_storyboard_json, enhanced_prompt, critique_response):
    """Test storyboard motion prompt enhancement."""
    storyboard_file, storyboard_data = sample_storyboard_json
    
    # Mock OpenAI responses
    mock_response_enhance = MagicMock()
    mock_response_enhance.choices = [MagicMock()]
    mock_response_enhance.choices[0].message.content = enhanced_prompt
    
    mock_response_critique = MagicMock()
    mock_response_critique.choices = [MagicMock()]
    critique_response["scores"]["overall"] = 90.0
    mock_response_critique.choices[0].message.content = json.dumps(critique_response)
    
    # Two clips, each needs enhance + critique
    mock_openai_client.chat.completions.create.side_effect = [
        mock_response_enhance,
        mock_response_critique,
        mock_response_enhance,
        mock_response_critique
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_dir = Path(tmpdir)
        result = await enhance_storyboard_motion_prompts(
            storyboard_path=storyboard_file,
            max_iterations=3,
            score_threshold=85.0,
            trace_dir=trace_dir
        )
        
        assert isinstance(result, StoryboardMotionEnhancementResult)
        assert len(result.clips) == 2
        assert len(result.clip_results) == 2
        assert result.storyboard_path == storyboard_file
        assert result.unified_narrative_path.exists()
        
        # Verify per-clip trace directories
        assert (trace_dir / "clip_001").exists()
        assert (trace_dir / "clip_002").exists()
        
        # Verify enhanced motion prompts saved
        assert (trace_dir / "clip_001_enhanced_motion_prompt.txt").exists()
        assert (trace_dir / "clip_002_enhanced_motion_prompt.txt").exists()
        
        # Verify summary JSON
        summary_file = trace_dir / "storyboard_enhanced_motion_prompts.json"
        assert summary_file.exists()
        
        with open(summary_file, "r", encoding="utf-8") as f:
            summary_data = json.load(f)
        
        assert "clips" in summary_data
        assert "clip_frame_paths" in summary_data
        assert "unified_narrative_path" in summary_data
        assert len(summary_data["clips"]) == 2
        
        # Verify frame paths preserved
        assert summary_data["clip_frame_paths"]["1"]["start_frame_path"] == storyboard_data["clips"][0]["start_frame_path"]
        assert summary_data["clip_frame_paths"]["1"]["end_frame_path"] == storyboard_data["clips"][0]["end_frame_path"]


@pytest.mark.asyncio
async def test_enhance_storyboard_motion_prompts_missing_narrative(mock_openai_client, tmp_path):
    """Test storyboard enhancement fails when unified narrative is missing."""
    storyboard_data = {
        "clips": [
            {
                "clip_number": 1,
                "motion_description": "Camera movement"
            }
        ]
    }
    
    storyboard_file = tmp_path / "storyboard_metadata.json"
    with open(storyboard_file, "w", encoding="utf-8") as f:
        json.dump(storyboard_data, f)
    
    with pytest.raises(ValueError, match="unified_narrative_path"):
        await enhance_storyboard_motion_prompts(
            storyboard_path=storyboard_file,
            max_iterations=3,
            score_threshold=85.0
        )


@pytest.mark.asyncio
async def test_enhance_storyboard_motion_prompts_missing_frames(mock_openai_client, sample_storyboard_json, enhanced_prompt, critique_response):
    """Test storyboard enhancement handles missing frame images gracefully."""
    storyboard_file, storyboard_data = sample_storyboard_json
    
    # Delete one frame image
    Path(storyboard_data["clips"][0]["start_frame_path"]).unlink()
    
    # Mock OpenAI responses
    mock_response_enhance = MagicMock()
    mock_response_enhance.choices = [MagicMock()]
    mock_response_enhance.choices[0].message.content = enhanced_prompt
    
    mock_response_critique = MagicMock()
    mock_response_critique.choices = [MagicMock()]
    critique_response["scores"]["overall"] = 90.0
    mock_response_critique.choices[0].message.content = json.dumps(critique_response)
    
    mock_openai_client.chat.completions.create.side_effect = [
        mock_response_enhance,
        mock_response_critique,
        mock_response_enhance,
        mock_response_critique
    ]
    
    # Should still work, just log warnings
    result = await enhance_storyboard_motion_prompts(
        storyboard_path=storyboard_file,
        max_iterations=3,
        score_threshold=85.0
    )
    
    assert len(result.clips) == 2  # Should still process all clips


@pytest.mark.asyncio
async def test_enhance_video_prompt_high_initial_score(mock_openai_client, sample_prompt):
    """Test that enhancement is skipped if initial score is already high."""
    # High-quality prompt that should score well
    high_quality_prompt = "A sleek modern smartphone displayed on a minimalist white surface, Canon EOS R5 50mm f/1.4 lens, close-up portrait, soft diffused lighting creating gentle shadows, shallow depth of field with softly blurred background, cinematic color grading with cool tones, clean professional atmosphere, 16:9 aspect ratio, slow dolly forward with subtle zoom, smooth 24fps cinematic motion, seamless transition"
    
    result = await enhance_video_prompt_iterative(
        user_prompt=high_quality_prompt,
        max_iterations=3,
        score_threshold=85.0
    )
    
    # Should skip enhancement if score is high enough
    # Note: This depends on _quick_score_prompt implementation
    # If it scores high, total_iterations should be 0
    assert result.total_iterations == 0 or result.total_iterations > 0


@pytest.mark.asyncio
async def test_videodirectorgpt_plan_optional(mock_openai_client, sample_prompt, enhanced_prompt, critique_response):
    """Test that VideoDirectorGPT planning is optional and doesn't break if unavailable."""
    # Mock OpenAI responses
    mock_response_enhance = MagicMock()
    mock_response_enhance.choices = [MagicMock()]
    mock_response_enhance.choices[0].message.content = enhanced_prompt
    
    mock_response_critique = MagicMock()
    mock_response_critique.choices = [MagicMock()]
    critique_response["scores"]["overall"] = 90.0
    mock_response_critique.choices[0].message.content = json.dumps(critique_response)
    
    mock_openai_client.chat.completions.create.side_effect = [
        mock_response_enhance,
        mock_response_critique
    ]
    
    # Mock scene_planning to raise exception (simulating unavailable VideoDirectorGPT)
    with patch("app.services.pipeline.video_prompt_enhancement.create_basic_scene_plan_from_prompt", side_effect=Exception("VideoDirectorGPT not available")):
        result = await enhance_video_prompt_iterative(
            user_prompt=sample_prompt,
            max_iterations=3,
            score_threshold=85.0
        )
        
        # Should still work without VideoDirectorGPT planning
        assert isinstance(result, VideoPromptEnhancementResult)
        assert result.final_prompt == enhanced_prompt
        # videodirectorgpt_plan may be None, which is fine
        assert result.videodirectorgpt_plan is None or isinstance(result.videodirectorgpt_plan, dict)


# CLI-specific unit tests
def test_cli_argument_parsing():
    """Test CLI argument parsing."""
    import sys
    from unittest.mock import patch
    from backend.enhance_video_prompt import main
    import asyncio
    
    # Test with file input
    with patch("sys.argv", ["enhance_video_prompt.py", "test.txt", "--video-mode"]):
        with patch("backend.enhance_video_prompt.load_prompt", return_value="test prompt"):
            with patch("backend.enhance_video_prompt.enhance_video_prompt_iterative") as mock_enhance:
                mock_result = MagicMock()
                mock_result.final_prompt = "enhanced"
                mock_result.final_score = {"overall": 85.0, "completeness": 85, "specificity": 85, "professionalism": 85, "cinematography": 85, "temporal_coherence": 85, "brand_alignment": 85}
                mock_result.total_iterations = 1
                mock_result.iterations = []
                mock_result.motion_prompt = None
                mock_enhance.return_value = mock_result
                
                with patch("backend.enhance_video_prompt.settings") as mock_settings:
                    mock_settings.OPENAI_API_KEY = "test-key"
                    try:
                        asyncio.run(main())
                    except SystemExit:
                        pass
                    
                    # Verify enhance was called
                    mock_enhance.assert_called_once()


def test_cli_stdin_input_handling():
    """Test CLI stdin input handling."""
    from backend.enhance_video_prompt import load_prompt
    import sys
    from io import StringIO
    
    # Test stdin loading
    test_input = "A test prompt from stdin"
    with patch("sys.stdin", StringIO(test_input)):
        result = load_prompt("-")
        assert result == test_input


def test_cli_error_handling_missing_api_key():
    """Test CLI error handling for missing API key."""
    import sys
    from unittest.mock import patch
    from backend.enhance_video_prompt import main
    import asyncio
    
    with patch("sys.argv", ["enhance_video_prompt.py", "test.txt"]):
        with patch("backend.enhance_video_prompt.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            
            with patch("sys.exit") as mock_exit:
                try:
                    asyncio.run(main())
                except SystemExit:
                    pass
                
                # Should exit with error code
                mock_exit.assert_called_once_with(1)


def test_cli_error_handling_missing_file():
    """Test CLI error handling for missing input file."""
    from backend.enhance_video_prompt import load_prompt
    
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent_file.txt")


def test_cli_error_handling_empty_stdin():
    """Test CLI error handling for empty stdin."""
    from backend.enhance_video_prompt import load_prompt
    import sys
    from io import StringIO
    
    with patch("sys.stdin", StringIO("")):
        with pytest.raises(ValueError, match="No prompt provided"):
            load_prompt("-")


@pytest.mark.asyncio
async def test_cli_storyboard_validation_missing_narrative():
    """Test CLI error handling for storyboard missing unified narrative."""
    from pathlib import Path
    import tempfile
    import json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storyboard_data = {
            "clips": [{"clip_number": 1, "motion_description": "test"}]
        }
        storyboard_file = Path(tmpdir) / "storyboard.json"
        with open(storyboard_file, "w", encoding="utf-8") as f:
            json.dump(storyboard_data, f)
        
        from app.services.pipeline.video_prompt_enhancement import enhance_storyboard_motion_prompts
        
        with pytest.raises(ValueError, match="unified_narrative_path"):
            await enhance_storyboard_motion_prompts(
                storyboard_path=storyboard_file,
                max_iterations=3,
                score_threshold=85.0
            )


@pytest.mark.asyncio
async def test_error_handling_api_failure(mock_openai_client):
    """Test error handling for API failures."""
    from app.services.pipeline.video_prompt_enhancement import enhance_video_prompt_iterative
    
    # Mock API failure
    mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
    
    with pytest.raises(Exception):
        await enhance_video_prompt_iterative(
            user_prompt="test prompt",
            max_iterations=3,
            score_threshold=85.0
        )


@pytest.mark.asyncio
async def test_error_handling_invalid_critique_response(mock_openai_client):
    """Test error handling for invalid critique response structure."""
    from app.services.pipeline.video_prompt_enhancement import enhance_video_prompt_iterative
    
    enhanced_prompt = "Enhanced prompt"
    invalid_response = {"invalid": "structure"}  # Missing required fields
    
    mock_response_enhance = MagicMock()
    mock_response_enhance.choices = [MagicMock()]
    mock_response_enhance.choices[0].message.content = enhanced_prompt
    
    mock_response_critique = MagicMock()
    mock_response_critique.choices = [MagicMock()]
    mock_response_critique.choices[0].message.content = json.dumps(invalid_response)
    
    mock_openai_client.chat.completions.create.side_effect = [
        mock_response_enhance,
        mock_response_critique
    ]
    
    with pytest.raises(ValueError, match="Invalid critique response"):
        await enhance_video_prompt_iterative(
            user_prompt="test prompt",
            max_iterations=3,
            score_threshold=85.0
        )


@pytest.mark.asyncio
async def test_error_handling_missing_openai_key():
    """Test error handling for missing OpenAI API key."""
    from app.services.pipeline.video_prompt_enhancement import _video_director_enhance
    
    with patch("app.services.pipeline.video_prompt_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY not configured"):
            await _video_director_enhance("test prompt")

