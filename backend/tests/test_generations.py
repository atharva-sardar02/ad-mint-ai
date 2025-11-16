"""
Integration tests for generations/gallery routes.
"""
import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.generation import Generation
from app.db.models.user import User
from app.main import app

client = TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user for authentication."""
    from app.core.security import hash_password
    
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
    """Create a second test user for ownership testing."""
    from app.core.security import hash_password
    
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
def auth_token(test_user):
    """Get JWT token for test user."""
    from app.core.security import create_access_token
    
    # Create token directly without using login endpoint
    token_data = {
        "sub": test_user.id,
        "username": test_user.username,
    }
    token = create_access_token(data=token_data)
    return token


@pytest.fixture
def test_generations(db_session: Session, test_user, test_user2):
    """Create test generations for both users."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create generations for test_user (5 total)
    generations_user1 = []
    for i in range(5):
        gen = Generation(
            user_id=test_user.id,
            prompt=f"Test prompt {i}",
            status="completed" if i < 3 else "processing",
            video_url=f"https://example.com/video{i}.mp4",
            thumbnail_url=f"https://example.com/thumb{i}.jpg",
            duration=15,
            cost=1.5 + i * 0.5,
            created_at=datetime.utcnow() - timedelta(days=5-i),
            completed_at=datetime.utcnow() - timedelta(days=5-i) if i < 3 else None,
        )
        db_session.add(gen)
        generations_user1.append(gen)
    
    # Create generations for test_user2 (2 total)
    generations_user2 = []
    for i in range(2):
        gen = Generation(
            user_id=test_user2.id,
            prompt=f"User2 prompt {i}",
            status="completed",
            video_url=f"https://example.com/user2_video{i}.mp4",
            thumbnail_url=f"https://example.com/user2_thumb{i}.jpg",
            duration=15,
            cost=2.0,
            created_at=datetime.utcnow() - timedelta(days=i),
        )
        db_session.add(gen)
        generations_user2.append(gen)
    
    db_session.commit()
    for gen in generations_user1 + generations_user2:
        db_session.refresh(gen)
    
    app.dependency_overrides.clear()
    
    return {
        "user1": generations_user1,
        "user2": generations_user2,
    }


def test_get_generations_success(db_session: Session, test_user, auth_token, test_generations):
    """Test GET /api/generations returns paginated list (AC-4.1.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.get(
        "/api/generations?limit=20&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify response structure
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "generations" in data
    assert isinstance(data["generations"], list)
    
    # Verify pagination fields
    assert data["total"] == 5  # Only test_user's generations
    assert data["limit"] == 20
    assert data["offset"] == 0
    
    # Verify generations array
    assert len(data["generations"]) == 5
    
    # Verify generation item structure
    gen = data["generations"][0]
    assert "id" in gen
    assert "prompt" in gen
    assert "status" in gen
    assert "video_url" in gen
    assert "thumbnail_url" in gen
    assert "duration" in gen
    assert "cost" in gen
    assert "created_at" in gen
    assert "completed_at" in gen
    
    app.dependency_overrides.clear()


def test_get_generations_only_user_videos(db_session: Session, test_user, test_user2, auth_token, test_generations):
    """Test GET /api/generations only returns videos for authenticated user (AC-4.1.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.get(
        "/api/generations?limit=20&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should only return test_user's generations (5), not test_user2's (2)
    assert data["total"] == 5
    assert len(data["generations"]) == 5
    
    # Verify all generations belong to test_user
    for gen in data["generations"]:
        # Find the generation in database to verify user_id
        db_gen = db_session.query(Generation).filter(Generation.id == gen["id"]).first()
        assert db_gen.user_id == test_user.id
    
    app.dependency_overrides.clear()


def test_get_generations_sorted_newest_first(db_session: Session, test_user, auth_token, test_generations):
    """Test GET /api/generations sorts results by created_at DESC (AC-4.1.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.get(
        "/api/generations?limit=20&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify generations are sorted by created_at DESC (newest first)
    generations = data["generations"]
    for i in range(len(generations) - 1):
        current_date = datetime.fromisoformat(generations[i]["created_at"].replace("Z", "+00:00"))
        next_date = datetime.fromisoformat(generations[i + 1]["created_at"].replace("Z", "+00:00"))
        assert current_date >= next_date
    
    app.dependency_overrides.clear()


def test_get_generations_unauthorized():
    """Test GET /api/generations returns 403 if JWT token is missing (AC-4.1.1)."""
    response = client.get("/api/generations?limit=20&offset=0")
    
    # FastAPI returns 403 Forbidden when no auth header is provided
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_get_generations_invalid_token():
    """Test GET /api/generations returns 401 if JWT token is invalid (AC-4.1.1)."""
    response = client.get(
        "/api/generations?limit=20&offset=0",
        headers={"Authorization": "Bearer invalid_token"},
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_generations_pagination(db_session: Session, test_user, auth_token, test_generations):
    """Test GET /api/generations pagination works correctly (AC-4.1.3)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # First page
    response1 = client.get(
        "/api/generations?limit=2&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response1.status_code == status.HTTP_200_OK
    data1 = response1.json()
    assert data1["total"] == 5
    assert len(data1["generations"]) == 2
    
    # Second page
    response2 = client.get(
        "/api/generations?limit=2&offset=2",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response2.status_code == status.HTTP_200_OK
    data2 = response2.json()
    assert data2["total"] == 5
    assert len(data2["generations"]) == 2
    
    # Verify different results
    assert data1["generations"][0]["id"] != data2["generations"][0]["id"]
    
    app.dependency_overrides.clear()


def test_get_generations_status_filter(db_session: Session, test_user, auth_token, test_generations):
    """Test GET /api/generations with status filter returns only matching videos (AC-4.1.4)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Filter by completed
    response = client.get(
        "/api/generations?limit=20&offset=0&status=completed",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should only return completed generations (3 out of 5)
    assert data["total"] == 3
    assert len(data["generations"]) == 3
    
    # Verify all are completed
    for gen in data["generations"]:
        assert gen["status"] == "completed"
    
    app.dependency_overrides.clear()


def test_get_generations_search_filter(db_session: Session, test_user, auth_token, test_generations):
    """Test GET /api/generations with q parameter performs case-insensitive search (AC-4.1.4)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Search for "Test prompt"
    response = client.get(
        "/api/generations?limit=20&offset=0&q=Test prompt",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should return all 5 generations (all have "Test prompt" in prompt)
    assert data["total"] == 5
    
    # Case-insensitive search
    response2 = client.get(
        "/api/generations?limit=20&offset=0&q=test PROMPT",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response2.status_code == status.HTTP_200_OK
    data2 = response2.json()
    assert data2["total"] == 5
    
    app.dependency_overrides.clear()


def test_get_generations_limit_validation(db_session: Session, test_user, auth_token):
    """Test GET /api/generations validates limit parameter (AC-4.1.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Limit too high
    response = client.get(
        "/api/generations?limit=101&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Limit too low
    response2 = client.get(
        "/api/generations?limit=0&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    app.dependency_overrides.clear()


def test_get_generations_offset_validation(db_session: Session, test_user, auth_token):
    """Test GET /api/generations validates offset parameter (AC-4.1.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Negative offset
    response = client.get(
        "/api/generations?limit=20&offset=-1",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    app.dependency_overrides.clear()


def test_delete_generation_success(db_session: Session, test_user, auth_token):
    """Test DELETE /api/generations/{id} successfully deletes generation (AC-4.3.1)."""
    import os
    import tempfile
    from pathlib import Path
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    # Override dependencies to use test session and test user
    app.dependency_overrides[get_db] = lambda: db_session
    # Override get_current_user to return test_user directly (bypassing database query)
    # Note: FastAPI dependency override - we need to match the callable, not the signature
    # The override will be called by FastAPI's dependency injection system
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create a temporary video file
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, "test_video.mp4")
    thumbnail_path = os.path.join(temp_dir, "test_thumbnail.jpg")
    
    # Create dummy files
    Path(video_path).touch()
    Path(thumbnail_path).touch()
    
    # Create a generation with file paths
    generation = Generation(
        user_id=test_user.id,
        prompt="Test video to delete",
        status="completed",
        video_path=video_path,
        video_url=f"https://example.com/video.mp4",
        thumbnail_url=thumbnail_path,
        duration=15,
        cost=1.5,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    generation_id = generation.id
    
    # Verify files exist
    assert os.path.exists(video_path)
    assert os.path.exists(thumbnail_path)
    
    # Delete the generation
    response = client.delete(
        f"/api/generations/{generation_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Video deleted successfully"
    assert data["generation_id"] == generation_id
    
    # Verify database record is deleted
    deleted_gen = db_session.query(Generation).filter(Generation.id == generation_id).first()
    assert deleted_gen is None
    
    # Verify files are deleted
    assert not os.path.exists(video_path)
    assert not os.path.exists(thumbnail_path)
    
    app.dependency_overrides.clear()
    
    # Clean up temp directory
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_delete_generation_ownership_verification(db_session: Session, test_user, test_user2, auth_token):
    """Test DELETE /api/generations/{id} returns 403 for non-owner (AC-4.3.5)."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    # Override dependencies to use test session and test_user (who doesn't own the generation)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create a generation owned by test_user2
    generation = Generation(
        user_id=test_user2.id,
        prompt="User2's video",
        status="completed",
        video_url="https://example.com/video.mp4",
        thumbnail_url="https://example.com/thumb.jpg",
        duration=15,
        cost=1.5,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    generation_id = generation.id
    
    # Try to delete as test_user (doesn't own it)
    response = client.delete(
        f"/api/generations/{generation_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error"]["code"] == "FORBIDDEN"
    assert "permission" in data["detail"]["error"]["message"].lower()
    
    # Verify generation still exists
    existing_gen = db_session.query(Generation).filter(Generation.id == generation_id).first()
    assert existing_gen is not None
    assert existing_gen.id == generation_id
    
    app.dependency_overrides.clear()


def test_delete_generation_not_found(db_session: Session, test_user, auth_token):
    """Test DELETE /api/generations/{id} returns 404 for non-existent generation (AC-4.3.1)."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    from uuid import uuid4
    
    # Override dependencies to use test session and test user
    app.dependency_overrides[get_db] = lambda: db_session
    # Override get_current_user to return test_user directly (bypassing database query)
    # Note: FastAPI dependency override - we need to match the callable, not the signature
    # The override will be called by FastAPI's dependency injection system
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    fake_id = str(uuid4())
    
    response = client.delete(
        f"/api/generations/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error"]["code"] == "GENERATION_NOT_FOUND"
    
    app.dependency_overrides.clear()


def test_delete_generation_unauthorized(db_session: Session, test_user):
    """Test DELETE /api/generations/{id} returns 403 without token (AC-4.3.1)."""
    from app.db.session import get_db
    
    # Override get_db to use test session (don't override get_current_user - we want 403 for missing token)
    app.dependency_overrides[get_db] = lambda: db_session
    
    generation = Generation(
        user_id=test_user.id,
        prompt="Test video",
        status="completed",
        video_url="https://example.com/video.mp4",
        thumbnail_url="https://example.com/thumb.jpg",
        duration=15,
        cost=1.5,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    generation_id = generation.id
    
    # Try to delete without token - HTTPBearer returns 403 for missing credentials
    response = client.delete(f"/api/generations/{generation_id}")
    
    # HTTPBearer returns 403 Forbidden when Authorization header is missing
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    app.dependency_overrides.clear()


def test_delete_generation_file_not_found_graceful(db_session: Session, test_user, auth_token):
    """Test DELETE /api/generations/{id} handles missing files gracefully (AC-4.3.1)."""
    import os
    from app.db.session import get_db
    from app.api.deps import get_current_user
    
    # Override dependencies to use test session and test user
    app.dependency_overrides[get_db] = lambda: db_session
    # Override get_current_user to return test_user directly (bypassing database query)
    # Note: FastAPI dependency override - we need to match the callable, not the signature
    # The override will be called by FastAPI's dependency injection system
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Create a generation with file paths that don't exist
    generation = Generation(
        user_id=test_user.id,
        prompt="Test video with missing files",
        status="completed",
        video_path="/nonexistent/path/video.mp4",
        video_url="https://example.com/video.mp4",
        thumbnail_url="/nonexistent/path/thumb.jpg",
        duration=15,
        cost=1.5,
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    
    generation_id = generation.id
    
    # Verify files don't exist
    assert not os.path.exists(generation.video_path)
    assert not os.path.exists(generation.thumbnail_url)
    
    # Delete should succeed even if files are missing
    response = client.delete(
        f"/api/generations/{generation_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Video deleted successfully"
    
    # Verify database record is deleted
    deleted_gen = db_session.query(Generation).filter(Generation.id == generation_id).first()
    assert deleted_gen is None
    
    app.dependency_overrides.clear()

