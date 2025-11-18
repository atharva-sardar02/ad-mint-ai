"""
Unit tests for unified narrative generation in storyboard prompt enhancement.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.pipeline.storyboard_prompt_enhancement import (
    _generate_unified_narrative,
    _narrative_json_to_markdown,
    NARRATIVE_CREATIVE_DIRECTOR_SYSTEM_PROMPT,
    NARRATIVE_EDITOR_SYSTEM_PROMPT
)


@pytest.fixture
def mock_visual_elements():
    """Mock visual elements extracted from reference image."""
    return {
        "brand_identity": {
            "brand_name": "Test Brand",
            "brand_colors": ["#FF0000", "#00FF00"],
            "logo_style": "minimalist"
        },
        "product_details": {
            "bottle_shape": "rectangular, sleek design",
            "materials": "glass, metal cap",
            "distinctive_elements": "golden accents"
        },
        "color_palette": {
            "dominant_colors": ["#FF0000", "#00FF00"],
            "accent_colors": ["#FFFF00"],
            "scheme": "vibrant"
        },
        "style_aesthetic": {
            "visual_style": "luxury",
            "mood": "elegant, sophisticated",
            "composition": "centered, balanced",
            "lighting_characteristics": "soft, warm"
        },
        "composition_elements": {
            "framing": "close-up",
            "perspective": "eye-level",
            "background_style": "minimal"
        }
    }


@pytest.fixture
def mock_narrative_json():
    """Mock narrative JSON structure."""
    return {
        "overall_story": {
            "narrative": "This is a test narrative describing the complete ad story following the Sensory Journey framework. It tells a compelling story of discovery, transformation, and desire.",
            "framework": "Sensory Journey",
            "total_scenes": 3,
            "target_duration": 15
        },
        "emotional_arc": {
            "scene_1": {
                "scene_type": "Discovery",
                "emotional_state": "Anticipation, mystery, curiosity",
                "visual_mood": "Abstract, mysterious, ethereal",
                "product_visibility": "hidden",
                "narrative_purpose": "Create intrigue and anticipation"
            },
            "scene_2": {
                "scene_type": "Transformation",
                "emotional_state": "Recognition, connection, understanding",
                "visual_mood": "Product-focused, revealing, engaging",
                "product_visibility": "partial",
                "narrative_purpose": "Build connection with product"
            },
            "scene_3": {
                "scene_type": "Desire",
                "emotional_state": "Aspiration, desire, action",
                "visual_mood": "Lifestyle, elegant, aspirational",
                "product_visibility": "full",
                "narrative_purpose": "Inspire action and desire"
            }
        },
        "scene_connections": {
            "scene_1_to_2": {
                "narrative_transition": "Story moves from mystery to revelation",
                "visual_transition": "Visuals evolve from abstract to concrete",
                "emotional_transition": "Emotions shift from curiosity to recognition"
            },
            "scene_2_to_3": {
                "narrative_transition": "Story moves from connection to aspiration",
                "visual_transition": "Visuals evolve from product-focused to lifestyle",
                "emotional_transition": "Emotions shift from recognition to desire"
            }
        },
        "visual_progression": {
            "scene_1": "Abstract shapes, shadows, reflections, mysterious lighting",
            "scene_2": "Product details emerge, clearer composition, focused lighting",
            "scene_3": "Full product reveal, lifestyle integration, aspirational setting"
        },
        "product_reveal_strategy": {
            "scene_1": "Product hidden or very subtle (abstract shapes suggesting product)",
            "scene_2": "Product partially visible (side angle, close-up details, application)",
            "scene_3": "Product fully visible (hero shot, lifestyle integration)"
        },
        "brand_narrative": {
            "brand_identity": "Luxury brand with minimalist aesthetic",
            "color_palette": {
                "dominant_colors": ["#FF0000", "#00FF00"],
                "usage_across_scenes": "Colors used consistently to maintain brand identity"
            },
            "style_consistency": "Maintains elegant, sophisticated style throughout",
            "brand_message": "Quality and sophistication"
        }
    }


@pytest.fixture
def mock_openai_response_narrative(mock_narrative_json):
    """Mock OpenAI response for narrative generation."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = json.dumps(mock_narrative_json)
    return response


@pytest.fixture
def mock_openai_response_critique():
    """Mock OpenAI response for narrative critique."""
    critique_result = {
        "scores": {
            "narrative_coherence": 85,
            "emotional_arc": 82,
            "scene_connections": 78,
            "visual_progression": 88,
            "brand_integration": 90,
            "framework_alignment": 85,
            "overall": 84.7
        },
        "critique": "The narrative is well-structured and follows the framework correctly.",
        "improvements": ["Add more detail to scene transitions", "Strengthen brand message integration"]
    }
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = json.dumps(critique_result)
    return response


def test_narrative_json_to_markdown(mock_narrative_json):
    """Test conversion of narrative JSON to markdown format."""
    md = _narrative_json_to_markdown(mock_narrative_json)
    
    # Verify markdown structure
    assert "# Unified Narrative: Ad Story" in md
    assert "## Overall Ad Story" in md
    assert "## Emotional Arc" in md
    assert "## Scene Connections" in md
    assert "## Visual Progression" in md
    assert "## Product Reveal Strategy" in md
    assert "## Brand Narrative" in md
    
    # Verify content
    assert "Sensory Journey" in md
    assert "Discovery" in md
    assert "Transformation" in md
    assert "Desire" in md
    assert "Anticipation, mystery, curiosity" in md


@pytest.mark.asyncio
async def test_generate_unified_narrative_success(
    mock_visual_elements,
    mock_openai_response_narrative,
    mock_openai_response_critique,
    tmp_path
):
    """Test successful unified narrative generation."""
    original_prompt = "Create a luxury perfume advertisement"
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    
    with patch("app.services.pipeline.storyboard_prompt_enhancement.openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock responses for both agents
        mock_client.chat.completions.create = MagicMock(
            side_effect=[mock_openai_response_narrative, mock_openai_response_critique]
        )
        
        # Mock settings
        with patch("app.services.pipeline.storyboard_prompt_enhancement.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            
            result = await _generate_unified_narrative(
                original_prompt=original_prompt,
                visual_elements=mock_visual_elements,
                num_scenes=3,
                max_iterations=3,
                score_threshold=85.0,
                trace_dir=trace_dir
            )
            
            # Verify result structure
            assert "narrative_json" in result
            assert "narrative_md" in result
            assert "iterations" in result
            assert "final_score" in result
            
            # Verify narrative JSON structure
            narrative_json = result["narrative_json"]
            assert "overall_story" in narrative_json
            assert "emotional_arc" in narrative_json
            assert "scene_connections" in narrative_json
            assert "visual_progression" in narrative_json
            assert "product_reveal_strategy" in narrative_json
            assert "brand_narrative" in narrative_json
            
            # Verify markdown was generated
            assert len(result["narrative_md"]) > 0
            assert "# Unified Narrative" in result["narrative_md"]
            
            # Verify iterations
            assert len(result["iterations"]) == 1
            assert result["iterations"][0]["iteration"] == 1
            assert "scores" in result["iterations"][0]
            
            # Verify trace files were created
            assert (trace_dir / "narrative_iteration_1_agent1.txt").exists()
            assert (trace_dir / "narrative_iteration_1_agent2.txt").exists()


@pytest.mark.asyncio
async def test_generate_unified_narrative_iteration_loop(
    mock_visual_elements,
    mock_openai_response_narrative,
    tmp_path
):
    """Test narrative generation with multiple iterations."""
    original_prompt = "Create a luxury perfume advertisement"
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    
    # Create critique responses with increasing scores
    critique_responses = []
    for i in range(3):
        critique_result = {
            "scores": {
                "narrative_coherence": 70 + i * 5,
                "emotional_arc": 75 + i * 3,
                "scene_connections": 65 + i * 5,
                "visual_progression": 80 + i * 3,
                "brand_integration": 85 + i * 2,
                "framework_alignment": 80 + i * 3,
                "overall": 75.0 + i * 4.0
            },
            "critique": f"Iteration {i+1} critique",
            "improvements": [f"Improvement {i+1}"]
        }
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message = MagicMock()
        response.choices[0].message.content = json.dumps(critique_result)
        critique_responses.append(response)
    
    with patch("app.services.pipeline.storyboard_prompt_enhancement.openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock responses: 3 narrative generations + 3 critiques
        mock_responses = []
        for i in range(3):
            mock_responses.append(mock_openai_response_narrative)
            mock_responses.append(critique_responses[i])
        
        mock_client.chat.completions.create = MagicMock(side_effect=mock_responses)
        
        with patch("app.services.pipeline.storyboard_prompt_enhancement.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            
            result = await _generate_unified_narrative(
                original_prompt=original_prompt,
                visual_elements=mock_visual_elements,
                num_scenes=3,
                max_iterations=3,
                score_threshold=85.0,
                trace_dir=trace_dir
            )
            
            # Verify all iterations were executed
            assert len(result["iterations"]) == 3
            
            # Verify scores improved
            scores = [it["scores"]["overall"] for it in result["iterations"]]
            assert scores[0] < scores[1] < scores[2]


@pytest.mark.asyncio
async def test_generate_unified_narrative_early_stopping(
    mock_visual_elements,
    mock_openai_response_narrative,
    tmp_path
):
    """Test narrative generation with early stopping when threshold is met."""
    original_prompt = "Create a luxury perfume advertisement"
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    
    # Create critique response with high score (above threshold)
    critique_result = {
        "scores": {
            "narrative_coherence": 90,
            "emotional_arc": 88,
            "scene_connections": 85,
            "visual_progression": 92,
            "brand_integration": 90,
            "framework_alignment": 88,
            "overall": 89.0
        },
        "critique": "Excellent narrative",
        "improvements": []
    }
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = json.dumps(critique_result)
    
    with patch("app.services.pipeline.storyboard_prompt_enhancement.openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Only one iteration should be executed (narrative + critique)
        mock_client.chat.completions.create = MagicMock(
            side_effect=[mock_openai_response_narrative, response]
        )
        
        with patch("app.services.pipeline.storyboard_prompt_enhancement.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            
            result = await _generate_unified_narrative(
                original_prompt=original_prompt,
                visual_elements=mock_visual_elements,
                num_scenes=3,
                max_iterations=3,
                score_threshold=85.0,
                trace_dir=trace_dir
            )
            
            # Verify only one iteration was executed (early stopping)
            assert len(result["iterations"]) == 1
            assert result["iterations"][0]["scores"]["overall"] >= 85.0


@pytest.mark.asyncio
async def test_generate_unified_narrative_missing_api_key(mock_visual_elements):
    """Test narrative generation fails when API key is missing."""
    with patch("app.services.pipeline.storyboard_prompt_enhancement.settings") as mock_settings:
        mock_settings.OPENAI_API_KEY = None
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY not configured"):
            await _generate_unified_narrative(
                original_prompt="test",
                visual_elements=mock_visual_elements,
                num_scenes=3
            )


@pytest.mark.asyncio
async def test_generate_unified_narrative_invalid_structure(
    mock_visual_elements,
    tmp_path
):
    """Test narrative generation fails with invalid JSON structure."""
    original_prompt = "Create a luxury perfume advertisement"
    trace_dir = tmp_path / "trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    
    # Create response with missing required keys
    invalid_narrative = {
        "overall_story": {
            "narrative": "Test"
        }
        # Missing other required keys
    }
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = json.dumps(invalid_narrative)
    
    with patch("app.services.pipeline.storyboard_prompt_enhancement.openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = MagicMock(return_value=response)
        
        with patch("app.services.pipeline.storyboard_prompt_enhancement.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            
            with pytest.raises(ValueError, match="Missing required key in narrative"):
                await _generate_unified_narrative(
                    original_prompt=original_prompt,
                    visual_elements=mock_visual_elements,
                    num_scenes=3,
                    trace_dir=trace_dir
                )


@pytest.mark.asyncio
async def test_narrative_context_integration_in_scene_prompts(
    mock_visual_elements,
    mock_narrative_json
):
    """Test that narrative context is properly integrated into scene prompt generation."""
    from app.services.pipeline.storyboard_prompt_enhancement import _cinematic_creative_enhance
    
    original_prompt = "Create a luxury perfume advertisement"
    
    # Mock OpenAI response for scene prompt generation
    scene_prompt_response = {
        "start_frame_prompt": "A mysterious abstract scene with golden light",
        "end_frame_prompt": "Product emerges from shadows",
        "motion_description": "Camera slowly reveals the product"
    }
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = json.dumps(scene_prompt_response)
    
    with patch("app.services.pipeline.storyboard_prompt_enhancement.openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = MagicMock(return_value=response)
        
        with patch("app.services.pipeline.storyboard_prompt_enhancement.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            
            # Test with narrative context
            result = await _cinematic_creative_enhance(
                original_prompt=original_prompt,
                scene_number=1,
                scene_type="Discovery",
                product_visibility="hidden",
                visual_elements=mock_visual_elements,
                previous_feedback=None,
                unified_narrative=mock_narrative_json,
                model="gpt-4-turbo"
            )
            
            # Verify narrative context was included in the API call
            call_args = mock_client.chat.completions.create.call_args
            user_message = call_args[1]["messages"][1]["content"]
            
            # Verify narrative elements are in the prompt
            assert "UNIFIED NARRATIVE CONTEXT" in user_message
            assert "Overall Story" in user_message
            assert "Scene Emotional State" in user_message
            assert "Scene Visual Mood" in user_message
            assert "Visual Progression" in user_message
            assert "Product Reveal Strategy" in user_message
            assert "Brand Narrative" in user_message
            
            # Verify result structure
            assert "start_frame_prompt" in result
            assert "end_frame_prompt" in result
            assert "motion_description" in result


@pytest.mark.asyncio
async def test_narrative_context_optional_parameter():
    """Test that narrative context is optional (backward compatibility)."""
    from app.services.pipeline.storyboard_prompt_enhancement import _cinematic_creative_enhance
    
    original_prompt = "Create a luxury perfume advertisement"
    mock_visual_elements = {
        "brand_identity": {"brand_colors": []},
        "product_details": {"bottle_shape": "test"},
        "color_palette": {"scheme": "test"},
        "style_aesthetic": {"visual_style": "test", "mood": "test"}
    }
    
    scene_prompt_response = {
        "start_frame_prompt": "Test start",
        "end_frame_prompt": "Test end",
        "motion_description": "Test motion"
    }
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = json.dumps(scene_prompt_response)
    
    with patch("app.services.pipeline.storyboard_prompt_enhancement.openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create = MagicMock(return_value=response)
        
        with patch("app.services.pipeline.storyboard_prompt_enhancement.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            
            # Test without narrative context (should still work)
            result = await _cinematic_creative_enhance(
                original_prompt=original_prompt,
                scene_number=1,
                scene_type="Discovery",
                product_visibility="hidden",
                visual_elements=mock_visual_elements,
                previous_feedback=None,
                unified_narrative=None,  # No narrative
                model="gpt-4-turbo"
            )
            
            # Verify it still works
            assert "start_frame_prompt" in result
            assert "end_frame_prompt" in result
            assert "motion_description" in result


@pytest.mark.asyncio
async def test_metadata_includes_narrative_references(tmp_path):
    """Test that storyboard metadata includes narrative references."""
    from app.services.pipeline.storyboard_service import create_storyboard
    from app.services.pipeline.storyboard_prompt_enhancement import enhance_storyboard_prompts
    
    # Create a mock reference image
    reference_image = tmp_path / "reference.png"
    reference_image.write_bytes(b"fake image data")
    
    # Mock the enhancement result to include narrative
    mock_narrative_json = {
        "overall_story": {
            "narrative": "Test narrative for metadata integration test"
        },
        "emotional_arc": {},
        "scene_connections": {},
        "visual_progression": {},
        "product_reveal_strategy": {},
        "brand_narrative": {}
    }
    
    with patch("app.services.pipeline.storyboard_service.enhance_storyboard_prompts") as mock_enhance, \
         patch("app.services.pipeline.storyboard_service.generate_images") as mock_generate:
        
        from app.services.pipeline.storyboard_prompt_enhancement import (
            StoryboardEnhancementResult,
            ScenePromptSet
        )
        from app.services.pipeline.image_generation import ImageGenerationResult
        
        # Mock enhancement result with narrative
        mock_enhance_result = StoryboardEnhancementResult(
            original_prompt="test prompt",
            reference_image_path=str(reference_image),
            extracted_visual_elements={},
            scene_prompts=[
                ScenePromptSet(
                    scene_number=1,
                    scene_type="Discovery",
                    start_frame_prompt="start",
                    end_frame_prompt="end",
                    motion_description="motion",
                    product_visibility="hidden"
                )
            ],
            iterations=[],
            final_scores={},
            total_iterations=0,
            unified_narrative_md="# Test",
            unified_narrative_json=mock_narrative_json,
            unified_narrative_path=str(tmp_path / "unified_narrative.md"),
            narrative_iterations=[]
        )
        mock_enhance.return_value = mock_enhance_result
        
        # Mock image generation
        mock_image_result = ImageGenerationResult(
            image_path=str(tmp_path / "test.png"),
            image_url=None,
            model_name="test",
            seed=None,
            aspect_ratio="16:9",
            prompt="test",
            cost=0.01,
            generation_time=1.0,
            timestamp="2025-01-01"
        )
        mock_generate.return_value = [mock_image_result]
        
        # Create storyboard
        result = await create_storyboard(
            prompt="test prompt",
            num_clips=1,
            reference_image_path=str(reference_image),
            output_dir=tmp_path
        )
        
        # Verify metadata includes narrative references
        assert "unified_narrative_path" in result.metadata
        assert result.metadata["unified_narrative_path"] is not None
        assert "narrative_summary" in result.metadata
        assert result.metadata["narrative_summary"] is not None

