"""
Tests for user profile endpoint.
"""
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models.user import User
from app.core.security import create_access_token, hash_password

client = TestClient(app)


def test_get_profile_with_valid_token(db_session: Session):
    """Test GET /api/user/profile with valid JWT token returns user data with all fields (AC-5.1.1)."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create user with all fields
    user = User(
        username="testuser",
        password_hash=hash_password("password123"),
        email="test@example.com",
        total_generations=45,
        total_cost=87.32,
        created_at=datetime.utcnow() - timedelta(days=30),
        last_login=datetime.utcnow() - timedelta(hours=2),
    )
    db_session.add(user)
    db_session.commit()
    
    # Create token
    token_data = {"sub": user.id, "username": user.username}
    token = create_access_token(token_data)
    
    # Make request with token
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user.id
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["total_generations"] == 45
    assert data["total_cost"] == 87.32
    assert "created_at" in data
    assert "last_login" in data
    assert data["last_login"] is not None
    
    app.dependency_overrides.clear()


def test_get_profile_without_token(db_session: Session):
    """Test GET /api/user/profile without token returns 401 Unauthorized (AC-5.1.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.get("/api/user/profile")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN  # FastAPI HTTPBearer returns 403
    
    app.dependency_overrides.clear()


def test_get_profile_with_invalid_token(db_session: Session):
    """Test GET /api/user/profile with invalid/expired token returns 401 Unauthorized (AC-5.1.1)."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Make request with invalid token
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": "Bearer invalid-token"},
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    app.dependency_overrides.clear()


def test_get_profile_with_null_last_login(db_session: Session):
    """Test GET /api/user/profile handles null last_login correctly (AC-5.1.1)."""
    from app.db.session import get_db
    from app.api.deps import get_current_user
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create user with null last_login
    user = User(
        username="newuser",
        password_hash=hash_password("password123"),
        email=None,
        total_generations=0,
        total_cost=0.0,
        created_at=datetime.utcnow(),
        last_login=None,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create token
    token_data = {"sub": user.id, "username": user.username}
    token = create_access_token(token_data)
    
    # Make request with token
    response = client.get(
        "/api/user/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["last_login"] is None
    assert data["email"] is None
    
    app.dependency_overrides.clear()

