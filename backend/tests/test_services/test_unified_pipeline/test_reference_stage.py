"""
Unit tests for reference stage module.

Tests AC#1, AC#2, AC#3, AC#8 from Story 1.2
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.unified_pipeline.reference_stage import ReferenceStage, execute_reference_stage
from app.schemas.unified_pipeline import (
    BrandAssets,
    ReferenceImage,
    ReferenceImageAnalysis,
    PipelineConfig
)


@pytest.fixture
def default_config():
    """Default pipeline configuration."""
    return PipelineConfig(
        pipeline_name="test",
        reference_count=3,
        reference_quality_threshold=0.7
    )


@pytest.fixture
def mock_s3_storage():
    """Mock S3 storage service."""
    with patch("app.services.unified_pipeline.reference_stage.get_s3_storage") as mock:
        s3_instance = MagicMock()
        s3_instance.bucket_name = "test-bucket"
        s3_instance.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-bucket/test.jpg?signature=..."
        mock.return_value = s3_instance
        yield s3_instance


@pytest.fixture
def mock_image_processor():
    """Mock image processor with Vision API."""
    with patch("app.services.unified_pipeline.reference_stage.get_image_processor") as mock:
        processor = MagicMock()
        processor.analyze_with_vision = AsyncMock(return_value=ReferenceImageAnalysis(
            character_description="Young woman, casual clothing, brown hair",
            product_features="Blue water bottle, 500ml capacity",
            colors=["#1E90FF", "#FFFFFF"],
            style="photorealistic",
            environment="outdoor, natural lighting"
        ))
        mock.return_value = processor
        yield processor


class TestReferenceStageInitialization:
    """Test reference stage initialization."""

    def test_init_with_config(self, default_config, mock_s3_storage, mock_image_processor):
        """Test reference stage initializes correctly."""
        stage = ReferenceStage(default_config)
        assert stage.config == default_config
        assert stage.s3_storage is not None
        assert stage.image_processor is not None


class TestBrandAssetIntegration:
    """Test AC#2: Brand asset integration."""

    @pytest.mark.asyncio
    async def test_use_brand_assets_priority_order(self, default_config, mock_s3_storage, mock_image_processor):
        """Test brand assets prioritized correctly: product[0], character[0], logo."""
        brand_assets = BrandAssets(
            product_images=["s3://bucket/product1.jpg", "s3://bucket/product2.jpg"],
            character_images=["s3://bucket/char1.jpg"],
            logo="s3://bucket/logo.png"
        )

        stage = ReferenceStage(default_config)
        result = await stage._use_brand_assets(brand_assets, "gen-123")

        # Check we got 3 reference images
        assert len(result) == 3

        # Check priority order: product, character, logo
        assert result[0].type == "product"
        assert result[0].url == "s3://bucket/product1.jpg"

        assert result[1].type == "character"
        assert result[1].url == "s3://bucket/char1.jpg"

        assert result[2].type == "logo"
        assert result[2].url == "s3://bucket/logo.png"

    @pytest.mark.asyncio
    async def test_use_brand_assets_fills_remaining_slots(self, default_config, mock_s3_storage, mock_image_processor):
        """Test brand assets fill remaining slots with additional images."""
        brand_assets = BrandAssets(
            product_images=["s3://bucket/product1.jpg", "s3://bucket/product2.jpg", "s3://bucket/product3.jpg"],
            character_images=["s3://bucket/char1.jpg", "s3://bucket/char2.jpg"],
            logo="s3://bucket/logo.png"
        )

        stage = ReferenceStage(default_config)
        result = await stage._use_brand_assets(brand_assets, "gen-123")

        # Should take first 3: product[0], character[0], logo
        assert len(result) == 3
        assert result[0].type == "product"
        assert result[1].type == "character"
        assert result[2].type == "logo"

    @pytest.mark.asyncio
    async def test_use_brand_assets_calls_vision_analysis(self, default_config, mock_s3_storage, mock_image_processor):
        """Test brand assets are analyzed with Vision API."""
        brand_assets = BrandAssets(
            product_images=["s3://bucket/product1.jpg"]
        )

        stage = ReferenceStage(default_config)
        result = await stage._use_brand_assets(brand_assets, "gen-123")

        # Check Vision API was called
        assert mock_image_processor.analyze_with_vision.called
        assert mock_image_processor.analyze_with_vision.call_count == 1

        # Check analysis was attached
        assert result[0].analysis is not None
        assert result[0].analysis.character_description is not None


class TestAutoGenerationFallback:
    """Test AC#3: Auto-generation fallback."""

    @pytest.mark.asyncio
    async def test_generate_reference_images_creates_three(self, default_config, mock_s3_storage, mock_image_processor):
        """Test auto-generation creates 3 diverse reference images."""
        story = "An eco-friendly water bottle ad targeting millennials..."

        stage = ReferenceStage(default_config)
        result = await stage._generate_reference_images(story, "gen-123")

        # Should generate 3 images
        assert len(result) == 3

        # Should have diverse types
        types = [img.type for img in result]
        assert "character" in types
        assert "product" in types
        assert "environment" in types

    @pytest.mark.asyncio
    async def test_generate_reference_images_uses_story_content(self, default_config, mock_s3_storage, mock_image_processor):
        """Test auto-generation derives prompts from story."""
        story = "An eco-friendly water bottle ad featuring a young athlete..."

        stage = ReferenceStage(default_config)
        result = await stage._generate_reference_images(story, "gen-123")

        # All images should have placeholder URLs (real Replicate generation is TODO)
        for img in result:
            assert img.url.startswith("s3://test-bucket/generations/gen-123/references/")


class TestConsistencyContextFormatter:
    """Test AC#6: Consistency context formatting."""

    def test_build_consistency_context_all_fields(self, default_config, mock_s3_storage, mock_image_processor):
        """Test consistency context includes all 5 sections."""
        reference_images = [
            ReferenceImage(
                url="s3://bucket/ref1.jpg",
                type="character",
                analysis=ReferenceImageAnalysis(
                    character_description="Young woman, casual clothing",
                    product_features="Blue water bottle",
                    colors=["#1E90FF", "#FFFFFF"],
                    style="photorealistic",
                    environment="outdoor, natural lighting"
                )
            )
        ]

        stage = ReferenceStage(default_config)
        context = stage.build_consistency_context(reference_images)

        # Check all sections present
        assert "CHARACTER APPEARANCE:" in context
        assert "PRODUCT FEATURES:" in context
        assert "COLOR PALETTE:" in context
        assert "VISUAL STYLE:" in context
        assert "ENVIRONMENTAL CONTEXT:" in context

    def test_build_consistency_context_deduplicates_colors(self, default_config, mock_s3_storage, mock_image_processor):
        """Test consistency context deduplicates repeated colors."""
        reference_images = [
            ReferenceImage(
                url="s3://bucket/ref1.jpg",
                type="product",
                analysis=ReferenceImageAnalysis(
                    colors=["#1E90FF", "#FFFFFF"],
                    style="photorealistic"
                )
            ),
            ReferenceImage(
                url="s3://bucket/ref2.jpg",
                type="character",
                analysis=ReferenceImageAnalysis(
                    colors=["#1E90FF", "#000000"],  # #1E90FF repeated
                    style="photorealistic"
                )
            )
        ]

        stage = ReferenceStage(default_config)
        context = stage.build_consistency_context(reference_images)

        # Check #1E90FF appears only once
        assert context.count("#1E90FF") == 1
        assert "#FFFFFF" in context
        assert "#000000" in context


class TestHasBrandAssets:
    """Test brand asset detection."""

    def test_has_brand_assets_with_products(self, default_config, mock_s3_storage, mock_image_processor):
        """Test detects brand assets with product images."""
        brand_assets = BrandAssets(product_images=["s3://bucket/product.jpg"])
        stage = ReferenceStage(default_config)
        assert stage._has_brand_assets(brand_assets) is True

    def test_has_brand_assets_with_logo(self, default_config, mock_s3_storage, mock_image_processor):
        """Test detects brand assets with logo."""
        brand_assets = BrandAssets(logo="s3://bucket/logo.png")
        stage = ReferenceStage(default_config)
        assert stage._has_brand_assets(brand_assets) is True

    def test_has_brand_assets_with_characters(self, default_config, mock_s3_storage, mock_image_processor):
        """Test detects brand assets with character images."""
        brand_assets = BrandAssets(character_images=["s3://bucket/char.jpg"])
        stage = ReferenceStage(default_config)
        assert stage._has_brand_assets(brand_assets) is True

    def test_has_brand_assets_empty(self, default_config, mock_s3_storage, mock_image_processor):
        """Test detects no brand assets when empty."""
        brand_assets = BrandAssets()
        stage = ReferenceStage(default_config)
        assert stage._has_brand_assets(brand_assets) is False


class TestExecuteConvenienceFunction:
    """Test execute_reference_stage convenience function."""

    @pytest.mark.asyncio
    async def test_execute_reference_stage_returns_tuple(self, default_config, mock_s3_storage, mock_image_processor):
        """Test convenience function returns (reference_images, consistency_context) tuple."""
        brand_assets = BrandAssets(product_images=["s3://bucket/product.jpg"])

        result = await execute_reference_stage(
            story="Test story",
            brand_assets=brand_assets,
            generation_id="gen-123",
            config=default_config
        )

        # Should return tuple
        assert isinstance(result, tuple)
        assert len(result) == 2

        reference_images, consistency_context = result

        # Check reference images
        assert isinstance(reference_images, list)
        assert len(reference_images) > 0

        # Check consistency context
        assert isinstance(consistency_context, str)
        assert len(consistency_context) > 0
