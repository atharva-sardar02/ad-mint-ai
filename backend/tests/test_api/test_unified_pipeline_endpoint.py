"""
Integration tests for unified pipeline API endpoint.

Tests AC-6: Unified API endpoint POST /api/v2/generate.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestUnifiedPipelineEndpoint:
    """Test unified pipeline API endpoint."""

    def test_generate_endpoint_accepts_valid_request(self):
        """Test that endpoint accepts valid generation request (AC-6)."""
        request_data = {
            "prompt": "Create a 30-second ad for eco-friendly water bottle targeting millennials",
            "framework": "AIDA",
            "interactive": True
        }

        response = client.post("/api/v2/generate", json=request_data)

        assert response.status_code == 202  # Accepted
        data = response.json()

        assert "generation_id" in data
        assert "session_id" in data
        assert "websocket_url" in data
        assert data["status"] == "pending"

    def test_generate_endpoint_with_brand_assets(self):
        """Test endpoint with brand assets provided."""
        request_data = {
            "prompt": "Athletic shoe advertisement",
            "framework": "PAS",
            "brand_assets": {
                "product_images": ["s3://bucket/shoe1.jpg", "s3://bucket/shoe2.jpg"],
                "logo": "s3://bucket/logo.png"
            },
            "interactive": False
        }

        response = client.post("/api/v2/generate", json=request_data)

        assert response.status_code == 202
        data = response.json()
        assert "generation_id" in data

    def test_generate_endpoint_requires_prompt(self):
        """Test that prompt is required (AC-6 validation)."""
        request_data = {
            "framework": "AIDA",
            "interactive": True
        }

        response = client.post("/api/v2/generate", json=request_data)

        assert response.status_code == 422  # Validation error
        error_data = response.json()
        assert "error" in error_data

    def test_generate_endpoint_rejects_short_prompt(self):
        """Test prompt minimum length validation."""
        request_data = {
            "prompt": "Short",  # Less than 10 characters
            "interactive": True
        }

        response = client.post("/api/v2/generate", json=request_data)

        assert response.status_code == 422

    def test_generate_endpoint_automated_mode(self):
        """Test automated mode (non-interactive) generation."""
        request_data = {
            "prompt": "Create an advertisement for wireless headphones",
            "interactive": False
        }

        response = client.post("/api/v2/generate", json=request_data)

        assert response.status_code == 202
        data = response.json()
        assert "generation_id" in data
        # Automated mode may not have websocket_url or it's empty

    def test_generate_endpoint_with_config_overrides(self):
        """Test config overrides in request."""
        request_data = {
            "prompt": "Skincare product advertisement",
            "config": {
                "story_max_iterations": 5,
                "vbench_enabled": False
            },
            "interactive": True
        }

        response = client.post("/api/v2/generate", json=request_data)

        assert response.status_code == 202
        data = response.json()
        assert "generation_id" in data

    def test_get_generation_status_returns_404_for_nonexistent(self):
        """Test GET endpoint returns 404 for non-existent generation."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/api/v2/generate/{fake_id}")

        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
