"""
Integration tests for authentication routes.
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.main import app

client = TestClient(app)


def test_register_user_success(db_session: Session):
    """Test successful user registration (AC-2.1.1)."""
    # Override get_db dependency to use test session
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "password123",
            "email": "test@example.com",
        },
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "message" in data
    assert data["message"] == "User created successfully"
    assert "user_id" in data
    assert len(data["user_id"]) > 0
    
    # Verify user was created in database
    user = db_session.query(User).filter(User.username == "testuser").first()
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.password_hash != "password123"  # Password should be hashed
    assert user.password_hash.startswith("$2b$12$")  # bcrypt with cost factor 12
    
    app.dependency_overrides.clear()


def test_register_user_duplicate_username(db_session: Session):
    """Test registration with duplicate username returns 400 (AC-2.1.1)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create first user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "password123",
        },
    )
    
    # Try to create duplicate
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "password456",
        },
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"]["code"] == "USERNAME_EXISTS"
    
    app.dependency_overrides.clear()


def test_register_validation_username_too_short(db_session: Session):
    """Test registration validation - username too short (AC-2.1.2)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post(
        "/api/auth/register",
        json={
            "username": "ab",  # Too short (min 3)
            "password": "password123",
        },
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    app.dependency_overrides.clear()


def test_register_validation_password_too_short(db_session: Session):
    """Test registration validation - password too short (AC-2.1.2)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "password": "short",  # Too short (min 8)
        },
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    app.dependency_overrides.clear()


def test_register_validation_invalid_username_format(db_session: Session):
    """Test registration validation - invalid username format (AC-2.1.2)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post(
        "/api/auth/register",
        json={
            "username": "test-user!",  # Invalid characters
            "password": "password123",
        },
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    app.dependency_overrides.clear()


def test_login_success(db_session: Session):
    """Test successful login (AC-2.1.3)."""
    from app.core.security import hash_password
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create user directly in database
    user = User(
        username="testuser",
        password_hash=hash_password("password123"),
        email="test@example.com",
    )
    db_session.add(user)
    db_session.commit()
    
    # Login
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "password123",
        },
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["id"] == user.id
    
    # Verify last_login was updated
    db_session.refresh(user)
    assert user.last_login is not None
    
    app.dependency_overrides.clear()


def test_login_invalid_username(db_session: Session):
    """Test login with invalid username (AC-2.1.4)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post(
        "/api/auth/login",
        json={
            "username": "nonexistent",
            "password": "password123",
        },
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"]["code"] == "INVALID_CREDENTIALS"
    assert "Invalid username or password" in data["detail"]["error"]["message"]
    
    app.dependency_overrides.clear()


def test_login_invalid_password(db_session: Session):
    """Test login with invalid password (AC-2.1.4)."""
    from app.core.security import hash_password
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create user
    user = User(
        username="testuser",
        password_hash=hash_password("correct_password"),
    )
    db_session.add(user)
    db_session.commit()
    
    # Login with wrong password
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "wrong_password",
        },
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"]["code"] == "INVALID_CREDENTIALS"
    
    app.dependency_overrides.clear()


def test_get_me_with_valid_token(db_session: Session):
    """Test GET /api/auth/me with valid token (AC-2.1.5)."""
    from app.core.security import create_access_token, hash_password
    from app.db.session import get_db
    from app.api.deps import get_current_user
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Create user
    user = User(
        username="testuser",
        password_hash=hash_password("password123"),
        email="test@example.com",
        total_generations=5,
        total_cost=12.50,
    )
    db_session.add(user)
    db_session.commit()
    
    # Create token
    token_data = {"sub": user.id, "username": user.username}
    token = create_access_token(token_data)
    
    # Make request with token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user.id
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["total_generations"] == 5
    assert data["total_cost"] == 12.50
    
    app.dependency_overrides.clear()


def test_get_me_without_token(db_session: Session):
    """Test GET /api/auth/me without token (AC-2.1.6)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.get("/api/auth/me")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    app.dependency_overrides.clear()


def test_get_me_with_invalid_token(db_session: Session):
    """Test GET /api/auth/me with invalid token (AC-2.1.6)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    app.dependency_overrides.clear()


def test_register_user_without_email(db_session: Session):
    """Test registration without optional email field."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser2",
            "password": "password123",
        },
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "user_id" in data
    
    # Verify user was created without email
    user = db_session.query(User).filter(User.username == "testuser2").first()
    assert user is not None
    assert user.email is None
    
    app.dependency_overrides.clear()

