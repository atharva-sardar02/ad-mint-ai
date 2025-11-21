"""
Unit tests for video generation CLI service.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil

from app.services.pipeline.video_generation_cli import (
    generate_text_to_video,
    generate_image_to_video,
    generate_storyboard_videos,
    VideoGenerationResult,
    VideoMetadata,
    StoryboardVideoGenerationResult,
)
from app.services.pipeline.video_quality_scoring import (
    score_video,
    score_videos_batch,
    rank_videos_by_quality,
    calculate_overall_quality_score,
)


@pytest.fixture
def mock_video_generation():
    """Mock video generation function."""
    with patch('app.services.pipeline.video_generation_cli.generate_video_clip_with_model') as mock:
        yield mock


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_video_path(tmp_path):
    """Create a sample video file."""
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b"fake video content")
    return str(video_path)


@pytest.mark.asyncio
async def test_generate_text_to_video_success(mock_video_generation, temp_output_dir):
    """Test successful text-to-video generation."""
    # Mock video generation
    mock_video_generation.return_value = (
        str(temp_output_dir / "video_001.mp4"),
        "openai/sora-2"
    )
    
    # Create fake video file
    video_file = temp_output_dir / "video_001.mp4"
    video_file.write_bytes(b"fake video")
    
    result = await generate_text_to_video(
        prompt="A beautiful sunset",
        num_attempts=2,
        model_name="openai/sora-2",
        duration=5,
        output_dir=temp_output_dir,
    )
    
    assert result.mode == "text-to-video"
    assert len(result.videos) == 2
    assert result.generation_trace["mode"] == "text-to-video"
    assert result.generation_trace["prompt"] == "A beautiful sunset"
    assert mock_video_generation.call_count == 2


@pytest.mark.asyncio
async def test_generate_image_to_video_success(mock_video_generation, temp_output_dir):
    """Test successful image-to-video generation."""
    # Create hero frame
    hero_frame = temp_output_dir / "hero.png"
    hero_frame.write_bytes(b"fake image")
    
    # Mock video generation
    mock_video_generation.return_value = (
        str(temp_output_dir / "video_001.mp4"),
        "openai/sora-2"
    )
    
    # Create fake video file
    video_file = temp_output_dir / "video_001.mp4"
    video_file.write_bytes(b"fake video")
    
    result = await generate_image_to_video(
        hero_frame_path=str(hero_frame),
        motion_prompt="camera pans left",
        num_attempts=2,
        model_name="openai/sora-2",
        duration=5,
        output_dir=temp_output_dir,
    )
    
    assert result.mode == "image-to-video"
    assert result.hero_frame_path == str(hero_frame.absolute())
    assert len(result.videos) == 2
    assert result.generation_trace["mode"] == "image-to-video"
    assert result.generation_trace["motion_prompt"] == "camera pans left"


@pytest.mark.asyncio
async def test_generate_image_to_video_hero_frame_not_found(temp_output_dir):
    """Test image-to-video generation with missing hero frame."""
    with pytest.raises(FileNotFoundError):
        await generate_image_to_video(
            hero_frame_path="nonexistent.png",
            motion_prompt="camera pans left",
            num_attempts=1,
            output_dir=temp_output_dir,
        )


@pytest.mark.asyncio
async def test_generate_storyboard_videos_success(mock_video_generation, temp_output_dir):
    """Test successful storyboard video generation."""
    # Create storyboard JSON
    storyboard_json = temp_output_dir / "storyboard.json"
    storyboard_data = {
        "storyboard_path": "storyboard_metadata.json",
        "unified_narrative_path": "unified_narrative.md",
        "clips": [
            {
                "clip_number": 1,
                "enhanced_motion_prompt": "camera pans left",
                "start_frame_path": "clip_001_start.png",
                "end_frame_path": "clip_001_end.png",
            }
        ],
        "clip_frame_paths": {
            "1": {
                "start_frame_path": "clip_001_start.png",
                "end_frame_path": "clip_001_end.png",
            }
        },
    }
    storyboard_json.write_text(json.dumps(storyboard_data))
    
    # Create frame images
    start_frame = temp_output_dir / "clip_001_start.png"
    start_frame.write_bytes(b"fake image")
    
    # Mock video generation
    mock_video_generation.return_value = (
        str(temp_output_dir / "clip_001" / "video_001.mp4"),
        "openai/sora-2"
    )
    
    # Create fake video file
    clip_dir = temp_output_dir / "clip_001"
    clip_dir.mkdir()
    video_file = clip_dir / "video_001.mp4"
    video_file.write_bytes(b"fake video")
    
    result = await generate_storyboard_videos(
        storyboard_json_path=str(storyboard_json),
        num_attempts=1,
        output_dir=temp_output_dir,
    )
    
    assert result.storyboard_path == str(storyboard_json.absolute())
    assert len(result.clip_results) == 1
    assert result.summary["total_clips"] == 1


@pytest.mark.asyncio
async def test_generate_storyboard_videos_missing_json(temp_output_dir):
    """Test storyboard generation with missing JSON file."""
    with pytest.raises(FileNotFoundError):
        await generate_storyboard_videos(
            storyboard_json_path="nonexistent.json",
            num_attempts=1,
            output_dir=temp_output_dir,
        )


@pytest.mark.asyncio
async def test_generate_storyboard_videos_invalid_json(temp_output_dir):
    """Test storyboard generation with invalid JSON structure."""
    storyboard_json = temp_output_dir / "storyboard.json"
    storyboard_json.write_text('{"invalid": "structure"}')
    
    with pytest.raises(ValueError, match="missing 'clips'"):
        await generate_storyboard_videos(
            storyboard_json_path=str(storyboard_json),
            num_attempts=1,
            output_dir=temp_output_dir,
        )


def test_calculate_overall_quality_score():
    """Test overall quality score calculation."""
    vbench_scores = {
        "subject_consistency": 80.0,
        "background_consistency": 75.0,
        "motion_smoothness": 85.0,
        "dynamic_degree": 70.0,
        "aesthetic_quality": 90.0,
        "imaging_quality": 85.0,
        "object_class_alignment": 80.0,
        "text_video_alignment": 75.0,
    }
    
    overall = calculate_overall_quality_score(vbench_scores)
    
    # Should be weighted combination
    assert 0 <= overall <= 100
    assert isinstance(overall, float)


def test_calculate_overall_quality_score_missing_dimensions():
    """Test overall quality score with missing dimensions."""
    vbench_scores = {
        "subject_consistency": 80.0,
        "aesthetic_quality": 90.0,
    }
    
    overall = calculate_overall_quality_score(vbench_scores)
    
    # Should still calculate with available dimensions
    assert 0 <= overall <= 100


@patch('app.services.pipeline.video_quality_scoring.evaluate_vbench')
def test_score_video_success(mock_evaluate_vbench, sample_video_path):
    """Test video scoring."""
    mock_evaluate_vbench.return_value = {
        "temporal_quality": 80.0,
        "subject_consistency": 75.0,
        "overall_quality": 80.0,
    }
    
    scores = score_video(sample_video_path, "test prompt")
    
    assert "overall_quality" in scores
    assert scores["overall_quality"] > 0
    mock_evaluate_vbench.assert_called_once()


@patch('app.services.pipeline.video_quality_scoring.evaluate_vbench')
def test_score_videos_batch_success(mock_evaluate_vbench, sample_video_path):
    """Test batch video scoring."""
    mock_evaluate_vbench.return_value = {
        "temporal_quality": 80.0,
        "subject_consistency": 75.0,
        "overall_quality": 80.0,
    }
    
    video_paths = [sample_video_path, sample_video_path]
    prompt_texts = ["prompt 1", "prompt 2"]
    
    scores_list = score_videos_batch(video_paths, prompt_texts)
    
    assert len(scores_list) == 2
    assert mock_evaluate_vbench.call_count == 2


def test_rank_videos_by_quality():
    """Test video ranking by quality."""
    video_paths = ["video1.mp4", "video2.mp4", "video3.mp4"]
    scores_list = [
        {"overall_quality": 70.0},
        {"overall_quality": 90.0},
        {"overall_quality": 80.0},
    ]
    
    ranked = rank_videos_by_quality(video_paths, scores_list)
    
    assert len(ranked) == 3
    # Best video should be first
    assert ranked[0][1]["overall_quality"] == 90.0
    assert ranked[0][2] == 1  # Rank 1
    assert ranked[1][1]["overall_quality"] == 80.0
    assert ranked[1][2] == 2  # Rank 2
    assert ranked[2][1]["overall_quality"] == 70.0
    assert ranked[2][2] == 3  # Rank 3


def test_rank_videos_by_quality_mismatched_lengths():
    """Test ranking with mismatched video paths and scores."""
    video_paths = ["video1.mp4", "video2.mp4"]
    scores_list = [{"overall_quality": 70.0}]
    
    with pytest.raises(ValueError, match="must have the same length"):
        rank_videos_by_quality(video_paths, scores_list)


