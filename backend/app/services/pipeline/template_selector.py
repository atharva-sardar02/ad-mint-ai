"""
Template Selector (Stage 0)
Analyzes user prompt to intelligently select the best story template.
"""

import json
import logging
from typing import Dict, Any, Optional

import openai

from app.core.config import settings
from app.services.pipeline.story_templates import get_templates_summary, get_template

logger = logging.getLogger(__name__)


def get_template_selector_prompt() -> str:
    """Generate system prompt for template selection."""
    templates_summary = get_templates_summary()
    
    templates_desc = "\n".join([
        f"{i+1}. **{t['name']}** ({t['template_id']})\n"
        f"   - Description: {t['description']}\n"
        f"   - Best for: {', '.join(t['best_for'])}\n"
        f"   - Keywords: {', '.join(t['keywords'][:5])}\n"
        f"   - Tone: {t['emotional_tone']}"
        for i, t in enumerate(templates_summary)
    ])
    
    return f"""You are an expert creative director and advertising strategist. Your job is to analyze a user's advertisement prompt and select the OPTIMAL storytelling template that will create the most compelling narrative.

Available Story Templates:

{templates_desc}

Your task:
1. Analyze the user's prompt deeply
2. Identify key themes, emotions, product type, target audience
3. Match to the BEST template based on:
   - Product category (tech, food, fashion, service, lifestyle, etc.)
   - Emotional intent (inspire, solve problem, delight, reassure, excite)
   - Marketing goal (awareness, conversion, engagement, trust)
   - Brand personality signals (bold, warm, sophisticated, playful, premium)
   - Keywords and phrases in the prompt

4. Return your analysis in JSON format

IMPORTANT: Be decisive. Choose the ONE template that fits best, but also provide an alternative backup.

Return JSON in this EXACT format:
{{
  "selected_template": "template_id",
  "confidence": 0.85,
  "reasoning": "Clear explanation of why this template fits best",
  "alternative_template": "backup_template_id",
  "narrative_focus": "What should be emphasized in the story (e.g., 'transformation journey', 'sensory indulgence', 'community belonging')",
  "emotional_goal": "Primary emotion to evoke (e.g., 'empowerment', 'comfort', 'excitement', 'trust')",
  "key_themes": ["theme1", "theme2", "theme3"],
  "product_category": "category name",
  "target_audience": "audience description"
}}

Examples:

User Prompt: "Luxury perfume capturing midnight elegance"
Response: {{
  "selected_template": "teaser-reveal",
  "confidence": 0.92,
  "reasoning": "Luxury product + 'midnight' suggests mystery. Best served with anticipation and dramatic reveal.",
  "alternative_template": "sensory-experience",
  "narrative_focus": "Mystery and sophistication with dramatic reveal",
  "emotional_goal": "Intrigue and desire",
  "key_themes": ["luxury", "mystery", "elegance"],
  "product_category": "luxury fragrance",
  "target_audience": "sophisticated adults seeking premium products"
}}

User Prompt: "Fitness app for busy moms to stay healthy"
Response: {{
  "selected_template": "problem-agitate-solve",
  "confidence": 0.88,
  "reasoning": "Clear problem (busy moms struggling with health). PAS template empathizes with pain and positions app as solution.",
  "alternative_template": "before-after-bridge",
  "narrative_focus": "Empathy with busy lifestyle, app as empowering solution",
  "emotional_goal": "Relief and empowerment",
  "key_themes": ["time pressure", "health", "empowerment"],
  "product_category": "fitness app",
  "target_audience": "busy mothers balancing family and health"
}}

User Prompt: "Artisan coffee that starts your morning right"
Response: {{
  "selected_template": "emotional-arc",
  "confidence": 0.87,
  "reasoning": "Coffee + morning = intimate ritual. Emotional arc captures warmth and comfort of morning moments.",
  "alternative_template": "sensory-experience",
  "narrative_focus": "Warm morning ritual, comfort and connection",
  "emotional_goal": "Comfort and contentment",
  "key_themes": ["morning ritual", "comfort", "quality"],
  "product_category": "artisan coffee",
  "target_audience": "coffee enthusiasts who value quality and ritual"
}}

Now analyze the user's prompt and return your template selection."""


async def select_template(
    user_prompt: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Analyze user prompt and select optimal story template.
    
    Args:
        user_prompt: User's advertisement prompt
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Template selection with reasoning and metadata
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured. Falling back to default template.")
        return {
            "selected_template": "aida",
            "confidence": 0.5,
            "reasoning": "No API key configured - using default AIDA template",
            "alternative_template": "problem-agitate-solve",
            "narrative_focus": "General product presentation",
            "emotional_goal": "Interest and desire",
            "key_themes": ["product", "benefit"],
            "product_category": "unknown",
            "target_audience": "general"
        }
    
    model = "gpt-4o-mini"  # Fast and cost-effective for classification
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = get_template_selector_prompt()
    user_message = f"Analyze this advertisement prompt and select the best storytelling template:\n\n\"{user_prompt}\""
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Template Selector] Analyzing prompt, attempt {attempt}/{max_retries}")
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,  # Low temperature for consistent classification
                    max_tokens=800,
                )
                
                if not response.choices or not response.choices[0].message:
                    error_msg = "Empty response from OpenAI API"
                    logger.error(f"[Template Selector Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                content = response.choices[0].message.content
                if not content:
                    error_msg = "Response content is None"
                    logger.error(f"[Template Selector Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Parse JSON
                try:
                    selection = json.loads(content)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON: {e}. Content: {content[:200]}"
                    logger.warning(f"[Template Selector Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Validate template exists
                selected_template_id = selection.get("selected_template")
                if not selected_template_id:
                    raise ValueError("Missing 'selected_template' in response")
                
                template = get_template(selected_template_id)
                if not template:
                    logger.warning(f"[Template Selector] Invalid template ID '{selected_template_id}', falling back to AIDA")
                    selection["selected_template"] = "aida"
                    selection["reasoning"] += " (Note: Original selection was invalid, defaulted to AIDA)"
                
                # Validate alternative template
                alt_template_id = selection.get("alternative_template")
                if alt_template_id:
                    alt_template = get_template(alt_template_id)
                    if not alt_template:
                        logger.warning(f"[Template Selector] Invalid alternative template ID '{alt_template_id}'")
                        selection["alternative_template"] = "aida"
                
                logger.info(f"✅ Template selected: {selection['selected_template']} (confidence: {selection.get('confidence', 'N/A')})")
                logger.info(f"   Reasoning: {selection.get('reasoning', 'N/A')}")
                
                return selection
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Template Selector Error] Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 10))
                    continue
        
        # If all retries failed, return default
        logger.error(f"[Template Selector] All attempts failed. Falling back to default AIDA template. Last error: {last_error}")
        return {
            "selected_template": "aida",
            "confidence": 0.3,
            "reasoning": f"Template selection failed after {max_retries} attempts. Using default AIDA template.",
            "alternative_template": "problem-agitate-solve",
            "narrative_focus": "General product presentation",
            "emotional_goal": "Interest and desire",
            "key_themes": ["product", "benefit"],
            "product_category": "unknown",
            "target_audience": "general",
            "error": str(last_error)
        }
    
    finally:
        await async_client.close()


async def select_template_with_override(
    user_prompt: str,
    template_override: Optional[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Select template with optional manual override.
    
    Args:
        user_prompt: User's advertisement prompt
        template_override: Optional manual template selection (overrides AI)
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Template selection with reasoning and metadata
    """
    # If user manually specified a template, use it
    if template_override:
        template = get_template(template_override)
        if template:
            logger.info(f"✅ Using manually specified template: {template_override}")
            return {
                "selected_template": template_override,
                "confidence": 1.0,
                "reasoning": f"Manually specified by user: {template['name']}",
                "alternative_template": "aida",
                "narrative_focus": template["narrative_guidance"],
                "emotional_goal": template["emotional_tone"],
                "key_themes": template["keywords"][:3],
                "product_category": "user-specified",
                "target_audience": "user-specified",
                "manual_override": True
            }
        else:
            logger.warning(f"Invalid template override '{template_override}', falling back to AI selection")
    
    # Otherwise, use AI selection
    return await select_template(user_prompt, max_retries)

