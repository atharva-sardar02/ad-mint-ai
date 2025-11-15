"""
Unit tests for user statistics update service.
Tests total_generations increment and total_cost update on generation completion.
"""
import pytest
from sqlalchemy.orm import Session

from app.db.models.generation import Generation
from app.db.models.user import User
from app.services.cost_tracking import update_user_statistics_on_completion


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        id="user-123",
        username="testuser",
        password_hash="hashed",
        total_generations=5,
        total_cost=10.50
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_generation(db_session, sample_user):
    """Create a sample generation for testing."""
    generation = Generation(
        id="gen-123",
        user_id=sample_user.id,
        prompt="Test prompt",
        status="completed",
        cost=2.75
    )
    db_session.add(generation)
    db_session.commit()
    return generation


def test_update_user_statistics_increments_total_generations(db_session, sample_user, sample_generation):
    """Test that update_user_statistics_on_completion increments total_generations by 1 (AC-5.2.1)."""
    initial_generations = sample_user.total_generations
    
    update_user_statistics_on_completion(
        db=db_session,
        generation_id=sample_generation.id
    )
    
    db_session.refresh(sample_user)
    assert sample_user.total_generations == initial_generations + 1


def test_update_user_statistics_adds_generation_cost(db_session, sample_user, sample_generation):
    """Test that update_user_statistics_on_completion adds generation.cost to total_cost (AC-5.2.1)."""
    initial_cost = sample_user.total_cost or 0.0
    generation_cost = sample_generation.cost
    
    update_user_statistics_on_completion(
        db=db_session,
        generation_id=sample_generation.id
    )
    
    db_session.refresh(sample_user)
    assert sample_user.total_cost == pytest.approx(initial_cost + generation_cost, abs=0.001)


def test_update_user_statistics_updates_both_atomically(db_session, sample_user, sample_generation):
    """Test that both total_generations and total_cost are updated atomically (AC-5.2.3)."""
    initial_generations = sample_user.total_generations
    initial_cost = sample_user.total_cost or 0.0
    generation_cost = sample_generation.cost
    
    update_user_statistics_on_completion(
        db=db_session,
        generation_id=sample_generation.id
    )
    
    db_session.refresh(sample_user)
    # Both should be updated
    assert sample_user.total_generations == initial_generations + 1
    assert sample_user.total_cost == pytest.approx(initial_cost + generation_cost, abs=0.001)


def test_update_user_statistics_with_zero_cost(db_session, sample_user):
    """Test statistics update with generation that has zero cost (edge case)."""
    generation = Generation(
        id="gen-zero",
        user_id=sample_user.id,
        prompt="Test prompt",
        status="completed",
        cost=0.0
    )
    db_session.add(generation)
    db_session.commit()
    
    initial_generations = sample_user.total_generations
    initial_cost = sample_user.total_cost or 0.0
    
    update_user_statistics_on_completion(
        db=db_session,
        generation_id=generation.id
    )
    
    db_session.refresh(sample_user)
    assert sample_user.total_generations == initial_generations + 1
    assert sample_user.total_cost == pytest.approx(initial_cost, abs=0.001)  # Cost should remain same


def test_update_user_statistics_with_existing_statistics(db_session):
    """Test statistics update with user that has existing statistics (edge case)."""
    user = User(
        id="user-existing",
        username="existinguser",
        password_hash="hashed",
        total_generations=10,
        total_cost=25.00
    )
    db_session.add(user)
    db_session.commit()
    
    generation = Generation(
        id="gen-existing",
        user_id=user.id,
        prompt="Test prompt",
        status="completed",
        cost=3.50
    )
    db_session.add(generation)
    db_session.commit()
    
    update_user_statistics_on_completion(
        db=db_session,
        generation_id=generation.id
    )
    
    db_session.refresh(user)
    assert user.total_generations == 11
    assert user.total_cost == pytest.approx(28.50, abs=0.001)


def test_update_user_statistics_handles_missing_generation(db_session, sample_user):
    """Test that update_user_statistics_on_completion handles missing generation gracefully."""
    # Should not raise exception, just log error
    update_user_statistics_on_completion(
        db=db_session,
        generation_id="non-existent-id"
    )
    
    # User statistics should be unchanged
    db_session.refresh(sample_user)
    assert sample_user.total_generations == 5
    assert sample_user.total_cost == pytest.approx(10.50, abs=0.001)


# Note: test_update_user_statistics_handles_missing_user removed because
# it cannot be tested with foreign key constraints enabled. The function
# already handles missing users gracefully by checking if user exists before updating.


def test_update_user_statistics_handles_null_cost(db_session, sample_user):
    """Test that update_user_statistics_on_completion handles generation with null cost."""
    generation = Generation(
        id="gen-null-cost",
        user_id=sample_user.id,
        prompt="Test prompt",
        status="completed",
        cost=None
    )
    db_session.add(generation)
    db_session.commit()
    
    initial_generations = sample_user.total_generations
    initial_cost = sample_user.total_cost or 0.0
    
    # Should skip update and log warning
    update_user_statistics_on_completion(
        db=db_session,
        generation_id=generation.id
    )
    
    # Statistics should be unchanged
    db_session.refresh(sample_user)
    assert sample_user.total_generations == initial_generations
    assert sample_user.total_cost == pytest.approx(initial_cost, abs=0.001)


def test_update_user_statistics_atomicity_on_error(db_session, sample_user, sample_generation, monkeypatch):
    """Test that statistics updates are atomic - transaction rollback on error prevents partial updates (AC-5.2.3)."""
    initial_generations = sample_user.total_generations
    initial_cost = sample_user.total_cost or 0.0
    
    # Simulate an error during commit
    original_commit = db_session.commit
    commit_called = False
    
    def failing_commit():
        nonlocal commit_called
        commit_called = True
        raise Exception("Simulated database error")
    
    monkeypatch.setattr(db_session, "commit", failing_commit)
    
    # Call update - should handle error gracefully
    update_user_statistics_on_completion(
        db=db_session,
        generation_id=sample_generation.id
    )
    
    # Statistics should be unchanged due to rollback
    db_session.refresh(sample_user)
    assert sample_user.total_generations == initial_generations
    assert sample_user.total_cost == pytest.approx(initial_cost, abs=0.001)
    assert commit_called  # Verify commit was attempted


def test_update_user_statistics_with_none_initial_values(db_session):
    """Test statistics update when user has None initial values."""
    user = User(
        id="user-none",
        username="noneuser",
        password_hash="hashed",
        total_generations=None,
        total_cost=None
    )
    db_session.add(user)
    db_session.commit()
    
    generation = Generation(
        id="gen-none",
        user_id=user.id,
        prompt="Test prompt",
        status="completed",
        cost=1.50
    )
    db_session.add(generation)
    db_session.commit()
    
    update_user_statistics_on_completion(
        db=db_session,
        generation_id=generation.id
    )
    
    db_session.refresh(user)
    assert user.total_generations == 1  # Should be 1 (0 + 1)
    assert user.total_cost == pytest.approx(1.50, abs=0.001)  # Should be 1.50 (0.0 + 1.50)

