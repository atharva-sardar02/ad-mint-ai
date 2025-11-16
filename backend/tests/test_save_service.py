"""
Unit tests for save service.
Tests saving editing sessions, validation, and state management.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.editing_session import EditingSession
from app.db.models.generation import Generation
from app.db.models.user import User
from app.services.editor.save_service import save_editing_session


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
    """Create a sample editing session."""
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
            },
            {
                "id": "clip-2",
                "original_path": "/path/to/clip2.mp4",
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
        status="active",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def test_save_editing_session_with_new_state(db_session, sample_editing_session):
    """Test saving editing session with new editing state."""
    new_editing_state = {
        "clips": [
            {
                "id": "clip-1",
                "original_path": "/path/to/clip1.mp4",
                "start_time": 0.0,
                "end_time": 5.0,
                "trim_start": 0.5,
                "trim_end": 4.5,
                "split_points": [],
                "merged_with": [],
            },
        ],
        "version": 2,
    }
    
    result = save_editing_session(
        editing_session=sample_editing_session,
        editing_state=new_editing_state,
        db=db_session
    )
    
    assert result.status == "saved"
    assert result.editing_state == new_editing_state
    assert result.updated_at is not None
    
    # Verify in database
    db_session.refresh(sample_editing_session)
    assert sample_editing_session.status == "saved"
    assert sample_editing_session.editing_state == new_editing_state


def test_save_editing_session_without_new_state(db_session, sample_editing_session):
    """Test saving editing session without providing new state (uses existing state)."""
    original_state = sample_editing_session.editing_state.copy()
    
    result = save_editing_session(
        editing_session=sample_editing_session,
        editing_state=None,
        db=db_session
    )
    
    assert result.status == "saved"
    assert result.editing_state == original_state
    assert result.updated_at is not None
    
    # Verify in database
    db_session.refresh(sample_editing_session)
    assert sample_editing_session.status == "saved"
    assert sample_editing_session.editing_state == original_state


def test_save_editing_session_invalid_state_missing_clips(db_session, sample_editing_session):
    """Test saving with invalid editing state (missing clips key)."""
    invalid_state = {
        "version": 1,
        # Missing "clips" key
    }
    
    with pytest.raises(ValueError, match="Invalid editing_state structure"):
        save_editing_session(
            editing_session=sample_editing_session,
            editing_state=invalid_state,
            db=db_session
        )


def test_save_editing_session_invalid_state_not_dict(db_session, sample_editing_session):
    """Test saving with invalid editing state (not a dictionary)."""
    invalid_state = "not a dict"
    
    with pytest.raises(ValueError, match="Invalid editing_state structure"):
        save_editing_session(
            editing_session=sample_editing_session,
            editing_state=invalid_state,
            db=db_session
        )


def test_save_editing_session_updates_timestamp(db_session, sample_editing_session):
    """Test that saving updates the updated_at timestamp."""
    original_updated_at = sample_editing_session.updated_at
    
    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(0.1)
    
    result = save_editing_session(
        editing_session=sample_editing_session,
        editing_state=None,
        db=db_session
    )
    
    assert result.updated_at > original_updated_at


def test_save_editing_session_preserves_original_video_path(db_session, sample_editing_session):
    """Test that saving preserves the original_video_path."""
    original_path = sample_editing_session.original_video_path
    
    result = save_editing_session(
        editing_session=sample_editing_session,
        editing_state=None,
        db=db_session
    )
    
    assert result.original_video_path == original_path
    
    # Verify in database
    db_session.refresh(sample_editing_session)
    assert sample_editing_session.original_video_path == original_path

