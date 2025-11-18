"""
Integration tests for enhance_image_prompt.py CLI tool.
"""
import pytest
import subprocess
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.pipeline.image_prompt_enhancement import ImagePromptEnhancementResult


@pytest.fixture
def sample_prompt_file(tmp_path):
    """Create a temporary prompt file."""
    prompt_file = tmp_path / "test_prompt.txt"
    prompt_file.write_text("A cat in a city", encoding="utf-8")
    return prompt_file


@pytest.fixture
def mock_enhancement_result():
    """Mock enhancement result."""
    return ImagePromptEnhancementResult(
        original_prompt="A cat in a city",
        final_prompt="A sleek black cat sprinting across a rain-soaked neon city street at night. Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting",
        iterations=[
            {
                "iteration": 1,
                "enhanced_prompt": "A sleek black cat sprinting across a rain-soaked neon city street at night. Canon EOS R5, 85mm f/1.2 lens, wide aerial shot, dramatic side lighting",
                "scores": {
                    "completeness": 85,
                    "specificity": 82,
                    "professionalism": 90,
                    "cinematography": 88,
                    "brand_alignment": 75,
                    "overall": 84.0
                },
                "critique": "Good prompt",
                "improvements": ["Add more brand details"],
                "timestamp": "2025-01-15T10:00:00"
            }
        ],
        final_score={
            "completeness": 85,
            "specificity": 82,
            "professionalism": 90,
            "cinematography": 88,
            "brand_alignment": 75,
            "overall": 84.0
        },
        total_iterations=1
    )


def test_cli_file_input(sample_prompt_file, mock_enhancement_result):
    """Test CLI with file input."""
    with patch("app.services.pipeline.image_prompt_enhancement.enhance_prompt_iterative") as mock_enhance:
        mock_enhance.return_value = mock_enhancement_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"
            
            result = subprocess.run(
                [
                    sys.executable,
                    "backend/enhance_image_prompt.py",
                    str(sample_prompt_file),
                    "--output-dir",
                    str(output_dir)
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            # Should succeed
            assert result.returncode == 0
            assert "IMAGE PROMPT ENHANCEMENT RESULTS" in result.stdout
            assert "Final Score" in result.stdout


def test_cli_stdin_input(mock_enhancement_result):
    """Test CLI with stdin input."""
    with patch("app.services.pipeline.image_prompt_enhancement.enhance_prompt_iterative") as mock_enhance:
        mock_enhance.return_value = mock_enhancement_result
        
        result = subprocess.run(
            [
                sys.executable,
                "backend/enhance_image_prompt.py",
                "-"
            ],
            input="A cat in a city\n",
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Should succeed
        assert result.returncode == 0
        assert "IMAGE PROMPT ENHANCEMENT RESULTS" in result.stdout


def test_cli_custom_options(sample_prompt_file, mock_enhancement_result):
    """Test CLI with custom options."""
    with patch("app.services.pipeline.image_prompt_enhancement.enhance_prompt_iterative") as mock_enhance:
        mock_enhance.return_value = mock_enhancement_result
        
        result = subprocess.run(
            [
                sys.executable,
                "backend/enhance_image_prompt.py",
                str(sample_prompt_file),
                "--max-iterations",
                "5",
                "--threshold",
                "90",
                "--verbose"
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Should succeed
        assert result.returncode == 0
        # Verify options were passed
        mock_enhance.assert_called_once()
        call_kwargs = mock_enhance.call_args[1]
        assert call_kwargs["max_iterations"] == 5
        assert call_kwargs["score_threshold"] == 90.0


def test_cli_missing_api_key(sample_prompt_file):
    """Test CLI fails gracefully without API key."""
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        
        result = subprocess.run(
            [
                sys.executable,
                "backend/enhance_image_prompt.py",
                str(sample_prompt_file)
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # Should fail with error message
        assert result.returncode == 1
        assert "OPENAI_API_KEY not configured" in result.stdout or "OPENAI_API_KEY not configured" in result.stderr


def test_cli_trace_files_created(sample_prompt_file, mock_enhancement_result):
    """Test CLI creates trace files correctly."""
    with patch("app.services.pipeline.image_prompt_enhancement.enhance_prompt_iterative") as mock_enhance:
        mock_enhance.return_value = mock_enhancement_result
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output" / "image_prompt_traces" / "test_timestamp"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Mock the enhancement to actually create trace files
            def create_trace_files(*args, **kwargs):
                trace_dir = kwargs.get("trace_dir")
                if trace_dir:
                    trace_dir.mkdir(parents=True, exist_ok=True)
                    (trace_dir / "00_original_prompt.txt").write_text("A cat in a city")
                    (trace_dir / "05_final_enhanced_prompt.txt").write_text("Enhanced prompt")
                    (trace_dir / "prompt_trace_summary.json").write_text(json.dumps({"test": "data"}))
                return mock_enhancement_result
            
            mock_enhance.side_effect = create_trace_files
            
            result = subprocess.run(
                [
                    sys.executable,
                    "backend/enhance_image_prompt.py",
                    str(sample_prompt_file),
                    "--output-dir",
                    str(output_dir.parent.parent)
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent
            )
            
            # Should succeed
            assert result.returncode == 0
            
            # Check that trace directory was created (timestamp-based)
            trace_dirs = list(output_dir.parent.glob("*"))
            assert len(trace_dirs) > 0

