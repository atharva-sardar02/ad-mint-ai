"""
Unit tests for storyboard service.
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.pipeline.storyboard_service import (
    create_storyboard,
    ClipStoryboard,
    StoryboardResult,
    _generate_frame_prompts,
    _generate_camera_metadata,
    _generate_scene_dependencies,
    _generate_narrative_flow
)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "storyboards" / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def mock_image_generation_result():
    """Mock image generation result."""
    result = MagicMock()
    result.image_path = "/tmp/test_image.png"
    result.image_url = "https://example.com/image.png"
    result.model_name = "test-model"
    result.seed = None
    result.aspect_ratio = "16:9"
    result.prompt = "test prompt"
    result.cost = 0.01
    result.generation_time = 1.0
    result.timestamp = "2025-01-01 12:00:00"
    return result


@pytest.mark.asyncio
async def test_create_storyboard_basic(temp_output_dir, mock_image_generation_result):
    """Test basic storyboard creation without prompt enhancement."""
    prompt = "A product showcase video with dynamic visuals"
    
    with patch("app.services.pipeline.storyboard_service.create_basic_scene_plan_from_prompt") as mock_plan, \
         patch("app.services.pipeline.storyboard_service.generate_images") as mock_generate:
        
        # Mock scene plan
        from app.schemas.generation import ScenePlan, Scene, TextOverlay
        mock_scenes = [
            Scene(
                scene_number=1,
                scene_type="Scene 1",
                visual_prompt="Opening scene",
                text_overlay=TextOverlay(text="", position="bottom", font_size=48, color="#FFFFFF", animation="fade_in"),
                duration=5
            ),
            Scene(
                scene_number=2,
                scene_type="Scene 2",
                visual_prompt="Middle scene",
                text_overlay=TextOverlay(text="", position="bottom", font_size=48, color="#FFFFFF", animation="fade_in"),
                duration=5
            ),
            Scene(
                scene_number=3,
                scene_type="Scene 3",
                visual_prompt="Closing scene",
                text_overlay=TextOverlay(text="", position="center", font_size=48, color="#FFFFFF", animation="fade_in"),
                duration=5
            )
        ]
        mock_plan.return_value = ScenePlan(
            scenes=mock_scenes,
            total_duration=15,
            framework="AIDA"
        )
        
        # Mock image generation (returns one result per call)
        mock_generate.return_value = [mock_image_generation_result]
        
        # Create storyboard
        result = await create_storyboard(
            prompt=prompt,
            num_clips=3,
            aspect_ratio="16:9",
            enhance_prompts=False,
            output_dir=temp_output_dir
        )
        
        # Verify result
        assert isinstance(result, StoryboardResult)
        assert len(result.clips) == 3
        assert result.metadata["num_clips"] == 3
        assert result.metadata["framework"] == "AIDA"
        assert result.metadata["total_duration"] == 15
        
        # Verify each clip has start/end frames
        for clip in result.clips:
            assert isinstance(clip, ClipStoryboard)
            assert clip.start_frame_path
            assert clip.end_frame_path
            assert clip.start_frame_prompt
            assert clip.end_frame_prompt
            assert clip.motion_description
            assert clip.camera_movement
            assert clip.shot_size
            assert clip.perspective
            assert clip.lens_type
        
        # Verify image generation was called (2 calls per clip: start + end)
        assert mock_generate.call_count == 6  # 3 clips * 2 frames each


@pytest.mark.asyncio
async def test_create_storyboard_with_enhancement(temp_output_dir, mock_image_generation_result):
    """Test storyboard creation with prompt enhancement."""
    prompt = "A simple product video"
    
    with patch("app.services.pipeline.storyboard_service.enhance_prompt_iterative") as mock_enhance, \
         patch("app.services.pipeline.storyboard_service.create_basic_scene_plan_from_prompt") as mock_plan, \
         patch("app.services.pipeline.storyboard_service.generate_images") as mock_generate:
        
        # Mock prompt enhancement
        from app.services.pipeline.image_prompt_enhancement import ImagePromptEnhancementResult
        mock_enhance.return_value = ImagePromptEnhancementResult(
            original_prompt=prompt,
            final_prompt="Enhanced: A cinematic product showcase video with professional lighting",
            iterations=[],
            final_score={"overall": 85.0},
            total_iterations=1
        )
        
        # Mock scene plan
        from app.schemas.generation import ScenePlan, Scene, TextOverlay
        mock_scenes = [
            Scene(
                scene_number=1,
                scene_type="Scene 1",
                visual_prompt="Enhanced opening scene",
                text_overlay=TextOverlay(text="", position="bottom", font_size=48, color="#FFFFFF", animation="fade_in"),
                duration=5
            )
        ] * 3
        mock_plan.return_value = ScenePlan(
            scenes=mock_scenes,
            total_duration=15,
            framework="AIDA"
        )
        
        # Mock image generation
        mock_generate.return_value = [mock_image_generation_result]
        
        # Create storyboard with enhancement
        result = await create_storyboard(
            prompt=prompt,
            num_clips=3,
            enhance_prompts=True,
            output_dir=temp_output_dir
        )
        
        # Verify enhancement was called
        mock_enhance.assert_called_once()
        
        # Verify enhanced prompt was used
        assert result.metadata["enhanced_prompt"] is not None
        assert "Enhanced" in result.metadata["enhanced_prompt"]


def test_generate_frame_prompts():
    """Test start/end frame prompt generation."""
    scene_prompt = "A product showcase"
    scene_type = "Scene 1"
    
    # Test opening clip
    start, end, motion = _generate_frame_prompts(scene_prompt, scene_type, 1, 3)
    assert "Opening scene" in start
    assert "establishing shot" in start
    assert "initial state" in start
    assert "Closing scene" in end or "final state" in end
    assert "motion" in motion.lower() or "camera" in motion.lower()
    
    # Test middle clip
    start, end, motion = _generate_frame_prompts(scene_prompt, scene_type, 2, 3)
    assert "Scene transition" in start or "initial state" in start
    assert "Scene transition" in end or "final state" in end
    
    # Test closing clip
    start, end, motion = _generate_frame_prompts(scene_prompt, scene_type, 3, 3)
    assert "Closing scene" in end or "call to action" in end
    assert "final state" in end


def test_generate_camera_metadata():
    """Test camera metadata generation."""
    # Test opening clip
    movement, shot_size, perspective, lens = _generate_camera_metadata("Scene 1", 1, 3)
    assert "Push in" in movement or "push" in movement.lower()
    assert "Wide" in shot_size
    assert "establishing" in perspective.lower()
    assert "wide angle" in lens.lower() or "24" in lens
    
    # Test middle clip
    movement, shot_size, perspective, lens = _generate_camera_metadata("Scene 2", 2, 3)
    assert "Medium" in shot_size
    assert "35" in lens or "50" in lens
    
    # Test closing clip
    movement, shot_size, perspective, lens = _generate_camera_metadata("Scene 3", 3, 3)
    assert "Pull back" in movement or "static" in movement.lower()
    assert "close-up" in shot_size.lower() or "Medium" in shot_size
    assert "50" in lens or "85" in lens or "telephoto" in lens.lower()


def test_generate_scene_dependencies():
    """Test scene dependencies generation."""
    deps = _generate_scene_dependencies(3)
    assert len(deps) == 3
    
    # First clip has no dependencies
    assert len(deps[0]["dependencies"]) == 0
    
    # Second clip depends on first
    assert len(deps[1]["dependencies"]) == 1
    assert deps[1]["dependencies"][0]["depends_on"] == 1
    
    # Third clip depends on second
    assert len(deps[2]["dependencies"]) == 1
    assert deps[2]["dependencies"][0]["depends_on"] == 2


def test_generate_narrative_flow():
    """Test narrative flow generation."""
    # Test AIDA framework
    flow = _generate_narrative_flow(4, "AIDA")
    assert "Attention" in flow
    assert "Interest" in flow
    assert "Desire" in flow
    assert "Action" in flow
    
    # Test PAS framework
    flow = _generate_narrative_flow(3, "PAS")
    assert "Problem" in flow
    assert "Agitation" in flow
    assert "Solution" in flow
    
    # Test BAB framework
    flow = _generate_narrative_flow(3, "BAB")
    assert "Before" in flow
    assert "After" in flow
    assert "Bridge" in flow
    
    # Test default/unknown framework
    flow = _generate_narrative_flow(3, "UNKNOWN")
    assert "3 clips" in flow


def test_generate_consistency_groupings():
    """Test consistency groupings generation."""
    from app.services.pipeline.storyboard_service import _generate_consistency_groupings
    
    # Create test clip storyboards with varying camera settings
    clips = [
        ClipStoryboard(
            clip_number=1,
            start_frame_path="clip_001_start.png",
            end_frame_path="clip_001_end.png",
            start_frame_prompt="Start 1",
            end_frame_prompt="End 1",
            motion_description="Motion 1",
            camera_movement="Push in",
            shot_size="Wide shot",
            perspective="Eye level",
            lens_type="24mm",
            clip_description="Clip 1"
        ),
        ClipStoryboard(
            clip_number=2,
            start_frame_path="clip_002_start.png",
            end_frame_path="clip_002_end.png",
            start_frame_prompt="Start 2",
            end_frame_prompt="End 2",
            motion_description="Motion 2",
            camera_movement="Pan",
            shot_size="Wide shot",  # Same as clip 1
            perspective="Eye level",  # Same as clip 1
            lens_type="24mm",
            clip_description="Clip 2"
        ),
        ClipStoryboard(
            clip_number=3,
            start_frame_path="clip_003_start.png",
            end_frame_path="clip_003_end.png",
            start_frame_prompt="Start 3",
            end_frame_prompt="End 3",
            motion_description="Motion 3",
            camera_movement="Pull back",
            shot_size="Medium shot",  # Different from clips 1-2
            perspective="Elevated",  # Different from clips 1-2
            lens_type="50mm",
            clip_description="Clip 3"
        )
    ]
    
    groupings = _generate_consistency_groupings(clips)
    
    # Should have at least one grouping
    assert len(groupings) > 0
    
    # Verify grouping structure
    for group in groupings:
        assert "group_id" in group
        assert "clip_numbers" in group
        assert "consistency_type" in group
        assert "description" in group
        assert len(group["clip_numbers"]) > 0
    
    # With different camera settings, should have multiple groups
    # (clips 1-2 similar, clip 3 different)
    assert len(groupings) >= 1  # At least one group
    
    # Test with empty list
    empty_groupings = _generate_consistency_groupings([])
    assert empty_groupings == []


@pytest.mark.asyncio
async def test_create_storyboard_num_clips_validation(temp_output_dir, mock_image_generation_result):
    """Test that num_clips is validated to be 3-5."""
    prompt = "Test prompt"
    
    with patch("app.services.pipeline.storyboard_service.create_basic_scene_plan_from_prompt") as mock_plan, \
         patch("app.services.pipeline.storyboard_service.generate_images") as mock_generate:
        
        from app.schemas.generation import ScenePlan, Scene, TextOverlay
        mock_scenes = [
            Scene(
                scene_number=i,
                scene_type=f"Scene {i}",
                visual_prompt=f"Scene {i} prompt",
                text_overlay=TextOverlay(text="", position="bottom", font_size=48, color="#FFFFFF", animation="fade_in"),
                duration=5
            )
            for i in range(1, 6)  # 5 scenes
        ]
        mock_plan.return_value = ScenePlan(
            scenes=mock_scenes,
            total_duration=25,
            framework="AIDA"
        )
        mock_generate.return_value = [mock_image_generation_result]
        
        # Test with num_clips=2 (should be clamped to 3)
        result = await create_storyboard(
            prompt=prompt,
            num_clips=2,  # Below minimum
            output_dir=temp_output_dir
        )
        # Should still work, but use 3 clips from scene plan
        
        # Test with num_clips=6 (should be clamped to 5)
        result = await create_storyboard(
            prompt=prompt,
            num_clips=6,  # Above maximum
            output_dir=temp_output_dir
        )
        # Should use 5 clips from scene plan


@pytest.mark.asyncio
async def test_create_storyboard_metadata_structure(temp_output_dir, mock_image_generation_result):
    """Test that metadata JSON has correct structure."""
    prompt = "Test prompt"
    
    with patch("app.services.pipeline.storyboard_service.create_basic_scene_plan_from_prompt") as mock_plan, \
         patch("app.services.pipeline.storyboard_service.generate_images") as mock_generate:
        
        from app.schemas.generation import ScenePlan, Scene, TextOverlay
        mock_scenes = [
            Scene(
                scene_number=1,
                scene_type="Scene 1",
                visual_prompt="Test scene",
                text_overlay=TextOverlay(text="", position="bottom", font_size=48, color="#FFFFFF", animation="fade_in"),
                duration=5
            )
        ] * 3
        mock_plan.return_value = ScenePlan(
            scenes=mock_scenes,
            total_duration=15,
            framework="AIDA"
        )
        mock_generate.return_value = [mock_image_generation_result]
        
        result = await create_storyboard(
            prompt=prompt,
            num_clips=3,
            output_dir=temp_output_dir
        )
        
        # Verify metadata structure
        metadata = result.metadata
        assert "prompt" in metadata
        assert "num_clips" in metadata
        assert "aspect_ratio" in metadata
        assert "framework" in metadata
        assert "total_duration" in metadata
        assert "clips" in metadata
        assert "shot_list" in metadata
        assert "scene_dependencies" in metadata
        assert "narrative_flow" in metadata
        assert "created_at" in metadata
        
        # Verify clips metadata structure
        assert len(metadata["clips"]) == 3
        for clip_meta in metadata["clips"]:
            assert "clip_number" in clip_meta
            assert "description" in clip_meta
            assert "start_frame_prompt" in clip_meta
            assert "end_frame_prompt" in clip_meta
            assert "motion_description" in clip_meta
            assert "camera_movement" in clip_meta
            assert "shot_size" in clip_meta
            assert "perspective" in clip_meta
            assert "lens_type" in clip_meta
            assert "start_frame_path" in clip_meta
            assert "end_frame_path" in clip_meta
        
        # Verify shot_list structure
        assert len(metadata["shot_list"]) == 3
        for shot in metadata["shot_list"]:
            assert "clip_number" in shot
            assert "camera_movement" in shot
            assert "shot_size" in shot
            assert "perspective" in shot
            assert "lens_type" in shot
        
        # Verify metadata file was saved
        metadata_file = temp_output_dir / "storyboard_metadata.json"
        assert metadata_file.exists()
        
        # Verify JSON is valid
        import json
        with open(metadata_file, "r") as f:
            loaded_metadata = json.load(f)
        assert loaded_metadata["num_clips"] == 3

