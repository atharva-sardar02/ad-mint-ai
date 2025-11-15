"""
Unit tests for post-processing and export service.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import numpy as np

from app.services.pipeline.export import (
    export_final_video,
    _apply_color_grading,
    _generate_thumbnail
)


@pytest.fixture
def mock_video_clip():
    """Mock MoviePy VideoFileClip."""
    clip = MagicMock()
    clip.duration = 15.0
    clip.fps = 24.0
    clip.size = (1920, 1080)  # 1080p resolution
    clip.write_videofile = MagicMock()
    clip.get_frame = MagicMock(return_value=np.zeros((1920, 1080, 3), dtype=np.uint8))
    clip.fl = MagicMock(return_value=clip)  # Color grading returns clip via fl()
    clip.resize = MagicMock(return_value=clip)  # Resize returns clip
    clip.close = MagicMock()
    return clip


@patch('app.services.pipeline.export.VideoFileClip')
@patch('app.services.pipeline.export.cv2.imwrite')
def test_export_final_video_basic(
    mock_imwrite,
    mock_video_clip_class,
    tmp_path
):
    """Test basic video export with thumbnail generation."""
    # Setup video mock
    mock_video = MagicMock()
    mock_video.duration = 15.0
    mock_video.fps = 24.0
    mock_video.size = (1920, 1080)  # 1080p resolution
    mock_video.write_videofile = MagicMock()
    mock_video.get_frame = MagicMock(
        return_value=np.zeros((1920, 1080, 3), dtype=np.uint8)
    )
    mock_video.fl = MagicMock(return_value=mock_video)  # Color grading returns clip via fl()
    mock_video.resize = MagicMock(return_value=mock_video)  # Resize returns clip
    mock_video.close = MagicMock()
    mock_video_clip_class.return_value = mock_video
    
    # Test
    video_url, thumbnail_url = export_final_video(
        video_path=str(tmp_path / "input.mp4"),
        brand_style="cinematic",
        output_dir=str(tmp_path),
        generation_id="test-123"
    )
    
    # Assertions
    assert video_url.startswith("videos/")
    assert thumbnail_url.startswith("thumbnails/")
    assert "test-123" in video_url
    assert "test-123" in thumbnail_url
    
    # Verify video export
    assert mock_video.write_videofile.called
    write_args = mock_video.write_videofile.call_args
    assert write_args[1]['codec'] == 'libx264'
    assert write_args[1]['fps'] == 24
    
    # Verify thumbnail generation
    assert mock_imwrite.called
    assert mock_video.get_frame.called
    
    # Verify cleanup
    mock_video.close.assert_called()


def test_apply_color_grading_cinematic(mock_video_clip):
    """Test color grading for cinematic style."""
    result = _apply_color_grading(mock_video_clip, "cinematic")
    assert result is not None


def test_apply_color_grading_luxury(mock_video_clip):
    """Test color grading for luxury style."""
    result = _apply_color_grading(mock_video_clip, "luxury")
    assert result is not None


def test_apply_color_grading_vibrant(mock_video_clip):
    """Test color grading for vibrant style."""
    result = _apply_color_grading(mock_video_clip, "vibrant")
    assert result is not None


def test_apply_color_grading_default(mock_video_clip):
    """Test color grading for default/unknown style."""
    result = _apply_color_grading(mock_video_clip, "unknown")
    assert result is not None


@patch('app.services.pipeline.export.cv2.imwrite')
@patch('app.services.pipeline.export.cv2.cvtColor')
def test_generate_thumbnail(
    mock_cvt_color,
    mock_imwrite,
    mock_video_clip,
    tmp_path
):
    """Test thumbnail generation from video frame."""
    # Setup mocks
    mock_cvt_color.return_value = np.zeros((1920, 1080, 3), dtype=np.uint8)
    mock_imwrite.return_value = True
    
    # Test
    output_path = str(tmp_path / "thumbnail.jpg")
    _generate_thumbnail(mock_video_clip, output_path)
    
    # Assertions
    assert mock_video_clip.get_frame.called
    assert mock_cvt_color.called
    assert mock_imwrite.called
    
    # Verify output path
    imwrite_args = mock_imwrite.call_args
    assert output_path in str(imwrite_args[0][0])


def test_export_final_video_cancellation(tmp_path):
    """Test export with cancellation check."""
    cancellation_called = [False]
    
    def check_cancellation():
        cancellation_called[0] = True
        return True
    
    with pytest.raises(RuntimeError, match="cancelled"):
        export_final_video(
            video_path=str(tmp_path / "input.mp4"),
            brand_style="cinematic",
            output_dir=str(tmp_path),
            generation_id="test-123",
            cancellation_check=check_cancellation
        )
    
    assert cancellation_called[0]


@patch('app.services.pipeline.export.VideoFileClip')
def test_export_final_video_output_directories_created(
    mock_video_clip_class,
    tmp_path
):
    """Test that output directories are created if they don't exist."""
    # Setup video mock
    mock_video = MagicMock()
    mock_video.duration = 15.0
    mock_video.fps = 24.0
    mock_video.size = (1920, 1080)  # 1080p resolution
    mock_video.write_videofile = MagicMock()
    mock_video.get_frame = MagicMock(
        return_value=np.zeros((1920, 1080, 3), dtype=np.uint8)
    )
    mock_video.fl = MagicMock(return_value=mock_video)  # Color grading returns clip via fl()
    mock_video.resize = MagicMock(return_value=mock_video)  # Resize returns clip
    mock_video.close = MagicMock()
    mock_video_clip_class.return_value = mock_video
    
    # Test
    output_dir = tmp_path / "output"
    export_final_video(
        video_path=str(tmp_path / "input.mp4"),
        brand_style="cinematic",
        output_dir=str(output_dir),
        generation_id="test-123"
    )
    
    # Verify directories were created
    assert (output_dir / "videos").exists()
    assert (output_dir / "thumbnails").exists()

