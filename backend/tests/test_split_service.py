"""
Unit tests for split service.
Tests split validation, editing session state updates, and metadata preservation.
"""
import pytest
from sqlalchemy.orm import Session

from app.db.models.editing_session import EditingSession
from app.db.models.generation import Generation
from app.db.models.user import User
from app.services.editor.split_service import (
    validate_split_point,
    apply_split_to_editing_session,
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
    """Create a sample generation."""
    generation = Generation(
        id="gen-123",
        user_id=sample_user.id,
        prompt="Test prompt",
        status="completed",
        video_path="/output/videos/gen-123.mp4",
        video_url="/output/videos/gen-123.mp4",
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    return generation


@pytest.fixture
def sample_editing_session(db_session, sample_generation, sample_user):
    """Create a sample editing session with clips."""
    editing_state = {
        "clips": [
            {
                "id": "clip-1",
                "original_path": "/path/to/clip1.mp4",
                "start_time": 0.0,
                "end_time": 10.0,
                "trim_start": None,
                "trim_end": None,
                "split_points": [],
                "merged_with": [],
                "scene_number": 1,
                "text_overlay": {
                    "text": "Test Overlay",
                    "position": "top",
                    "font_size": 48,
                    "color": "#FFFFFF",
                    "animation": "fade_in",
                },
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
        status="active",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def test_validate_split_point_valid():
    """Test validation of valid split point."""
    is_valid, error = validate_split_point(
        clip_start_time=0.0,
        clip_end_time=10.0,
        split_time=5.0,
    )

    assert is_valid is True
    assert error is None


def test_validate_split_point_at_start():
    """Test validation fails when split point is at clip start."""
    is_valid, error = validate_split_point(
        clip_start_time=0.0,
        clip_end_time=10.0,
        split_time=0.0,
    )

    assert is_valid is False
    assert "cannot be at clip start" in error


def test_validate_split_point_at_end():
    """Test validation fails when split point is at clip end."""
    is_valid, error = validate_split_point(
        clip_start_time=0.0,
        clip_end_time=10.0,
        split_time=10.0,
    )

    assert is_valid is False
    assert "cannot be at clip end" in error


def test_validate_split_point_below_minimum_duration_first_clip():
    """Test validation fails when first clip would be too short."""
    is_valid, error = validate_split_point(
        clip_start_time=0.0,
        clip_end_time=10.0,
        split_time=0.3,  # Less than 0.5s minimum
    )

    assert is_valid is False
    assert "First clip duration must be at least" in error


def test_validate_split_point_below_minimum_duration_second_clip():
    """Test validation fails when second clip would be too short."""
    is_valid, error = validate_split_point(
        clip_start_time=0.0,
        clip_end_time=10.0,
        split_time=9.7,  # Second clip would be 0.3s (< 0.5s minimum)
    )

    assert is_valid is False
    assert "Second clip duration must be at least" in error


def test_apply_split_to_editing_session_success(
    db_session, sample_editing_session
):
    """Test successful split operation."""
    result = apply_split_to_editing_session(
        editing_session=sample_editing_session,
        clip_id="clip-1",
        split_time=5.0,
        db=db_session,
    )

    assert result["original_clip_id"] == "clip-1"
    assert len(result["new_clips"]) == 2
    assert result["new_clips"][0]["duration"] == 5.0
    assert result["new_clips"][1]["duration"] == 5.0

    # Verify editing state was updated
    db_session.refresh(sample_editing_session)
    updated_state = sample_editing_session.editing_state
    assert len(updated_state["clips"]) == 2
    assert updated_state["version"] == 2

    # Verify both clips have metadata preserved
    first_clip = updated_state["clips"][0]
    second_clip = updated_state["clips"][1]

    assert first_clip["scene_number"] == 1
    assert first_clip["text_overlay"] is not None
    assert first_clip["text_overlay"]["text"] == "Test Overlay"

    assert second_clip["scene_number"] == 1
    assert second_clip["text_overlay"] is not None
    assert second_clip["text_overlay"]["text"] == "Test Overlay"


def test_apply_split_to_editing_session_clip_not_found(
    db_session, sample_editing_session
):
    """Test split operation fails when clip not found."""
    with pytest.raises(ValueError, match="Clip.*not found"):
        apply_split_to_editing_session(
            editing_session=sample_editing_session,
            clip_id="nonexistent-clip",
            split_time=5.0,
            db=db_session,
        )


def test_apply_split_to_editing_session_invalid_split_point(
    db_session, sample_editing_session
):
    """Test split operation fails with invalid split point."""
    with pytest.raises(ValueError, match="Split point cannot be at clip start"):
        apply_split_to_editing_session(
            editing_session=sample_editing_session,
            clip_id="clip-1",
            split_time=0.0,  # Invalid: at clip start
            db=db_session,
        )


def test_apply_split_to_editing_session_with_trimmed_clip(
    db_session, sample_editing_session
):
    """Test split operation with trimmed clip."""
    # First, trim the clip
    editing_state = sample_editing_session.editing_state
    editing_state["clips"][0]["trim_start"] = 1.0
    editing_state["clips"][0]["trim_end"] = 9.0
    sample_editing_session.editing_state = editing_state
    db_session.commit()

    # Split at 5.0 (relative to clip start, which is valid within trimmed boundaries)
    result = apply_split_to_editing_session(
        editing_session=sample_editing_session,
        clip_id="clip-1",
        split_time=5.0,
        db=db_session,
    )

    assert len(result["new_clips"]) == 2
    # First clip: 0.0 to 5.0 (but trimmed to 1.0-5.0 effectively)
    # Second clip: 5.0 to 10.0 (but trimmed to 5.0-9.0 effectively)
    assert result["new_clips"][0]["duration"] == 5.0
    assert result["new_clips"][1]["duration"] == 5.0


def test_apply_split_to_editing_session_preserves_original_path(
    db_session, sample_editing_session
):
    """Test that split clips preserve original_path."""
    result = apply_split_to_editing_session(
        editing_session=sample_editing_session,
        clip_id="clip-1",
        split_time=5.0,
        db=db_session,
    )

    db_session.refresh(sample_editing_session)
    updated_state = sample_editing_session.editing_state

    first_clip = updated_state["clips"][0]
    second_clip = updated_state["clips"][1]

    assert first_clip["original_path"] == "/path/to/clip1.mp4"
    assert second_clip["original_path"] == "/path/to/clip1.mp4"


def test_apply_split_to_editing_session_creates_unique_clip_ids(
    db_session, sample_editing_session
):
    """Test that split creates unique clip IDs."""
    result = apply_split_to_editing_session(
        editing_session=sample_editing_session,
        clip_id="clip-1",
        split_time=5.0,
        db=db_session,
    )

    first_clip_id = result["new_clips"][0]["clip_id"]
    second_clip_id = result["new_clips"][1]["clip_id"]

    assert first_clip_id != second_clip_id
    assert first_clip_id != "clip-1"
    assert second_clip_id != "clip-1"
    assert first_clip_id.startswith("clip-1-")
    assert second_clip_id.startswith("clip-1-")


def test_apply_split_to_editing_session_maintains_sequence_order(
    db_session, sample_editing_session
):
    """Test that split clips maintain correct sequence order."""
    # Add another clip after clip-1
    editing_state = sample_editing_session.editing_state
    editing_state["clips"].append({
        "id": "clip-2",
        "original_path": "/path/to/clip2.mp4",
        "start_time": 10.0,
        "end_time": 20.0,
        "trim_start": None,
        "trim_end": None,
        "split_points": [],
        "merged_with": [],
        "scene_number": 2,
        "text_overlay": None,
    })
    sample_editing_session.editing_state = editing_state
    db_session.commit()

    # Split clip-1
    result = apply_split_to_editing_session(
        editing_session=sample_editing_session,
        clip_id="clip-1",
        split_time=5.0,
        db=db_session,
    )

    db_session.refresh(sample_editing_session)
    updated_state = sample_editing_session.editing_state

    # Should have 3 clips: split clip-1 (2 clips) + clip-2
    assert len(updated_state["clips"]) == 3

    # First two clips should be the split clips
    assert updated_state["clips"][0]["start_time"] == 0.0
    assert updated_state["clips"][0]["end_time"] == 5.0
    assert updated_state["clips"][1]["start_time"] == 5.0
    assert updated_state["clips"][1]["end_time"] == 10.0
    # Third clip should be clip-2
    assert updated_state["clips"][2]["id"] == "clip-2"
    assert updated_state["clips"][2]["start_time"] == 10.0

