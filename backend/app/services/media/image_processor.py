"""
Image Processor Service

Handles image analysis using GPT-4 Vision API to extract visual characteristics
for reference image consistency system.

Story 1.2: Master Mode 3-Reference-Image Consistency System
AC#4: GPT-4 Vision analysis for each reference image
AC#5: Parse Vision API response into ReferenceImageAnalysis schema
"""
import logging
import json
import os
from typing import Optional
import httpx

from app.schemas.unified_pipeline import ReferenceImageAnalysis
from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Image analysis service using GPT-4 Vision API.

    Extracts visual characteristics from reference images:
    - Character appearance (age, gender, clothing, hair, facial features, body type)
    - Product features (color, shape, size, branding, key visual elements)
    - Color palette (dominant colors as hex codes, accent colors)
    - Visual style (photorealistic, illustrated, 3D render, sketch)
    - Environmental context (indoor/outdoor, lighting, setting)
    """

    def __init__(self, vision_model: Optional[str] = None):
        """
        Initialize image processor with OpenAI API key.

        Args:
            vision_model: Optional GPT-4 Vision model name override
                         (defaults to gpt-4-vision-preview or env var VISION_MODEL)
        """
        self.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found - Vision analysis will fail")

        self.api_url = "https://api.openai.com/v1/chat/completions"
        # Make Vision model configurable (LOW priority fix from code review)
        self.model = vision_model or os.getenv("VISION_MODEL", "gpt-4-vision-preview")
        self.max_retries = 3
        self.timeout = 30  # seconds

        logger.info(f"Image processor initialized with {self.model}")

    async def analyze_with_vision(
        self,
        image_url: str,
        image_type: str = "unknown"
    ) -> ReferenceImageAnalysis:
        """
        Analyze image with GPT-4 Vision to extract visual characteristics (AC#4).

        This method implements:
        - Vision API call with structured analysis prompt
        - Extraction of 5 key characteristics:
          1. Character appearance
          2. Product features
          3. Color palette
          4. Visual style
          5. Environmental context
        - Parsing response into ReferenceImageAnalysis schema (AC#5)
        - Retry logic with exponential backoff

        Args:
            image_url: Public URL or pre-signed S3 URL of image to analyze
            image_type: Image type hint (product, character, logo, environment)

        Returns:
            ReferenceImageAnalysis with extracted characteristics

        Raises:
            RuntimeError: If Vision API call fails after retries
        """
        logger.info(f"Analyzing {image_type} image with GPT-4 Vision: {image_url[:50]}...")

        # Build Vision analysis prompt (AC#4)
        analysis_prompt = self._build_analysis_prompt(image_type)

        # Prepare Vision API request payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.2  # Low temperature for consistent, factual analysis
        }

        # Call Vision API with retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.api_url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                        timeout=self.timeout
                    )

                    if response.status_code == 200:
                        # Success - parse response (AC#5)
                        analysis = self._parse_vision_response(response.json())
                        logger.info(f"✓ Vision analysis complete: {len(analysis.colors)} colors, style: {analysis.style}")
                        return analysis

                    elif response.status_code in {429, 500, 502, 503, 504}:
                        # Transient error - retry with exponential backoff
                        # Wait times: 2s (attempt 1), 4s (attempt 2), 8s (attempt 3)
                        wait_time = 2 ** attempt
                        logger.warning(f"Vision API returned {response.status_code}, retrying in {wait_time}s (attempt {attempt}/{self.max_retries})")

                        if attempt < self.max_retries:
                            import asyncio
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise RuntimeError(f"Vision API failed after {self.max_retries} retries: {response.status_code}")

                    else:
                        # Permanent error (4xx) - fail immediately
                        error_detail = response.json().get("error", {}).get("message", "Unknown error")
                        logger.error(f"Vision API permanent error ({response.status_code}): {error_detail}")
                        raise RuntimeError(f"Vision API error: {error_detail}")

            except httpx.TimeoutException:
                logger.warning(f"Vision API timeout (attempt {attempt}/{self.max_retries})")
                if attempt >= self.max_retries:
                    raise RuntimeError(f"Vision API timeout after {self.max_retries} attempts")
                import asyncio
                await asyncio.sleep(2 ** attempt)
                continue

            except Exception as e:
                logger.error(f"Unexpected error during Vision API call: {e}", exc_info=True)
                raise RuntimeError(f"Vision analysis failed: {str(e)}")

        # Should never reach here due to exception handling above
        raise RuntimeError("Vision analysis failed: max retries exceeded")

    def _build_analysis_prompt(self, image_type: str) -> str:
        """
        Build Vision analysis prompt for extracting characteristics (AC#4).

        Args:
            image_type: Image type hint (product, character, logo, environment)

        Returns:
            Structured analysis prompt
        """
        prompt = f"""
Analyze this {image_type} image and extract the following visual characteristics in JSON format:

1. **Character Appearance** (if visible): Age, gender, clothing, hair, facial features, body type
2. **Product Features** (if visible): Color, shape, size, branding, key visual elements
3. **Color Palette**: List of dominant and accent colors as hex codes (e.g., ["#FF5733", "#C70039"])
4. **Visual Style**: Photorealistic, illustrated, 3D render, sketch, cartoon, etc.
5. **Environmental Context**: Indoor/outdoor, lighting type, setting description

Return ONLY a valid JSON object with these exact keys:
{{
  "character_description": "detailed character appearance or null if not visible",
  "product_features": "detailed product features or null if not visible",
  "colors": ["#hexcode1", "#hexcode2", ...],
  "style": "visual style description",
  "environment": "environmental context description"
}}

Be specific and detailed. Focus on visual characteristics that will help maintain consistency across multiple video clips.
"""
        return prompt.strip()

    def _parse_vision_response(self, response_data: dict) -> ReferenceImageAnalysis:
        """
        Parse Vision API response into ReferenceImageAnalysis schema (AC#5).

        Args:
            response_data: Raw Vision API response JSON

        Returns:
            ReferenceImageAnalysis with extracted characteristics

        Raises:
            RuntimeError: If response parsing fails
        """
        try:
            # Extract content from Vision API response
            content = response_data["choices"][0]["message"]["content"]
            logger.debug(f"Vision API raw content: {content[:200]}...")

            # Parse JSON from response (Vision API should return JSON)
            # Handle markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content.split("```json\n", 1)[1]
                content = content.rsplit("\n```", 1)[0]
            elif content.startswith("```"):
                content = content.split("```\n", 1)[1]
                content = content.rsplit("\n```", 1)[0]

            analysis_data = json.loads(content)

            # Create ReferenceImageAnalysis from parsed JSON
            analysis = ReferenceImageAnalysis(
                character_description=analysis_data.get("character_description"),
                product_features=analysis_data.get("product_features"),
                colors=analysis_data.get("colors", []),
                style=analysis_data.get("style"),
                environment=analysis_data.get("environment")
            )

            logger.debug(f"Parsed analysis: {analysis.model_dump()}")
            return analysis

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Vision API response: {e}")
            logger.error(f"Response data: {response_data}")

            # Return fallback analysis rather than failing
            logger.warning("Returning fallback analysis due to parsing error")
            return ReferenceImageAnalysis(
                character_description="Unable to analyze - parsing error",
                product_features="Unable to analyze - parsing error",
                colors=["#CCCCCC"],
                style="unknown",
                environment="unknown"
            )


# Global image processor instance
_image_processor: Optional[ImageProcessor] = None


def get_image_processor() -> ImageProcessor:
    """Get or create image processor instance."""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor
