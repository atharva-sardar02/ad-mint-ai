"""
Unit tests for quality control regeneration logic.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

from app.services.pipeline.quality_control import regenerate_clip
from app.schemas.generation import Scene


@pytest.fixture
def sample_scene():
    """Create a sample scene for testing."""
    return Scene(
        scene_number=1,
        scene_type="Problem",
        visual_prompt="A person walking in a park",
        duration=5
    )


@pytest.fixture
def mock_quality_metric():
    """Create a mock quality metric."""
    metric = Mock()
    metric.regeneration_attempts = 0
    metric.generation_id = "test-gen"
    metric.scene_number = 1
    metric.clip_path = "/original/clip.mp4"
    metric.passed_threshold = False
    metric.vbench_scores = {"overall_quality": 60.0}
    metric.overall_quality = 60.0
    return metric


@pytest.mark.asyncio
async def test_regenerate_clip_max_attempts_reached(mock_quality_metric, sample_scene):
    """Test that regeneration stops when max attempts reached."""
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = mock_quality_metric
    
    # Set attempts to max
    mock_quality_metric.regeneration_attempts = 2
    
    result = await regenerate_clip(
        db=db,
        generation_id="test-gen",
        scene_number=1,
        scene=sample_scene,
        output_dir="/tmp",
        original_clip_path="/original/clip.mp4",
        prompt_text="test prompt",
        max_attempts=2
    )
    
    clip_path, success, details = result
    
    assert clip_path is None
    assert success is False
    assert "Max regeneration attempts" in details.get("error", "")


@pytest.mark.asyncio
async def test_regenerate_clip_no_metric_found(sample_scene):
    """Test that regeneration fails if no quality metric exists."""
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None
    
    result = await regenerate_clip(
        db=db,
        generation_id="test-gen",
        scene_number=1,
        scene=sample_scene,
        output_dir="/tmp",
        original_clip_path="/original/clip.mp4",
        prompt_text="test prompt"
    )
    
    clip_path, success, details = result
    
    assert clip_path is None
    assert success is False
    assert "No quality metric found" in details.get("error", "")


@pytest.mark.asyncio
async def test_regenerate_clip_successful_improvement(mock_quality_metric, sample_scene):
    """Test successful regeneration that improves quality."""
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = mock_quality_metric
    db.commit = Mock()
    
    with patch("app.services.video_generation_standalone.generate_video_clip") as mock_gen, \
         patch("app.services.pipeline.quality_control.evaluate_vbench") as mock_eval, \
         patch("app.services.pipeline.quality_control.check_quality_thresholds") as mock_check:
        
        # Mock successful regeneration
        mock_gen.return_value = ("/new/clip.mp4", "model-used")
        
        # Mock quality evaluation - improved quality
        mock_eval.return_value = {"overall_quality": 85.0}
        mock_check.return_value = (True, {"passed": True, "failed_dimensions": []})
        
        result = await regenerate_clip(
            db=db,
            generation_id="test-gen",
            scene_number=1,
            scene=sample_scene,
            output_dir="/tmp",
            original_clip_path="/original/clip.mp4",
            prompt_text="test prompt",
            max_attempts=2
        )
        
        clip_path, success, details = result
        
        assert clip_path == "/new/clip.mp4"
        assert success is True
        assert details.get("quality_passed") is True
        assert mock_quality_metric.regeneration_attempts == 1
        assert mock_quality_metric.passed_threshold is True
        db.commit.assert_called()


@pytest.mark.asyncio
async def test_regenerate_clip_still_below_threshold(mock_quality_metric, sample_scene):
    """Test regeneration that still doesn't meet threshold."""
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = mock_quality_metric
    db.commit = Mock()
    
    with patch("app.services.video_generation_standalone.generate_video_clip") as mock_gen, \
         patch("app.services.pipeline.quality_control.evaluate_vbench") as mock_eval, \
         patch("app.services.pipeline.quality_control.check_quality_thresholds") as mock_check:
        
        # Mock regeneration
        mock_gen.return_value = ("/new/clip.mp4", "model-used")
        
        # Mock quality evaluation - still below threshold
        mock_eval.return_value = {"overall_quality": 65.0}
        mock_check.return_value = (False, {"passed": False, "failed_dimensions": ["overall_quality"]})
        
        # Set attempts to max to prevent recursion
        mock_quality_metric.regeneration_attempts = 1
        
        result = await regenerate_clip(
            db=db,
            generation_id="test-gen",
            scene_number=1,
            scene=sample_scene,
            output_dir="/tmp",
            original_clip_path="/original/clip.mp4",
            prompt_text="test prompt",
            max_attempts=2
        )
        
        clip_path, success, details = result
        
        # Should return the clip even if quality is below threshold (max attempts reached)
        assert clip_path == "/new/clip.mp4"
        assert success is False
        assert details.get("quality_passed") is False
        assert details.get("max_attempts_reached") is True

