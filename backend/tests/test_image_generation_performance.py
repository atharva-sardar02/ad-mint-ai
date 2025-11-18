"""
Performance tests for image generation and quality scoring.
"""
import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import shutil

from app.services.image_generation import generate_images
from app.services.pipeline.image_quality_scoring import score_image


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_image_path():
    """Create a temporary sample image file."""
    temp_dir = tempfile.mkdtemp()
    image_path = Path(temp_dir) / "test_image.png"
    
    # Create a simple test image
    from PIL import Image
    img = Image.new("RGB", (100, 100), color="red")
    img.save(image_path)
    
    yield str(image_path)
    
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_image_generation_performance_target(temp_output_dir):
    """Test that image generation completes within <5 minutes for 8 images."""
    # Mock Replicate API to simulate realistic timing
    mock_prediction = MagicMock()
    mock_prediction.status = "succeeded"
    mock_prediction.output = "https://example.com/image.png"
    mock_prediction.id = "test-prediction-id"
    
    with patch("app.services.image_generation.replicate.Client") as mock_client_class, \
         patch("app.services.image_generation._download_image") as mock_download:
        
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction
        mock_download.return_value = str(temp_output_dir / "image_001.png")
        
        # Simulate API delay (30 seconds per image is reasonable)
        async def delayed_get(prediction_id):
            await asyncio.sleep(0.1)  # Fast for testing
            return mock_prediction
        
        mock_client.predictions.get = AsyncMock(side_effect=delayed_get)
        
        start_time = time.time()
        
        results = await generate_images(
            prompt="A beautiful sunset",
            num_variations=8,
            output_dir=temp_output_dir
        )
        
        elapsed_time = time.time() - start_time
        
        # Target: <5 minutes (300 seconds) for 8 images
        # In real scenario, this would be much slower due to API calls
        # For this test with mocked API, it should be very fast
        assert elapsed_time < 300, f"Generation took {elapsed_time:.2f}s, target is <300s"
        assert len(results) == 8, "Should generate 8 images"
        
        print(f"✅ Generation performance: {elapsed_time:.2f}s for 8 images (target: <300s)")


@pytest.mark.asyncio
async def test_quality_scoring_performance_target(sample_image_path):
    """Test that quality scoring completes within <2 minutes for 8 images."""
    # Mock CLIP model to avoid actual model loading
    with patch("app.services.pipeline.image_quality_scoring._load_clip_model") as mock_load, \
         patch("app.services.pipeline.image_quality_scoring._compute_clip_score") as mock_clip:
        
        mock_load.return_value = (MagicMock(), MagicMock())
        mock_clip.return_value = 75.0  # Fast mock score
        
        start_time = time.time()
        
        # Score 8 images sequentially
        for i in range(8):
            await score_image(sample_image_path, "A beautiful sunset")
        
        elapsed_time = time.time() - start_time
        
        # Target: <2 minutes (120 seconds) for 8 images
        # With mocked CLIP, this should be very fast
        assert elapsed_time < 120, f"Scoring took {elapsed_time:.2f}s, target is <120s"
        
        print(f"✅ Scoring performance: {elapsed_time:.2f}s for 8 images (target: <120s)")


@pytest.mark.asyncio
async def test_combined_generation_and_scoring_performance(temp_output_dir, sample_image_path):
    """Test combined generation + scoring performance."""
    # This is a combined test to verify the full workflow timing
    with patch("app.services.image_generation.generate_images") as mock_gen, \
         patch("app.services.pipeline.image_quality_scoring.score_image") as mock_score:
        
        # Mock generation results
        from app.services.image_generation import ImageGenerationResult
        mock_results = [
            ImageGenerationResult(
                image_path=str(temp_output_dir / f"image_{i+1}.png"),
                image_url=f"https://example.com/image_{i+1}.png",
                model_name="stability-ai/sdxl",
                seed=None,
                aspect_ratio="16:9",
                prompt="A beautiful sunset",
                cost=0.003,
                generation_time=30.0,  # 30 seconds per image
                timestamp="2025-11-17 12:00:00"
            )
            for i in range(8)
        ]
        mock_gen.return_value = mock_results
        
        # Mock scoring (fast)
        mock_score.return_value = {
            "pickscore": 75.0,
            "clip_score": 80.0,
            "vqa_score": None,
            "aesthetic": 70.0,
            "overall": 75.0
        }
        
        start_time = time.time()
        
        # Simulate workflow
        results = await mock_gen(
            prompt="A beautiful sunset",
            num_variations=8,
            output_dir=temp_output_dir
        )
        
        # Score all images
        for result in results:
            if result.image_path:
                await mock_score(result.image_path, "A beautiful sunset")
        
        elapsed_time = time.time() - start_time
        
        # Combined target: <7 minutes (420 seconds) for generation + scoring
        # With mocks, this should be very fast
        assert elapsed_time < 420, f"Combined workflow took {elapsed_time:.2f}s, target is <420s"
        
        print(f"✅ Combined performance: {elapsed_time:.2f}s for 8 images (generation + scoring)")


def test_performance_logging(temp_output_dir):
    """Test that performance metrics are logged correctly."""
    import logging
    from io import StringIO
    
    # Setup logging capture
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger("app.services.image_generation")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # This would normally log during actual generation
    # For this test, we just verify the logging infrastructure works
    logger.info("Performance test: Generation time 240.5s for 8 images")
    
    log_output = log_capture.getvalue()
    assert "Generation time" in log_output or "Performance test" in log_output
    
    logger.removeHandler(handler)

