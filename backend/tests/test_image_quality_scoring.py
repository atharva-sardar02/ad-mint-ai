"""
Unit tests for image quality scoring service.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from PIL import Image
import numpy as np

from app.services.pipeline.image_quality_scoring import (
    score_image,
    rank_images_by_quality,
    _compute_clip_score,
    _compute_pickscore,
    _compute_vqa_score,
    _compute_aesthetic_score,
    _load_clip_model
)


@pytest.fixture
def sample_image_path():
    """Create a temporary sample image file."""
    temp_dir = tempfile.mkdtemp()
    image_path = Path(temp_dir) / "test_image.png"
    
    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path)
    
    yield str(image_path)
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_prompt():
    """Sample prompt text."""
    return "A beautiful sunset over mountains"


@pytest.mark.asyncio
async def test_score_image_success(sample_image_path, sample_prompt):
    """Test successful image scoring."""
    with patch("app.services.pipeline.image_quality_scoring._compute_clip_score") as mock_clip, \
         patch("app.services.pipeline.image_quality_scoring._compute_pickscore") as mock_pick, \
         patch("app.services.pipeline.image_quality_scoring._compute_vqa_score") as mock_vqa, \
         patch("app.services.pipeline.image_quality_scoring._compute_aesthetic_score") as mock_aesthetic:
        
        mock_clip.return_value = 75.0
        mock_pick.return_value = 80.0
        mock_vqa.return_value = 70.0
        mock_aesthetic.return_value = 65.0
        
        scores = await score_image(sample_image_path, sample_prompt)
        
        assert "pickscore" in scores
        assert "clip_score" in scores
        assert "vqa_score" in scores
        assert "aesthetic" in scores
        assert "overall" in scores
        
        assert 0 <= scores["pickscore"] <= 100
        assert 0 <= scores["clip_score"] <= 100
        assert 0 <= scores["aesthetic"] <= 100
        assert 0 <= scores["overall"] <= 100
        
        # Overall should be weighted combination
        assert scores["overall"] > 0


@pytest.mark.asyncio
async def test_score_image_missing_file(sample_prompt):
    """Test that missing image file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        await score_image("/nonexistent/image.png", sample_prompt)


@pytest.mark.asyncio
async def test_score_image_without_vqa(sample_image_path, sample_prompt):
    """Test scoring when VQAScore is unavailable."""
    with patch("app.services.pipeline.image_quality_scoring._compute_clip_score") as mock_clip, \
         patch("app.services.pipeline.image_quality_scoring._compute_pickscore") as mock_pick, \
         patch("app.services.pipeline.image_quality_scoring._compute_vqa_score") as mock_vqa, \
         patch("app.services.pipeline.image_quality_scoring._compute_aesthetic_score") as mock_aesthetic:
        
        mock_clip.return_value = 75.0
        mock_pick.return_value = 80.0
        mock_vqa.return_value = None  # VQAScore unavailable
        mock_aesthetic.return_value = 65.0
        
        scores = await score_image(sample_image_path, sample_prompt)
        
        assert scores["vqa_score"] is None
        assert "overall" in scores
        # Overall should still be calculated (weights adjusted)
        assert scores["overall"] > 0


def test_rank_images_by_quality():
    """Test ranking images by overall quality score."""
    image_results = [
        ("image1.png", {"overall": 75.0, "pickscore": 80.0}),
        ("image2.png", {"overall": 90.0, "pickscore": 85.0}),
        ("image3.png", {"overall": 60.0, "pickscore": 70.0}),
    ]
    
    ranked = rank_images_by_quality(image_results)
    
    assert len(ranked) == 3
    # Should be sorted by overall score (descending)
    assert ranked[0][2] == 1  # Rank 1 (best)
    assert ranked[0][0] == "image2.png"  # Highest score
    assert ranked[1][2] == 2  # Rank 2
    assert ranked[1][0] == "image1.png"
    assert ranked[2][2] == 3  # Rank 3 (lowest)
    assert ranked[2][0] == "image3.png"


def test_rank_images_single_image():
    """Test ranking with single image."""
    image_results = [
        ("image1.png", {"overall": 75.0}),
    ]
    
    ranked = rank_images_by_quality(image_results)
    
    assert len(ranked) == 1
    assert ranked[0][2] == 1  # Rank 1
    assert ranked[0][0] == "image1.png"


@pytest.mark.skip(reason="Requires transformers and torch libraries - tested via integration tests")
def test_compute_clip_score_success(sample_image_path, sample_prompt):
    """Test CLIP-Score computation."""
    # This test requires transformers and torch to be installed
    # Skipped in unit tests, will be tested in integration tests
    pass


def test_compute_clip_score_missing_transformers(sample_image_path, sample_prompt):
    """Test CLIP-Score computation when transformers not available."""
    with patch("app.services.pipeline.image_quality_scoring._load_clip_model", return_value=(None, None)):
        score = _compute_clip_score(sample_image_path, sample_prompt)
        
        # Should return default score
        assert score == 50.0


def test_compute_pickscore_placeholder(sample_image_path, sample_prompt):
    """Test PickScore computation (placeholder implementation)."""
    score = _compute_pickscore(sample_image_path, sample_prompt)
    
    # Currently returns default score (placeholder)
    assert score == 50.0


def test_compute_vqa_score_placeholder(sample_image_path, sample_prompt):
    """Test VQAScore computation (placeholder implementation)."""
    score = _compute_vqa_score(sample_image_path, sample_prompt)
    
    # Currently returns None (placeholder)
    assert score is None


def test_compute_aesthetic_score_placeholder(sample_image_path):
    """Test Aesthetic Score computation (placeholder implementation)."""
    score = _compute_aesthetic_score(sample_image_path)
    
    # Currently returns default score (placeholder)
    assert score == 50.0


@pytest.mark.skip(reason="Requires transformers and torch libraries - tested via integration tests")
def test_load_clip_model_caching():
    """Test that CLIP model is cached after first load."""
    # This test requires transformers and torch to be installed
    # Skipped in unit tests, will be tested in integration tests
    pass

