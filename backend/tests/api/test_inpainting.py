"""
Tests for Inpainting API Endpoint (Story 4: Advanced Image Editing)

Tests cover:
- POST /api/v1/interactive/{session_id}/inpaint
- Image validation (exists, valid index)
- Session ownership verification
- Edit history tracking
- Error responses (404, 403, 400, 500)
"""

import base64
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import status

from app.schemas.interactive import PipelineSessionState


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_session():
    """Create mock session with images."""
    session = PipelineSessionState(
        session_id="test_session_123",
        user_id="user_123",
        status="reference_image",
        current_stage="Reference Image Review",
        created_at="2025-11-20T10:00:00",
        updated_at="2025-11-20T10:05:00",
        expires_at="2025-11-20T11:00:00",
        prompt="Test prompt",
        target_duration=15,
        mode="interactive",
        outputs={
            "reference_image": {
                "images": [
                    {"url": "/path/to/image_0.png", "prompt": "test"},
                    {"url": "/path/to/image_1.png", "prompt": "test"},
                ]
            }
        },
        stage_data={}
    )
    return session


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = Mock()
    user.id = "user_123"
    return user


@pytest.fixture
def inpaint_request_data():
    """Create sample inpaint request data."""
    # Create simple base64 mask
    mask_data = bytes([255] * (100 * 100))
    mask_base64 = base64.b64encode(mask_data).decode("utf-8")

    return {
        "image_id": 0,
        "mask_data": mask_base64,
        "prompt": "red sports car",
        "negative_prompt": "blurry, low quality"
    }


# ============================================================================
# Inpainting Endpoint Tests (AC #5, #7, #8)
# ============================================================================

@pytest.mark.asyncio
async def test_inpaint_image_success(client, mock_session, mock_user, inpaint_request_data):
    """Test successful image inpainting."""
    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.get_current_user", return_value=mock_user), \
         patch("app.services.pipeline.inpainting_service.inpaint_image") as mock_inpaint:

        # Setup mocks
        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=mock_session)
        mock_orchestrator._save_session = AsyncMock()
        mock_get_orch.return_value = mock_orchestrator

        mock_inpaint.return_value = "/path/to/edited_image_0.png"

        # Make request
        response = await client.post(
            "/api/v1/interactive/test_session_123/inpaint",
            json=inpaint_request_data
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["session_id"] == "test_session_123"
    assert data["edited_image_url"] == "/path/to/edited_image_0.png"
    assert data["original_image_url"] == "/path/to/image_0.png"
    assert data["version"] == 1
    assert len(data["edit_history"]) == 2  # Original + edit
    assert data["message"].startswith("Image edited successfully")

    # Verify inpainting service was called
    mock_inpaint.assert_called_once()


@pytest.mark.asyncio
async def test_inpaint_session_not_found(client, mock_user, inpaint_request_data):
    """Test 404 when session doesn't exist."""
    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.get_current_user", return_value=mock_user):

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=None)
        mock_get_orch.return_value = mock_orchestrator

        response = await client.post(
            "/api/v1/interactive/nonexistent_session/inpaint",
            json=inpaint_request_data
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Session not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_inpaint_unauthorized_user(client, mock_session, inpaint_request_data):
    """Test 403 when session belongs to different user."""
    different_user = Mock()
    different_user.id = "different_user_456"

    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.get_current_user", return_value=different_user):

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=mock_session)
        mock_get_orch.return_value = mock_orchestrator

        response = await client.post(
            "/api/v1/interactive/test_session_123/inpaint",
            json=inpaint_request_data
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "access" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_inpaint_no_images_in_stage(client, mock_user, inpaint_request_data):
    """Test 400 when current stage has no images."""
    session_no_images = Mock()
    session_no_images.session_id = "test_session"
    session_no_images.user_id = "user_123"
    session_no_images.status = "story"  # Story stage has no images
    session_no_images.outputs = {"story": {"narrative": "text"}}

    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.get_current_user", return_value=mock_user):

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=session_no_images)
        mock_get_orch.return_value = mock_orchestrator

        response = await client.post(
            "/api/v1/interactive/test_session/inpaint",
            json=inpaint_request_data
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "no images" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_inpaint_image_index_out_of_range(client, mock_session, mock_user):
    """Test 404 when image_id is out of range."""
    inpaint_data = {
        "image_id": 999,  # Out of range (only 0-1 exist)
        "mask_data": "base64data",
        "prompt": "test",
        "negative_prompt": ""
    }

    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.get_current_user", return_value=mock_user):

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=mock_session)
        mock_get_orch.return_value = mock_orchestrator

        response = await client.post(
            "/api/v1/interactive/test_session_123/inpaint",
            json=inpaint_data
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "out of range" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_inpaint_invalid_mask_data(client, mock_session, mock_user):
    """Test 400 when mask data is invalid."""
    inpaint_data = {
        "image_id": 0,
        "mask_data": "invalid_base64!!!",
        "prompt": "test",
        "negative_prompt": ""
    }

    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.get_current_user", return_value=mock_user), \
         patch("app.services.pipeline.inpainting_service.inpaint_image") as mock_inpaint:

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=mock_session)
        mock_get_orch.return_value = mock_orchestrator

        # Inpainting service raises ValueError for invalid mask
        mock_inpaint.side_effect = ValueError("Invalid base64 encoding")

        response = await client.post(
            "/api/v1/interactive/test_session_123/inpaint",
            json=inpaint_data
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid base64" in response.json()["detail"]


@pytest.mark.asyncio
async def test_inpaint_service_failure(client, mock_session, mock_user, inpaint_request_data):
    """Test 500 when inpainting service fails."""
    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.get_current_user", return_value=mock_user), \
         patch("app.services.pipeline.inpainting_service.inpaint_image") as mock_inpaint:

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=mock_session)
        mock_get_orch.return_value = mock_orchestrator

        # Inpainting service raises RuntimeError
        mock_inpaint.side_effect = RuntimeError("Model API error")

        response = await client.post(
            "/api/v1/interactive/test_session_123/inpaint",
            json=inpaint_request_data
        )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Inpainting failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_inpaint_edit_history_tracking(client, mock_session, mock_user, inpaint_request_data):
    """Test edit history is tracked correctly (AC #8)."""
    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.get_current_user", return_value=mock_user), \
         patch("app.services.pipeline.inpainting_service.inpaint_image") as mock_inpaint:

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=mock_session)
        mock_orchestrator._save_session = AsyncMock()
        mock_get_orch.return_value = mock_orchestrator

        mock_inpaint.return_value = "/path/to/edited_v1.png"

        # First edit
        response1 = await client.post(
            "/api/v1/interactive/test_session_123/inpaint",
            json=inpaint_request_data
        )

        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["version"] == 1
        assert len(data1["edit_history"]) == 2  # original + edit1

        # Simulate second edit on same image
        mock_inpaint.return_value = "/path/to/edited_v2.png"

        # Update session with existing edit history
        mock_session.stage_data = {
            "edit_history_0": ["/path/to/image_0.png", "/path/to/edited_v1.png"]
        }

        response2 = await client.post(
            "/api/v1/interactive/test_session_123/inpaint",
            json=inpaint_request_data
        )

        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["version"] == 2
        assert len(data2["edit_history"]) == 3  # original + edit1 + edit2
