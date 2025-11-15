"""
LLM enhancement service for processing user prompts into structured ad specifications.
"""
import asyncio
import json
import logging
from typing import Optional
import openai
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.generation import AdSpecification

logger = logging.getLogger(__name__)

# Retry configuration for rate limits
INITIAL_RETRY_DELAY = 2  # seconds
MAX_RETRY_DELAY = 60  # seconds

# System prompt for LLM enhancement
SYSTEM_PROMPT = """You are an expert advertising copywriter and strategist. Your task is to analyze a user's product description and create a comprehensive ad specification that will be used to generate a professional video advertisement.

Analyze the user's prompt and extract:
1. Product description - A clear, compelling description of the product or service
2. Brand guidelines - Brand name, colors (hex codes), visual style keywords, and mood
3. Ad specifications - Target audience, call-to-action, and tone
4. Framework selection - Choose the best framework (PAS, BAB, or AIDA) based on the product type:
   - PAS (Problem-Agitation-Solution): Best for products that solve a specific problem
   - BAB (Before-After-Bridge): Best for transformation or improvement products
   - AIDA (Attention-Interest-Desire-Action): Best for general products needing awareness
5. Scene breakdown - REQUIRED: You MUST create 3-5 scenes (minimum 3, maximum 5) that follow the selected framework, each with:
   - Scene number (1, 2, 3...)
   - Scene type (framework-specific, e.g., "Problem", "Agitation", "Solution" for PAS)
   - Visual prompt (detailed description for video generation)
   - Text overlay (text, position, font_size, color, animation)
   - Duration (3-7 seconds per scene)

CRITICAL: The "scenes" array MUST contain at least 3 scenes and at most 5 scenes. Do not return fewer than 3 scenes.

Return your response as valid JSON matching this exact structure:
{
  "product_description": "string",
  "brand_guidelines": {
    "brand_name": "string",
    "brand_colors": ["#hex1", "#hex2"],
    "visual_style_keywords": "string",
    "mood": "string"
  },
  "ad_specifications": {
    "target_audience": "string",
    "call_to_action": "string",
    "tone": "string"
  },
  "framework": "PAS" | "BAB" | "AIDA",
  "scenes": [
    {
      "scene_number": 1,
      "scene_type": "string",
      "visual_prompt": "string",
      "text_overlay": {
        "text": "string",
        "position": "top" | "center" | "bottom",
        "font_size": 48,
        "color": "#hex",
        "animation": "fade_in" | "slide_up" | "none"
      },
      "duration": 5
    },
    {
      "scene_number": 2,
      "scene_type": "string",
      "visual_prompt": "string",
      "text_overlay": {
        "text": "string",
        "position": "top" | "center" | "bottom",
        "font_size": 48,
        "color": "#hex",
        "animation": "fade_in" | "slide_up" | "none"
      },
      "duration": 5
    },
    {
      "scene_number": 3,
      "scene_type": "string",
      "visual_prompt": "string",
      "text_overlay": {
        "text": "string",
        "position": "top" | "center" | "bottom",
        "font_size": 48,
        "color": "#hex",
        "animation": "fade_in" | "slide_up" | "none"
      },
      "duration": 5
    }
  ]
}

IMPORTANT: 
- The "scenes" array MUST have at least 3 items (you can add 4 or 5 if appropriate)
- Ensure the total duration of all scenes equals approximately 15 seconds for MVP
- Each scene must have a unique scene_number (1, 2, 3, etc.)"""


async def enhance_prompt_with_llm(
    user_prompt: str, max_retries: int = 3
) -> AdSpecification:
    """
    Send user prompt to OpenAI GPT-4 Turbo API and return structured AdSpecification.
    
    Args:
        user_prompt: User's text prompt (10-500 characters)
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        AdSpecification: Validated Pydantic model with ad specification
    
    Raises:
        ValueError: If API key is missing or invalid
        openai.APIError: If API call fails after retries
        ValidationError: If LLM response doesn't match schema
    """
    # Mask API key for logging (first 4 + last 4 chars)
    def mask_key(key: str) -> str:
        if not key or len(key) < 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"
    
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured")
        raise ValueError("OpenAI API key is not configured. API Key: (not set)")
    
    masked_key = mask_key(settings.OPENAI_API_KEY)
    logger.info(f"Using OpenAI API key: {masked_key}")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    last_error = None
    current_prompt = user_prompt  # Use a mutable variable for retries
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Calling OpenAI API (attempt {attempt}/{max_retries})")
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": current_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content}")
            
            # Parse JSON
            try:
                json_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in LLM response (attempt {attempt}): {e}")
                if attempt < max_retries:
                    continue
                raise ValueError(f"LLM returned invalid JSON: {e}")
            
            # Check scenes count before validation for better error messages
            scenes_count = len(json_data.get("scenes", []))
            if scenes_count < 3:
                logger.warning(
                    f"LLM returned only {scenes_count} scene(s), but at least 3 are required (attempt {attempt})"
                )
                if attempt < max_retries:
                    # Add a more explicit instruction for retry
                    current_prompt = f"{user_prompt}\n\nIMPORTANT: You must return at least 3 scenes in the 'scenes' array. You previously returned only {scenes_count} scene(s)."
                    continue
                raise ValueError(
                    f"LLM returned only {scenes_count} scene(s), but at least 3 are required. "
                    f"Please ensure your prompt is clear about needing multiple scenes."
                )
            
            # Validate with Pydantic schema
            try:
                ad_spec = AdSpecification(**json_data)
                logger.info(f"Successfully validated LLM response (attempt {attempt})")
                
                # Log cost (approximate - GPT-4 Turbo pricing)
                # Input tokens ~500, output tokens ~1500 = ~$0.01 per generation
                logger.info(f"LLM enhancement completed - framework: {ad_spec.framework}, scenes: {len(ad_spec.scenes)}")
                
                return ad_spec
                
            except ValidationError as e:
                logger.warning(f"Pydantic validation failed (attempt {attempt}): {e}")
                if attempt < max_retries:
                    continue
                raise ValueError(f"LLM response doesn't match schema: {e}")
                
        except openai.RateLimitError as e:
            last_error = e
            if attempt < max_retries:
                # Exponential backoff for rate limits (429 errors)
                delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
                logger.warning(
                    f"OpenAI rate limit/quota exceeded (attempt {attempt}/{max_retries}). "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
                continue
            logger.error(f"OpenAI rate limit exceeded after {max_retries} attempts: {e}")
            error_msg = f"OpenAI rate limit/quota exceeded after {max_retries} attempts. "
            error_msg += f"API Key: {masked_key}. "
            error_msg += "Please check your OpenAI account billing and quota limits."
            raise RuntimeError(error_msg)
        
        except openai.APIError as e:
            last_error = e
            # Check if it's a 429 error (rate limit/quota) - check status_code or response body
            status_code = getattr(e, 'status_code', None)
            response_body = getattr(e, 'response', None) or getattr(e, 'body', None)
            
            # Check for 429 in status code or error response
            is_rate_limit = (
                status_code == 429 or
                (response_body and isinstance(response_body, dict) and 
                 response_body.get('error', {}).get('code') == 'insufficient_quota') or
                (hasattr(e, 'message') and 'quota' in str(e.message).lower()) or
                (hasattr(e, 'message') and '429' in str(e.message))
            )
            
            if is_rate_limit:
                if attempt < max_retries:
                    # Exponential backoff for 429/quota errors
                    delay = min(INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), MAX_RETRY_DELAY)
                    logger.warning(
                        f"OpenAI 429/quota error (attempt {attempt}/{max_retries}). "
                        f"Retrying in {delay}s... Error: {e}"
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"OpenAI 429/quota error after {max_retries} attempts: {e}")
                error_msg = f"OpenAI rate limit/quota exceeded after {max_retries} attempts. "
                error_msg += f"API Key: {masked_key}. "
                error_msg += "Please check your OpenAI account billing and quota limits at https://platform.openai.com/account/billing"
                raise RuntimeError(error_msg)
            
            logger.warning(f"OpenAI API error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                # Small delay for other API errors
                await asyncio.sleep(1)
                continue
            raise
    
    # If we get here, all retries failed
    if last_error:
        raise last_error
    raise ValueError("Failed to get valid response from LLM after retries")

