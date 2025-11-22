"""
Unit tests for quality control service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from pathlib import Path

from app.services.pipeline.quality_control import (
    evaluate_vbench,
    check_quality_thresholds,
    store_quality_metric,
    evaluate_and_store_quality,
    _compute_overall_quality,
)


def test_evaluate_vbench_file_not_found():
    """Test that evaluate_vbench raises FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError):
        evaluate_vbench("/nonexistent/video.mp4", "test prompt")


def test_check_quality_thresholds_passed():
    """Test threshold checking with passing scores."""
    scores = {
        "temporal_quality": 80.0,
        "aesthetic_quality": 85.0,
        "imaging_quality": 82.0,
        "text_video_alignment": 75.0,
        "overall_quality": 80.0,
    }
    
    passed, details = check_quality_thresholds(scores)
    
    assert passed is True
    assert details["passed"] is True
    assert len(details["failed_dimensions"]) == 0


def test_check_quality_thresholds_failed():
    """Test threshold checking with failing scores."""
    scores = {
        "temporal_quality": 60.0,  # Below threshold
        "aesthetic_quality": 65.0,  # Below threshold
        "imaging_quality": 68.0,  # Below threshold
        "text_video_alignment": 55.0,  # Below threshold
        "overall_quality": 62.0,  # Below threshold
    }
    
    passed, details = check_quality_thresholds(scores)
    
    assert passed is False
    assert details["passed"] is False
    assert len(details["failed_dimensions"]) > 0


def test_check_quality_thresholds_custom_thresholds():
    """Test threshold checking with custom thresholds."""
    scores = {
        "temporal_quality": 75.0,
        "aesthetic_quality": 75.0,
        "imaging_quality": 75.0,
        "text_video_alignment": 75.0,
        "overall_quality": 75.0,
    }
    
    custom_thresholds = {
        "temporal_quality": 80.0,
        "frame_wise_quality": 80.0,
        "text_video_alignment": 80.0,
        "overall_quality": 80.0,
    }
    
    passed, details = check_quality_thresholds(scores, thresholds=custom_thresholds)
    
    assert passed is False  # Should fail with higher thresholds


def test_compute_overall_quality():
    """Test overall quality score computation."""
    scores = {
        "temporal_quality": 80.0,
        "subject_consistency": 75.0,
        "background_consistency": 70.0,
        "motion_smoothness": 85.0,
        "dynamic_degree": 60.0,
        "aesthetic_quality": 90.0,
        "imaging_quality": 88.0,
        "object_class_alignment": 70.0,
        "text_video_alignment": 75.0,
    }
    
    overall = _compute_overall_quality(scores)
    
    assert isinstance(overall, (int, float))
    assert 0 <= overall <= 100
    # Overall should be weighted average, not simple mean
    simple_mean = sum(scores.values()) / len(scores)
    assert overall != simple_mean


@pytest.mark.asyncio
async def test_evaluate_and_store_quality_disabled():
    """Test that quality evaluation is skipped when vbench_quality_control is disabled."""
    db = Mock()
    coherence_settings = {"vbench_quality_control": False}
    
    passed, details = await evaluate_and_store_quality(
        db=db,
        generation_id="test-gen",
        scene_number=1,
        clip_path="/test/video.mp4",
        prompt_text="test prompt",
        coherence_settings=coherence_settings
    )
    
    assert passed is True
    assert details.get("skipped") is True
    assert details.get("reason") == "vbench_quality_control disabled"
    # Should not call db.add
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_evaluate_and_store_quality_enabled():
    """Test quality evaluation when enabled (mocked)."""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    
    coherence_settings = {"vbench_quality_control": True}
    
    with patch("app.services.pipeline.quality_control.evaluate_vbench") as mock_eval, \
         patch("app.services.pipeline.quality_control.check_quality_thresholds") as mock_check, \
         patch("app.services.pipeline.quality_control.store_quality_metric") as mock_store:
        
        mock_eval.return_value = {
            "temporal_quality": 80.0,
            "aesthetic_quality": 85.0,
            "imaging_quality": 82.0,
            "text_video_alignment": 75.0,
            "overall_quality": 80.0,
        }
        mock_check.return_value = (True, {"passed": True, "failed_dimensions": []})
        mock_store.return_value = "metric-id-123"
        
        # Create a temporary file for the test
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            passed, details = await evaluate_and_store_quality(
                db=db,
                generation_id="test-gen",
                scene_number=1,
                clip_path=tmp_path,
                prompt_text="test prompt",
                coherence_settings=coherence_settings
            )
            
            assert passed is True
            assert details.get("skipped") is False
            assert "scores" in details
            mock_eval.assert_called_once()
            mock_check.assert_called_once()
            mock_store.assert_called_once()
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


def test_store_quality_metric():
    """Test storing quality metric in database."""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    
    # Mock the QualityMetric model
    with patch("app.services.pipeline.quality_control.QualityMetric") as mock_model:
        mock_instance = Mock()
        mock_instance.id = "metric-id-123"
        mock_model.return_value = mock_instance
        
        metric_id = store_quality_metric(
            db=db,
            generation_id="test-gen",
            scene_number=1,
            clip_path="/test/video.mp4",
            vbench_scores={"overall_quality": 80.0},
            passed_threshold=True,
            regeneration_attempts=0
        )
        
        assert metric_id == "metric-id-123"
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

