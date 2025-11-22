"""
Unit tests for Stage 3 Scene Assembler with brand/product style JSON integration.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from app.services.pipeline.stage3_scene_assembler import (
    run_stage3_scene_assembler,
    _format_brand_style_json,
    _format_product_style_json,
)
from app.services.pipeline.llm_schemas import Stage1Blueprint, ScentProfile, BlueprintScene, SceneDescription


@pytest.fixture
def sample_stage1_blueprint():
    """Create a sample Stage 1 blueprint with 5 scenes."""
    scenes = []
    for i in range(1, 6):
        scenes.append(BlueprintScene(
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
        ))
    
    return Stage1Blueprint(
        framework="AIDA",
        total_duration_seconds=15,
        reference_image_path="test.jpg",
        reference_image_usage="inspiration",
        style_tone="cinematic",
        scenes=scenes,
        music={"track": "test.mp3"},
    )


@pytest.fixture
def sample_scent_profile():
    """Create a sample Stage 2 scent profile."""
    return ScentProfile(
        scent_profile_source="inferred",
        top_notes=["lemon", "bergamot"],
        heart_notes=["lavender", "jasmine"],
        base_notes=["musk", "amber"],
        lighting_cues="soft golden hour",
        color_palette="warm amber and gold",
        motion_physics="smooth, flowing",
        surface_textures="silk and satin",
        atmosphere_density="airy, light",
        sound_motifs="gentle ambient",
        emotional_register="calm, serene",
    )


@pytest.fixture
def sample_brand_style_json():
    """Create a sample brand style JSON."""
    return {
        "color_palette": {
            "primary_colors": ["#FF5733", "#33FF57"],
            "secondary_colors": ["#3357FF"],
            "accent_colors": ["#FF33F5"],
        },
        "visual_style": {
            "aesthetic": "modern minimalist",
            "mood": "sophisticated",
            "composition_style": "centered",
        },
        "lighting_cues": "dramatic studio lighting",
        "texture_surfaces": "matte finish",
        "atmosphere_density": "dense, rich",
        "brand_markers": ["logo top-right", "minimalist design"],
    }


@pytest.fixture
def sample_product_style_json():
    """Create a sample product style JSON."""
    return {
        "product_characteristics": {
            "form_factor": "bottle",
            "material_appearance": "frosted glass",
            "surface_quality": "matte",
        },
        "visual_style": {
            "composition": "centered",
            "background_treatment": "white gradient",
            "perspective": "eye_level",
        },
        "color_profile": {
            "dominant_colors": ["#FFFFFF", "#000000"],
            "contrast_level": "high",
        },
        "product_usage_context": "luxury perfume bottle in lifestyle setting",
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response with 5 scenes."""
    return """Scene 1: Opening
A cinematic shot of a perfume bottle in golden hour lighting.

Scene 2: Discovery
The bottle is revealed with dramatic lighting.

Scene 3: Experience
Someone uses the perfume in an elegant setting.

Scene 4: Transformation
The mood shifts to show the perfume's effect.

Scene 5: Closing
Final shot of the bottle with brand colors."""


@patch("app.services.pipeline.stage3_scene_assembler.call_chat_model")
@pytest.mark.asyncio
async def test_run_stage3_without_brand_style(
    mock_call_chat_model,
    sample_stage1_blueprint,
    sample_scent_profile,
    mock_llm_response,
):
    """Test Stage 3 scene assembler without brand/product style JSON (backward compatibility)."""
    mock_call_chat_model.return_value = mock_llm_response
    
    result = await run_stage3_scene_assembler(
        stage1_blueprint=sample_stage1_blueprint,
        scent_profile=sample_scent_profile,
    )
    
    assert len(result) == 5
    assert all(isinstance(scene, str) for scene in result)
    mock_call_chat_model.assert_called_once()


@patch("app.services.pipeline.stage3_scene_assembler.call_chat_model")
@pytest.mark.asyncio
async def test_run_stage3_with_brand_style(
    mock_call_chat_model,
    sample_stage1_blueprint,
    sample_scent_profile,
    sample_brand_style_json,
    mock_llm_response,
):
    """Test Stage 3 scene assembler with brand style JSON."""
    mock_call_chat_model.return_value = mock_llm_response
    
    result = await run_stage3_scene_assembler(
        stage1_blueprint=sample_stage1_blueprint,
        scent_profile=sample_scent_profile,
        brand_style_json=sample_brand_style_json,
    )
    
    assert len(result) == 5
    # Verify brand style JSON was included in the prompt
    call_args = mock_call_chat_model.call_args
    user_message = call_args[1]["messages"][1]["content"]
    assert "BRAND STYLE INFORMATION" in user_message
    assert "modern minimalist" in user_message  # From visual_style.aesthetic
    assert "#FF5733" in user_message  # From color_palette.primary_colors
    mock_call_chat_model.assert_called_once()


@patch("app.services.pipeline.stage3_scene_assembler.call_chat_model")
@pytest.mark.asyncio
async def test_run_stage3_with_product_style(
    mock_call_chat_model,
    sample_stage1_blueprint,
    sample_scent_profile,
    sample_product_style_json,
    mock_llm_response,
):
    """Test Stage 3 scene assembler with product style JSON."""
    mock_call_chat_model.return_value = mock_llm_response
    
    result = await run_stage3_scene_assembler(
        stage1_blueprint=sample_stage1_blueprint,
        scent_profile=sample_scent_profile,
        product_style_json=sample_product_style_json,
    )
    
    assert len(result) == 5
    # Verify product style JSON was included in the prompt
    call_args = mock_call_chat_model.call_args
    user_message = call_args[1]["messages"][1]["content"]
    assert "PRODUCT STYLE INFORMATION" in user_message
    assert "bottle" in user_message  # From product_characteristics.form_factor
    assert "frosted glass" in user_message  # From product_characteristics.material_appearance
    mock_call_chat_model.assert_called_once()


@patch("app.services.pipeline.stage3_scene_assembler.call_chat_model")
@pytest.mark.asyncio
async def test_run_stage3_with_both_brand_and_product_style(
    mock_call_chat_model,
    sample_stage1_blueprint,
    sample_scent_profile,
    sample_brand_style_json,
    sample_product_style_json,
    mock_llm_response,
):
    """Test Stage 3 scene assembler with both brand and product style JSON."""
    mock_call_chat_model.return_value = mock_llm_response
    
    result = await run_stage3_scene_assembler(
        stage1_blueprint=sample_stage1_blueprint,
        scent_profile=sample_scent_profile,
        brand_style_json=sample_brand_style_json,
        product_style_json=sample_product_style_json,
    )
    
    assert len(result) == 5
    # Verify both brand and product style JSON were included
    call_args = mock_call_chat_model.call_args
    user_message = call_args[1]["messages"][1]["content"]
    assert "BRAND STYLE INFORMATION" in user_message
    assert "PRODUCT STYLE INFORMATION" in user_message
    assert "modern minimalist" in user_message  # Brand style
    assert "bottle" in user_message  # Product style
    mock_call_chat_model.assert_called_once()


def test_format_brand_style_json(sample_brand_style_json):
    """Test formatting brand style JSON to text."""
    result = _format_brand_style_json(sample_brand_style_json)
    
    assert "Color Palette:" in result
    assert "#FF5733" in result
    assert "Visual Style:" in result
    assert "modern minimalist" in result
    assert "Lighting cues:" in result
    assert "dramatic studio lighting" in result


def test_format_brand_style_json_empty():
    """Test formatting empty brand style JSON."""
    result = _format_brand_style_json({})
    assert result == ""


def test_format_product_style_json(sample_product_style_json):
    """Test formatting product style JSON to text."""
    result = _format_product_style_json(sample_product_style_json)
    
    assert "Product Characteristics:" in result
    assert "bottle" in result
    assert "frosted glass" in result
    assert "Visual Style:" in result
    assert "centered" in result
    assert "Color Profile:" in result
    assert "#FFFFFF" in result


def test_format_product_style_json_empty():
    """Test formatting empty product style JSON."""
    result = _format_product_style_json({})
    assert result == ""


@pytest.mark.asyncio
async def test_run_stage3_invalid_scene_count(sample_scent_profile):
    """Test Stage 3 scene assembler with invalid scene count."""
    # Create blueprint with wrong number of scenes
    scenes = [
        BlueprintScene(
            scene_number=1,
            stage="Scene 1",
            duration_seconds=3,
            scene_description=SceneDescription(
                visual="Visual 1",
                action="Action 1",
                camera="Camera 1",
                lighting="Lighting 1",
                mood="Mood 1",
                product_usage="Product usage 1",
            ),
            sound_design="Sound 1",
            voiceover="Voiceover 1",
            overlay_text="Overlay 1",
        )
    ]
    
    blueprint = Stage1Blueprint(
        framework="AIDA",
        total_duration_seconds=3,
        reference_image_path="test.jpg",
        reference_image_usage="inspiration",
        style_tone="cinematic",
        scenes=scenes,
        music={"track": "test.mp3"},
    )
    
    with pytest.raises(ValueError, match="Stage 1 must contain exactly 5 scenes"):
        await run_stage3_scene_assembler(
            stage1_blueprint=blueprint,
            scent_profile=sample_scent_profile,
        )

