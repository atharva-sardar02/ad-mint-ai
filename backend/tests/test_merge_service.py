"""
Unit tests for merge service.
Tests merge validation, editing session state updates, and metadata preservation.
"""
import pytest
from sqlalchemy.orm import Session

from app.db.models.editing_session import EditingSession
from app.db.models.generation import Generation
from app.db.models.user import User
from app.services.editor.merge_service import (
    validate_clip_adjacency,
    apply_merge_to_editing_session,
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
def sample_editing_session_with_multiple_clips(db_session, sample_generation, sample_user):
    """Create a sample editing session with multiple adjacent clips."""
    editing_state = {
        "clips": [
            {
                "id": "clip-1",
                "original_path": "/path/to/clip1.mp4",
                "start_time": 0.0,
                "end_time": 5.0,
                "trim_start": None,
                "trim_end": None,
                "split_points": [],
                "merged_with": [],
                "scene_number": 1,
                "text_overlay": {
                    "text": "Scene 1",
                    "position": "top",
                    "font_size": 48,
                    "color": "#FFFFFF",
                    "animation": "fade_in",
                },
            },
            {
                "id": "clip-2",
                "original_path": "/path/to/clip2.mp4",
                "start_time": 5.0,
                "end_time": 10.0,
                "trim_start": None,
                "trim_end": None,
                "split_points": [],
                "merged_with": [],
                "scene_number": 2,
                "text_overlay": {
                    "text": "Scene 2",
                    "position": "bottom",
                    "font_size": 48,
                    "color": "#FFFFFF",
                    "animation": "fade_in",
                },
            },
            {
                "id": "clip-3",
                "original_path": "/path/to/clip3.mp4",
                "start_time": 10.0,
                "end_time": 15.0,
                "trim_start": None,
                "trim_end": None,
                "split_points": [],
                "merged_with": [],
                "scene_number": 3,
                "text_overlay": None,
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


def test_validate_clip_adjacency_valid():
    """Test validation of adjacent clips."""
    clips = [
        {"id": "clip-1", "start_time": 0.0, "end_time": 5.0},
        {"id": "clip-2", "start_time": 5.0, "end_time": 10.0},
    ]
    clip_ids = ["clip-1", "clip-2"]

    is_valid, error = validate_clip_adjacency(clips, clip_ids)

    assert is_valid is True
    assert error is None


def test_validate_clip_adjacency_not_adjacent():
    """Test validation fails when clips are not adjacent."""
    clips = [
        {"id": "clip-1", "start_time": 0.0, "end_time": 5.0},
        {"id": "clip-2", "start_time": 5.0, "end_time": 10.0},
        {"id": "clip-3", "start_time": 10.0, "end_time": 15.0},
    ]
    clip_ids = ["clip-1", "clip-3"]  # Not adjacent

    is_valid, error = validate_clip_adjacency(clips, clip_ids)

    assert is_valid is False
    assert "not adjacent" in error.lower()


def test_validate_clip_adjacency_insufficient_clips():
    """Test validation fails when less than 2 clips provided."""
    clips = [
        {"id": "clip-1", "start_time": 0.0, "end_time": 5.0},
    ]
    clip_ids = ["clip-1"]

    is_valid, error = validate_clip_adjacency(clips, clip_ids)

    assert is_valid is False
    assert "at least 2 clips" in error.lower()


def test_validate_clip_adjacency_missing_clip():
    """Test validation fails when clip not found."""
    clips = [
        {"id": "clip-1", "start_time": 0.0, "end_time": 5.0},
    ]
    clip_ids = ["clip-1", "clip-nonexistent"]

    is_valid, error = validate_clip_adjacency(clips, clip_ids)

    assert is_valid is False
    assert "not found" in error.lower()


def test_validate_clip_adjacency_wrong_order():
    """Test validation fails when clips are not in consecutive order."""
    clips = [
        {"id": "clip-1", "start_time": 0.0, "end_time": 5.0},
        {"id": "clip-2", "start_time": 5.0, "end_time": 10.0},
        {"id": "clip-3", "start_time": 10.0, "end_time": 15.0},
    ]
    clip_ids = ["clip-1", "clip-3"]  # clip-2 is between them

    is_valid, error = validate_clip_adjacency(clips, clip_ids)

    assert is_valid is False
    assert "consecutive" in error.lower() or "not adjacent" in error.lower()


def test_validate_clip_adjacency_floating_point_tolerance():
    """Test validation handles small floating point differences."""
    clips = [
        {"id": "clip-1", "start_time": 0.0, "end_time": 5.005},  # Slightly over 5.0
        {"id": "clip-2", "start_time": 5.0, "end_time": 10.0},
    ]
    clip_ids = ["clip-1", "clip-2"]

    is_valid, error = validate_clip_adjacency(clips, clip_ids)

    # Should be valid (gap < 0.01s tolerance)
    assert is_valid is True


def test_apply_merge_to_editing_session_success(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test successful merge operation."""
    result = apply_merge_to_editing_session(
        editing_session=sample_editing_session_with_multiple_clips,
        clip_ids=["clip-1", "clip-2"],
        db=db_session,
    )

    assert "merged_clip_id" in result
    assert result["new_duration"] == 10.0  # 5.0 + 5.0
    assert "updated_state" in result

    # Verify editing state was updated
    db_session.refresh(sample_editing_session_with_multiple_clips)
    updated_state = sample_editing_session_with_multiple_clips.editing_state
    assert len(updated_state["clips"]) == 2  # 2 original clips merged into 1, plus clip-3
    assert updated_state["version"] == 2

    # Verify merged clip exists
    merged_clip = next(
        (c for c in updated_state["clips"] if c["id"] == result["merged_clip_id"]),
        None
    )
    assert merged_clip is not None
    assert merged_clip["start_time"] == 0.0
    assert merged_clip["end_time"] == 10.0
    assert merged_clip["merged_with"] == ["clip-1", "clip-2"]


def test_apply_merge_to_editing_session_preserves_metadata(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test that merge preserves metadata from source clips."""
    result = apply_merge_to_editing_session(
        editing_session=sample_editing_session_with_multiple_clips,
        clip_ids=["clip-1", "clip-2"],
        db=db_session,
    )

    db_session.refresh(sample_editing_session_with_multiple_clips)
    updated_state = sample_editing_session_with_multiple_clips.editing_state

    merged_clip = next(
        (c for c in updated_state["clips"] if c["id"] == result["merged_clip_id"]),
        None
    )

    # Should preserve scene number (uses first clip's)
    assert merged_clip["scene_number"] == 1
    # Should preserve text overlay (uses first clip's)
    assert merged_clip["text_overlay"] is not None
    assert merged_clip["text_overlay"]["text"] == "Scene 1"


def test_apply_merge_to_editing_session_clip_not_found(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test merge operation fails when clip not found."""
    with pytest.raises(ValueError, match="not found"):
        apply_merge_to_editing_session(
            editing_session=sample_editing_session_with_multiple_clips,
            clip_ids=["clip-1", "nonexistent-clip"],  # One exists, one doesn't
            db=db_session,
        )


def test_apply_merge_to_editing_session_not_adjacent(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test merge operation fails when clips are not adjacent."""
    with pytest.raises(ValueError, match="not adjacent"):
        apply_merge_to_editing_session(
            editing_session=sample_editing_session_with_multiple_clips,
            clip_ids=["clip-1", "clip-3"],  # Not adjacent
            db=db_session,
        )


def test_apply_merge_to_editing_session_minimum_duration(
    db_session, sample_generation, sample_user
):
    """Test merge operation fails when merged clip would be too short."""
    # Create clips that when merged would be < 0.5s
    editing_state = {
        "clips": [
            {
                "id": "clip-1",
                "original_path": "/path/to/clip1.mp4",
                "start_time": 0.0,
                "end_time": 0.2,
                "trim_start": None,
                "trim_end": None,
                "split_points": [],
                "merged_with": [],
                "scene_number": 1,
                "text_overlay": None,
            },
            {
                "id": "clip-2",
                "original_path": "/path/to/clip2.mp4",
                "start_time": 0.2,
                "end_time": 0.3,  # Total would be 0.3s < 0.5s minimum
                "trim_start": None,
                "trim_end": None,
                "split_points": [],
                "merged_with": [],
                "scene_number": 2,
                "text_overlay": None,
            },
        ],
        "version": 1,
    }

    session = EditingSession(
        id="session-short",
        generation_id=sample_generation.id,
        user_id=sample_user.id,
        original_video_path="/output/videos/gen-123.mp4",
        editing_state=editing_state,
        status="active",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    with pytest.raises(ValueError, match="below minimum"):
        apply_merge_to_editing_session(
            editing_session=session,
            clip_ids=["clip-1", "clip-2"],
            db=db_session,
        )


def test_apply_merge_to_editing_session_with_trimmed_clips(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test merge operation with trimmed clips preserves trim points."""
    from sqlalchemy.orm.attributes import flag_modified
    
    # Trim both clips
    editing_state = sample_editing_session_with_multiple_clips.editing_state
    editing_state["clips"][0]["trim_start"] = 1.0
    editing_state["clips"][0]["trim_end"] = 4.0
    editing_state["clips"][1]["trim_start"] = 0.5
    editing_state["clips"][1]["trim_end"] = 4.5
    sample_editing_session_with_multiple_clips.editing_state = editing_state
    flag_modified(sample_editing_session_with_multiple_clips, "editing_state")
    db_session.commit()

    result = apply_merge_to_editing_session(
        editing_session=sample_editing_session_with_multiple_clips,
        clip_ids=["clip-1", "clip-2"],
        db=db_session,
    )

    db_session.refresh(sample_editing_session_with_multiple_clips)
    updated_state = sample_editing_session_with_multiple_clips.editing_state

    merged_clip = next(
        (c for c in updated_state["clips"] if c["id"] == result["merged_clip_id"]),
        None
    )

    # Should preserve trim points (min of trim_starts, max of trim_ends)
    assert merged_clip["trim_start"] == 0.5  # min(1.0, 0.5)
    assert merged_clip["trim_end"] == 4.5  # max(4.0, 4.5)


def test_apply_merge_to_editing_session_maintains_sequence_order(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test that merged clip maintains correct position in sequence."""
    result = apply_merge_to_editing_session(
        editing_session=sample_editing_session_with_multiple_clips,
        clip_ids=["clip-1", "clip-2"],
        db=db_session,
    )

    db_session.refresh(sample_editing_session_with_multiple_clips)
    updated_state = sample_editing_session_with_multiple_clips.editing_state

    # Should have 2 clips: merged clip + clip-3
    assert len(updated_state["clips"]) == 2

    # First clip should be merged clip (0.0 to 10.0)
    assert updated_state["clips"][0]["start_time"] == 0.0
    assert updated_state["clips"][0]["end_time"] == 10.0
    assert updated_state["clips"][0]["id"] == result["merged_clip_id"]

    # Second clip should be clip-3 (10.0 to 15.0)
    assert updated_state["clips"][1]["id"] == "clip-3"
    assert updated_state["clips"][1]["start_time"] == 10.0
    assert updated_state["clips"][1]["end_time"] == 15.0


def test_apply_merge_to_editing_session_three_clips(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test merging three adjacent clips."""
    result = apply_merge_to_editing_session(
        editing_session=sample_editing_session_with_multiple_clips,
        clip_ids=["clip-1", "clip-2", "clip-3"],
        db=db_session,
    )

    assert result["new_duration"] == 15.0  # 5.0 + 5.0 + 5.0

    db_session.refresh(sample_editing_session_with_multiple_clips)
    updated_state = sample_editing_session_with_multiple_clips.editing_state

    # Should have only 1 clip (all three merged)
    assert len(updated_state["clips"]) == 1
    assert updated_state["clips"][0]["id"] == result["merged_clip_id"]
    assert updated_state["clips"][0]["merged_with"] == ["clip-1", "clip-2", "clip-3"]


def test_apply_merge_to_editing_session_creates_unique_clip_id(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test that merge creates unique clip ID."""
    result = apply_merge_to_editing_session(
        editing_session=sample_editing_session_with_multiple_clips,
        clip_ids=["clip-1", "clip-2"],
        db=db_session,
    )

    merged_clip_id = result["merged_clip_id"]
    assert merged_clip_id.startswith("merged-")
    assert merged_clip_id != "clip-1"
    assert merged_clip_id != "clip-2"


def test_apply_merge_to_editing_session_preserves_original_path(
    db_session, sample_editing_session_with_multiple_clips
):
    """Test that merged clip preserves original_path."""
    result = apply_merge_to_editing_session(
        editing_session=sample_editing_session_with_multiple_clips,
        clip_ids=["clip-1", "clip-2"],
        db=db_session,
    )

    db_session.refresh(sample_editing_session_with_multiple_clips)
    updated_state = sample_editing_session_with_multiple_clips.editing_state

    merged_clip = next(
        (c for c in updated_state["clips"] if c["id"] == result["merged_clip_id"]),
        None
    )

    # Should use first clip's original_path
    assert merged_clip["original_path"] == "/path/to/clip1.mp4"

