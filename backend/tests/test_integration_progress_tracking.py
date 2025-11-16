"""
Integration tests for progress tracking, status endpoint, cancel endpoint, and cancellation flow.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models.user import User
from app.db.models.generation import Generation
from app.main import app
from app.core.security import hash_password

client = TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        password_hash=hash_password("password123"),
        email="test@example.com",
        total_generations=0,
        total_cost=0.0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session: Session):
    """Create a second test user for authorization testing."""
    user = User(
        username="testuser2",
        password_hash=hash_password("password123"),
        email="test2@example.com",
        total_generations=0,
        total_cost=0.0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user, db_session: Session):
    """Get auth token for test user."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    
    token = response.json()["access_token"]
    return token


@pytest.fixture
def sample_generation(test_user, db_session: Session):
    """Create a sample generation."""
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="processing",
        progress=50,
        current_step="Generating video clips",
        duration=15,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    return generation


def test_status_endpoint_pending_generation(auth_token, test_user, db_session: Session):
    """Integration test: Status endpoint with pending generation state."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create pending generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="pending",
        progress=0,
        current_step="Initializing",
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    # Get status
    response = client.get(
        f"/api/status/{generation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["generation_id"] == generation.id
    assert data["status"] == "pending"
    assert data["progress"] == 0
    assert data["current_step"] == "Initializing"
    assert data["video_url"] is None
    assert data["cost"] is None
    assert data["error"] is None
    
    app.dependency_overrides.clear()


def test_status_endpoint_processing_generation(auth_token, test_user, db_session: Session):
    """Integration test: Status endpoint with processing generation state."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create processing generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="processing",
        progress=45,
        current_step="Generating video clip 2 of 3",
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    # Get status
    response = client.get(
        f"/api/status/{generation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "processing"
    assert data["progress"] == 45
    assert data["current_step"] == "Generating video clip 2 of 3"
    
    app.dependency_overrides.clear()


def test_status_endpoint_completed_generation(auth_token, test_user, db_session: Session):
    """Integration test: Status endpoint with completed generation state."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create completed generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="completed",
        progress=100,
        current_step="Complete",
        video_url="/output/video_123.mp4",
        cost=0.15,
        completed_at=datetime.utcnow(),
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    # Get status
    response = client.get(
        f"/api/status/{generation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "completed"
    assert data["progress"] == 100
    assert data["current_step"] == "Complete"
    assert data["video_url"] == "/output/video_123.mp4"
    assert data["cost"] == 0.15
    
    app.dependency_overrides.clear()


def test_status_endpoint_failed_generation(auth_token, test_user, db_session: Session):
    """Integration test: Status endpoint with failed generation state."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create failed generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="failed",
        progress=30,
        current_step="Generating video clips",
        error_message="Video generation failed: API error",
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    # Get status
    response = client.get(
        f"/api/status/{generation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "failed"
    assert data["error"] == "Video generation failed: API error"
    
    app.dependency_overrides.clear()


def test_status_endpoint_not_found(auth_token, test_user, db_session: Session):
    """Integration test: Status endpoint returns 404 for nonexistent generation."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    response = client.get(
        "/api/status/nonexistent-id",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    app.dependency_overrides.clear()


def test_status_endpoint_unauthorized(auth_token, test_user, test_user2, db_session: Session):
    """Integration test: Status endpoint returns 403 for other user's generation."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create generation for user2
    generation = Generation(
        user_id=test_user2.id,
        prompt="Test prompt",
        status="processing",
        progress=50,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    # Try to access as user1
    response = client.get(
        f"/api/status/{generation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    app.dependency_overrides.clear()


def test_cancel_endpoint_processing_generation(auth_token, test_user, db_session: Session):
    """Integration test: Cancel endpoint with processing generation."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create processing generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="processing",
        progress=50,
        current_step="Generating video clips",
        cancellation_requested=False,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    # Cancel generation
    response = client.post(
        f"/api/generations/{generation.id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "failed"
    assert data["error"] == "Cancelled by user"
    
    # Verify in database
    db_session.refresh(generation)
    assert generation.cancellation_requested is True
    assert generation.status == "failed"
    assert generation.error_message == "Cancelled by user"
    
    app.dependency_overrides.clear()


def test_cancel_endpoint_pending_generation(auth_token, test_user, db_session: Session):
    """Integration test: Cancel endpoint with pending generation."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create pending generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="pending",
        progress=0,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    # Cancel generation
    response = client.post(
        f"/api/generations/{generation.id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "failed"
    
    app.dependency_overrides.clear()


def test_cancel_endpoint_unauthorized(auth_token, test_user, test_user2, db_session: Session):
    """Integration test: Cancel endpoint returns 403 for other user's generation."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create generation for user2
    generation = Generation(
        user_id=test_user2.id,
        prompt="Test prompt",
        status="processing",
        progress=50,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    # Try to cancel as user1
    response = client.post(
        f"/api/generations/{generation.id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    app.dependency_overrides.clear()


def test_progress_updates_throughout_pipeline(test_user, db_session: Session):
    """Integration test: Progress updates throughout pipeline stages."""
    from app.services.pipeline.progress_tracking import update_generation_progress
    
    # Create generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="pending",
        progress=0,
    )
    db_session.add(generation)
    db_session.commit()
    
    # Simulate progress updates at each stage
    stages = [
        (10, "LLM Enhancement", "processing"),
        (20, "Scene Planning", None),
        (30, "Generating video clip 1 of 3", None),
        (50, "Generating video clip 2 of 3", None),
        (70, "Generating video clip 3 of 3", None),
        (80, "Stitching video clips", None),
        (90, "Adding audio layer", None),
        (100, "Complete", "completed"),
    ]
    
    for progress, step, status_val in stages:
        update_generation_progress(
            db=db_session,
            generation_id=generation.id,
            progress=progress,
            current_step=step,
            status=status_val
        )
        
        db_session.refresh(generation)
        assert generation.progress == progress
        assert generation.current_step == step
        if status_val:
            assert generation.status == status_val


def test_cost_calculation_and_user_total_cost_update(test_user, db_session: Session):
    """Integration test: Cost calculation and user.total_cost update atomically."""
    from app.services.cost_tracking import track_complete_generation_cost
    
    # Create generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="processing",
    )
    db_session.add(generation)
    db_session.commit()
    
    # Initial user cost
    initial_cost = test_user.total_cost or 0.0
    
    # Track complete generation cost
    video_cost = 0.12
    llm_cost = 0.01
    track_complete_generation_cost(
        db=db_session,
        generation_id=generation.id,
        video_cost=video_cost,
        llm_cost=llm_cost
    )
    
    # Verify generation cost
    db_session.refresh(generation)
    assert generation.cost == pytest.approx(video_cost + llm_cost, abs=0.001)
    
    # Verify user total_cost updated atomically
    db_session.refresh(test_user)
    assert test_user.total_cost == pytest.approx(initial_cost + video_cost + llm_cost, abs=0.001)


def test_cancellation_flow_request_stop_cleanup(test_user, db_session: Session, tmp_path, monkeypatch):
    """Integration test: Complete cancellation flow (request → stop → cleanup)."""
    from app.services.cancellation import request_cancellation, handle_cancellation, cleanup_generation_temp_files
    from pathlib import Path
    
    # Create processing generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="processing",
        progress=50,
        cancellation_requested=False,
    )
    db_session.add(generation)
    db_session.commit()
    
    # Step 1: Request cancellation
    result = request_cancellation(db_session, generation.id)
    assert result is True
    
    db_session.refresh(generation)
    assert generation.cancellation_requested is True
    
    # Step 2: Handle cancellation (updates status, cleanup)
    # Mock temp directory
    temp_dir = tmp_path / "output" / "temp"
    temp_dir.mkdir(parents=True)
    gen_dir = temp_dir / generation.id
    gen_dir.mkdir()
    (gen_dir / "test.txt").write_text("test")
    
    # Mock Path for cleanup
    import app.services.cancellation as cancellation_module
    original_path = cancellation_module.Path
    
    def mock_path(path_str):
        if path_str == "output/temp":
            return temp_dir
        return original_path(path_str)
    
    monkeypatch.setattr(cancellation_module, "Path", mock_path)
    
    handle_cancellation(db_session, generation.id, cleanup_temp_files=True)
    
    # Step 3: Verify status updated
    db_session.refresh(generation)
    assert generation.status == "failed"
    assert generation.error_message == "Cancelled by user"
    
    # Step 4: Verify cleanup (directory should be removed)
    assert not gen_dir.exists()

