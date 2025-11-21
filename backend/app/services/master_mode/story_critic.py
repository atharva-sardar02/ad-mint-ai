"""
Story Critic Agent for Master Mode.

The Story Critic evaluates story drafts and provides detailed feedback for improvements.
It assesses alignment with user prompts, narrative coherence, and advertisement effectiveness.
"""
import json
import logging
from typing import List, Optional

import openai

from app.core.config import settings
from app.services.master_mode.schemas import CritiqueResult

logger = logging.getLogger(__name__)

# System prompt for Story Critic
STORY_CRITIC_SYSTEM_PROMPT = """You are an expert advertisement story critic with extensive experience evaluating video advertisement concepts for production readiness.

Your role:
- Critically evaluate advertisement story drafts for video generation readiness
- Assess alignment with user prompts and brand requirements
- Identify narrative strengths and weaknesses
- **CRITICALLY EVALUATE VISUAL DETAIL SUFFICIENCY** for video production
- Provide specific, actionable feedback for improvement
- Score stories on multiple quality dimensions

Evaluation Criteria:

1. **Alignment with User Prompt** (0-20 points)
   - Does the story match the user's vision?
   - Are key elements from the prompt included?
   - Is the brand/product properly featured?
   - Does it serve the intended purpose?

2. **Visual Detail Sufficiency for Video Generation** (0-25 points) ⚠️ MOST CRITICAL
   - **Character/Product Descriptions**: Are they detailed enough to reproduce visually?
     - Characters: Forensic-level detail (age, height, build, hair color/style, face shape, eye color, skin tone, features, clothing)?
     - Products: Engineering-level specs (dimensions, materials, exact colors, shapes, branding, textures)?
   - **Scene Visual Descriptions**: Are scenes described with enough detail (80-150 words per scene)?
     - Environment, lighting, camera angles, composition, color palette?
     - Starting and ending poses/positions?
   - **Cinematography Specifications**: Camera angles, movements, focal lengths, shot types?
   - **Subject Consistency**: Is it clear which scenes have the subject and which don't?
   - **Production Specifications**: Aspect ratio, color grading, lighting setups?
   - Can a video generation AI create this without ambiguity?

3. **Narrative Coherence** (0-15 points)
   - Is the story logically structured?
   - Do scenes flow naturally?
   - Is the narrative arc clear and compelling?
   - Are transitions well-planned?

4. **Character/Product Development** (0-10 points)
   - Are characters/products well-defined?
   - Do they serve the story purpose?
   - Are they described consistently across scenes?
   - Is the subject identity maintained?

5. **Scene Flow and Pacing** (0-10 points)
   - Is pacing appropriate for advertisement length?
   - Do scenes build effectively?
   - Are scene durations justified (3-7 seconds each)?
   - Are transitions smooth and purposeful?

6. **Emotional Impact** (0-10 points)
   - Does the story evoke the intended emotions?
   - Are emotional beats well-placed?
   - Is the call-to-action compelling?
   - Does it follow AIDA framework effectively?

7. **Advertisement Effectiveness** (0-5 points)
   - Will this create an effective advertisement?
   - Is the message clear and memorable?
   - Does it serve the brand's goals?

8. **Technical Production Readiness** (0-5 points)
   - Are all technical specifications provided?
   - Is the story unambiguous and actionable?
   - Can this be handed to a production team as-is?

Output Format:
You MUST return a valid JSON object with this exact structure:
{
    "approval_status": "approved" or "needs_revision",
    "overall_score": <number 0-100>,
    "critique": "<detailed critique text explaining your evaluation, focusing heavily on visual detail sufficiency>",
    "strengths": ["strength 1", "strength 2", ...],
    "improvements": ["improvement 1", "improvement 2", ...],
    "priority_fixes": ["most important fix 1", "most important fix 2", ...]
}

Approval Guidelines:
- "approved": Story is production-ready (score >= 85) AND has SUFFICIENT VISUAL DETAIL for video generation
- "needs_revision": Story needs improvements (score < 85) OR lacks critical visual details

⚠️ CRITICAL EVALUATION FOCUS:
Your PRIMARY focus should be on whether the story contains enough visual detail to generate consistent, high-quality videos:
- Are character/product descriptions specific enough? (not "woman in her 30s" but "32-year-old woman, 5'6", chestnut brown shoulder-length hair...")
- Are scenes visually described in detail? (not "product on table" but "8-inch frosted glass bottle centered on white marble surface, soft overhead lighting from 45-degree angle...")
- Are camera specifications provided? (not "close-up" but "close-up shot, 50mm lens, f/1.4, eye-level angle, static camera...")
- Is subject consistency maintained? (does story specify which scenes have the subject and reference "EXACT SAME" appearance?)

Common Issues to Flag:
- Generic descriptions ("woman", "bottle", "kitchen") → Request specific details
- Missing measurements or exact colors → Request precise specifications
- Vague camera work ("shot of...") → Request camera angle, lens, movement
- Inconsistent subject appearance → Request consistency markers
- Missing scene durations → Request 3-7 second durations per scene
- Ambiguous lighting → Request specific lighting setup
- No mention of whether subject appears in each scene → Request subject presence specification

Be thorough but constructive. Your feedback will guide story improvements. PRIORITIZE visual detail feedback above all else.
"""


async def critique_story(
    story_draft: str,
    user_prompt: str,
    conversation_history: Optional[List[dict]] = None,
    model: str = "gpt-4o",
    max_retries: int = 3
) -> CritiqueResult:
    """
    Critique a story draft and provide detailed feedback.
    
    Args:
        story_draft: The story draft to critique (Markdown format)
        user_prompt: The original user prompt for reference
        conversation_history: Optional conversation history for context
        model: OpenAI model to use (default: gpt-4o)
        max_retries: Maximum retry attempts on errors
        
    Returns:
        CritiqueResult with approval status, score, and feedback
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Build context from conversation history
    context_messages = []
    if conversation_history:
        for entry in conversation_history:
            if entry.get("role") == "critic":
                critique = entry.get("content", {})
                context_messages.append({
                    "role": "assistant",
                    "content": f"Previous critique (Iteration {entry.get('iteration', '?')}):\n\n{json.dumps(critique, indent=2)}"
                })
    
    # Build the main user message
    user_message = f"""Evaluate this advertisement story draft:

ORIGINAL USER PROMPT:
"{user_prompt}"

STORY DRAFT TO EVALUATE:
{story_draft}

Provide a comprehensive critique following the evaluation criteria."""
    
    if conversation_history:
        user_message += "\n\nConsider previous critiques in the conversation history when evaluating improvements."
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Story Critic] Critiquing story, attempt {attempt}/{max_retries}")
                
                messages = [
                    {"role": "system", "content": STORY_CRITIC_SYSTEM_PROMPT},
                    *context_messages,
                    {"role": "user", "content": user_message}
                ]
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.7,  # Analytical but creative in feedback
                    max_tokens=2000,
                )
                
                if not response.choices or not response.choices[0].message:
                    error_msg = "Empty response from OpenAI API"
                    logger.error(f"[Story Critic Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                content = response.choices[0].message.content
                if not content:
                    error_msg = "Response content is None"
                    logger.error(f"[Story Critic Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Parse JSON response
                try:
                    critique_data = json.loads(content)
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON response: {str(e)}"
                    logger.error(f"[Story Critic Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Validate and create CritiqueResult
                critique_result = CritiqueResult(**critique_data)
                
                logger.info(
                    f"[Story Critic] Critique complete - "
                    f"Status: {critique_result.approval_status}, "
                    f"Score: {critique_result.overall_score:.1f}/100"
                )
                
                return critique_result
                
            except Exception as e:
                logger.error(f"[Story Critic Error] Attempt {attempt}/{max_retries} failed: {str(e)}")
                if attempt < max_retries:
                    last_error = str(e)
                    continue
                raise
        
        # Should not reach here, but just in case
        raise ValueError(f"Failed after {max_retries} attempts. Last error: {last_error}")
        
    finally:
        await async_client.close()

