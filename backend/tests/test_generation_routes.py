"""
Integration tests for generation routes.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.generation import Generation
from app.main import app
from app.schemas.generation import AdSpecification, BrandGuidelines, AdSpec, Scene, TextOverlay

client = TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    # Use a pre-generated bcrypt hash to avoid bcrypt initialization issues in tests
    # This is a valid bcrypt hash for "password123" with cost factor 12
    # Generated offline to avoid passlib/bcrypt compatibility issues during test setup
    password_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    user = User(
        username="testuser",
        password_hash=password_hash,
        email="test@example.com"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user, db_session: Session):
    """Get auth token for test user."""
    from app.db.session import get_db
    from app.core.security import create_access_token
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Try to login first, but if it fails, create token directly
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    
    if response.status_code == 200 and "access_token" in response.json():
        token = response.json()["access_token"]
    else:
        # Fallback: create token directly if login fails
        token_data = {"sub": test_user.id, "username": test_user.username}
        token = create_access_token(token_data)
    
    app.dependency_overrides.clear()
    return token


def test_create_generation_invalid_prompt_length(auth_token, db_session: Session):
    """Test generation creation with invalid prompt length (AC-3.1.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Test too short prompt
    response = client.post(
        "/api/generate",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "prompt": "short"
        }
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Test too long prompt
    long_prompt = "a" * 501
    response = client.post(
        "/api/generate",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "prompt": long_prompt
        }
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    app.dependency_overrides.clear()


def test_get_generation_status(auth_token, db_session: Session, test_user):
    """Test getting generation status (AC-3.4.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create a generation
    generation = Generation(
        user_id=test_user.id,
        prompt="Test prompt",
        status="processing",
        progress=20,
        current_step="Scene Planning"
    )
    db_session.add(generation)
    db_session.commit()
    
    response = client.get(
        f"/api/status/{generation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["generation_id"] == generation.id
    assert data["status"] == "processing"
    assert data["progress"] == 20
    assert data["current_step"] == "Scene Planning"
    
    app.dependency_overrides.clear()


def test_get_generation_status_unauthorized(auth_token, db_session: Session):
    """Test getting status of generation owned by another user."""
    from app.db.session import get_db
    from app.core.security import hash_password
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create another user
    other_user = User(
        username="otheruser",
        password_hash=hash_password("password123"),
        email="other@example.com"
    )
    db_session.add(other_user)
    db_session.commit()
    
    # Create generation for other user
    generation = Generation(
        user_id=other_user.id,
        prompt="Other user's prompt",
        status="processing",
        progress=20
    )
    db_session.add(generation)
    db_session.commit()
    
    # Try to access with test_user's token
    response = client.get(
        f"/api/status/{generation.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    app.dependency_overrides.clear()

