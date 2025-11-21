"""
Tests for API health endpoint.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that GET /api/health returns 200 OK with health status."""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_health_endpoint_content_type():
    """Test that health endpoint returns JSON content type."""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


