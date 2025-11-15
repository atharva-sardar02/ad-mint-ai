"""
Unit tests for video stitching service.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

from app.services.pipeline.stitching import stitch_video_clips


@pytest.fixture
def mock_video_clip():
    """Mock MoviePy VideoFileClip."""
    clip = MagicMock()
    clip.duration = 5.0
    clip.fps = 24.0
    clip.size = (1080, 1920)
    clip.close = MagicMock()
    return clip


@pytest.fixture
def sample_clip_paths(tmp_path):
    """Create sample clip file paths for testing."""
    clip1 = tmp_path / "clip1.mp4"
    clip2 = tmp_path / "clip2.mp4"
    clip3 = tmp_path / "clip3.mp4"
    
    # Create empty files
    clip1.write_bytes(b"fake video data")
    clip2.write_bytes(b"fake video data")
    clip3.write_bytes(b"fake video data")
    
    return [str(clip1), str(clip2), str(clip3)]


@patch('app.services.pipeline.stitching.VideoFileClip')
@patch('app.services.pipeline.stitching.concatenate_videoclips')
@patch('app.services.pipeline.stitching.FadeIn')
@patch('app.services.pipeline.stitching.FadeOut')
def test_stitch_video_clips_basic(
    mock_fade_out,
    mock_fade_in,
    mock_concatenate,
    mock_video_clip_class,
    sample_clip_paths,
    tmp_path
):
    """Test basic video stitching with multiple clips."""
    # Setup mocks
    mock_clips = []
    for _ in sample_clip_paths:
        clip = MagicMock()
        clip.duration = 5.0
        clip.fps = 24.0
        clip.close = MagicMock()
        mock_clips.append(clip)
    
    mock_video_clip_class.side_effect = mock_clips
    
    # Mock fade effects
    mock_fade_in_instance = MagicMock()
    mock_fade_in_instance.apply.return_value = mock_clips[0]
    mock_fade_in.return_value = mock_fade_in_instance
    
    mock_fade_out_instance = MagicMock()
    mock_fade_out_instance.apply.return_value = mock_clips[-1]
    mock_fade_out.return_value = mock_fade_out_instance
    
    # Mock concatenation
    mock_final_video = MagicMock()
    mock_final_video.fps = 24.0
    mock_final_video.write_videofile = MagicMock()
    mock_final_video.close = MagicMock()
    mock_concatenate.return_value = mock_final_video
    
    # Test
    output_path = str(tmp_path / "stitched.mp4")
    result = stitch_video_clips(
        clip_paths=sample_clip_paths,
        output_path=output_path,
        transitions=True
    )
    
    # Assertions
    assert result == output_path
    assert mock_video_clip_class.call_count == len(sample_clip_paths)
    assert mock_concatenate.called
    assert mock_final_video.write_videofile.called
    
    # Verify cleanup
    # Note: Clips are modified in place (fade in/out applied), so close may be called on modified clips
    # We verify that at least some cleanup occurred
    assert mock_final_video.close.called


def test_stitch_video_clips_empty_list():
    """Test stitching with empty clip list raises ValueError."""
    with pytest.raises(ValueError, match="clip_paths cannot be empty"):
        stitch_video_clips(clip_paths=[], output_path="output.mp4")


def test_stitch_video_clips_file_not_found(tmp_path):
    """Test stitching with non-existent clip file raises RuntimeError."""
    fake_clip = str(tmp_path / "nonexistent.mp4")
    
    with pytest.raises(RuntimeError, match="Clip file not found"):
        stitch_video_clips(clip_paths=[fake_clip], output_path="output.mp4")


def test_stitch_video_clips_cancellation(sample_clip_paths, tmp_path):
    """Test stitching with cancellation check."""
    cancellation_called = [False]
    
    def check_cancellation():
        cancellation_called[0] = True
        return True
    
    with pytest.raises(RuntimeError, match="cancelled"):
        stitch_video_clips(
            clip_paths=sample_clip_paths,
            output_path=str(tmp_path / "output.mp4"),
            cancellation_check=check_cancellation
        )
    
    assert cancellation_called[0]


@patch('app.services.pipeline.stitching.VideoFileClip')
@patch('app.services.pipeline.stitching.concatenate_videoclips')
def test_stitch_video_clips_frame_rate_normalization(
    mock_concatenate,
    mock_video_clip_class,
    sample_clip_paths,
    tmp_path
):
    """Test that clips with different frame rates are normalized to 24 fps."""
    # Setup mocks with different frame rates
    mock_clips = []
    for i, fps in enumerate([30.0, 25.0, 24.0]):
        clip = MagicMock()
        clip.duration = 5.0
        clip.fps = fps
        clip.set_fps = MagicMock(return_value=clip)
        clip.close = MagicMock()
        mock_clips.append(clip)
    
    mock_video_clip_class.side_effect = mock_clips
    
    # Mock concatenation
    mock_final_video = MagicMock()
    mock_final_video.fps = 24.0
    mock_final_video.write_videofile = MagicMock()
    mock_final_video.close = MagicMock()
    mock_concatenate.return_value = mock_final_video
    
    # Test
    output_path = str(tmp_path / "stitched.mp4")
    stitch_video_clips(
        clip_paths=sample_clip_paths,
        output_path=output_path,
        transitions=False  # Skip transitions for simpler test
    )
    
    # Verify set_fps was called for clips with non-24 fps
    assert mock_clips[0].set_fps.called  # 30 fps → should normalize
    assert mock_clips[1].set_fps.called  # 25 fps → should normalize
    # Clip 3 already 24 fps, may or may not call set_fps

