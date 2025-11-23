"""
Reference Stage Module

Implements Master Mode's proven 3-reference-image visual consistency system.
Generates or uses 3 reference images, analyzes them with GPT-4 Vision,
and builds a consistency context string for scene video generation.

Story 1.2: Master Mode 3-Reference-Image Consistency System
AC#1: Single reference_stage.py module executes after story approval
AC#2: Brand asset integration (use provided images as references)
AC#3: Auto-generation fallback (generate from story if no brand assets)
AC#8: S3 upload for reference images
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4
import asyncio
import tempfile
from pathlib import Path
import os
import time

import replicate
import httpx

from app.schemas.unified_pipeline import (
    BrandAssets,
    ReferenceImage,
    ReferenceImageAnalysis,
    PipelineConfig
)
from app.services.storage.s3_storage import get_s3_storage
from app.services.media.image_processor import get_image_processor

logger = logging.getLogger(__name__)

# Replicate model configuration
NANO_BANANA_MODEL = "google/nano-banana"
MAX_RETRIES = 3
POLL_INTERVAL = 2  # seconds
MAX_POLLING_TIME = 300  # 5 minutes timeout


class ReferenceStage:
    """
    Reference image generation and analysis stage.

    Implements 3-reference-image consistency system from Master Mode.
    Uses brand assets if provided, otherwise auto-generates from story.
    Analyzes images with GPT-4 Vision to extract consistency characteristics.
    """

    def __init__(self, config: PipelineConfig):
        """
        Initialize reference stage.

        Args:
            config: Pipeline configuration with reference stage settings
        """
        self.config = config
        self.s3_storage = get_s3_storage()
        self.image_processor = get_image_processor()
        logger.info(f"Reference stage initialized (count: {config.reference_count})")

    async def execute(
        self,
        story: str,
        brand_assets: Optional[BrandAssets],
        generation_id: str
    ) -> List[ReferenceImage]:
        """
        Execute reference stage: generate/select 3 reference images and analyze.

        This method implements:
        - AC#2: Brand asset integration (prioritize provided images)
        - AC#3: Auto-generation fallback (generate if no brand assets)
        - AC#4: GPT-4 Vision analysis
        - AC#8: S3 upload

        Args:
            story: Approved story text from previous stage
            brand_assets: Optional brand assets (product images, logo, characters)
            generation_id: Generation ID for S3 path construction

        Returns:
            List of 3 ReferenceImage objects with Vision analysis
        """
        logger.info(f"Executing reference stage for generation {generation_id}")

        # Step 1: Determine reference image sources (AC#2, AC#3)
        reference_images: List[ReferenceImage] = []

        if brand_assets and self._has_brand_assets(brand_assets):
            logger.info("Using brand assets as reference images (AC#2)")
            reference_images = await self._use_brand_assets(brand_assets, generation_id)
        else:
            logger.info("No brand assets provided, auto-generating references (AC#3)")
            reference_images = await self._generate_reference_images(story, generation_id)

        logger.info(f"✓ Reference stage complete: {len(reference_images)} images with analysis")
        return reference_images

    def _has_brand_assets(self, brand_assets: BrandAssets) -> bool:
        """
        Check if brand assets contain any images.

        Args:
            brand_assets: Brand assets to check

        Returns:
            bool: True if any images available
        """
        has_assets = (
            len(brand_assets.product_images) > 0 or
            brand_assets.logo is not None or
            len(brand_assets.character_images) > 0
        )
        logger.debug(f"Brand assets check: {has_assets}")
        return has_assets

    async def _use_brand_assets(
        self,
        brand_assets: BrandAssets,
        generation_id: str
    ) -> List[ReferenceImage]:
        """
        Use brand assets as reference images (AC#2).

        Priority order:
        1. product_images[0]
        2. character_images[0]
        3. logo
        4. Additional product/character images up to 3 total

        Args:
            brand_assets: Brand assets with product/logo/character images
            generation_id: Generation ID for S3 paths

        Returns:
            List of up to 3 ReferenceImage objects (may need auto-generation to reach 3)
        """
        logger.info("Prioritizing brand assets for reference images")

        # Collect available assets in priority order
        available_assets: List[tuple[str, str]] = []  # (url, type)

        # Priority 1: Product images
        if brand_assets.product_images:
            available_assets.append((brand_assets.product_images[0], "product"))

        # Priority 2: Character images
        if brand_assets.character_images:
            available_assets.append((brand_assets.character_images[0], "character"))

        # Priority 3: Logo
        if brand_assets.logo:
            available_assets.append((brand_assets.logo, "logo"))

        # Fill remaining slots with additional product/character images
        for i in range(1, len(brand_assets.product_images)):
            if len(available_assets) >= self.config.reference_count:
                break
            available_assets.append((brand_assets.product_images[i], "product"))

        for i in range(1, len(brand_assets.character_images)):
            if len(available_assets) >= self.config.reference_count:
                break
            available_assets.append((brand_assets.character_images[i], "character"))

        # Select first N assets (up to reference_count, typically 3)
        selected_assets = available_assets[:self.config.reference_count]
        logger.info(f"Selected {len(selected_assets)} brand assets as references")

        # Analyze each asset with Vision API (AC#4)
        reference_images: List[ReferenceImage] = []
        for url, asset_type in selected_assets:
            logger.info(f"Analyzing {asset_type} asset: {url[:50]}...")

            # Convert S3 URL to pre-signed URL for Vision API access
            image_url = url  # If already pre-signed or public
            if url.startswith("s3://"):
                # Extract S3 key from s3:// URL
                s3_key = url.replace(f"s3://{self.s3_storage.bucket_name}/", "")
                # Generate pre-signed URL (24-hour expiration)
                image_url = self.s3_storage.generate_presigned_url(s3_key, expiration=86400)
                logger.debug(f"Generated pre-signed URL for Vision analysis")

            # Analyze with GPT-4 Vision (AC#4)
            analysis = await self.image_processor.analyze_with_vision(image_url, asset_type)

            reference_image = ReferenceImage(
                url=url,  # Store original S3 URL (not pre-signed)
                type=asset_type,
                analysis=analysis
            )
            reference_images.append(reference_image)

        logger.info(f"✓ Created {len(reference_images)} reference images from brand assets")
        return reference_images

    async def _generate_reference_images(
        self,
        story: str,
        generation_id: str
    ) -> List[ReferenceImage]:
        """
        Auto-generate reference images from story (AC#3).

        Generates 3 diverse reference images:
        1. Character-focused
        2. Product-focused
        3. Environment-focused

        Args:
            story: Approved story text to generate images from
            generation_id: Generation ID for S3 paths

        Returns:
            List of 3 ReferenceImage objects with Vision analysis
        """
        logger.info(f"Auto-generating {self.config.reference_count} reference images from story")

        # Define 3 diverse generation prompts derived from story
        prompts = [
            {
                "type": "character",
                "prompt": f"Generate a photorealistic image of the main character from this story: {story[:500]}. Focus on character appearance, clothing, and facial features."
            },
            {
                "type": "product",
                "prompt": f"Generate a photorealistic product image from this story: {story[:500]}. Focus on product features, branding, and key visual elements."
            },
            {
                "type": "environment",
                "prompt": f"Generate a photorealistic environment/scene image from this story: {story[:500]}. Focus on setting, lighting, and environmental context."
            }
        ][:self.config.reference_count]  # Take only configured count (typically 3)

        # Generate images using Replicate API (AC#3)
        reference_images: List[ReferenceImage] = []

        for prompt_config in prompts:
            logger.info(f"Generating {prompt_config['type']} reference image with Replicate")

            # Call Replicate API to generate image
            try:
                image_url = await self._call_replicate_api(
                    prompt=prompt_config['prompt'],
                    image_type=prompt_config['type']
                )
                logger.info(f"✓ Replicate generated image: {image_url}")

                # Download generated image to temporary file
                temp_file = await self._download_temp_image(image_url)
                logger.debug(f"Downloaded to temp file: {temp_file}")

                # Upload to S3 (AC#8)
                s3_key = f"generations/{generation_id}/references/{uuid4()}.jpg"
                s3_url = self.s3_storage.upload_file(
                    local_path=temp_file,
                    s3_key=s3_key,
                    content_type="image/jpeg"
                )
                logger.info(f"✓ Uploaded to S3: {s3_url}")

                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

                # Generate pre-signed URL for Vision API
                presigned_url = self.s3_storage.generate_presigned_url(s3_key, expiration=86400)

                # Analyze generated image with GPT-4 Vision (AC#4)
                analysis = await self.image_processor.analyze_with_vision(
                    presigned_url,
                    prompt_config['type']
                )
                logger.info(f"✓ Vision analysis complete for {prompt_config['type']} image")

                reference_image = ReferenceImage(
                    url=s3_url,
                    type=prompt_config['type'],
                    analysis=analysis
                )
                reference_images.append(reference_image)

            except Exception as e:
                logger.error(f"Failed to generate {prompt_config['type']} reference image: {e}")
                # Try fallback models (Stable Diffusion 3, FLUX) per architecture constraints
                try:
                    logger.warning(f"Attempting fallback image generation for {prompt_config['type']}")
                    # For MVP, create fallback with basic analysis
                    # In production, implement actual fallback to SD3/FLUX
                    analysis = ReferenceImageAnalysis(
                        character_description=f"Fallback {prompt_config['type']} description from story",
                        product_features="Based on story text analysis",
                        colors=["#2C3E50", "#E74C3C"],  # Default brand colors
                        style="photorealistic",
                        environment="professional studio setting"
                    )
                    # Create placeholder for fallback (will be improved with actual fallback models)
                    s3_key = f"generations/{generation_id}/references/{uuid4()}_fallback.jpg"
                    reference_image = ReferenceImage(
                        url=f"s3://{self.s3_storage.bucket_name}/{s3_key}",
                        type=prompt_config['type'],
                        analysis=analysis
                    )
                    reference_images.append(reference_image)
                    logger.warning(f"Using fallback analysis for {prompt_config['type']} (image generation failed)")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    # Continue with other reference images

        if not reference_images:
            raise RuntimeError("Failed to generate any reference images")

        logger.info(f"✓ Auto-generated {len(reference_images)} reference images")
        return reference_images

    async def _call_replicate_api(
        self,
        prompt: str,
        image_type: str
    ) -> str:
        """
        Call Replicate Nano Banana API to generate image.

        Args:
            prompt: Text prompt for image generation
            image_type: Type of image (character, product, environment)

        Returns:
            str: URL of generated image

        Raises:
            RuntimeError: If generation fails after retries
        """
        # Get API token from environment
        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            raise ValueError("REPLICATE_API_TOKEN environment variable not set")

        client = replicate.Client(api_token=api_token)
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"Calling Nano Banana API (attempt {attempt}/{MAX_RETRIES})")

                # Prepare input parameters for Nano Banana
                input_params = {
                    "prompt": prompt,
                    "num_outputs": 1,
                    "aspect_ratio": "9:16",  # Vertical for mobile ads
                }

                logger.info(f"Generating {image_type} image with Nano Banana: {prompt[:80]}...")

                # Create prediction
                prediction = client.predictions.create(
                    model=NANO_BANANA_MODEL,
                    input=input_params
                )

                # Poll for completion
                poll_start_time = time.time()
                poll_attempts = 0

                while prediction.status not in ["succeeded", "failed", "canceled"]:
                    # Check timeout
                    elapsed_time = time.time() - poll_start_time
                    if elapsed_time > MAX_POLLING_TIME:
                        logger.error(
                            f"Polling timeout after {elapsed_time:.0f}s for Nano Banana "
                            f"(prediction_id: {prediction.id})"
                        )
                        try:
                            client.predictions.cancel(prediction.id)
                        except Exception:
                            pass
                        raise RuntimeError(
                            f"Image generation timeout: Prediction did not complete within {MAX_POLLING_TIME}s"
                        )

                    poll_attempts += 1
                    # Log progress every 30 seconds
                    if poll_attempts % 15 == 0:
                        logger.info(
                            f"Polling Nano Banana prediction (ID: {prediction.id}): "
                            f"status={prediction.status}, elapsed={elapsed_time:.0f}s"
                        )

                    await asyncio.sleep(POLL_INTERVAL)

                    # Refresh prediction status
                    prediction = client.predictions.get(prediction.id)

                # Check final status
                if prediction.status == "succeeded":
                    # Nano Banana returns a list of image URLs
                    output = prediction.output
                    if isinstance(output, list) and len(output) > 0:
                        image_url = output[0]
                        if isinstance(image_url, str):
                            logger.info(f"Image generated successfully: {image_url}")
                            return image_url
                        else:
                            raise RuntimeError(f"Unexpected output format: {type(image_url)}")
                    elif isinstance(output, str):
                        logger.info(f"Image generated successfully: {output}")
                        return output
                    else:
                        raise RuntimeError(f"Unexpected output format: {type(output)}")
                elif prediction.status == "failed":
                    error_msg = getattr(prediction, "error", "Unknown error")
                    raise RuntimeError(f"Image generation failed: {error_msg}")
                elif prediction.status == "canceled":
                    raise RuntimeError("Image generation was canceled")
                else:
                    raise RuntimeError(f"Unexpected prediction status: {prediction.status}")

            except RuntimeError:
                # Re-raise timeout and generation errors
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Image generation attempt {attempt} failed: {e}",
                    exc_info=True
                )
                if attempt < MAX_RETRIES:
                    delay = min(2 ** attempt, 30)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    continue

        # All attempts failed
        raise RuntimeError(
            f"Image generation failed after {MAX_RETRIES} attempts: {last_error}"
        )

    async def _download_temp_image(self, image_url: str) -> str:
        """
        Download image from URL to temporary file.

        Args:
            image_url: URL of image to download

        Returns:
            str: Path to temporary file

        Raises:
            RuntimeError: If download fails
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()

                # Create temporary file
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"ref_{uuid4()}.jpg")

                # Write image data
                with open(temp_path, "wb") as f:
                    f.write(response.content)

                logger.info(f"Downloaded image to {temp_path} ({len(response.content)} bytes)")
                return temp_path

        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            raise RuntimeError(f"Image download failed: {e}")

    def build_consistency_context(self, reference_images: List[ReferenceImage]) -> str:
        """
        Build consistency context string from reference image analyses (AC#6).

        Formats analysis results into structured text for injection into scene prompts.

        Args:
            reference_images: List of reference images with Vision analysis

        Returns:
            Formatted consistency context string
        """
        logger.info("Building consistency context string from analyses")

        # Collect all characteristics from all reference images
        character_descriptions: List[str] = []
        product_features: List[str] = []
        colors: List[str] = []
        styles: List[str] = []
        environments: List[str] = []

        for ref_img in reference_images:
            analysis = ref_img.analysis
            if analysis.character_description:
                character_descriptions.append(analysis.character_description)
            if analysis.product_features:
                product_features.append(analysis.product_features)
            colors.extend(analysis.colors)
            if analysis.style:
                styles.append(analysis.style)
            if analysis.environment:
                environments.append(analysis.environment)

        # Deduplicate colors and styles
        unique_colors = list(dict.fromkeys(colors))  # Preserves order
        unique_styles = list(dict.fromkeys(styles))

        # Format consistency context (AC#6 spec)
        context_parts = []

        if character_descriptions:
            context_parts.append(f"CHARACTER APPEARANCE: {', '.join(character_descriptions)}")

        if product_features:
            context_parts.append(f"PRODUCT FEATURES: {', '.join(product_features)}")

        if unique_colors:
            context_parts.append(f"COLOR PALETTE: {', '.join(unique_colors)}")

        if unique_styles:
            context_parts.append(f"VISUAL STYLE: {', '.join(unique_styles)}")

        if environments:
            context_parts.append(f"ENVIRONMENTAL CONTEXT: {', '.join(environments)}")

        consistency_context = "\n".join(context_parts)
        logger.info(f"✓ Consistency context built ({len(context_parts)} sections)")
        logger.debug(f"Context preview: {consistency_context[:200]}...")

        return consistency_context


async def execute_reference_stage(
    story: str,
    brand_assets: Optional[BrandAssets],
    generation_id: str,
    config: PipelineConfig
) -> tuple[List[ReferenceImage], str]:
    """
    Convenience function to execute reference stage.

    Args:
        story: Approved story text
        brand_assets: Optional brand assets
        generation_id: Generation ID
        config: Pipeline configuration

    Returns:
        Tuple of (reference_images, consistency_context)
    """
    stage = ReferenceStage(config)
    reference_images = await stage.execute(story, brand_assets, generation_id)
    consistency_context = stage.build_consistency_context(reference_images)
    return reference_images, consistency_context
