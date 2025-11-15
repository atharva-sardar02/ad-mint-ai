"""
LLM enhancement service for processing user prompts into structured ad specifications.
"""
import json
import logging
from typing import Optional
import openai
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.generation import AdSpecification

logger = logging.getLogger(__name__)

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
5. Scene breakdown - 3-5 scenes that follow the selected framework, each with:
   - Scene number (1, 2, 3...)
   - Scene type (framework-specific, e.g., "Problem", "Solution" for PAS)
   - Visual prompt (detailed description for video generation)
   - Text overlay (text, position, font_size, color, animation)
   - Duration (3-7 seconds per scene)

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
    }
  ]
}

Ensure the total duration of all scenes equals approximately 15 seconds for MVP."""


async def enhance_prompt_with_llm(
    user_prompt: str, max_retries: int = 3
) -> AdSpecification:
    """
    Send user prompt to OpenAI GPT-4 API and return structured AdSpecification.
    
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
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured")
        raise ValueError("OpenAI API key is not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Calling OpenAI API (attempt {attempt}/{max_retries})")
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
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
            
            # Validate with Pydantic schema
            try:
                ad_spec = AdSpecification(**json_data)
                logger.info(f"Successfully validated LLM response (attempt {attempt})")
                
                # Log cost (approximate - GPT-4 pricing)
                # Input tokens ~500, output tokens ~1500 = ~$0.01 per generation
                logger.info(f"LLM enhancement completed - framework: {ad_spec.framework}, scenes: {len(ad_spec.scenes)}")
                
                return ad_spec
                
            except ValidationError as e:
                logger.warning(f"Pydantic validation failed (attempt {attempt}): {e}")
                if attempt < max_retries:
                    continue
                raise ValueError(f"LLM response doesn't match schema: {e}")
                
        except openai.APIError as e:
            last_error = e
            logger.warning(f"OpenAI API error (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                continue
            raise
    
    # If we get here, all retries failed
    if last_error:
        raise last_error
    raise ValueError("Failed to get valid response from LLM after retries")

