"""
Integration tests for enhance_video_prompt.py CLI tool.
Tests end-to-end CLI execution with mocked OpenAI API.
"""
import pytest
import subprocess
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image


@pytest.fixture
def sample_prompt_file(tmp_path):
    """Create a sample prompt file."""
    prompt_file = tmp_path / "test_prompt.txt"
    prompt_file.write_text("A sleek smartphone on a minimalist desk", encoding="utf-8")
    return prompt_file


@pytest.fixture
def sample_storyboard_json(tmp_path):
    """Create a sample storyboard JSON file with all required fields."""
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
            "scene_1_to_2": "Smooth transition"
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
    
    # Create frame images
    start_img_1 = Image.new("RGB", (1920, 1080), color="red")
    end_img_1 = Image.new("RGB", (1920, 1080), color="blue")
    start_img_2 = Image.new("RGB", (1920, 1080), color="green")
    end_img_2 = Image.new("RGB", (1920, 1080), color="yellow")
    
    start_path_1 = tmp_path / "clip_001_start.png"
    end_path_1 = tmp_path / "clip_001_end.png"
    start_path_2 = tmp_path / "clip_002_start.png"
    end_path_2 = tmp_path / "clip_002_end.png"
    
    start_img_1.save(start_path_1)
    end_img_1.save(end_path_1)
    start_img_2.save(start_path_2)
    end_img_2.save(end_path_2)
    
    # Create storyboard JSON
    storyboard_data = {
        "unified_narrative_path": str(narrative_file),
        "clips": [
            {
                "clip_number": 1,
                "motion_description": "Camera slowly pushes in from wide establishing shot to medium shot",
                "camera_movement": "Push in from wide to medium",
                "shot_size": "Wide shot",
                "perspective": "Eye level, establishing",
                "lens_type": "Standard",
                "start_frame_path": str(start_path_1),
                "end_frame_path": str(end_path_1)
            },
            {
                "clip_number": 2,
                "motion_description": "Smooth camera movement with subject motion",
                "camera_movement": "Smooth pan or dolly movement",
                "shot_size": "Medium shot",
                "perspective": "Eye level, dynamic",
                "lens_type": "Standard",
                "start_frame_path": str(start_path_2),
                "end_frame_path": str(end_path_2)
            }
        ]
    }
    
    storyboard_file = tmp_path / "storyboard_metadata.json"
    with open(storyboard_file, "w", encoding="utf-8") as f:
        json.dump(storyboard_data, f, indent=2)
    
    return storyboard_file, storyboard_data


def mock_openai_responses():
    """Create mock OpenAI responses for video prompt enhancement."""
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
    
    return enhanced_prompt, critique_response


@pytest.mark.integration
def test_cli_single_prompt_mode(sample_prompt_file, tmp_path):
    """Test CLI with single prompt file input."""
    enhanced_prompt, critique_response = mock_openai_responses()
    
    with patch("app.services.pipeline.video_prompt_enhancement.openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock responses
        mock_response_enhance = MagicMock()
        mock_response_enhance.choices = [MagicMock()]
        mock_response_enhance.choices[0].message.content = enhanced_prompt
        
        mock_response_critique = MagicMock()
        mock_response_critique.choices = [MagicMock()]
        mock_response_critique.choices[0].message.content = json.dumps(critique_response)
        
        # Set high score to trigger early stopping
        critique_response["scores"]["overall"] = 90.0
        
        mock_client.chat.completions.create.side_effect = [
            mock_response_enhance,
            mock_response_critique
        ]
        
        # Run CLI
        output_dir = tmp_path / "test_output"
        result = subprocess.run(
            [
                "python3", "enhance_video_prompt.py",
                str(sample_prompt_file),
                "--video-mode",
                "--output-dir", str(output_dir)
            ],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )
        
        # Verify CLI executed successfully
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Verify output directory created
        assert output_dir.exists()
        
        # Verify trace files created
        assert (output_dir / "00_original_prompt.txt").exists()
        assert (output_dir / "05_final_enhanced_prompt.txt").exists()
        assert (output_dir / "prompt_trace_summary.json").exists()
        
        # Verify summary JSON structure
        with open(output_dir / "prompt_trace_summary.json", "r", encoding="utf-8") as f:
            summary = json.load(f)
        
        assert "original_prompt" in summary
        assert "final_prompt" in summary
        assert "final_score" in summary
        assert "temporal_coherence" in summary["final_score"]


@pytest.mark.integration
def test_cli_stdin_input(tmp_path):
    """Test CLI with stdin input."""
    enhanced_prompt, critique_response = mock_openai_responses()
    
    with patch("app.services.pipeline.video_prompt_enhancement.openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response_enhance = MagicMock()
        mock_response_enhance.choices = [MagicMock()]
        mock_response_enhance.choices[0].message.content = enhanced_prompt
        
        mock_response_critique = MagicMock()
        mock_response_critique.choices = [MagicMock()]
        critique_response["scores"]["overall"] = 90.0
        mock_response_critique.choices[0].message.content = json.dumps(critique_response)
        
        mock_client.chat.completions.create.side_effect = [
            mock_response_enhance,
            mock_response_critique
        ]
        
        # Run CLI with stdin
        output_dir = tmp_path / "test_output"
        result = subprocess.run(
            [
                "python3", "enhance_video_prompt.py",
                "-",
                "--video-mode",
                "--output-dir", str(output_dir)
            ],
            cwd=Path(__file__).parent.parent.parent,
            input="A cat in a city",
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_dir.exists()
        assert (output_dir / "00_original_prompt.txt").exists()


@pytest.mark.integration
def test_cli_storyboard_mode(sample_storyboard_json, tmp_path):
    """Test CLI with storyboard JSON input."""
    storyboard_file, storyboard_data = sample_storyboard_json
    enhanced_prompt, critique_response = mock_openai_responses()
    
    with patch("app.services.pipeline.video_prompt_enhancement.openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response_enhance = MagicMock()
        mock_response_enhance.choices = [MagicMock()]
        mock_response_enhance.choices[0].message.content = enhanced_prompt
        
        mock_response_critique = MagicMock()
        mock_response_critique.choices = [MagicMock()]
        critique_response["scores"]["overall"] = 90.0
        mock_response_critique.choices[0].message.content = json.dumps(critique_response)
        
        # Two clips, each needs enhance + critique
        mock_client.chat.completions.create.side_effect = [
            mock_response_enhance,
            mock_response_critique,
            mock_response_enhance,
            mock_response_critique
        ]
        
        # Run CLI with storyboard
        output_dir = tmp_path / "test_output"
        result = subprocess.run(
            [
                "python3", "enhance_video_prompt.py",
                "--storyboard", str(storyboard_file),
                "--output-dir", str(output_dir)
            ],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_dir.exists()
        
        # Verify per-clip directories created
        assert (output_dir / "clip_001").exists()
        assert (output_dir / "clip_002").exists()
        
        # Verify enhanced motion prompts saved
        assert (output_dir / "clip_001_enhanced_motion_prompt.txt").exists()
        assert (output_dir / "clip_002_enhanced_motion_prompt.txt").exists()
        
        # Verify summary JSON
        summary_file = output_dir / "storyboard_enhanced_motion_prompts.json"
        assert summary_file.exists()
        
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
        
        assert "clips" in summary
        assert "clip_frame_paths" in summary
        assert "unified_narrative_path" in summary
        assert len(summary["clips"]) == 2
        
        # Verify frame paths preserved
        assert summary["clip_frame_paths"]["1"]["start_frame_path"] == storyboard_data["clips"][0]["start_frame_path"]
        assert summary["clip_frame_paths"]["1"]["end_frame_path"] == storyboard_data["clips"][0]["end_frame_path"]


@pytest.mark.integration
def test_cli_image_to_video_mode(sample_prompt_file, tmp_path):
    """Test CLI with image-to-video mode."""
    enhanced_prompt, critique_response = mock_openai_responses()
    motion_prompt = "slow dolly forward, smooth 24fps cinematic motion"
    
    with patch("app.services.pipeline.video_prompt_enhancement.openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response_enhance = MagicMock()
        mock_response_enhance.choices = [MagicMock()]
        mock_response_enhance.choices[0].message.content = enhanced_prompt
        
        mock_response_critique = MagicMock()
        mock_response_critique.choices = [MagicMock()]
        critique_response["scores"]["overall"] = 90.0
        mock_response_critique.choices[0].message.content = json.dumps(critique_response)
        
        mock_response_motion = MagicMock()
        mock_response_motion.choices = [MagicMock()]
        mock_response_motion.choices[0].message.content = motion_prompt
        
        mock_client.chat.completions.create.side_effect = [
            mock_response_enhance,
            mock_response_critique,
            mock_response_motion
        ]
        
        output_dir = tmp_path / "test_output"
        result = subprocess.run(
            [
                "python3", "enhance_video_prompt.py",
                str(sample_prompt_file),
                "--video-mode",
                "--image-to-video",
                "--output-dir", str(output_dir)
            ],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert (output_dir / "motion_prompt.txt").exists()
        
        # Verify motion prompt content
        motion_content = (output_dir / "motion_prompt.txt").read_text(encoding="utf-8")
        assert "motion" in motion_content.lower() or "fps" in motion_content.lower()


@pytest.mark.integration
def test_cli_error_handling_missing_file(tmp_path):
    """Test CLI error handling for missing input file."""
    result = subprocess.run(
        [
            "python3", "enhance_video_prompt.py",
            "nonexistent_file.txt",
            "--video-mode"
        ],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


@pytest.mark.integration
def test_cli_error_handling_missing_storyboard(tmp_path):
    """Test CLI error handling for missing storyboard file."""
    result = subprocess.run(
        [
            "python3", "enhance_video_prompt.py",
            "--storyboard", "nonexistent_storyboard.json"
        ],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


@pytest.mark.integration
def test_cli_error_handling_invalid_storyboard_json(tmp_path):
    """Test CLI error handling for invalid storyboard JSON."""
    invalid_json = tmp_path / "invalid_storyboard.json"
    invalid_json.write_text("{ invalid json }", encoding="utf-8")
    
    result = subprocess.run(
        [
            "python3", "enhance_video_prompt.py",
            "--storyboard", str(invalid_json)
        ],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True
    )
    
    # Should fail gracefully
    assert result.returncode != 0


@pytest.mark.integration
def test_cli_console_output_format(sample_prompt_file, tmp_path):
    """Test that CLI produces properly formatted console output."""
    enhanced_prompt, critique_response = mock_openai_responses()
    
    with patch("app.services.pipeline.video_prompt_enhancement.openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response_enhance = MagicMock()
        mock_response_enhance.choices = [MagicMock()]
        mock_response_enhance.choices[0].message.content = enhanced_prompt
        
        mock_response_critique = MagicMock()
        mock_response_critique.choices = [MagicMock()]
        critique_response["scores"]["overall"] = 90.0
        mock_response_critique.choices[0].message.content = json.dumps(critique_response)
        
        mock_client.chat.completions.create.side_effect = [
            mock_response_enhance,
            mock_response_critique
        ]
        
        output_dir = tmp_path / "test_output"
        result = subprocess.run(
            [
                "python3", "enhance_video_prompt.py",
                str(sample_prompt_file),
                "--video-mode",
                "--output-dir", str(output_dir)
            ],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        # Verify console output contains expected elements
        output = result.stdout
        assert "VIDEO PROMPT ENHANCEMENT RESULTS" in output
        assert "Final Score" in output or "score" in output.lower()
        assert "Temporal Coherence" in output
        assert "Trace files saved" in output or "trace" in output.lower()


