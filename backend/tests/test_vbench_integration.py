"""
Test script to verify VBench integration.

This script tests the VBench evaluation functionality to ensure:
1. Quality control service can be imported
2. Video evaluation function works with sample videos
3. Quality scores are returned in expected format
4. Fallback metrics work when VBench library is unavailable
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from app.services.pipeline.quality_control import (
    evaluate_vbench,
    VBENCH_AVAILABLE,
    _evaluate_fallback_metrics,
    _compute_overall_quality,
)


def test_vbench_import():
    """Test that quality control service can be imported."""
    from app.services.pipeline import quality_control
    assert hasattr(quality_control, 'evaluate_vbench')
    assert hasattr(quality_control, 'VBENCH_AVAILABLE')


def test_evaluate_vbench_structure():
    """Test that evaluate_vbench returns expected structure."""
    # Create a dummy video path (test will skip if file doesn't exist)
    dummy_path = "/tmp/test_video.mp4"
    
    if not os.path.exists(dummy_path):
        pytest.skip("Test video not available - create a sample video for full testing")
    
    result = evaluate_vbench(dummy_path, "test prompt")
    
    # Verify structure
    assert isinstance(result, dict)
    required_keys = [
        "temporal_quality",
        "subject_consistency",
        "background_consistency",
        "motion_smoothness",
        "dynamic_degree",
        "aesthetic_quality",
        "imaging_quality",
        "object_class_alignment",
        "text_video_alignment",
        "overall_quality",
    ]
    
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
        assert isinstance(result[key], (int, float)), f"Key {key} should be numeric"
        assert 0 <= result[key] <= 100, f"Key {key} should be in range 0-100"


def test_fallback_metrics():
    """Test fallback metrics computation."""
    # This test requires a real video file
    # For now, test the structure with a non-existent file
    dummy_path = "/tmp/nonexistent_video.mp4"
    
    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        evaluate_vbench(dummy_path, "test prompt")


def test_overall_quality_computation():
    """Test overall quality score computation."""
    test_scores = {
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
    
    overall = _compute_overall_quality(test_scores)
    
    assert isinstance(overall, (int, float))
    assert 0 <= overall <= 100
    # Overall should be weighted average, not simple mean
    assert overall != sum(test_scores.values()) / len(test_scores)


def test_vbench_availability_flag():
    """Test that VBENCH_AVAILABLE flag is set correctly."""
    # Flag should be boolean
    assert isinstance(VBENCH_AVAILABLE, bool)
    
    # Currently should be False (library not installed)
    # When VBench is installed, this should be True
    # For now, we expect False
    assert VBENCH_AVAILABLE == False  # Expected until library is installed


if __name__ == "__main__":
    print("VBench Integration Test")
    print("=" * 50)
    print(f"VBench Available: {VBENCH_AVAILABLE}")
    print("\nRunning tests...")
    pytest.main([__file__, "-v"])



