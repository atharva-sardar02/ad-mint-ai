"""
Unit tests for enhanced reference image generation with prompt enhancement and quality scoring.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import shutil
import json

from app.services.pipeline.image_generation_batch import (
    generate_enhanced_reference_images_with_sequential_references
)
from app.services.pipeline.image_prompt_enhancement import ImagePromptEnhancementResult
from app.services.image_generation import ImageGenerationResult


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return [
        "A person jogging in a park",
        "The same person checking their phone",
        "The same person at a gym"
    ]


@pytest.fixture
def mock_enhancement_result():
    """Mock ImagePromptEnhancementResult."""
    return ImagePromptEnhancementResult(
        original_prompt="A person jogging in a park",
        final_prompt="A person jogging in a park, cinematic lighting, professional photography",
        iterations=[],
        final_score={"overall": 85.0, "completeness": 80, "specificity": 85},
        total_iterations=2,
        negative_prompt="blurry, low quality"
    )


@pytest.fixture
def mock_image_results():
    """Mock ImageGenerationResult list."""
    return [
        ImageGenerationResult(
            image_path="/tmp/image1.png",
            image_url="https://example.com/image1.png",
            model_name="flux-schnell",
            seed=123,
            aspect_ratio="16:9",
            prompt="enhanced prompt",
            cost=0.003,
            generation_time=2.5,
            timestamp="2025-01-01 12:00:00"
        ),
        ImageGenerationResult(
            image_path="/tmp/image2.png",
            image_url="https://example.com/image2.png",
            model_name="flux-schnell",
            seed=124,
            aspect_ratio="16:9",
            prompt="enhanced prompt",
            cost=0.003,
            generation_time=2.6,
            timestamp="2025-01-01 12:00:01"
        ),
        ImageGenerationResult(
            image_path="/tmp/image3.png",
            image_url="https://example.com/image3.png",
            model_name="flux-schnell",
            seed=125,
            aspect_ratio="16:9",
            prompt="enhanced prompt",
            cost=0.003,
            generation_time=2.7,
            timestamp="2025-01-01 12:00:02"
        ),
        ImageGenerationResult(
            image_path="/tmp/image4.png",
            image_url="https://example.com/image4.png",
            model_name="flux-schnell",
            seed=126,
            aspect_ratio="16:9",
            prompt="enhanced prompt",
            cost=0.003,
            generation_time=2.8,
            timestamp="2025-01-01 12:00:03"
        )
    ]


@pytest.fixture
def mock_scores():
    """Mock quality scores."""
    return {
        "pickscore": 75.0,
        "clip_score": 80.0,
        "vqa_score": 70.0,
        "aesthetic": 65.0,
        "overall": 72.5
    }


@pytest.mark.asyncio
async def test_generate_enhanced_reference_images_basic(
    temp_output_dir, sample_prompts, mock_enhancement_result, 
    mock_image_results, mock_scores
):
    """Test basic enhanced reference image generation."""
    generation_id = "test-gen-123"
    
    with patch("app.services.pipeline.image_generation_batch.enhance_prompt_iterative") as mock_enhance, \
         patch("app.services.pipeline.image_generation_batch.generate_images") as mock_generate, \
         patch("app.services.pipeline.image_generation_batch.score_image") as mock_score, \
         patch("app.services.pipeline.image_generation_batch.rank_images_by_quality") as mock_rank:
        
        # Setup mocks
        mock_enhance.return_value = mock_enhancement_result
        mock_generate.return_value = mock_image_results
        mock_score.return_value = mock_scores
        
        # Mock ranking: return images with scores and ranks
        ranked_results = [
            (mock_image_results[1].image_path, mock_scores, 1),  # Best
            (mock_image_results[0].image_path, mock_scores, 2),
            (mock_image_results[2].image_path, mock_scores, 3),
            (mock_image_results[3].image_path, mock_scores, 4),
        ]
        mock_rank.return_value = ranked_results
        
        # Create actual image files for the results
        for img_result in mock_image_results:
            Path(img_result.image_path).parent.mkdir(parents=True, exist_ok=True)
            Path(img_result.image_path).touch()
        
        result = await generate_enhanced_reference_images_with_sequential_references(
            prompts=sample_prompts,
            output_dir=str(temp_output_dir),
            generation_id=generation_id,
            num_variations=4,
            max_enhancement_iterations=4
        )
        
        # Verify results
        assert len(result) == len(sample_prompts)
        assert all(isinstance(path, str) for path in result)
        
        # Verify enhancement was called for each scene
        assert mock_enhance.call_count == len(sample_prompts)
        
        # Verify generation was called for each scene
        assert mock_generate.call_count == len(sample_prompts)
        
        # Verify scoring was called for all variations (4 per scene)
        assert mock_score.call_count == len(sample_prompts) * 4
        
        # Verify ranking was called for each scene
        assert mock_rank.call_count == len(sample_prompts)
        
        # Cleanup
        for img_result in mock_image_results:
            if Path(img_result.image_path).exists():
                Path(img_result.image_path).unlink()


@pytest.mark.asyncio
async def test_generate_enhanced_reference_images_sequential_chaining(
    temp_output_dir, sample_prompts, mock_enhancement_result,
    mock_image_results, mock_scores
):
    """Test that sequential chaining works correctly."""
    generation_id = "test-gen-456"
    
    with patch("app.services.pipeline.image_generation_batch.enhance_prompt_iterative") as mock_enhance, \
         patch("app.services.pipeline.image_generation_batch.generate_images") as mock_generate, \
         patch("app.services.pipeline.image_generation_batch.score_image") as mock_score, \
         patch("app.services.pipeline.image_generation_batch.rank_images_by_quality") as mock_rank:
        
        # Setup mocks
        mock_enhance.return_value = mock_enhancement_result
        mock_generate.return_value = mock_image_results
        mock_score.return_value = mock_scores
        
        ranked_results = [
            (mock_image_results[0].image_path, mock_scores, 1),
        ]
        mock_rank.return_value = ranked_results
        
        # Create actual image files
        for img_result in mock_image_results:
            Path(img_result.image_path).parent.mkdir(parents=True, exist_ok=True)
            Path(img_result.image_path).touch()
        
        initial_reference = "/tmp/initial_ref.png"
        Path(initial_reference).parent.mkdir(parents=True, exist_ok=True)
        Path(initial_reference).touch()
        
        result = await generate_enhanced_reference_images_with_sequential_references(
            prompts=sample_prompts,
            output_dir=str(temp_output_dir),
            generation_id=generation_id,
            initial_reference_image=initial_reference,
            num_variations=4,
            max_enhancement_iterations=4
        )
        
        # Verify first scene uses initial reference
        first_call = mock_generate.call_args_list[0]
        assert first_call.kwargs.get("image_input") == [initial_reference]
        
        # Verify subsequent scenes use previous scene's best image
        if len(mock_generate.call_args_list) > 1:
            second_call = mock_generate.call_args_list[1]
            # Should use first scene's best image
            assert second_call.kwargs.get("image_input") is not None
        
        # Cleanup
        for img_result in mock_image_results:
            if Path(img_result.image_path).exists():
                Path(img_result.image_path).unlink()
        if Path(initial_reference).exists():
            Path(initial_reference).unlink()


@pytest.mark.asyncio
async def test_generate_enhanced_reference_images_quality_threshold_warning(
    temp_output_dir, sample_prompts, mock_enhancement_result,
    mock_image_results
):
    """Test that quality threshold warnings are logged when score is below threshold."""
    generation_id = "test-gen-789"
    
    # Low quality scores (below threshold of 30.0)
    low_scores = {
        "pickscore": 20.0,
        "clip_score": 25.0,
        "vqa_score": 15.0,
        "aesthetic": 20.0,
        "overall": 20.0  # Below threshold
    }
    
    with patch("app.services.pipeline.image_generation_batch.enhance_prompt_iterative") as mock_enhance, \
         patch("app.services.pipeline.image_generation_batch.generate_images") as mock_generate, \
         patch("app.services.pipeline.image_generation_batch.score_image") as mock_score, \
         patch("app.services.pipeline.image_generation_batch.rank_images_by_quality") as mock_rank, \
         patch("app.services.pipeline.image_generation_batch.logger") as mock_logger:
        
        # Setup mocks
        mock_enhance.return_value = mock_enhancement_result
        mock_generate.return_value = mock_image_results
        mock_score.return_value = low_scores
        
        ranked_results = [
            (mock_image_results[0].image_path, low_scores, 1),
        ]
        mock_rank.return_value = ranked_results
        
        # Create actual image files
        for img_result in mock_image_results:
            Path(img_result.image_path).parent.mkdir(parents=True, exist_ok=True)
            Path(img_result.image_path).touch()
        
        result = await generate_enhanced_reference_images_with_sequential_references(
            prompts=sample_prompts[:1],  # Just one scene for this test
            output_dir=str(temp_output_dir),
            generation_id=generation_id,
            quality_threshold=30.0,
            num_variations=4,
            max_enhancement_iterations=4
        )
        
        # Verify warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "below threshold" in str(call).lower()]
        assert len(warning_calls) > 0
        
        # Verify result still returned (doesn't fail)
        assert len(result) == 1
        
        # Cleanup
        for img_result in mock_image_results:
            if Path(img_result.image_path).exists():
                Path(img_result.image_path).unlink()


@pytest.mark.asyncio
async def test_generate_enhanced_reference_images_enhancement_fallback(
    temp_output_dir, sample_prompts, mock_image_results, mock_scores
):
    """Test fallback when prompt enhancement fails."""
    generation_id = "test-gen-fallback"
    
    with patch("app.services.pipeline.image_generation_batch.enhance_prompt_iterative") as mock_enhance, \
         patch("app.services.pipeline.image_generation_batch.generate_images") as mock_generate, \
         patch("app.services.pipeline.image_generation_batch.score_image") as mock_score, \
         patch("app.services.pipeline.image_generation_batch.rank_images_by_quality") as mock_rank:
        
        # Mock enhancement failure
        mock_enhance.side_effect = Exception("Enhancement failed")
        
        mock_generate.return_value = mock_image_results
        mock_score.return_value = mock_scores
        
        ranked_results = [
            (mock_image_results[0].image_path, mock_scores, 1),
        ]
        mock_rank.return_value = ranked_results
        
        # Create actual image files
        for img_result in mock_image_results:
            Path(img_result.image_path).parent.mkdir(parents=True, exist_ok=True)
            Path(img_result.image_path).touch()
        
        # Should not raise exception, should fall back to original prompt
        result = await generate_enhanced_reference_images_with_sequential_references(
            prompts=sample_prompts[:1],  # Just one scene
            output_dir=str(temp_output_dir),
            generation_id=generation_id,
            num_variations=4,
            max_enhancement_iterations=4
        )
        
        # Verify fallback: generation should still be called with original prompt
        assert mock_generate.call_count == 1
        # First call should use original prompt (enhancement failed)
        first_call = mock_generate.call_args_list[0]
        # Prompt should contain original prompt text
        assert sample_prompts[0] in first_call.kwargs.get("prompt", "")
        
        # Verify result still returned
        assert len(result) == 1
        
        # Cleanup
        for img_result in mock_image_results:
            if Path(img_result.image_path).exists():
                Path(img_result.image_path).unlink()


@pytest.mark.asyncio
async def test_generate_enhanced_reference_images_generation_fallback(
    temp_output_dir, sample_prompts, mock_enhancement_result, mock_scores
):
    """Test fallback when image generation fails."""
    generation_id = "test-gen-gen-fallback"
    
    with patch("app.services.pipeline.image_generation_batch.enhance_prompt_iterative") as mock_enhance, \
         patch("app.services.pipeline.image_generation_batch.generate_images") as mock_generate, \
         patch("app.services.pipeline.image_generation_batch.score_image") as mock_score, \
         patch("app.services.pipeline.image_generation_batch.rank_images_by_quality") as mock_rank:
        
        # Setup mocks
        mock_enhance.return_value = mock_enhancement_result
        
        # First call fails, second call (retry) succeeds with single image
        single_image_result = [
            ImageGenerationResult(
                image_path="/tmp/fallback_image.png",
                image_url="https://example.com/fallback.png",
                model_name="flux-schnell",
                seed=999,
                aspect_ratio="16:9",
                prompt="original prompt",
                cost=0.003,
                generation_time=2.0,
                timestamp="2025-01-01 12:00:00"
            )
        ]
        
        mock_generate.side_effect = [
            Exception("Generation failed"),  # First attempt fails
            single_image_result  # Retry succeeds
        ]
        
        mock_score.return_value = mock_scores
        
        ranked_results = [
            (single_image_result[0].image_path, mock_scores, 1),
        ]
        mock_rank.return_value = ranked_results
        
        # Create actual image file
        Path(single_image_result[0].image_path).parent.mkdir(parents=True, exist_ok=True)
        Path(single_image_result[0].image_path).touch()
        
        # Should not raise exception, should retry and fall back
        result = await generate_enhanced_reference_images_with_sequential_references(
            prompts=sample_prompts[:1],  # Just one scene
            output_dir=str(temp_output_dir),
            generation_id=generation_id,
            num_variations=4,
            max_enhancement_iterations=4
        )
        
        # Verify retry was attempted
        assert mock_generate.call_count == 2
        
        # Verify result still returned
        assert len(result) == 1
        
        # Cleanup
        if Path(single_image_result[0].image_path).exists():
            Path(single_image_result[0].image_path).unlink()


@pytest.mark.asyncio
async def test_generate_enhanced_reference_images_scoring_fallback(
    temp_output_dir, sample_prompts, mock_enhancement_result, mock_image_results
):
    """Test fallback when quality scoring fails."""
    generation_id = "test-gen-score-fallback"
    
    with patch("app.services.pipeline.image_generation_batch.enhance_prompt_iterative") as mock_enhance, \
         patch("app.services.pipeline.image_generation_batch.generate_images") as mock_generate, \
         patch("app.services.pipeline.image_generation_batch.score_image") as mock_score, \
         patch("app.services.pipeline.image_generation_batch.rank_images_by_quality") as mock_rank:
        
        # Setup mocks
        mock_enhance.return_value = mock_enhancement_result
        mock_generate.return_value = mock_image_results
        
        # Scoring fails
        mock_score.side_effect = Exception("Scoring failed")
        
        # Should use first image without ranking
        ranked_results = [
            (mock_image_results[0].image_path, {"overall": 0.0}, 1),
        ]
        mock_rank.return_value = ranked_results
        
        # Create actual image files
        for img_result in mock_image_results:
            Path(img_result.image_path).parent.mkdir(parents=True, exist_ok=True)
            Path(img_result.image_path).touch()
        
        # Should not raise exception, should use first image
        result = await generate_enhanced_reference_images_with_sequential_references(
            prompts=sample_prompts[:1],  # Just one scene
            output_dir=str(temp_output_dir),
            generation_id=generation_id,
            num_variations=4,
            max_enhancement_iterations=4
        )
        
        # Verify result still returned (uses first image)
        assert len(result) == 1
        assert result[0] == mock_image_results[0].image_path
        
        # Cleanup
        for img_result in mock_image_results:
            if Path(img_result.image_path).exists():
                Path(img_result.image_path).unlink()


@pytest.mark.asyncio
async def test_generate_enhanced_reference_images_trace_cleanup(
    temp_output_dir, sample_prompts, mock_enhancement_result,
    mock_image_results, mock_scores
):
    """Test that trace files are cleaned up after completion."""
    generation_id = "test-gen-cleanup"
    
    with patch("app.services.pipeline.image_generation_batch.enhance_prompt_iterative") as mock_enhance, \
         patch("app.services.pipeline.image_generation_batch.generate_images") as mock_generate, \
         patch("app.services.pipeline.image_generation_batch.score_image") as mock_score, \
         patch("app.services.pipeline.image_generation_batch.rank_images_by_quality") as mock_rank, \
         patch("app.services.pipeline.image_generation_batch.shutil.rmtree") as mock_rmtree:
        
        # Setup mocks
        mock_enhance.return_value = mock_enhancement_result
        mock_generate.return_value = mock_image_results
        mock_score.return_value = mock_scores
        
        ranked_results = [
            (mock_image_results[0].image_path, mock_scores, 1),
        ]
        mock_rank.return_value = ranked_results
        
        # Create actual image files
        for img_result in mock_image_results:
            Path(img_result.image_path).parent.mkdir(parents=True, exist_ok=True)
            Path(img_result.image_path).touch()
        
        result = await generate_enhanced_reference_images_with_sequential_references(
            prompts=sample_prompts[:1],  # Just one scene
            output_dir=str(temp_output_dir),
            generation_id=generation_id,
            num_variations=4,
            max_enhancement_iterations=4
        )
        
        # Verify cleanup was called
        assert mock_rmtree.called
        
        # Cleanup
        for img_result in mock_image_results:
            if Path(img_result.image_path).exists():
                Path(img_result.image_path).unlink()


@pytest.mark.asyncio
async def test_generate_enhanced_reference_images_empty_prompts(temp_output_dir):
    """Test that empty prompts list raises ValueError."""
    with pytest.raises(ValueError, match="prompts list cannot be empty"):
        await generate_enhanced_reference_images_with_sequential_references(
            prompts=[],
            output_dir=str(temp_output_dir),
            generation_id="test-gen-empty",
            num_variations=4,
            max_enhancement_iterations=4
        )

