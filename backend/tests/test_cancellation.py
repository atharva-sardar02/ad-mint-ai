"""
Unit tests for cancellation service.
"""
import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from app.db.models.generation import Generation
from app.services.cancellation import (
    request_cancellation,
    check_cancellation,
    handle_cancellation,
    cleanup_generation_temp_files,
)


def test_request_cancellation(db_session: Session, sample_generation: Generation):
    """Test requesting cancellation for a processing generation."""
    sample_generation.status = "processing"
    db_session.commit()
    
    result = request_cancellation(db_session, sample_generation.id)
    
    assert result is True
    db_session.refresh(sample_generation)
    assert sample_generation.cancellation_requested is True


def test_request_cancellation_completed_generation(db_session: Session, sample_generation: Generation):
    """Test that cancellation cannot be requested for completed generation."""
    sample_generation.status = "completed"
    db_session.commit()
    
    result = request_cancellation(db_session, sample_generation.id)
    
    assert result is False
    db_session.refresh(sample_generation)
    assert sample_generation.cancellation_requested is False


def test_check_cancellation(db_session: Session, sample_generation: Generation):
    """Test checking cancellation flag."""
    sample_generation.cancellation_requested = True
    db_session.commit()
    
    result = check_cancellation(db_session, sample_generation.id)
    assert result is True
    
    sample_generation.cancellation_requested = False
    db_session.commit()
    
    result = check_cancellation(db_session, sample_generation.id)
    assert result is False


def test_handle_cancellation(db_session: Session, sample_generation: Generation):
    """Test handling cancellation."""
    sample_generation.status = "processing"
    sample_generation.cancellation_requested = True
    db_session.commit()
    
    handle_cancellation(db_session, sample_generation.id, cleanup_temp_files=False)
    
    db_session.refresh(sample_generation)
    assert sample_generation.status == "failed"
    assert sample_generation.error_message == "Cancelled by user"


def test_cleanup_generation_temp_files(tmp_path, monkeypatch):
    """Test cleanup of temporary files."""
    # Mock the temp directory
    temp_dir = tmp_path / "output" / "temp"
    temp_dir.mkdir(parents=True)
    
    generation_id = "test-gen-123"
    gen_dir = temp_dir / generation_id
    gen_dir.mkdir()
    (gen_dir / "test.txt").write_text("test")
    
    # Mock Path to use our temp directory
    import app.services.cancellation as cancellation_module
    original_path = cancellation_module.Path
    
    def mock_path(path_str):
        if path_str == "output/temp":
            return temp_dir
        return original_path(path_str)
    
    monkeypatch.setattr(cancellation_module, "Path", mock_path)
    
    cleanup_generation_temp_files(generation_id)
    
    # Directory should be removed
    assert not gen_dir.exists()

