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
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    
    token = response.json()["access_token"]
    app.dependency_overrides.clear()
    return token


def test_create_generation_success(auth_token, db_session: Session):
    """Test successful generation creation (AC-3.1.1, AC-3.1.2, AC-3.1.3)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Mock LLM enhancement response
    mock_ad_spec = AdSpecification(
        product_description="A premium coffee maker",
        brand_guidelines=BrandGuidelines(
            brand_name="CoffeePro",
            brand_colors=["#8B4513"],
            visual_style_keywords="luxury, modern",
            mood="sophisticated"
        ),
        ad_specifications=AdSpec(
            target_audience="Coffee enthusiasts",
            call_to_action="Order now",
            tone="premium"
        ),
        framework="PAS",
        scenes=[
            Scene(
                scene_number=1,
                scene_type="Problem",
                visual_prompt="Show someone struggling",
                text_overlay=TextOverlay(
                    text="Tired of bad coffee?",
                    position="top",
                    font_size=48,
                    color="#8B4513",
                    animation="fade_in"
                ),
                duration=5
            ),
            Scene(
                scene_number=2,
                scene_type="Agitation",
                visual_prompt="Show frustration",
                text_overlay=TextOverlay(
                    text="Every cup is different",
                    position="center",
                    font_size=48,
                    color="#8B4513",
                    animation="slide_up"
                ),
                duration=5
            ),
            Scene(
                scene_number=3,
                scene_type="Solution",
                visual_prompt="Show CoffeePro",
                text_overlay=TextOverlay(
                    text="CoffeePro - Perfect every time",
                    position="bottom",
                    font_size=48,
                    color="#8B4513",
                    animation="fade_in"
                ),
                duration=5
            )
        ]
    )
    
    with patch("app.services.pipeline.llm_enhancement.enhance_prompt_with_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_ad_spec
        
        response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "prompt": "Create a luxury coffee maker ad"
            }
        )
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "generation_id" in data
        assert data["status"] == "pending"
        assert "message" in data
        
        # Verify generation was created in database
        generation = db_session.query(Generation).filter(Generation.id == data["generation_id"]).first()
        assert generation is not None
        assert generation.prompt == "Create a luxury coffee maker ad"
        assert generation.status == "pending"
        assert generation.progress == 20  # Should be 20% after LLM + scene planning
        assert generation.llm_specification is not None
        assert generation.scene_plan is not None
        assert generation.framework == "PAS"
        assert generation.num_scenes == 3
    
    app.dependency_overrides.clear()


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


def test_create_generation_llm_api_failure(auth_token, db_session: Session):
    """Test generation creation when LLM API fails (AC-3.1.2 error handling)."""
    from app.db.session import get_db
    import openai
    app.dependency_overrides[get_db] = lambda: db_session
    
    with patch("app.services.pipeline.llm_enhancement.enhance_prompt_with_llm", new_callable=AsyncMock) as mock_llm:
        # Simulate OpenAI API error after retries
        mock_llm.side_effect = openai.APIError(
            message="API request failed",
            request=None,
            body=None
        )
        
        response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "prompt": "Create a luxury coffee maker ad"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "GENERATION_FAILED"
        
        # Verify generation was marked as failed
        # Get the most recent generation for this user
        generation = db_session.query(Generation).filter(
            Generation.user_id == db_session.query(User).filter(User.username == "testuser").first().id
        ).order_by(Generation.created_at.desc()).first()
        
        assert generation is not None
        assert generation.status == "failed"
        assert generation.error_message is not None
    
    app.dependency_overrides.clear()


def test_create_generation_invalid_llm_response(auth_token, db_session: Session):
    """Test generation creation when LLM returns invalid JSON (AC-3.1.2 validation)."""
    from app.db.session import get_db
    from app.services.pipeline.llm_enhancement import enhance_prompt_with_llm
    app.dependency_overrides[get_db] = lambda: db_session
    
    with patch("app.services.pipeline.llm_enhancement.enhance_prompt_with_llm", new_callable=AsyncMock) as mock_llm:
        # Simulate invalid JSON response (ValueError from JSON parsing)
        mock_llm.side_effect = ValueError("LLM returned invalid JSON: Expecting value")
        
        response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "prompt": "Create a luxury coffee maker ad"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "GENERATION_FAILED"
        assert "invalid JSON" in data["error"]["message"].lower() or "failed to process" in data["error"]["message"].lower()
    
    app.dependency_overrides.clear()


def test_create_generation_pydantic_validation_failure(auth_token, db_session: Session):
    """Test generation creation when LLM response fails Pydantic validation (AC-3.1.2)."""
    from app.db.session import get_db
    from pydantic import ValidationError
    app.dependency_overrides[get_db] = lambda: db_session
    
    with patch("app.services.pipeline.llm_enhancement.enhance_prompt_with_llm", new_callable=AsyncMock) as mock_llm:
        # Simulate Pydantic validation error
        mock_llm.side_effect = ValueError("LLM response doesn't match schema: validation error")
        
        response = client.post(
            "/api/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "prompt": "Create a luxury coffee maker ad"
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "GENERATION_FAILED"
    
    app.dependency_overrides.clear()


def test_create_generation_scene_planning_failure(auth_token, db_session: Session):
    """Test generation creation when scene planning fails (AC-3.1.3 error handling)."""
    from app.db.session import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Mock LLM to succeed but scene planning to fail
    mock_ad_spec = AdSpecification(
        product_description="A premium coffee maker",
        brand_guidelines=BrandGuidelines(
            brand_name="CoffeePro",
            brand_colors=["#8B4513"],
            visual_style_keywords="luxury, modern",
            mood="sophisticated"
        ),
        ad_specifications=AdSpec(
            target_audience="Coffee enthusiasts",
            call_to_action="Order now",
            tone="premium"
        ),
        framework="PAS",
        scenes=[
            Scene(
                scene_number=1,
                scene_type="Problem",
                visual_prompt="Show someone struggling",
                text_overlay=TextOverlay(
                    text="Tired of bad coffee?",
                    position="top",
                    font_size=48,
                    color="#8B4513",
                    animation="fade_in"
                ),
                duration=5
            )
        ]
    )
    
    with patch("app.services.pipeline.llm_enhancement.enhance_prompt_with_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_ad_spec
        
        with patch("app.services.pipeline.scene_planning.plan_scenes") as mock_plan:
            # Simulate scene planning failure
            mock_plan.side_effect = ValueError("Scene planning failed: invalid framework")
            
            response = client.post(
                "/api/generate",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "prompt": "Create a luxury coffee maker ad"
                }
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "GENERATION_FAILED"
    
    app.dependency_overrides.clear()

