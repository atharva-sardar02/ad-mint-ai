"""
Unit tests for scene planning module.
"""
import pytest
from app.schemas.generation import AdSpecification, BrandGuidelines, AdSpec, Scene, TextOverlay, ScenePlan
from app.services.pipeline.scene_planning import plan_scenes


@pytest.fixture
def sample_ad_spec_pas():
    """Sample AdSpecification with PAS framework."""
    return AdSpecification(
        product_description="A premium coffee maker that brews perfect espresso",
        brand_guidelines=BrandGuidelines(
            brand_name="CoffeePro",
            brand_colors=["#8B4513", "#D2691E"],
            visual_style_keywords="luxury, modern, elegant",
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
                visual_prompt="Show someone struggling with a cheap coffee maker",
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
                visual_prompt="Show the frustration of inconsistent coffee",
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
                visual_prompt="Show CoffeePro making perfect espresso",
                text_overlay=TextOverlay(
                    text="CoffeePro - Perfect every time",
                    position="bottom",
                    font_size=48,
                    color="#D2691E",
                    animation="fade_in"
                ),
                duration=5
            )
        ]
    )


@pytest.fixture
def sample_ad_spec_bab():
    """Sample AdSpecification with BAB framework."""
    return AdSpecification(
        product_description="A revolutionary skincare serum that transforms your skin",
        brand_guidelines=BrandGuidelines(
            brand_name="GlowUp",
            brand_colors=["#FF69B4", "#FFD700"],
            visual_style_keywords="radiant, transformative, luxurious",
            mood="confident"
        ),
        ad_specifications=AdSpec(
            target_audience="Beauty enthusiasts",
            call_to_action="Transform your skin",
            tone="inspiring"
        ),
        framework="BAB",
        scenes=[
            Scene(
                scene_number=1,
                scene_type="Before",
                visual_prompt="Show dull, tired skin before using the product",
                text_overlay=TextOverlay(
                    text="Before",
                    position="top",
                    font_size=48,
                    color="#FF69B4",
                    animation="fade_in"
                ),
                duration=5
            ),
            Scene(
                scene_number=2,
                scene_type="After",
                visual_prompt="Show radiant, glowing skin after using GlowUp",
                text_overlay=TextOverlay(
                    text="After",
                    position="center",
                    font_size=48,
                    color="#FFD700",
                    animation="slide_up"
                ),
                duration=5
            ),
            Scene(
                scene_number=3,
                scene_type="Bridge",
                visual_prompt="Show GlowUp serum being applied",
                text_overlay=TextOverlay(
                    text="GlowUp - Transform your skin",
                    position="bottom",
                    font_size=48,
                    color="#FF69B4",
                    animation="fade_in"
                ),
                duration=5
            )
        ]
    )


@pytest.fixture
def sample_ad_spec_aida():
    """Sample AdSpecification with AIDA framework."""
    return AdSpecification(
        product_description="A smart fitness tracker",
        brand_guidelines=BrandGuidelines(
            brand_name="FitTrack",
            brand_colors=["#00FF00", "#000000"],
            visual_style_keywords="sporty, energetic, modern",
            mood="motivational"
        ),
        ad_specifications=AdSpec(
            target_audience="Fitness enthusiasts",
            call_to_action="Start your journey",
            tone="energetic"
        ),
        framework="AIDA",
        scenes=[
            Scene(
                scene_number=1,
                scene_type="Attention",
                visual_prompt="Dynamic shot of athlete running",
                text_overlay=TextOverlay(
                    text="Transform your fitness",
                    position="top",
                    font_size=48,
                    color="#00FF00",
                    animation="fade_in"
                ),
                duration=4
            ),
            Scene(
                scene_number=2,
                scene_type="Interest",
                visual_prompt="Show FitTrack features",
                text_overlay=TextOverlay(
                    text="Track everything",
                    position="center",
                    font_size=48,
                    color="#00FF00",
                    animation="slide_up"
                ),
                duration=4
            ),
            Scene(
                scene_number=3,
                scene_type="Desire",
                visual_prompt="Show fitness goals achieved",
                text_overlay=TextOverlay(
                    text="Reach your goals",
                    position="center",
                    font_size=48,
                    color="#00FF00",
                    animation="fade_in"
                ),
                duration=4
            ),
            Scene(
                scene_number=4,
                scene_type="Action",
                visual_prompt="Show FitTrack product",
                text_overlay=TextOverlay(
                    text="Start your journey",
                    position="bottom",
                    font_size=48,
                    color="#00FF00",
                    animation="fade_in"
                ),
                duration=3
            )
        ]
    )


def test_plan_scenes_pas(sample_ad_spec_pas):
    """Test scene planning with PAS framework."""
    scene_plan = plan_scenes(sample_ad_spec_pas, target_duration=15)
    
    assert isinstance(scene_plan, ScenePlan)
    assert scene_plan.framework == "PAS"
    assert len(scene_plan.scenes) == 3
    assert scene_plan.total_duration == 15
    
    # Check scene types match PAS framework
    assert scene_plan.scenes[0].scene_type == "Problem"
    assert scene_plan.scenes[1].scene_type == "Agitation"
    assert scene_plan.scenes[2].scene_type == "Solution"


def test_plan_scenes_bab(sample_ad_spec_bab):
    """Test scene planning with BAB framework."""
    scene_plan = plan_scenes(sample_ad_spec_bab, target_duration=15)
    
    assert isinstance(scene_plan, ScenePlan)
    assert scene_plan.framework == "BAB"
    assert len(scene_plan.scenes) == 3
    assert scene_plan.total_duration == 15
    
    # Check scene types match BAB framework
    assert scene_plan.scenes[0].scene_type == "Before"
    assert scene_plan.scenes[1].scene_type == "After"
    assert scene_plan.scenes[2].scene_type == "Bridge"


def test_plan_scenes_aida(sample_ad_spec_aida):
    """Test scene planning with AIDA framework."""
    scene_plan = plan_scenes(sample_ad_spec_aida, target_duration=15)
    
    assert isinstance(scene_plan, ScenePlan)
    assert scene_plan.framework == "AIDA"
    assert len(scene_plan.scenes) == 4
    assert scene_plan.total_duration == 15
    
    # Check scene types match AIDA framework
    assert scene_plan.scenes[0].scene_type == "Attention"
    assert scene_plan.scenes[1].scene_type == "Interest"
    assert scene_plan.scenes[2].scene_type == "Desire"
    assert scene_plan.scenes[3].scene_type == "Action"


def test_plan_scenes_enriches_visual_prompts(sample_ad_spec_pas):
    """Test that visual prompts are enriched with brand keywords."""
    scene_plan = plan_scenes(sample_ad_spec_pas, target_duration=15)
    
    # Check that visual prompts contain brand keywords (enrichment adds these)
    for scene in scene_plan.scenes:
        assert "luxury" in scene.visual_prompt.lower() or "modern" in scene.visual_prompt.lower() or "elegant" in scene.visual_prompt.lower()
        assert "sophisticated" in scene.visual_prompt.lower()  # Mood is added during enrichment
        assert "#8B4513" in scene.visual_prompt or "#D2691E" in scene.visual_prompt  # Brand colors are added


def test_plan_scenes_adjusts_durations(sample_ad_spec_pas):
    """Test that scene durations are adjusted to match target."""
    # Create spec with wrong total duration (using valid durations 3-7)
    # Total = 7 + 7 + 7 = 21, target = 15
    ad_spec = sample_ad_spec_pas
    # Create new Scene objects with valid durations (max 7)
    ad_spec.scenes[0] = Scene(
        scene_number=1,
        scene_type="Problem",
        visual_prompt=ad_spec.scenes[0].visual_prompt,
        text_overlay=ad_spec.scenes[0].text_overlay,
        duration=7  # Valid max duration
    )
    ad_spec.scenes[1] = Scene(
        scene_number=2,
        scene_type="Agitation",
        visual_prompt=ad_spec.scenes[1].visual_prompt,
        text_overlay=ad_spec.scenes[1].text_overlay,
        duration=7
    )
    ad_spec.scenes[2] = Scene(
        scene_number=3,
        scene_type="Solution",
        visual_prompt=ad_spec.scenes[2].visual_prompt,
        text_overlay=ad_spec.scenes[2].text_overlay,
        duration=7
    )
    
    scene_plan = plan_scenes(ad_spec, target_duration=15)
    
    assert scene_plan.total_duration == 15
    assert sum(scene.duration for scene in scene_plan.scenes) == 15
    # Verify all durations are within valid range (3-7)
    for scene in scene_plan.scenes:
        assert 3 <= scene.duration <= 7

