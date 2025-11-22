"""
Integration tests for Pipeline Orchestrator with brand/product style JSON integration.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from app.services.pipeline.pipeline_orchestrator import generate_video_prompt
from app.db.models.brand_style import BrandStyleFolder
from app.db.models.uploaded_image import UploadedImage
from app.db.models.user import User


@pytest.fixture
def sample_user(db_session):
    """Create a sample user in the database."""
    user = User(
        id="test-user-id",
        username="testuser",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_brand_style_folder(db_session, sample_user):
    """Create a sample brand style folder with extracted style JSON."""
    brand_folder = BrandStyleFolder(
        id="test-brand-folder-id",
        user_id=sample_user.id,
        extracted_style_json={
            "color_palette": {
                "primary_colors": ["#FF5733", "#33FF57"],
                "secondary_colors": ["#3357FF"],
            },
            "visual_style": {
                "aesthetic": "modern minimalist",
                "mood": "sophisticated",
            },
            "lighting_cues": "dramatic studio lighting",
        },
    )
    db_session.add(brand_folder)
    db_session.commit()
    db_session.refresh(brand_folder)
    return brand_folder


@pytest.fixture
def sample_product_image(db_session, sample_user):
    """Create a sample product image with extracted product style JSON."""
    product_image = UploadedImage(
        id="test-product-image-id",
        folder_id="test-product-folder-id",
        folder_type="product",
        filename="product.jpg",
        file_path="/path/to/product.jpg",
        file_size=1024,
        extracted_product_style_json={
            "product_characteristics": {
                "form_factor": "bottle",
                "material_appearance": "frosted glass",
            },
            "visual_style": {
                "composition": "centered",
            },
            "color_profile": {
                "dominant_colors": ["#FFFFFF"],
            },
        },
    )
    db_session.add(product_image)
    db_session.commit()
    db_session.refresh(product_image)
    return product_image


@patch("app.services.pipeline.pipeline_option_c.run_stage1_blueprint")
@patch("app.services.pipeline.pipeline_option_c.run_stage2_scent_profile")
@patch("app.services.pipeline.stage3_scene_assembler.run_stage3_scene_assembler")
@pytest.mark.asyncio
async def test_pipeline_orchestrator_loads_brand_style_json(
    mock_stage3,
    mock_stage2,
    mock_stage1,
    db_session,
    sample_user,
    sample_brand_style_folder,
):
    """Test pipeline orchestrator loads brand style JSON from database."""
    # Mock Stage 1 and Stage 2 responses
    from app.services.pipeline.llm_schemas import Stage1Blueprint, ScentProfile, BlueprintScene, SceneDescription
    
    mock_stage1.return_value = Stage1Blueprint(
        framework="AIDA",
        total_duration_seconds=15,
        reference_image_path="test.jpg",
        reference_image_usage="inspiration",
        style_tone="cinematic",
        scenes=[
            BlueprintScene(
                scene_number=i,
                stage=f"Scene {i}",
                duration_seconds=3,
                scene_description=SceneDescription(
                    visual=f"Visual {i}",
                    action=f"Action {i}",
                    camera=f"Camera {i}",
                    lighting=f"Lighting {i}",
                    mood=f"Mood {i}",
                    product_usage=f"Product usage {i}",
                ),
                sound_design=f"Sound {i}",
                voiceover=f"Voiceover {i}",
                overlay_text=f"Overlay {i}",
            )
            for i in range(1, 6)
        ],
        music={"track": "test.mp3"},
    )
    
    mock_stage2.return_value = ScentProfile(
        scent_profile_source="inferred",
        top_notes=["lemon"],
        heart_notes=["lavender"],
        base_notes=["musk"],
        lighting_cues="soft",
        color_palette="warm",
        motion_physics="smooth",
        surface_textures="silk",
        atmosphere_density="airy",
        sound_motifs="gentle",
        emotional_register="calm",
    )
    
    mock_stage3.return_value = ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]
    
    result = await generate_video_prompt(
        user_prompt="Test prompt",
        user_id=sample_user.id,
        db=db_session,
    )
    
    # Verify Stage 3 was called with brand style JSON
    assert mock_stage3.called
    call_kwargs = mock_stage3.call_args[1]
    assert call_kwargs["brand_style_json"] is not None
    assert call_kwargs["brand_style_json"]["color_palette"]["primary_colors"] == ["#FF5733", "#33FF57"]
    assert result["stage3_scenes"] == ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]


@patch("app.services.pipeline.pipeline_option_c.run_stage1_blueprint")
@patch("app.services.pipeline.pipeline_option_c.run_stage2_scent_profile")
@patch("app.services.pipeline.stage3_scene_assembler.run_stage3_scene_assembler")
@pytest.mark.asyncio
async def test_pipeline_orchestrator_loads_product_style_json(
    mock_stage3,
    mock_stage2,
    mock_stage1,
    db_session,
    sample_user,
    sample_product_image,
):
    """Test pipeline orchestrator loads product style JSON from database."""
    # Mock Stage 1 and Stage 2 responses
    from app.services.pipeline.llm_schemas import Stage1Blueprint, ScentProfile, BlueprintScene, SceneDescription
    
    mock_stage1.return_value = Stage1Blueprint(
        framework="AIDA",
        total_duration_seconds=15,
        reference_image_path="test.jpg",
        reference_image_usage="inspiration",
        style_tone="cinematic",
        scenes=[
            BlueprintScene(
                scene_number=i,
                stage=f"Scene {i}",
                duration_seconds=3,
                scene_description=SceneDescription(
                    visual=f"Visual {i}",
                    action=f"Action {i}",
                    camera=f"Camera {i}",
                    lighting=f"Lighting {i}",
                    mood=f"Mood {i}",
                    product_usage=f"Product usage {i}",
                ),
                sound_design=f"Sound {i}",
                voiceover=f"Voiceover {i}",
                overlay_text=f"Overlay {i}",
            )
            for i in range(1, 6)
        ],
        music={"track": "test.mp3"},
    )
    
    mock_stage2.return_value = ScentProfile(
        scent_profile_source="inferred",
        top_notes=["lemon"],
        heart_notes=["lavender"],
        base_notes=["musk"],
        lighting_cues="soft",
        color_palette="warm",
        motion_physics="smooth",
        surface_textures="silk",
        atmosphere_density="airy",
        sound_motifs="gentle",
        emotional_register="calm",
    )
    
    mock_stage3.return_value = ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]
    
    result = await generate_video_prompt(
        user_prompt="Test prompt",
        product_image_id=sample_product_image.id,
        user_id=sample_user.id,
        db=db_session,
    )
    
    # Verify Stage 3 was called with product style JSON
    assert mock_stage3.called
    call_kwargs = mock_stage3.call_args[1]
    assert call_kwargs["product_style_json"] is not None
    assert call_kwargs["product_style_json"]["product_characteristics"]["form_factor"] == "bottle"
    assert result["stage3_scenes"] == ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]


@patch("app.services.pipeline.pipeline_option_c.run_stage1_blueprint")
@patch("app.services.pipeline.pipeline_option_c.run_stage2_scent_profile")
@patch("app.services.pipeline.stage3_scene_assembler.run_stage3_scene_assembler")
@pytest.mark.asyncio
async def test_pipeline_orchestrator_handles_missing_brand_style_gracefully(
    mock_stage3,
    mock_stage2,
    mock_stage1,
    db_session,
    sample_user,
):
    """Test pipeline orchestrator handles missing brand style JSON gracefully (backward compatibility)."""
    # Mock Stage 1 and Stage 2 responses
    from app.services.pipeline.llm_schemas import Stage1Blueprint, ScentProfile, BlueprintScene, SceneDescription
    
    mock_stage1.return_value = Stage1Blueprint(
        framework="AIDA",
        total_duration_seconds=15,
        reference_image_path="test.jpg",
        reference_image_usage="inspiration",
        style_tone="cinematic",
        scenes=[
            BlueprintScene(
                scene_number=i,
                stage=f"Scene {i}",
                duration_seconds=3,
                scene_description=SceneDescription(
                    visual=f"Visual {i}",
                    action=f"Action {i}",
                    camera=f"Camera {i}",
                    lighting=f"Lighting {i}",
                    mood=f"Mood {i}",
                    product_usage=f"Product usage {i}",
                ),
                sound_design=f"Sound {i}",
                voiceover=f"Voiceover {i}",
                overlay_text=f"Overlay {i}",
            )
            for i in range(1, 6)
        ],
        music={"track": "test.mp3"},
    )
    
    mock_stage2.return_value = ScentProfile(
        scent_profile_source="inferred",
        top_notes=["lemon"],
        heart_notes=["lavender"],
        base_notes=["musk"],
        lighting_cues="soft",
        color_palette="warm",
        motion_physics="smooth",
        surface_textures="silk",
        atmosphere_density="airy",
        sound_motifs="gentle",
        emotional_register="calm",
    )
    
    mock_stage3.return_value = ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]
    
    # User has no brand style folder
    result = await generate_video_prompt(
        user_prompt="Test prompt",
        user_id=sample_user.id,
        db=db_session,
    )
    
    # Verify Stage 3 was called without brand style JSON (None)
    assert mock_stage3.called
    call_kwargs = mock_stage3.call_args[1]
    assert call_kwargs["brand_style_json"] is None
    assert result["stage3_scenes"] == ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]


@patch("app.services.pipeline.pipeline_option_c.run_stage1_blueprint")
@patch("app.services.pipeline.pipeline_option_c.run_stage2_scent_profile")
@patch("app.services.pipeline.stage3_scene_assembler.run_stage3_scene_assembler")
@pytest.mark.asyncio
async def test_pipeline_orchestrator_handles_missing_product_style_gracefully(
    mock_stage3,
    mock_stage2,
    mock_stage1,
    db_session,
    sample_user,
):
    """Test pipeline orchestrator handles missing product style JSON gracefully."""
    # Mock Stage 1 and Stage 2 responses
    from app.services.pipeline.llm_schemas import Stage1Blueprint, ScentProfile, BlueprintScene, SceneDescription
    
    mock_stage1.return_value = Stage1Blueprint(
        framework="AIDA",
        total_duration_seconds=15,
        reference_image_path="test.jpg",
        reference_image_usage="inspiration",
        style_tone="cinematic",
        scenes=[
            BlueprintScene(
                scene_number=i,
                stage=f"Scene {i}",
                duration_seconds=3,
                scene_description=SceneDescription(
                    visual=f"Visual {i}",
                    action=f"Action {i}",
                    camera=f"Camera {i}",
                    lighting=f"Lighting {i}",
                    mood=f"Mood {i}",
                    product_usage=f"Product usage {i}",
                ),
                sound_design=f"Sound {i}",
                voiceover=f"Voiceover {i}",
                overlay_text=f"Overlay {i}",
            )
            for i in range(1, 6)
        ],
        music={"track": "test.mp3"},
    )
    
    mock_stage2.return_value = ScentProfile(
        scent_profile_source="inferred",
        top_notes=["lemon"],
        heart_notes=["lavender"],
        base_notes=["musk"],
        lighting_cues="soft",
        color_palette="warm",
        motion_physics="smooth",
        surface_textures="silk",
        atmosphere_density="airy",
        sound_motifs="gentle",
        emotional_register="calm",
    )
    
    mock_stage3.return_value = ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]
    
    # Product image ID doesn't exist
    result = await generate_video_prompt(
        user_prompt="Test prompt",
        product_image_id="non-existent-id",
        user_id=sample_user.id,
        db=db_session,
    )
    
    # Verify Stage 3 was called without product style JSON (None)
    assert mock_stage3.called
    call_kwargs = mock_stage3.call_args[1]
    assert call_kwargs["product_style_json"] is None
    assert result["stage3_scenes"] == ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]

