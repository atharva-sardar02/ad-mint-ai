"""
Tests for CORS configuration.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cors_allows_frontend_origin():
    """Test that CORS allows requests from frontend origin."""
    # Simulate request from frontend origin
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:5173"},
    )
    
    assert response.status_code == 200
    # Check CORS headers
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_allows_credentials():
    """Test that CORS allows credentials."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    
    assert response.status_code == 200
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_allows_methods():
    """Test that CORS allows common HTTP methods."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    
    assert response.status_code == 200
    assert "access-control-allow-methods" in response.headers
    allowed_methods = response.headers["access-control-allow-methods"]
    assert "GET" in allowed_methods
    assert "POST" in allowed_methods
    assert "PUT" in allowed_methods
    assert "DELETE" in allowed_methods
    assert "OPTIONS" in allowed_methods


def test_cors_blocks_unauthorized_origins():
    """Test that CORS blocks requests from unauthorized origins."""
    # Simulate request from unauthorized origin
    response = client.get(
        "/api/health",
        headers={"Origin": "https://malicious-site.com"},
    )
    
    # The request should still succeed (200 OK) but CORS headers should not allow the origin
    assert response.status_code == 200
    # Check that access-control-allow-origin is either not present or doesn't match unauthorized origin
    if "access-control-allow-origin" in response.headers:
        # If header is present, it should not be the unauthorized origin
        assert response.headers["access-control-allow-origin"] != "https://malicious-site.com"
        # It should either be a specific allowed origin or "*" (but we use specific origins)
        # Since we use specific origins, unauthorized origins should not get CORS headers
        # FastAPI CORS middleware behavior: unauthorized origins don't get access-control-allow-origin
        # So the header should either be absent or be an allowed origin
        allowed_origin = response.headers.get("access-control-allow-origin")
        # If header exists, verify it's from our allowed list
        if allowed_origin:
            from app.core.config import settings
            assert allowed_origin in settings.CORS_ALLOWED_ORIGINS

