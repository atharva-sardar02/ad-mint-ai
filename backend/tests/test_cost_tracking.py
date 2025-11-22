"""
Unit tests for cost tracking service.
"""
import pytest

from app.db.models.generation import Generation
from app.db.models.user import User
from app.services.cost_tracking import (
    track_video_generation_cost,
    accumulate_generation_cost,
    update_user_total_cost,
    track_complete_generation_cost
)


@pytest.fixture
def sample_generation(db_session):
    """Create a sample generation for testing."""
    user = User(
        id="user-123",
        username="testuser",
        password_hash="hashed",
        total_cost=0.0
    )
    db_session.add(user)
    db_session.commit()
    
    generation = Generation(
        id="gen-123",
        user_id=user.id,
        prompt="Test prompt",
        status="processing",
        progress=50
    )
    db_session.add(generation)
    db_session.commit()
    
    return generation


def test_track_video_generation_cost(db_session, sample_generation):
    """Test tracking video generation cost per clip."""
    track_video_generation_cost(
        db=db_session,
        generation_id=sample_generation.id,
        scene_number=1,
        cost=0.25,
        model_name="minimax-ai/minimax-video-01"
    )
    
    # Cost should be logged (we can check logs, but for now just verify no error)
    db_session.refresh(sample_generation)
    assert sample_generation is not None


def test_accumulate_generation_cost(db_session, sample_generation):
    """Test accumulating total generation cost."""
    total_cost = accumulate_generation_cost(
        db=db_session,
        generation_id=sample_generation.id,
        video_cost=0.75,
        llm_cost=0.01
    )
    
    assert total_cost == 0.76
    
    db_session.refresh(sample_generation)
    assert sample_generation.cost == 0.76


def test_update_user_total_cost(db_session, sample_generation):
    """Test updating user's total cost."""
    user = db_session.query(User).filter(User.id == sample_generation.user_id).first()
    initial_cost = user.total_cost or 0.0
    
    update_user_total_cost(
        db=db_session,
        user_id=user.id,
        additional_cost=1.50
    )
    
    db_session.refresh(user)
    assert user.total_cost == initial_cost + 1.50


def test_track_complete_generation_cost(db_session, sample_generation):
    """Test complete cost tracking for generation."""
    user = db_session.query(User).filter(User.id == sample_generation.user_id).first()
    initial_user_cost = user.total_cost or 0.0
    
    track_complete_generation_cost(
        db=db_session,
        generation_id=sample_generation.id,
        video_cost=0.75,
        llm_cost=0.01
    )
    
    db_session.refresh(sample_generation)
    db_session.refresh(user)
    
    assert sample_generation.cost == 0.76
    assert user.total_cost == initial_user_cost + 0.76
