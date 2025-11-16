"""
Unit tests for editor export service.
Tests export functionality, progress tracking, cancellation, and error handling.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
from sqlalchemy.orm import Session

from app.db.models.editing_session import EditingSession
from app.db.models.generation import Generation
from app.db.models.user import User
from app.services.editor.export_service import (
    export_edited_video,
    process_clip_with_edits,
    _validate_file_path,
)


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        id="user-123",
        username="testuser",
        password_hash="hashed",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_generation(db_session, sample_user):
    """Create a sample generation with metadata."""
    generation = Generation(
        id="gen-123",
        user_id=sample_user.id,
        prompt="Test prompt",
        status="completed",
        video_path="/output/videos/gen-123.mp4",
        video_url="/output/videos/gen-123.mp4",
        llm_specification={
            "brand_guidelines": {
                "visual_style_keywords": "cinematic",
                "mood": "professional",
            }
        },
        scene_plan={
            "scenes": [
                {"scene_number": 1, "description": "Scene 1"},
            ]
        },
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    return generation


@pytest.fixture
def sample_editing_session(db_session, sample_generation, sample_user):
    """Create a sample editing session with clips."""
    clip_dir = Path("output") / "temp"
    clip_dir.mkdir(parents=True, exist_ok=True)
    clip1_path = (clip_dir / "clip1.mp4").resolve()
    clip2_path = (clip_dir / "clip2.mp4").resolve()
    clip1_path.touch(exist_ok=True)
    clip2_path.touch(exist_ok=True)

    editing_state = {
        "clips": [
            {
                "id": "clip-1",
                "original_path": str(clip1_path),
                "start_time": 0.0,
                "end_time": 5.0,
                "trim_start": None,
                "trim_end": None,
                "split_points": [],
                "merged_with": [],
            },
            {
                "id": "clip-2",
                "original_path": str(clip2_path),
                "start_time": 5.0,
                "end_time": 10.0,
                "trim_start": 0.5,
                "trim_end": 9.5,
                "split_points": [],
                "merged_with": [],
            },
        ],
        "version": 1,
    }
    
    session = EditingSession(
        id="session-123",
        generation_id=sample_generation.id,
        user_id=sample_user.id,
        original_video_path="/output/videos/gen-123.mp4",
        editing_state=editing_state,
        status="saved",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def test_validate_file_path_valid():
    """Test file path validation with valid paths."""
    allowed_dirs = ["/output", "/tmp"]
    
    assert _validate_file_path("/output/videos/test.mp4", allowed_dirs) is True
    assert _validate_file_path("/tmp/test.mp4", allowed_dirs) is True
    assert _validate_file_path("/output/temp/clip1.mp4", allowed_dirs) is True


def test_validate_file_path_invalid():
    """Test file path validation with invalid paths."""
    allowed_dirs = ["/output", "/tmp"]
    
    assert _validate_file_path("/etc/passwd", allowed_dirs) is False
    assert _validate_file_path("/root/secret.mp4", allowed_dirs) is False
    assert _validate_file_path("../../etc/passwd", allowed_dirs) is False


@patch('app.services.editor.export_service.VideoFileClip')
def test_process_clip_with_edits_no_trim(mock_video_clip_class, tmp_path):
    """Test processing clip without trim operations."""
    mock_clip = MagicMock()
    mock_clip.duration = 10.0
    mock_clip.write_videofile = MagicMock()
    mock_clip.close = MagicMock()
    mock_video_clip_class.return_value = mock_clip
    
    clip_state = {
        "id": "clip-1",
        "original_path": str(tmp_path / "clip1.mp4"),
        "start_time": 0.0,
        "end_time": 10.0,
        "trim_start": None,
        "trim_end": None,
    }
    
    # Create dummy file
    (tmp_path / "clip1.mp4").touch()
    
    result = process_clip_with_edits(
        clip_state=clip_state,
        temp_dir=str(tmp_path),
        cancellation_check=None
    )
    
    assert result.endswith(".mp4")
    assert mock_clip.write_videofile.called
    mock_clip.close.assert_called()


@patch('app.services.editor.export_service.VideoFileClip')
def test_process_clip_with_edits_with_trim(mock_video_clip_class, tmp_path):
    """Test processing clip with trim operations."""
    mock_clip = MagicMock()
    mock_clip.duration = 10.0
    mock_trimmed = MagicMock()
    mock_trimmed.write_videofile = MagicMock()
    mock_trimmed.close = MagicMock()
    mock_clip.subclip = MagicMock(return_value=mock_trimmed)
    mock_clip.close = MagicMock()
    mock_video_clip_class.return_value = mock_clip
    
    clip_state = {
        "id": "clip-1",
        "original_path": str(tmp_path / "clip1.mp4"),
        "start_time": 0.0,
        "end_time": 10.0,
        "trim_start": 1.0,
        "trim_end": 9.0,
    }
    
    # Create dummy file
    (tmp_path / "clip1.mp4").touch()
    
    result = process_clip_with_edits(
        clip_state=clip_state,
        temp_dir=str(tmp_path),
        cancellation_check=None
    )
    
    assert result.endswith(".mp4")
    assert mock_clip.subclip.called
    assert mock_trimmed.write_videofile.called
    mock_clip.close.assert_called()


def test_process_clip_with_edits_missing_path(tmp_path):
    """Test processing clip with missing file path."""
    clip_state = {
        "id": "clip-1",
        "original_path": str(tmp_path / "nonexistent.mp4"),
        "start_time": 0.0,
        "end_time": 10.0,
    }
    
    with pytest.raises(ValueError, match="Clip original_path not found"):
        process_clip_with_edits(
            clip_state=clip_state,
            temp_dir=str(tmp_path),
            cancellation_check=None
        )


def test_process_clip_with_edits_cancellation(tmp_path):
    """Test processing clip with cancellation check."""
    clip_state = {
        "id": "clip-1",
        "original_path": str(tmp_path / "clip1.mp4"),
        "start_time": 0.0,
        "end_time": 10.0,
    }
    
    # Create dummy file
    (tmp_path / "clip1.mp4").touch()
    
    def cancellation_check():
        return True
    
    with pytest.raises(RuntimeError, match="Export cancelled"):
        process_clip_with_edits(
            clip_state=clip_state,
            temp_dir=str(tmp_path),
            cancellation_check=cancellation_check
        )


@patch('app.services.editor.export_service.export_final_video')
@patch('app.services.editor.export_service.add_audio_layer')
@patch('app.services.editor.export_service.stitch_video_clips')
@patch('app.services.editor.export_service.VideoFileClip')
def test_export_edited_video_success(
    mock_video_clip_class,
    mock_stitch,
    mock_audio,
    mock_export_final,
    db_session,
    sample_editing_session,
    tmp_path
):
    """Test successful export of edited video."""
    # Setup mocks
    mock_clip = MagicMock()
    mock_clip.duration = 10.0
    mock_clip.write_videofile = MagicMock()
    mock_clip.close = MagicMock()
    mock_video_clip_class.return_value = mock_clip
    
    mock_stitch.return_value = str(tmp_path / "stitched.mp4")
    mock_audio.return_value = str(tmp_path / "with_audio.mp4")
    mock_export_final.return_value = ("videos/export-123.mp4", "thumbnails/export-123.jpg")
    
    # Create dummy clip files
    clip1_path = tmp_path / "clip1.mp4"
    clip2_path = tmp_path / "clip2.mp4"
    clip1_path.touch()
    clip2_path.touch()
    
    # Update editing session with actual paths
    editing_state = sample_editing_session.editing_state.copy()
    editing_state["clips"][0]["original_path"] = str(clip1_path)
    editing_state["clips"][1]["original_path"] = str(clip2_path)
    sample_editing_session.editing_state = editing_state
    db_session.commit()
    
    # Track progress
    progress_calls = []
    def progress_callback(progress, step):
        progress_calls.append((progress, step))
    
    # Test export
    exported_path, export_id = export_edited_video(
        editing_session=sample_editing_session,
        output_dir=str(tmp_path),
        export_generation_id="export-123",
        cancellation_check=None,
        progress_callback=progress_callback
    )
    
    # Assertions
    assert exported_path is not None
    assert export_id == "export-123"
    assert mock_stitch.called
    assert mock_audio.called
    assert mock_export_final.called
    
    # Verify progress callbacks
    assert len(progress_calls) > 0
    assert progress_calls[0] == (10, "Export started")
    # Check that progress reached 100%
    final_progress = max(p[0] for p in progress_calls)
    assert final_progress == 100


def test_export_edited_video_no_editing_state(db_session, sample_editing_session):
    """Test export with no editing state."""
    sample_editing_session.editing_state = None
    db_session.commit()
    
    with pytest.raises(ValueError, match="Editing session has no editing_state"):
        export_edited_video(
            editing_session=sample_editing_session,
            output_dir="/output",
            export_generation_id="export-123",
        )


def test_export_edited_video_no_clips(db_session, sample_editing_session):
    """Test export with no clips in editing state."""
    sample_editing_session.editing_state = {"clips": [], "version": 1}
    db_session.commit()
    
    with pytest.raises(ValueError, match="Editing state has no clips"):
        export_edited_video(
            editing_session=sample_editing_session,
            output_dir="/output",
            export_generation_id="export-123",
        )


@patch('app.services.editor.export_service.VideoFileClip')
def test_export_edited_video_cancellation(
    mock_video_clip_class,
    db_session,
    sample_editing_session,
    tmp_path
):
    """Test export cancellation."""
    mock_clip = MagicMock()
    mock_clip.duration = 10.0
    mock_clip.write_videofile = MagicMock()
    mock_clip.close = MagicMock()
    mock_video_clip_class.return_value = mock_clip
    
    # Create dummy clip files
    clip1_path = tmp_path / "clip1.mp4"
    clip1_path.touch()
    
    editing_state = sample_editing_session.editing_state.copy()
    editing_state["clips"][0]["original_path"] = str(clip1_path)
    sample_editing_session.editing_state = editing_state
    db_session.commit()
    
    cancellation_called = [False]
    def cancellation_check():
        cancellation_called[0] = True
        return True
    
    with pytest.raises(RuntimeError, match="Export cancelled"):
        export_edited_video(
            editing_session=sample_editing_session,
            output_dir=str(tmp_path),
            export_generation_id="export-123",
            cancellation_check=cancellation_check,
        )
    
    assert cancellation_called[0] is True


@patch('app.services.editor.export_service.export_final_video')
@patch('app.services.editor.export_service.add_audio_layer')
@patch('app.services.editor.export_service.stitch_video_clips')
@patch('app.services.editor.export_service.VideoFileClip')
def test_export_edited_video_extracts_brand_style(
    mock_video_clip_class,
    mock_stitch,
    mock_audio,
    mock_export_final,
    db_session,
    sample_editing_session,
    sample_generation,
    tmp_path
):
    """Test that export extracts brand style from generation metadata."""
    # Setup mocks
    mock_clip = MagicMock()
    mock_clip.duration = 10.0
    mock_clip.write_videofile = MagicMock()
    mock_clip.close = MagicMock()
    mock_video_clip_class.return_value = mock_clip
    
    mock_stitch.return_value = str(tmp_path / "stitched.mp4")
    mock_audio.return_value = str(tmp_path / "with_audio.mp4")
    mock_export_final.return_value = ("videos/export-123.mp4", "thumbnails/export-123.jpg")
    
    # Create dummy clip files
    clip1_path = tmp_path / "clip1.mp4"
    clip1_path.touch()
    
    editing_state = sample_editing_session.editing_state.copy()
    editing_state["clips"][0]["original_path"] = str(clip1_path)
    sample_editing_session.editing_state = editing_state
    db_session.commit()
    
    # Test export
    export_edited_video(
        editing_session=sample_editing_session,
        output_dir=str(tmp_path),
        export_generation_id="export-123",
    )
    
    # Verify brand style was extracted and passed to export_final_video
    assert mock_export_final.called
    call_args = mock_export_final.call_args
    assert call_args[1]['brand_style'] == "cinematic"  # From llm_specification

