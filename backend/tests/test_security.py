"""
Unit tests for security utilities (password hashing and JWT).
"""
import time
from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password():
    """Test that password hashing produces a different string."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$12$")  # bcrypt with cost factor 12


def test_verify_password_correct():
    """Test password verification with correct password."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password."""
    password = "test_password_123"
    wrong_password = "wrong_password"
    hashed = hash_password(password)
    
    assert verify_password(wrong_password, hashed) is False


def test_hash_password_bcrypt_cost_factor():
    """Test that password hashing uses bcrypt cost factor 12."""
    password = "test_password_123"
    hashed = hash_password(password)
    
    # bcrypt hash format: $2b$12$... (cost factor 12)
    assert hashed.startswith("$2b$12$")


def test_create_access_token():
    """Test JWT token creation."""
    data = {"sub": "user123", "username": "testuser"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expiration():
    """Test JWT token creation with custom expiration."""
    data = {"sub": "user123", "username": "testuser"}
    expires_delta = timedelta(minutes=30)
    token = create_access_token(data, expires_delta=expires_delta)
    
    # Decode token to verify expiration
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert "exp" in payload
    assert "iat" in payload
    assert "sub" in payload
    assert payload["sub"] == "user123"


def test_create_access_token_default_expiration():
    """Test JWT token uses default expiration from settings."""
    data = {"sub": "user123", "username": "testuser"}
    token = create_access_token(data)
    
    # Decode token to verify expiration
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert "exp" in payload
    assert "iat" in payload
    
    # Verify expiration is approximately 7 days (10080 minutes)
    exp_time = payload["exp"]
    iat_time = payload["iat"]
    expiration_minutes = (exp_time - iat_time) / 60
    assert abs(expiration_minutes - settings.ACCESS_TOKEN_EXPIRE_MINUTES) < 1


def test_decode_access_token_valid():
    """Test decoding a valid JWT token."""
    data = {"sub": "user123", "username": "testuser"}
    token = create_access_token(data)
    
    payload = decode_access_token(token)
    
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["username"] == "testuser"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_access_token_expired():
    """Test decoding an expired JWT token."""
    data = {"sub": "user123", "username": "testuser"}
    # Create token with very short expiration
    expires_delta = timedelta(seconds=1)
    token = create_access_token(data, expires_delta=expires_delta)
    
    # Wait for token to expire
    time.sleep(2)
    
    payload = decode_access_token(token)
    assert payload is None


def test_decode_access_token_invalid():
    """Test decoding an invalid JWT token."""
    invalid_token = "invalid.token.here"
    
    payload = decode_access_token(invalid_token)
    assert payload is None


def test_decode_access_token_wrong_secret():
    """Test decoding a token signed with wrong secret."""
    data = {"sub": "user123", "username": "testuser"}
    # Create token with wrong secret
    wrong_token = jwt.encode(
        data, "wrong_secret_key", algorithm=settings.ALGORITHM
    )
    
    payload = decode_access_token(wrong_token)
    assert payload is None


def test_jwt_token_contains_required_fields():
    """Test that JWT token contains required fields (sub, username, exp, iat)."""
    data = {"sub": "user123", "username": "testuser"}
    token = create_access_token(data)
    
    payload = decode_access_token(token)
    assert payload is not None
    assert "sub" in payload
    assert "username" in payload
    assert "exp" in payload
    assert "iat" in payload

