"""
Integration tests for complete video generation pipeline.
Tests flow from clips → stitching → audio → export.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import numpy as np

from app.services.pipeline.stitching import stitch_video_clips
from app.services.pipeline.audio import add_audio_layer
from app.services.pipeline.export import export_final_video


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
def test_error_handling_stitching_failure(
    mock_concatenate,
    mock_video_clip,
    sample_clip_paths,
    tmp_path
):
    """Integration test: Error handling when stitching fails."""
    # Setup mocks to fail
    mock_clip = MagicMock()
    mock_clip.duration = 5.0
    mock_clip.fps = 24.0
    mock_clip.close = MagicMock()
    mock_video_clip.return_value = mock_clip
    
    mock_concatenate.side_effect = RuntimeError("Stitching failed")
    
    # Test error handling
    with pytest.raises(RuntimeError, match="Stitching failed"):
        stitch_video_clips(
            clip_paths=sample_clip_paths,
            output_path=str(tmp_path / "stitched.mp4"),
            transitions=True
        )


@patch('app.services.pipeline.audio.VideoFileClip')
@patch('app.services.pipeline.audio.AudioFileClip')
def test_error_handling_audio_failure(
    mock_audio_clip,
    mock_video_clip,
    tmp_path
):
    """Integration test: Error handling when audio addition fails."""
    # Setup mocks
    mock_video = MagicMock()
    mock_video.duration = 15.0
    mock_video.fps = 24.0
    mock_video.close = MagicMock()
    mock_video_clip.return_value = mock_video
    
    mock_audio_clip.side_effect = FileNotFoundError("Music file not found")
    
    # Test error handling
    with patch('app.services.pipeline.audio._select_music_file') as mock_select:
        mock_select.side_effect = FileNotFoundError("Music file not found")
        
        with pytest.raises(RuntimeError):
            add_audio_layer(
                video_path=str(tmp_path / "input.mp4"),
                music_style="professional",
                output_path=str(tmp_path / "output.mp4")
            )


@patch('app.services.pipeline.export.VideoFileClip')
def test_error_handling_export_failure(
    mock_video_clip,
    tmp_path
):
    """Integration test: Error handling when export fails."""
    # Setup mocks to fail
    mock_video = MagicMock()
    mock_video.duration = 15.0
    mock_video.fps = 24.0
    mock_video.size = (1920, 1080)  # 1080p resolution
    mock_video.fl = MagicMock(return_value=mock_video)  # Color grading
    mock_video.resize = MagicMock(return_value=mock_video)  # Resize
    mock_video.write_videofile.side_effect = RuntimeError("Export failed")
    mock_video.close = MagicMock()
    mock_video_clip.return_value = mock_video
    
    # Test error handling
    with pytest.raises(RuntimeError, match="Export failed"):
        export_final_video(
            video_path=str(tmp_path / "input.mp4"),
            brand_style="cinematic",
            output_dir=str(tmp_path),
            generation_id="test-123"
        )


def test_cancellation_during_processing(sample_clip_paths, tmp_path):
    """Integration test: Cancellation during processing stages."""
    cancellation_stage = [None]
    
    def check_cancellation():
        return cancellation_stage[0] is not None
    
    # Test cancellation during stitching
    cancellation_stage[0] = "stitching"
    with pytest.raises(RuntimeError, match="cancelled"):
        stitch_video_clips(
            clip_paths=sample_clip_paths,
            output_path=str(tmp_path / "stitched.mp4"),
            cancellation_check=check_cancellation
        )
    
    # Test cancellation during audio
    cancellation_stage[0] = "audio"
    with patch('app.services.pipeline.audio.VideoFileClip') as mock_video:
        mock_video_clip = MagicMock()
        mock_video_clip.duration = 15.0
        mock_video_clip.close = MagicMock()
        mock_video.return_value = mock_video_clip
        
        with pytest.raises(RuntimeError, match="cancelled"):
            add_audio_layer(
                video_path=str(tmp_path / "input.mp4"),
                music_style="professional",
                output_path=str(tmp_path / "output.mp4"),
                cancellation_check=check_cancellation
            )
    
    # Test cancellation during export
    cancellation_stage[0] = "export"
    with patch('app.services.pipeline.export.VideoFileClip') as mock_video:
        mock_video_clip = MagicMock()
        mock_video_clip.duration = 15.0
        mock_video_clip.close = MagicMock()
        mock_video.return_value = mock_video_clip
        
        with pytest.raises(RuntimeError, match="cancelled"):
            export_final_video(
                video_path=str(tmp_path / "input.mp4"),
                brand_style="cinematic",
                output_dir=str(tmp_path),
                generation_id="test-123",
                cancellation_check=check_cancellation
            )

