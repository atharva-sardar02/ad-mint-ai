"""
Unit tests for text overlay service.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.schemas.generation import TextOverlay
from app.services.pipeline.overlays import (
    add_text_overlay,
    _create_text_clip,
    _get_font_path,
    _get_shadow_color,
    _apply_animation,
    _position_text_clip
)


@pytest.fixture
def sample_text_overlay():
    """Sample TextOverlay for testing."""
    return TextOverlay(
        text="Test Text",
        position="center",
        font_size=48,
        color="#FF0000",
        animation="fade_in"
    )


@pytest.fixture
def mock_video_clip():
    """Mock MoviePy VideoFileClip."""
    clip = MagicMock()
    clip.duration = 5.0
    clip.size = (1080, 1920)  # 9:16 aspect ratio
    clip.fps = 24.0
    clip.close = MagicMock()
    return clip


def test_get_font_path():
    """Test font path retrieval."""
    font = _get_font_path()
    # Font path can be None (fallback to MoviePy default) or a string path
    assert font is None or isinstance(font, str)
    if font:
        assert len(font) > 0


def test_get_shadow_color():
    """Test shadow color generation."""
    shadow = _get_shadow_color("#FFFFFF")
    assert shadow == "black"
    
    shadow2 = _get_shadow_color("#000000")
    assert shadow2 == "black"


def test_apply_animation_fade_in(sample_text_overlay):
    """Test fade in animation."""
    # Mock TextClip
    with patch('app.services.pipeline.overlays.TextClip') as mock_text_clip:
        mock_clip = MagicMock()
        mock_text_clip.return_value = mock_clip
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.fx.return_value = mock_clip
        
        text_overlay = sample_text_overlay
        text_overlay.animation = "fade_in"
        
        # This will call the animation function
        # Since we're mocking, we just verify the function doesn't crash
        result = _apply_animation(mock_clip, "fade_in")
        assert result is not None


def test_position_text_clip_top(mock_video_clip, sample_text_overlay):
    """Test positioning text at top."""
    with patch('app.services.pipeline.overlays.TextClip') as mock_text_clip:
        mock_text = MagicMock()
        mock_text.h = 100
        mock_text.with_position.return_value = mock_text
        mock_text_clip.return_value = mock_text
        
        positioned = _position_text_clip(
            text_clip=mock_text,
            position="top",
            video_size=(1080, 1920)
        )
        
        assert positioned is not None
        mock_text.with_position.assert_called_once()


def test_position_text_clip_center(mock_video_clip, sample_text_overlay):
    """Test positioning text at center."""
    with patch('app.services.pipeline.overlays.TextClip') as mock_text_clip:
        mock_text = MagicMock()
        mock_text.h = 100
        mock_text.with_position.return_value = mock_text
        mock_text_clip.return_value = mock_text
        
        positioned = _position_text_clip(
            text_clip=mock_text,
            position="center",
            video_size=(1080, 1920)
        )
        
        assert positioned is not None
        mock_text.with_position.assert_called_once()


def test_position_text_clip_bottom(mock_video_clip, sample_text_overlay):
    """Test positioning text at bottom."""
    with patch('app.services.pipeline.overlays.TextClip') as mock_text_clip:
        mock_text = MagicMock()
        mock_text.h = 100
        mock_text.with_position.return_value = mock_text
        mock_text_clip.return_value = mock_text
        
        positioned = _position_text_clip(
            text_clip=mock_text,
            position="bottom",
            video_size=(1080, 1920)
        )
        
        assert positioned is not None
        mock_text.with_position.assert_called_once()


@pytest.mark.skip(reason="Requires actual video file and MoviePy - integration test")
def test_add_text_overlay_integration(tmp_path, sample_text_overlay):
    """Integration test for adding text overlay (requires actual video file)."""
    # This would require a real video file and MoviePy installation
    # Skip for unit tests, but useful for integration testing
    pass



