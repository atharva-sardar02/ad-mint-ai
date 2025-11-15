"""
Unit tests for progress tracking service.
"""
import pytest
from sqlalchemy.orm import Session

from app.db.models.generation import Generation
from app.services.pipeline.progress_tracking import (
    update_generation_progress,
    update_generation_status,
    update_generation_step,
)


def test_update_generation_progress(db_session: Session, sample_generation: Generation):
    """Test updating generation progress with all parameters."""
    update_generation_progress(
        db=db_session,
        generation_id=sample_generation.id,
        progress=50,
        current_step="Processing",
        status="processing"
    )
    
    db_session.refresh(sample_generation)
    assert sample_generation.progress == 50
    assert sample_generation.current_step == "Processing"
    assert sample_generation.status == "processing"


def test_update_generation_progress_clamps_invalid_values(db_session: Session, sample_generation: Generation):
    """Test that invalid progress values are clamped to 0-100."""
    update_generation_progress(
        db=db_session,
        generation_id=sample_generation.id,
        progress=150,  # Invalid value
        current_step="Test"
    )
    
    db_session.refresh(sample_generation)
    assert sample_generation.progress == 100  # Clamped
    
    update_generation_progress(
        db=db_session,
        generation_id=sample_generation.id,
        progress=-10,  # Invalid value
        current_step="Test"
    )
    
    db_session.refresh(sample_generation)
    assert sample_generation.progress == 0  # Clamped


def test_update_generation_status(db_session: Session, sample_generation: Generation):
    """Test updating generation status."""
    update_generation_status(
        db=db_session,
        generation_id=sample_generation.id,
        status="completed",
        error_message=None
    )
    
    db_session.refresh(sample_generation)
    assert sample_generation.status == "completed"


def test_update_generation_status_with_error(db_session: Session, sample_generation: Generation):
    """Test updating generation status with error message."""
    update_generation_status(
        db=db_session,
        generation_id=sample_generation.id,
        status="failed",
        error_message="Test error"
    )
    
    db_session.refresh(sample_generation)
    assert sample_generation.status == "failed"
    assert sample_generation.error_message == "Test error"


def test_update_generation_step(db_session: Session, sample_generation: Generation):
    """Test updating only the current step."""
    update_generation_step(
        db=db_session,
        generation_id=sample_generation.id,
        current_step="New step"
    )
    
    db_session.refresh(sample_generation)
    assert sample_generation.current_step == "New step"


def test_update_generation_progress_nonexistent(db_session: Session):
    """Test that updating progress for nonexistent generation doesn't crash."""
    update_generation_progress(
        db=db_session,
        generation_id="nonexistent-id",
        progress=50,
        current_step="Test"
    )
    # Should not raise exception, just log error

