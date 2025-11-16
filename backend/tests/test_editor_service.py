"""
Unit tests for editor service.
Tests clip extraction, editing session creation, and error handling.
"""
import pytest
from sqlalchemy.orm import Session

from app.db.models.generation import Generation
from app.db.models.editing_session import EditingSession
from app.db.models.user import User
from app.services.editor.editor_service import (
    extract_clips_from_generation,
    get_or_create_editing_session,
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
def sample_generation_with_clips(db_session, sample_user):
    """Create a sample generation with temp_clip_paths and scene_plan."""
    generation = Generation(
        id="gen-123",
        user_id=sample_user.id,
        prompt="Test prompt",
        status="completed",
        video_path="/output/videos/gen-123.mp4",
        video_url="/output/videos/gen-123.mp4",
        aspect_ratio="9:16",
        framework="PAS",
        temp_clip_paths=[
            "/output/temp/gen-123/gen-123_scene_1.mp4",
            "/output/temp/gen-123/gen-123_scene_2.mp4",
            "/output/temp/gen-123/gen-123_scene_3.mp4",
        ],
        scene_plan={
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_type": "Problem",
                    "visual_prompt": "Test scene 1",
                    "duration": 5,
                    "text_overlay": {
                        "text": "Scene 1 Text",
                        "position": "top",
                        "font_size": 48,
                        "color": "#FFFFFF",
                        "animation": "fade_in",
                    },
                },
                {
                    "scene_number": 2,
                    "scene_type": "Solution",
                    "visual_prompt": "Test scene 2",
                    "duration": 5,
                    "text_overlay": {
                        "text": "Scene 2 Text",
                        "position": "center",
                        "font_size": 48,
                        "color": "#FFFFFF",
                        "animation": "slide_up",
                    },
                },
                {
                    "scene_number": 3,
                    "scene_type": "Action",
                    "visual_prompt": "Test scene 3",
                    "duration": 5,
                    "text_overlay": None,
                },
            ],
            "total_duration": 15,
            "framework": "PAS",
        },
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    return generation


@pytest.fixture
def sample_generation_no_clips(db_session, sample_user):
    """Create a sample generation without temp_clip_paths."""
    generation = Generation(
        id="gen-456",
        user_id=sample_user.id,
        prompt="Test prompt",
        status="completed",
        video_path="/output/videos/gen-456.mp4",
        video_url="/output/videos/gen-456.mp4",
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    return generation


def test_extract_clips_from_generation_with_temp_clip_paths(
    db_session, sample_generation_with_clips
):
    """Test clip extraction from generation with temp_clip_paths."""
    clips = extract_clips_from_generation(sample_generation_with_clips, db_session)

    assert len(clips) == 3
    assert clips[0].scene_number == 1
    assert clips[0].clip_id == "clip-gen-123-1"
    assert clips[0].original_path == "/output/temp/gen-123/gen-123_scene_1.mp4"
    assert clips[0].duration == 5.0
    assert clips[0].start_time == 0.0
    assert clips[0].end_time == 5.0
    assert clips[0].text_overlay is not None
    assert clips[0].text_overlay["text"] == "Scene 1 Text"

    assert clips[1].scene_number == 2
    assert clips[1].start_time == 5.0
    assert clips[1].end_time == 10.0

    assert clips[2].scene_number == 3
    assert clips[2].start_time == 10.0
    assert clips[2].end_time == 15.0
    assert clips[2].text_overlay is None  # Third scene has no text overlay


def test_extract_clips_from_generation_no_clips(
    db_session, sample_generation_no_clips
):
    """Test clip extraction when temp_clip_paths is missing."""
    clips = extract_clips_from_generation(sample_generation_no_clips, db_session)

    assert len(clips) == 0


def test_get_or_create_editing_session_creates_new(
    db_session, sample_generation_with_clips, sample_user
):
    """Test creating a new editing session."""
    session = get_or_create_editing_session(
        generation=sample_generation_with_clips,
        user_id=sample_user.id,
        db=db_session,
    )

    assert session is not None
    assert session.generation_id == sample_generation_with_clips.id
    assert session.user_id == sample_user.id
    assert session.original_video_path == sample_generation_with_clips.video_path
    assert session.status == "active"
    assert session.editing_state is not None
    assert "clips" in session.editing_state
    assert len(session.editing_state["clips"]) == 3
    assert session.editing_state["version"] == 1

    # Verify session is persisted
    db_session.refresh(session)
    assert session.id is not None


def test_get_or_create_editing_session_returns_existing(
    db_session, sample_generation_with_clips, sample_user
):
    """Test retrieving an existing editing session."""
    # Create initial session
    session1 = get_or_create_editing_session(
        generation=sample_generation_with_clips,
        user_id=sample_user.id,
        db=db_session,
    )
    session_id = session1.id

    # Get again - should return same session
    session2 = get_or_create_editing_session(
        generation=sample_generation_with_clips,
        user_id=sample_user.id,
        db=db_session,
    )

    assert session2.id == session_id
    assert session2.generation_id == session1.generation_id
    assert session2.user_id == session1.user_id


def test_get_or_create_editing_session_initializes_state(
    db_session, sample_generation_with_clips, sample_user
):
    """Test that editing session state is properly initialized with clips."""
    session = get_or_create_editing_session(
        generation=sample_generation_with_clips,
        user_id=sample_user.id,
        db=db_session,
    )

    assert session.editing_state is not None
    assert "clips" in session.editing_state
    assert len(session.editing_state["clips"]) == 3

    # Verify clip structure in editing state
    clip_state = session.editing_state["clips"][0]
    assert "id" in clip_state
    assert "original_path" in clip_state
    assert "start_time" in clip_state
    assert "end_time" in clip_state
    assert clip_state["trim_start"] is None
    assert clip_state["trim_end"] is None
    assert clip_state["split_points"] == []
    assert clip_state["merged_with"] == []

