"""
Unit tests for authentication Pydantic schemas.
"""
import pytest
from pydantic import ValidationError

from app.schemas.auth import UserLogin, UserRegister, UserResponse, TokenResponse


def test_user_register_valid():
    """Test UserRegister schema with valid data."""
    data = {
        "username": "testuser",
        "password": "password123",
        "email": "test@example.com",
    }
    user = UserRegister(**data)
    assert user.username == "testuser"
    assert user.password == "password123"
    assert user.email == "test@example.com"


def test_user_register_without_email():
    """Test UserRegister schema without optional email."""
    data = {
        "username": "testuser",
        "password": "password123",
    }
    user = UserRegister(**data)
    assert user.username == "testuser"
    assert user.email is None


def test_user_register_username_too_short():
    """Test UserRegister validation - username too short."""
    with pytest.raises(ValidationError):
        UserRegister(username="ab", password="password123")


def test_user_register_username_too_long():
    """Test UserRegister validation - username too long."""
    with pytest.raises(ValidationError):
        UserRegister(username="a" * 51, password="password123")


def test_user_register_username_invalid_format():
    """Test UserRegister validation - invalid username format."""
    with pytest.raises(ValidationError):
        UserRegister(username="test-user!", password="password123")


def test_user_register_password_too_short():
    """Test UserRegister validation - password too short."""
    with pytest.raises(ValidationError):
        UserRegister(username="testuser", password="short")


def test_user_register_password_too_long():
    """Test UserRegister validation - password too long."""
    with pytest.raises(ValidationError):
        UserRegister(username="testuser", password="a" * 101)


def test_user_register_email_too_long():
    """Test UserRegister validation - email too long."""
    with pytest.raises(ValidationError):
        UserRegister(
            username="testuser",
            password="password123",
            email="a" * 256 + "@example.com",
        )


def test_user_login_valid():
    """Test UserLogin schema with valid data."""
    data = {
        "username": "testuser",
        "password": "password123",
    }
    user = UserLogin(**data)
    assert user.username == "testuser"
    assert user.password == "password123"


def test_user_login_username_too_short():
    """Test UserLogin validation - username too short."""
    with pytest.raises(ValidationError):
        UserLogin(username="ab", password="password123")


def test_user_login_password_too_short():
    """Test UserLogin validation - password too short."""
    with pytest.raises(ValidationError):
        UserLogin(username="testuser", password="short")


def test_user_response():
    """Test UserResponse schema."""
    data = {
        "id": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "total_generations": 5,
        "total_cost": 12.50,
    }
    user = UserResponse(**data)
    assert user.id == "user123"
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.total_generations == 5
    assert user.total_cost == 12.50


def test_user_response_without_email():
    """Test UserResponse schema without email."""
    data = {
        "id": "user123",
        "username": "testuser",
        "total_generations": 0,
        "total_cost": 0.0,
    }
    user = UserResponse(**data)
    assert user.email is None


def test_token_response():
    """Test TokenResponse schema."""
    user_data = {
        "id": "user123",
        "username": "testuser",
        "total_generations": 0,
        "total_cost": 0.0,
    }
    user = UserResponse(**user_data)
    
    token_data = {
        "access_token": "test_token",
        "token_type": "bearer",
        "user": user,
    }
    token = TokenResponse(**token_data)
    assert token.access_token == "test_token"
    assert token.token_type == "bearer"
    assert token.user.id == "user123"


def test_token_response_default_type():
    """Test TokenResponse schema with default token_type."""
    user_data = {
        "id": "user123",
        "username": "testuser",
        "total_generations": 0,
        "total_cost": 0.0,
    }
    user = UserResponse(**user_data)
    
    token_data = {
        "access_token": "test_token",
        "user": user,
    }
    token = TokenResponse(**token_data)
    assert token.token_type == "bearer"

