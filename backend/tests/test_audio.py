"""
Unit tests for audio layer service.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

from app.services.pipeline.audio import (
    add_audio_layer,
    _select_music_file,
    _select_sfx_file
)


@pytest.fixture
def mock_video_clip():
    """Mock MoviePy VideoFileClip."""
    clip = MagicMock()
    clip.duration = 15.0
    clip.fps = 24.0
    clip.set_audio = MagicMock(return_value=clip)
    clip.write_videofile = MagicMock()
    clip.close = MagicMock()
    return clip


@pytest.fixture
def mock_audio_clip():
    """Mock MoviePy AudioFileClip."""
    clip = MagicMock()
    clip.duration = 20.0
    clip.volumex = MagicMock(return_value=clip)
    clip.subclip = MagicMock(return_value=clip)
    clip.set_start = MagicMock(return_value=clip)
    clip.close = MagicMock()
    return clip


@patch('app.services.pipeline.audio.VideoFileClip')
@patch('app.services.pipeline.audio.AudioFileClip')
@patch('app.services.pipeline.audio.CompositeAudioClip')
def test_add_audio_layer_basic(
    mock_composite_audio,
    mock_audio_clip_class,
    mock_video_clip_class,
    tmp_path
):
    """Test basic audio layer addition."""
    # Setup video mock
    mock_video = MagicMock()
    mock_video.duration = 15.0
    mock_video.fps = 24.0
    mock_video.set_audio = MagicMock(return_value=mock_video)
    mock_video.write_videofile = MagicMock()
    mock_video.close = MagicMock()
    mock_video_clip_class.return_value = mock_video
    
    # Setup music mock
    mock_music = MagicMock()
    mock_music.duration = 20.0
    mock_music.volumex = MagicMock(return_value=mock_music)
    mock_music.subclip = MagicMock(return_value=mock_music)
    mock_music.close = MagicMock()
    mock_audio_clip_class.return_value = mock_music
    
    # Mock music file exists - patch the exists check on the returned path
    with patch('app.services.pipeline.audio._select_music_file') as mock_select:
        music_path = Path("backend/assets/music/professional.mp3")
        # Create a mock path that returns True for exists()
        mock_music_path = MagicMock(spec=Path)
        mock_music_path.exists.return_value = True
        mock_music_path.__str__ = lambda x: str(music_path)
        mock_select.return_value = mock_music_path
        
        # Test
        output_path = str(tmp_path / "with_audio.mp4")
        result = add_audio_layer(
            video_path=str(tmp_path / "input.mp4"),
            music_style="professional",
            output_path=output_path
        )
        
        # Assertions
        assert result == output_path
        assert mock_video_clip_class.called
        assert mock_audio_clip_class.called
        assert mock_music.volumex.called  # Volume adjustment
        assert mock_video.set_audio.called  # Audio attached
        assert mock_video.write_videofile.called
        
        # Verify cleanup
        mock_video.close.assert_called()
        mock_music.close.assert_called()


@patch('app.services.pipeline.audio.Path.exists')
def test_select_music_file_style_mapping(mock_exists):
    """Test music file selection based on style."""
    mock_exists.return_value = True
    
    # Test style mappings
    result = _select_music_file("professional")
    assert result is not None
    assert "professional" in str(result)
    
    result = _select_music_file("energetic")
    assert result is not None
    assert "energetic" in str(result)
    
    result = _select_music_file("calm")
    assert result is not None
    assert "calm" in str(result)
    
    # Test default fallback when specific style not found
    mock_exists.side_effect = lambda: True  # File exists
    result = _select_music_file("unknown_style")
    assert result is not None
    assert "professional" in str(result)  # Falls back to default


@patch('app.services.pipeline.audio.Path.exists')
def test_select_music_file_not_found(mock_exists):
    """Test music file selection when file not found - graceful fallback."""
    mock_exists.return_value = False
    
    # With graceful fallback, should return None instead of raising error
    result = _select_music_file("professional")
    assert result is None


@patch('app.services.pipeline.audio.Path.exists')
def test_select_sfx_file(mock_exists):
    """Test sound effect file selection."""
    mock_exists.return_value = True
    
    result = _select_sfx_file("transition")
    assert result is not None
    assert "transition" in str(result).lower()


@patch('app.services.pipeline.audio.Path.exists')
def test_select_sfx_file_not_found(mock_exists):
    """Test sound effect file selection when file not found."""
    mock_exists.return_value = False
    
    result = _select_sfx_file("nonexistent")
    assert result is None


@patch('app.services.pipeline.audio.VideoFileClip')
@patch('app.services.pipeline.audio.AudioFileClip')
def test_add_audio_layer_music_trimming(
    mock_audio_clip_class,
    mock_video_clip_class,
    tmp_path
):
    """Test that music is trimmed to video duration."""
    # Setup video (15s)
    mock_video = MagicMock()
    mock_video.duration = 15.0
    mock_video.fps = 24.0
    mock_video.set_audio = MagicMock(return_value=mock_video)
    mock_video.write_videofile = MagicMock()
    mock_video.close = MagicMock()
    mock_video_clip_class.return_value = mock_video
    
    # Setup music (longer than video - 30s)
    mock_music = MagicMock()
    mock_music.duration = 30.0
    mock_music.volumex = MagicMock(return_value=mock_music)
    mock_music.subclip = MagicMock(return_value=mock_music)
    mock_music.close = MagicMock()
    mock_audio_clip_class.return_value = mock_music
    
    # Mock music file exists - patch the exists check on the returned path
    with patch('app.services.pipeline.audio._select_music_file') as mock_select:
        music_path = Path("backend/assets/music/professional.mp3")
        # Create a mock path that returns True for exists()
        mock_music_path = MagicMock(spec=Path)
        mock_music_path.exists.return_value = True
        mock_music_path.__str__ = lambda x: str(music_path)
        mock_select.return_value = mock_music_path
        
        # Test
        output_path = str(tmp_path / "with_audio.mp4")
        add_audio_layer(
            video_path=str(tmp_path / "input.mp4"),
            music_style="professional",
            output_path=output_path
        )
        
        # Verify music was trimmed
        mock_music.subclip.assert_called_with(0, 15.0)


def test_add_audio_layer_cancellation(tmp_path):
    """Test audio layer addition with cancellation."""
    cancellation_called = [False]
    
    def check_cancellation():
        cancellation_called[0] = True
        return True
    
    with pytest.raises(RuntimeError, match="cancelled"):
        add_audio_layer(
            video_path=str(tmp_path / "input.mp4"),
            music_style="professional",
            output_path=str(tmp_path / "output.mp4"),
            cancellation_check=check_cancellation
        )
    
    assert cancellation_called[0]

