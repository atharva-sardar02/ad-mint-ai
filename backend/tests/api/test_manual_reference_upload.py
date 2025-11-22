"""
Tests for manual reference image upload endpoint.
"""
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status

from app.api.deps import get_current_user
from app.core.config import settings
from app.main import app


@pytest.fixture
def mock_session():
    session = Mock()
    session.session_id = "sess_manual_123"
    session.user_id = "user_123"
    session.status = "story"
    session.prompt = "Brand prompt"
    session.stage_data = {}
    return session


@pytest.fixture
def mock_user():
    user = Mock()
    user.id = "user_123"
    return user


@pytest.mark.asyncio
async def test_manual_reference_upload_success(client, tmp_path, mock_session, mock_user):
    """Uploading valid images stores metadata and registers with orchestrator."""
    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch, \
         patch("app.api.routes.interactive_generation.uuid4") as mock_uuid, \
         patch.object(settings, "OUTPUT_BASE_DIR", str(tmp_path)):

        mock_uuid.return_value = Mock(hex="deadbeefdeadbeefdeadbeefdeadbeef")

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=mock_session)
        mock_orchestrator.register_manual_reference_images = AsyncMock()
        mock_get_orch.return_value = mock_orchestrator

        files = {
            "images": ("hero.png", b"\x89PNG\r\n", "image/png"),
        }

        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            response = await client.post(
                "/api/v1/interactive/sess_manual_123/reference-images/upload",
                files=files,
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()

    assert payload["session_id"] == "sess_manual_123"
    assert len(payload["images"]) == 1
    assert payload["images"][0]["source"] == "manual"
    assert payload["images"][0]["url"].endswith("manual_ref_1_deadbeef.png")

    saved_dir = Path(tmp_path) / "interactive" / "sess_manual_123" / "reference_images"
    saved_file = saved_dir / "manual_ref_1_deadbeef.png"
    assert saved_file.exists()

    call_args = mock_orchestrator.register_manual_reference_images.call_args[0]
    assert call_args[0] == "sess_manual_123"
    saved_images = call_args[1]
    assert len(saved_images) == 1
    assert saved_images[0]["path"] == str(saved_file)


@pytest.mark.asyncio
async def test_manual_reference_upload_requires_story_stage(client, mock_user):
    """Endpoint returns 400 if session is not in story stage."""
    session = Mock()
    session.session_id = "sess_manual_456"
    session.user_id = "user_123"
    session.status = "reference_image"
    session.prompt = "Prompt"
    session.stage_data = {}

    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch:

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=session)
        mock_orchestrator.register_manual_reference_images = AsyncMock()
        mock_get_orch.return_value = mock_orchestrator

        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            response = await client.post(
                "/api/v1/interactive/sess_manual_456/reference-images/upload",
                files={"images": ("hero.png", b"\x89PNG\r\n", "image/png")},
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "story stage" in response.json()["detail"]
    mock_orchestrator.register_manual_reference_images.assert_not_called()


@pytest.mark.asyncio
async def test_manual_reference_upload_rejects_unauthorized_user(client, mock_session):
    """Endpoint returns 403 when user does not own the session."""
    user = Mock()
    user.id = "different_user"

    with patch("app.api.routes.interactive_generation.get_orchestrator") as mock_get_orch:

        mock_orchestrator = Mock()
        mock_orchestrator.get_session = AsyncMock(return_value=mock_session)
        mock_orchestrator.register_manual_reference_images = AsyncMock()
        mock_get_orch.return_value = mock_orchestrator

        app.dependency_overrides[get_current_user] = lambda: user
        try:
            response = await client.post(
                "/api/v1/interactive/sess_manual_123/reference-images/upload",
                files={"images": ("hero.png", b"\x89PNG\r\n", "image/png")},
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    mock_orchestrator.register_manual_reference_images.assert_not_called()

