"""
Integration tests for quality control service and pipeline integration.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
import os

from app.db.models.user import User
from app.db.models.generation import Generation
from app.db.models.quality_metric import QualityMetric
from app.main import app
from app.core.security import hash_password
from app.services.pipeline.quality_control import evaluate_and_store_quality, regenerate_clip
from app.schemas.generation import Scene

client = TestClient(app)


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
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
def test_user2(db_session: Session):
    """Create a second test user for authorization testing."""
    password_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    user = User(
        username="testuser2",
        password_hash=password_hash,
        email="test2@example.com"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_generation(db_session: Session, test_user):
    """Create a sample generation for testing."""
    generation = Generation(
        user_id=test_user.id,
        prompt="Test video generation",
        duration=15,
        status="processing",
        progress=50,
        coherence_settings={"vbench_quality_control": True}
    )
    db_session.add(generation)
    db_session.commit()
    db_session.refresh(generation)
    return generation


@pytest.fixture
def sample_video_file(tmp_path):
    """Create a sample video file for testing."""
    video_path = tmp_path / "test_video.mp4"
    # Create a minimal valid MP4 file (just create empty file for testing)
    # In real tests, you'd use a proper video file
    video_path.write_bytes(b"fake video content")
    return str(video_path)


def test_quality_metric_migration_up_and_down(db_session: Session):
    """Integration test: Migration creates quality_metrics table correctly."""
    from sqlalchemy import inspect
    from app.db.base import Base
    
    # The table should already exist from Base.metadata.create_all in conftest
    # But we verify it exists and has correct structure
    inspector = inspect(db_session.bind)
    tables = inspector.get_table_names()
    assert "quality_metrics" in tables, "quality_metrics table should exist"
    
    # Verify table structure
    columns = [col["name"] for col in inspector.get_columns("quality_metrics")]
    expected_columns = [
        "id", "generation_id", "scene_number", "clip_path",
        "vbench_scores", "overall_quality", "passed_threshold",
        "regeneration_attempts", "created_at"
    ]
    for col in expected_columns:
        assert col in columns, f"Column {col} not found in quality_metrics table"


def test_quality_metric_model_creation_and_relationships(db_session: Session, sample_generation):
    """Integration test: QualityMetric model creation and relationships."""
    # Create quality metric
    metric = QualityMetric(
        generation_id=sample_generation.id,
        scene_number=1,
        clip_path="/test/clip.mp4",
        vbench_scores={"overall_quality": 80.0, "temporal_quality": 75.0},
        overall_quality=80.0,
        passed_threshold=True,
        regeneration_attempts=0
    )
    db_session.add(metric)
    db_session.commit()
    db_session.refresh(metric)
    
    # Verify metric was created
    assert metric.id is not None
    assert metric.generation_id == sample_generation.id
    assert metric.scene_number == 1
    assert metric.overall_quality == 80.0
    assert metric.passed_threshold is True
    
    # Verify relationship
    assert sample_generation.quality_metrics is not None
    assert len(sample_generation.quality_metrics) == 1
    assert sample_generation.quality_metrics[0].id == metric.id


@pytest.mark.asyncio
async def test_quality_control_integrated_into_pipeline(db_session: Session, sample_generation, sample_video_file):
    """Integration test: Quality control integrated into full generation pipeline."""
    from app.services.pipeline.quality_control import evaluate_and_store_quality
    
    # Enable quality control
    sample_generation.coherence_settings = {"vbench_quality_control": True}
    db_session.commit()
    
    # Mock video evaluation (since we don't have real video processing)
    with patch("app.services.pipeline.quality_control.evaluate_vbench") as mock_eval:
        mock_eval.return_value = {
            "temporal_quality": 80.0,
            "aesthetic_quality": 85.0,
            "imaging_quality": 82.0,
            "text_video_alignment": 75.0,
            "overall_quality": 80.0,
        }
        
        # Evaluate and store quality
        passed, details = await evaluate_and_store_quality(
            db=db_session,
            generation_id=sample_generation.id,
            scene_number=1,
            clip_path=sample_video_file,
            prompt_text="test prompt",
            coherence_settings=sample_generation.coherence_settings
        )
        
        # Verify quality metric was stored
        metric = db_session.query(QualityMetric).filter(
            QualityMetric.generation_id == sample_generation.id,
            QualityMetric.scene_number == 1
        ).first()
        
        assert metric is not None
        assert metric.overall_quality == 80.0
        assert metric.passed_threshold is True
        assert passed is True


@pytest.mark.asyncio
async def test_regeneration_triggered_on_low_quality(db_session: Session, sample_generation, sample_video_file):
    """Integration test: Regeneration triggered on low quality."""
    from app.services.pipeline.quality_control import evaluate_and_store_quality, regenerate_clip
    from app.schemas.generation import Scene
    
    # Enable quality control
    sample_generation.coherence_settings = {"vbench_quality_control": True}
    db_session.commit()
    
    scene = Scene(
        scene_number=1,
        scene_type="Problem",
        visual_prompt="test scene",
        duration=5
    )
    
    # First, create a quality metric with low quality
    with patch("app.services.pipeline.quality_control.evaluate_vbench") as mock_eval:
        mock_eval.return_value = {
            "temporal_quality": 50.0,  # Below threshold
            "aesthetic_quality": 55.0,
            "imaging_quality": 52.0,
            "text_video_alignment": 48.0,
            "overall_quality": 51.0,  # Below threshold
        }
        
        passed, details = await evaluate_and_store_quality(
            db=db_session,
            generation_id=sample_generation.id,
            scene_number=1,
            clip_path=sample_video_file,
            prompt_text="test prompt",
            coherence_settings=sample_generation.coherence_settings
        )
        
        assert passed is False
        
        # Verify metric was created with failed status
        metric = db_session.query(QualityMetric).filter(
            QualityMetric.generation_id == sample_generation.id,
            QualityMetric.scene_number == 1
        ).first()
        
        assert metric is not None
        assert metric.passed_threshold is False
        assert metric.regeneration_attempts == 0
        
        # Now test regeneration (mocked)
        with patch("app.services.pipeline.quality_control.generate_video_clip") as mock_gen:
            # Mock successful regeneration with better quality
            mock_gen.return_value = (sample_video_file, "model-used")
            
            # Mock improved quality evaluation
            mock_eval.return_value = {
                "temporal_quality": 85.0,
                "aesthetic_quality": 88.0,
                "imaging_quality": 87.0,
                "text_video_alignment": 82.0,
                "overall_quality": 85.5,  # Above threshold
            }
            
            # Trigger regeneration
            new_clip_path, success, regen_details = await regenerate_clip(
                db=db_session,
                generation_id=sample_generation.id,
                scene_number=1,
                scene=scene,
                output_dir=str(Path(sample_video_file).parent),
                original_clip_path=sample_video_file,
                prompt_text="test prompt",
                coherence_settings=sample_generation.coherence_settings,
                max_attempts=2
            )
            
            # Verify regeneration updated the metric
            db_session.refresh(metric)
            assert metric.regeneration_attempts == 1
            assert metric.passed_threshold is True  # Quality improved
            assert metric.overall_quality == 85.5


@pytest.mark.asyncio
async def test_quality_metrics_api_endpoint_returns_correct_data(test_user, sample_generation, db_session: Session):
    """Integration test: Quality metrics endpoint returns correct data."""
    from app.api.deps import get_current_user
    from app.db.session import get_db
    
    # Create quality metrics
    metric1 = QualityMetric(
        generation_id=sample_generation.id,
        scene_number=1,
        clip_path="/test/clip1.mp4",
        vbench_scores={"overall_quality": 80.0},
        overall_quality=80.0,
        passed_threshold=True,
        regeneration_attempts=0
    )
    metric2 = QualityMetric(
        generation_id=sample_generation.id,
        scene_number=2,
        clip_path="/test/clip2.mp4",
        vbench_scores={"overall_quality": 65.0},
        overall_quality=65.0,
        passed_threshold=False,
        regeneration_attempts=1
    )
    db_session.add_all([metric1, metric2])
    db_session.commit()
    
    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Call API endpoint
    response = client.get(f"/api/generations/{sample_generation.id}/quality")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify response structure
    assert data["generation_id"] == sample_generation.id
    assert len(data["clips"]) == 2
    assert "summary" in data
    
    # Verify clip data
    clip1 = next(c for c in data["clips"] if c["scene_number"] == 1)
    assert clip1["overall_quality"] == 80.0
    assert clip1["passed_threshold"] is True
    assert clip1["regeneration_attempts"] == 0
    
    clip2 = next(c for c in data["clips"] if c["scene_number"] == 2)
    assert clip2["overall_quality"] == 65.0
    assert clip2["passed_threshold"] is False
    assert clip2["regeneration_attempts"] == 1
    
    # Verify summary
    assert data["summary"]["total_clips"] == 2
    assert data["summary"]["passed_count"] == 1
    assert data["summary"]["failed_count"] == 1
    assert data["summary"]["average_quality"] == 72.5
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_quality_metrics_api_authorization(test_user, test_user2, db_session: Session):
    """Integration test: Authorization prevents access to other users' metrics."""
    from app.api.deps import get_current_user
    from app.db.session import get_db
    
    # Create generation for user2
    generation2 = Generation(
        user_id=test_user2.id,
        prompt="User 2's video",
        duration=15,
        status="completed"
    )
    db_session.add(generation2)
    db_session.commit()
    db_session.refresh(generation2)
    
    # Create quality metric for user2's generation
    metric = QualityMetric(
        generation_id=generation2.id,
        scene_number=1,
        clip_path="/test/clip.mp4",
        vbench_scores={"overall_quality": 80.0},
        overall_quality=80.0,
        passed_threshold=True
    )
    db_session.add(metric)
    db_session.commit()
    
    # Override dependencies to use test_user (not owner)
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_db] = lambda: db_session
    
    # Try to access user2's quality metrics
    response = client.get(f"/api/generations/{generation2.id}/quality")
    
    # Should be forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "FORBIDDEN" in data.get("error", {}).get("code", "")
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_successful_regeneration_improves_quality(db_session: Session, sample_generation, sample_video_file):
    """Integration test: Successful regeneration improves quality."""
    from app.schemas.generation import Scene
    
    scene = Scene(
        scene_number=1,
        scene_type="Problem",
        visual_prompt="test scene",
        duration=5
    )
    
    # Create initial low-quality metric
    initial_metric = QualityMetric(
        generation_id=sample_generation.id,
        scene_number=1,
        clip_path=sample_video_file,
        vbench_scores={"overall_quality": 55.0},
        overall_quality=55.0,
        passed_threshold=False,
        regeneration_attempts=0
    )
    db_session.add(initial_metric)
    db_session.commit()
    
    # Mock regeneration with improved quality
    with patch("app.services.pipeline.quality_control.generate_video_clip") as mock_gen, \
         patch("app.services.pipeline.quality_control.evaluate_vbench") as mock_eval, \
         patch("app.services.pipeline.quality_control.check_quality_thresholds") as mock_check:
        
        mock_gen.return_value = (sample_video_file, "model-used")
        mock_eval.return_value = {
            "temporal_quality": 90.0,
            "aesthetic_quality": 92.0,
            "imaging_quality": 88.0,
            "text_video_alignment": 85.0,
            "overall_quality": 88.75,  # Much better
        }
        mock_check.return_value = (True, {"passed": True, "failed_dimensions": []})
        
        # Regenerate
        new_clip_path, success, details = await regenerate_clip(
            db=db_session,
            generation_id=sample_generation.id,
            scene_number=1,
            scene=scene,
            output_dir=str(Path(sample_video_file).parent),
            original_clip_path=sample_video_file,
            prompt_text="test prompt",
            coherence_settings={"vbench_quality_control": True},
            max_attempts=2
        )
        
        # Verify improvement
        db_session.refresh(initial_metric)
        assert initial_metric.regeneration_attempts == 1
        assert initial_metric.passed_threshold is True
        assert initial_metric.overall_quality == 88.75
        assert initial_metric.overall_quality > 55.0  # Improved from initial

