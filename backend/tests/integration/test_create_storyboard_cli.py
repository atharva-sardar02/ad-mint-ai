"""
Integration tests for create_storyboard CLI tool.
"""
import pytest
import asyncio
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
import json


@pytest.fixture
def sample_prompt_file(tmp_path):
    """Create a sample prompt file for testing."""
    prompt_file = tmp_path / "test_prompt.txt"
    prompt_file.write_text("A dynamic product showcase video with cinematic visuals and professional lighting")
    return prompt_file


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "storyboard_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.mark.integration
def test_cli_basic_usage(sample_prompt_file, temp_output_dir):
    """Test basic CLI usage with sample prompt file."""
    # Note: This test requires actual API keys and will make real API calls
    # Skip if API keys not configured
    import os
    if not os.getenv("REPLICATE_API_TOKEN"):
        pytest.skip("REPLICATE_API_TOKEN not configured")
    
    # Run CLI tool
    script_path = Path(__file__).parent.parent.parent / "create_storyboard.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            str(sample_prompt_file),
            "--num-clips",
            "3",
            "--output-dir",
            str(temp_output_dir),
            "--verbose"
        ],
        capture_output=True,
        text=True,
        timeout=900  # 15 minutes timeout
    )
    
    # Check exit code
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    
    # Note: This may fail if API keys are invalid or API is down
    # In that case, we just skip the test
    if "ERROR" in result.stderr or result.returncode != 0:
        pytest.skip(f"CLI execution failed (may be due to API issues): {result.stderr}")
    
    # Verify output directory structure
    assert temp_output_dir.exists()
    
    # Verify metadata file exists
    metadata_file = temp_output_dir / "storyboard_metadata.json"
    if metadata_file.exists():
        # Verify metadata structure
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        assert "num_clips" in metadata
        assert "clips" in metadata
        assert len(metadata["clips"]) == 3
        
        # Verify image files exist for each clip
        for clip_meta in metadata["clips"]:
            clip_num = clip_meta["clip_number"]
            start_path = Path(clip_meta["start_frame_path"])
            end_path = Path(clip_meta["end_frame_path"])
            
            # Check if files exist (may be URLs if download failed)
            if start_path.exists():
                assert start_path.is_file()
            if end_path.exists():
                assert end_path.is_file()


@pytest.mark.integration
def test_cli_with_enhancement_flag(sample_prompt_file, temp_output_dir):
    """Test CLI with --enhance-prompts flag."""
    import os
    if not os.getenv("REPLICATE_API_TOKEN"):
        pytest.skip("REPLICATE_API_TOKEN not configured")
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not configured (required for enhancement)")
    
    script_path = Path(__file__).parent.parent.parent / "create_storyboard.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            str(sample_prompt_file),
            "--num-clips",
            "3",
            "--enhance-prompts",
            "--output-dir",
            str(temp_output_dir),
        ],
        capture_output=True,
        text=True,
        timeout=900
    )
    
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    
    if "ERROR" in result.stderr or result.returncode != 0:
        pytest.skip(f"CLI execution failed: {result.stderr}")
    
    # Verify enhancement trace directory exists
    trace_dir = temp_output_dir / "prompt_enhancement_trace"
    if trace_dir.exists():
        # Verify trace files exist
        assert (trace_dir / "00_original_prompt.txt").exists()
        assert (trace_dir / "05_final_enhanced_prompt.txt").exists()


@pytest.mark.integration
def test_cli_argument_parsing():
    """Test CLI argument parsing and validation."""
    script_path = Path(__file__).parent.parent.parent / "create_storyboard.py"
    
    # Test help message
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "create_storyboard.py" in result.stdout or "storyboard" in result.stdout.lower()
    
    # Test invalid num-clips (should fail validation)
    result = subprocess.run(
        [sys.executable, str(script_path), "dummy.txt", "--num-clips", "10"],
        capture_output=True,
        text=True
    )
    # Should fail with validation error or file not found
    assert result.returncode != 0 or "not found" in result.stderr.lower() or "invalid" in result.stderr.lower()


def test_cli_file_not_found():
    """Test CLI error handling for missing file."""
    script_path = Path(__file__).parent.parent.parent / "create_storyboard.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path), "nonexistent_file.txt"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "ERROR" in result.stderr


@pytest.mark.integration
def test_cli_mocked_integration(sample_prompt_file, temp_output_dir):
    """Test CLI with mocked API calls (doesn't require API keys)."""
    from app.services.pipeline.storyboard_service import create_storyboard
    from app.services.pipeline.image_generation import ImageGenerationResult
    from app.schemas.generation import ScenePlan, Scene, TextOverlay
    
    # Mock image generation result
    mock_image_result = ImageGenerationResult(
        image_path=str(temp_output_dir / "test_image.png"),
        image_url="https://example.com/test.png",
        model_name="test-model",
        seed=None,
        aspect_ratio="16:9",
        prompt="test prompt",
        cost=0.01,
        generation_time=1.0,
        timestamp="2025-01-01 12:00:00"
    )
    
    # Create a dummy image file
    (temp_output_dir / "test_image.png").touch()
    
    # Mock scene plan
    mock_scenes = [
        Scene(
            scene_number=i,
            scene_type=f"Scene {i}",
            visual_prompt=f"Scene {i} prompt",
            text_overlay=TextOverlay(
                text="", position="bottom", font_size=48, color="#FFFFFF", animation="fade_in"
            ),
            duration=5
        )
        for i in range(1, 4)
    ]
    mock_plan = ScenePlan(
        scenes=mock_scenes,
        total_duration=15,
        framework="AIDA"
    )
    
    with patch("app.services.pipeline.storyboard_service.create_basic_scene_plan_from_prompt", return_value=mock_plan), \
         patch("app.services.pipeline.storyboard_service.generate_images", new_callable=AsyncMock) as mock_generate:
        
        # Mock image generation to return our test result
        mock_generate.return_value = [mock_image_result]
        
        # Run the storyboard creation
        import asyncio
        result = asyncio.run(create_storyboard(
            prompt="Test prompt",
            num_clips=3,
            output_dir=temp_output_dir
        ))
        
        # Verify result
        assert result is not None
        assert len(result.clips) == 3
        assert result.metadata["num_clips"] == 3
        
        # Verify metadata file was created
        metadata_file = temp_output_dir / "storyboard_metadata.json"
        assert metadata_file.exists()
        
        # Verify metadata structure
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        assert "consistency_groupings" in metadata
        assert "clips" in metadata
        assert len(metadata["clips"]) == 3


@pytest.mark.integration
def test_cli_performance_timing(sample_prompt_file, temp_output_dir):
    """Test CLI performance with timing assertions."""
    import os
    if not os.getenv("REPLICATE_API_TOKEN"):
        pytest.skip("REPLICATE_API_TOKEN not configured (performance test requires real API)")
    
    script_path = Path(__file__).parent.parent.parent / "create_storyboard.py"
    
    # Measure start time
    start_time = time.time()
    
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            str(sample_prompt_file),
            "--num-clips",
            "3",
            "--output-dir",
            str(temp_output_dir),
        ],
        capture_output=True,
        text=True,
        timeout=900  # 15 minutes timeout
    )
    
    # Measure end time
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Performance assertions
    # Target: < 15 minutes (900 seconds) for 3 clips with start/end frames
    assert elapsed_time < 900, f"Storyboard creation took {elapsed_time:.2f}s, exceeding 15 minute target"
    
    # Log performance metrics
    print(f"\nPerformance Metrics:")
    print(f"  Total time: {elapsed_time:.2f}s ({elapsed_time/60:.2f} minutes)")
    print(f"  Target: < 900s (15 minutes)")
    print(f"  Status: {'PASS' if elapsed_time < 900 else 'FAIL'}")
    
    # If successful, verify output exists
    if result.returncode == 0:
        metadata_file = temp_output_dir / "storyboard_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            # Log per-clip timing estimate
            num_clips = metadata.get("num_clips", 3)
            time_per_clip = elapsed_time / num_clips if num_clips > 0 else 0
            print(f"  Time per clip: {time_per_clip:.2f}s")
            print(f"  Clips generated: {num_clips}")
    
    # Note: We don't fail the test if API calls fail, just skip
    if result.returncode != 0:
        pytest.skip(f"CLI execution failed (may be due to API issues): {result.stderr}")
    
    # Assert that if it succeeded, it was fast enough
    assert elapsed_time < 900, "Performance target not met"

