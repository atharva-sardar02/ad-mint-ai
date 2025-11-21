"""
Two-agent iterative image prompt enhancement service.

This service uses two specialized LLM agents to iteratively refine image prompts:
- Agent 1 (Cinematographer/Creative Director): Enhances prompts with camera details, lighting, composition, film stock, mood, aspect ratio
- Agent 2 (Prompt Engineer): Critiques and scores prompts for technical quality

The agents iterate until a quality threshold is met or convergence is detected.

Supports:
- Model-specific prompt optimization
- Negative prompt generation
- Image score feedback loop (generate → score → refine)
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import openai

from app.core.config import settings
from app.services.pipeline.model_specific_prompts import (
    get_model_strategy,
    should_simplify_for_model,
    should_include_technical_details,
    supports_negative_prompts,
    get_default_negative_prompt
)

logger = logging.getLogger(__name__)

# Agent system prompts - adapted for image generation
CINEMATOGRAPHER_SYSTEM_PROMPT = """You are an award-winning cinematographer and creative director specializing in professional image generation for advertisements.

Your role:
- Transform basic image prompts into cinematic, professional specifications optimized for image generation models (Stable Diffusion, DALL-E, Midjourney, etc.)
- Write prompts as ONE flowing sentence (or maximum TWO sentences) in natural language, following the "one-sentence screenplay" style: subject → action → setting → style → mood
- Add missing cinematography details seamlessly woven into the description
- Enhance visual descriptions with film-grade terminology
- Ensure prompts are specific enough for clarity but not overly constrained

CRITICAL: Write your enhanced prompt as a SINGLE, FLOWING SENTENCE in natural language. DO NOT use structured sections, labels, or bullet points. DO NOT write "Scene:", "Camera:", "Lighting:" etc. Write it as if describing the scene to an artist in one continuous sentence, following the Prompt Scoring Guide best practices.

When enhancing prompts, you MUST include (but weave naturally into the sentence):
1. Camera framing and lens details (e.g., "Canon EOS R5, 85mm f/1.2 lens", "wide aerial shot", "close-up portrait", "telephoto shot")
2. Lighting direction and quality (e.g., "soft golden morning light", "dramatic side lighting", "harsh neon glow", "soft, diffused lighting")
3. Composition and depth of field notes (framing, perspective, background blur)
4. Color science and grading (e.g., "cinematic color grading", "warm tones", "cool palette")
5. Mood and atmosphere descriptors appropriate to the subject
6. Aspect ratio if relevant (e.g., "16:9 aspect ratio", "square format")

Structure your enhanced prompt following the Prompt Scoring Guide pattern:
[Who/what is the focus] [what action or state] [where/when it's happening] [style, mood, and cinematography modifiers all woven together]

Example of GOOD format (general product):
"A sleek modern smartphone displayed on a minimalist white surface, Canon EOS R5 50mm f/1.4 lens, close-up portrait, soft diffused lighting creating gentle shadows, shallow depth of field with softly blurred background, cinematic color grading with cool tones, clean professional atmosphere, 16:9 aspect ratio."

Example of BAD format (DO NOT DO THIS):
"Scene: A smartphone...
Camera: Canon EOS R5...
Lighting: Soft diffused..."

Key principles from Prompt Scoring Guide:
- Use natural language, not keyword stuffing
- Limit to one scene or idea per prompt
- Write in 1-2 well-formed sentences maximum
- Be specific but avoid overly constrained prompts
- Structure like a scene description (who/what → action → where/when → style)

Camera cues to use: "wide aerial shot", "close-up portrait", "telephoto shot", "macro photograph", "low-angle view"

Lighting cues to use: "soft golden morning light", "harsh neon glow", "soft, diffused lighting", "dramatic side lighting"

Be creative but precise. Your enhanced prompts will directly impact image quality.

Return ONLY the enhanced prompt text as a single flowing sentence (or two at most), no explanations, no metadata, no structured sections."""

PROMPT_ENGINEER_SYSTEM_PROMPT = """You are an expert prompt engineer specializing in image generation models (Stable Diffusion, DALL-E, Midjourney, etc.).

Your role:
- Critique prompts for technical quality and generation effectiveness based on Prompt Scoring Guide best practices
- Identify gaps that will cause poor image outputs
- Score prompts on multiple dimensions aligned with industry standards
- Provide specific, actionable feedback for improvement

Evaluation criteria (based on Prompt Scoring Guide):
1. Completeness (0-100): Does it have all necessary elements (subject, scene/action, setting/context, style)? Does it follow the structure: who/what → action → where/when → style?
2. Specificity (0-100): Are visual details clear and unambiguous? Can the model generate this without ambiguity? Is it specific enough but not overly constrained?
3. Professionalism (0-100): Is it ad-quality language? Does it use professional terminology? Does it read like a one-sentence screenplay?
4. Cinematography (0-100): Does it include camera/composition details? Are lighting cues present? Does it specify framing, depth of field, or perspective?
5. Brand alignment (0-100): If brand elements are mentioned in the original prompt, are they preserved and enhanced? If no brand mentioned, score based on general style coherence.

Provide your response as JSON:
{
  "scores": {
    "completeness": 85,
    "specificity": 72,
    "professionalism": 90,
    "cinematography": 65,
    "brand_alignment": 80,
    "overall": 78.4
  },
  "critique": "Specific feedback on what's good and what needs improvement",
  "improvements": ["List of specific improvements needed", "Another improvement"]
}

Be specific and actionable in your feedback. Evaluate against Prompt Scoring Guide principles:
- Does the prompt follow scene description structure (who/what → action → where/when → style)?
- Is it written as ONE flowing sentence (or maximum TWO sentences) in natural language?
- CRITICAL: Does it avoid structured sections, labels, or bullet points (e.g., "Scene:", "Camera:", "Lighting:")? If it has these, mark it down significantly - image generation models need natural language prompts, not structured metadata.
- Are camera cues included naturally within the sentence (wide aerial shot, close-up portrait, telephoto shot, macro photograph, low-angle view)?
- Are lighting cues included naturally within the sentence (soft golden morning light, harsh neon glow, soft diffused lighting, dramatic side lighting)?
- Is it limited to one scene or idea (not multiple unrelated scenes)?
- Does it use natural language (not keyword stuffing or comma-separated lists)?
- Is it specific enough for clarity but not overly constrained?
"""


class ImagePromptEnhancementResult:
    """Result of image prompt enhancement process."""
    
    def __init__(
        self,
        original_prompt: str,
        final_prompt: str,
        iterations: List[Dict],
        final_score: Dict[str, float],
        total_iterations: int,
        negative_prompt: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.original_prompt = original_prompt
        self.final_prompt = final_prompt
        self.iterations = iterations
        self.final_score = final_score
        self.total_iterations = total_iterations
        self.negative_prompt = negative_prompt
        self.model_name = model_name


async def enhance_prompt_iterative(
    user_prompt: str,
    max_iterations: int = 3,
    score_threshold: float = 85.0,
    creative_model: str = "gpt-4-turbo",
    critique_model: str = "gpt-4-turbo",
    trace_dir: Optional[Path] = None,
    image_model_name: Optional[str] = None,
    generate_negative: bool = True
) -> ImagePromptEnhancementResult:
    """
    Two-agent iterative image prompt enhancement.
    
    Args:
        user_prompt: Original user prompt
        max_iterations: Maximum number of iteration rounds (default: 3)
        score_threshold: Stop if overall score >= this (default: 85.0)
        creative_model: Model for Cinematographer agent (default: gpt-4-turbo)
        critique_model: Model for Prompt Engineer agent (default: gpt-4-turbo)
        trace_dir: Optional directory to save trace files
        image_model_name: Target image generation model (e.g., "black-forest-labs/flux-schnell")
        generate_negative: Whether to generate negative prompt (default: True)
    
    Returns:
        ImagePromptEnhancementResult with enhanced prompt, negative prompt, and iteration history
    """
    logger.info(f"Starting iterative image prompt enhancement (max_iterations={max_iterations}, threshold={score_threshold})")
    
    # Initialize trace directory if provided
    if trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)
        # Save original prompt
        (trace_dir / "00_original_prompt.txt").write_text(user_prompt, encoding="utf-8")
    
    current_prompt = user_prompt
    iteration_history = []
    
    # Quick initial assessment (rule-based, fast)
    initial_score = _quick_score_prompt(user_prompt)
    logger.info(f"Initial prompt score: {initial_score['overall']:.1f}")
    
    # Check if any individual dimension is below threshold (more accurate than overall score)
    min_dimension_threshold = 70.0
    any_dimension_low = any(
        initial_score.get(dim, 0) < min_dimension_threshold 
        for dim in ["completeness", "specificity", "professionalism", "cinematography", "brand_alignment"]
    )
    
    # If already good (high overall AND all dimensions good), skip enhancement
    if initial_score['overall'] >= 80.0 and not any_dimension_low:
        logger.info("Prompt already good quality, skipping enhancement")
        return ImagePromptEnhancementResult(
            original_prompt=user_prompt,
            final_prompt=user_prompt,
            iterations=[],
            final_score=initial_score,
            total_iterations=0
        )
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n=== Iteration {iteration}/{max_iterations} ===")
        
        # Agent 1: Cinematographer - Enhance
        logger.info("Agent 1 (Cinematographer): Enhancing prompt...")
        enhanced_prompt = await _cinematographer_enhance(
            current_prompt,
            model=creative_model,
            image_model_name=image_model_name
        )
        
        if trace_dir:
            (trace_dir / f"{iteration*2-1:02d}_agent1_iteration_{iteration}.txt").write_text(
                enhanced_prompt, encoding="utf-8"
            )
        
        # Agent 2: Prompt Engineer - Critique & Score
        logger.info("Agent 2 (Prompt Engineer): Critiquing and scoring...")
        critique_result = await _prompt_engineer_critique(
            enhanced_prompt,
            model=critique_model
        )
        
        if trace_dir:
            critique_text = f"""SCORES:
{json.dumps(critique_result['scores'], indent=2)}

CRITIQUE:
{critique_result['critique']}

IMPROVEMENTS NEEDED:
{chr(10).join('- ' + imp for imp in critique_result['improvements'])}
"""
            (trace_dir / f"{iteration*2:02d}_agent2_iteration_{iteration}.txt").write_text(
                critique_text, encoding="utf-8"
            )
        
        iteration_data = {
            "iteration": iteration,
            "enhanced_prompt": enhanced_prompt,
            "scores": critique_result["scores"],
            "critique": critique_result["critique"],
            "improvements": critique_result["improvements"],
            "timestamp": datetime.now().isoformat()
        }
        iteration_history.append(iteration_data)
        
        overall_score = critique_result["scores"]["overall"]
        logger.info(f"Iteration {iteration} complete - Overall score: {overall_score:.1f}")
        
        # Early stopping: score threshold met
        if overall_score >= score_threshold:
            logger.info(f"Score threshold ({score_threshold}) reached, stopping early")
            current_prompt = enhanced_prompt
            break
        
        # Convergence check: improvement < 2 points
        if iteration > 1:
            prev_score = iteration_history[-2]["scores"]["overall"]
            improvement = overall_score - prev_score
            if improvement < 2.0:
                logger.info(f"Convergence detected (improvement: {improvement:.1f} points), stopping")
                current_prompt = enhanced_prompt
                break
        
        # Prepare next iteration with feedback
        feedback_context = f"Previous critique: {critique_result['critique']}\n\nImprovements needed:\n" + "\n".join(f"- {imp}" for imp in critique_result["improvements"])
        current_prompt = f"{enhanced_prompt}\n\n[Based on feedback: {feedback_context}]"
    
    # Save final enhanced prompt
    final_prompt = iteration_history[-1]["enhanced_prompt"] if iteration_history else user_prompt
    final_score = iteration_history[-1]["scores"] if iteration_history else initial_score
    
    # Generate negative prompt if requested and model supports it
    negative_prompt = None
    if generate_negative and image_model_name and supports_negative_prompts(image_model_name):
        logger.info("Generating negative prompt...")
        negative_prompt = await _generate_negative_prompt(
            final_prompt,
            user_prompt,
            image_model_name,
            model=creative_model
        )
        logger.info(f"Generated negative prompt: {negative_prompt[:100]}...")
    
    if trace_dir:
        (trace_dir / "05_final_enhanced_prompt.txt").write_text(final_prompt, encoding="utf-8")
        if negative_prompt:
            (trace_dir / "06_negative_prompt.txt").write_text(negative_prompt, encoding="utf-8")
        
        # Save summary
        summary = {
            "original_prompt": user_prompt,
            "final_prompt": final_prompt,
            "negative_prompt": negative_prompt,
            "model_name": image_model_name,
            "initial_score": initial_score,
            "final_score": final_score,
            "total_iterations": len(iteration_history),
            "iterations": iteration_history,
            "timestamp": datetime.now().isoformat()
        }
        (trace_dir / "prompt_trace_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    
    logger.info(f"\n=== Enhancement Complete ===")
    logger.info(f"Final score: {final_score['overall']:.1f} (improvement: {final_score['overall'] - initial_score['overall']:.1f} points)")
    logger.info(f"Total iterations: {len(iteration_history)}")
    if negative_prompt:
        logger.info(f"Negative prompt generated: {len(negative_prompt)} characters")
    
    return ImagePromptEnhancementResult(
        original_prompt=user_prompt,
        final_prompt=final_prompt,
        iterations=iteration_history,
        final_score=final_score,
        total_iterations=len(iteration_history),
        negative_prompt=negative_prompt,
        model_name=image_model_name
    )


async def _cinematographer_enhance(
    prompt: str,
    model: str = "gpt-4-turbo",
    image_model_name: Optional[str] = None
) -> str:
    """Agent 1: Cinematographer enhances the prompt with model-specific guidance."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    # Get model-specific strategy
    system_prompt = CINEMATOGRAPHER_SYSTEM_PROMPT
    if image_model_name:
        strategy = get_model_strategy(image_model_name)
        model_guidance = f"""

MODEL-SPECIFIC GUIDANCE for {strategy['name']}:
{strategy['description']}

Key preferences:
- Style: {strategy['preferences']['style']}
- Length: {strategy['preferences']['length']}
- Technical details: {strategy['preferences']['technical_details']}
- Structure: {strategy['preferences']['structure']}

Tips for this model:
{chr(10).join(f"- {tip}" for tip in strategy['tips'])}

"""
        
        # Add model-specific instructions
        if should_simplify_for_model(image_model_name):
            model_guidance += "\nIMPORTANT: This model prefers CONCISE prompts. Keep it shorter and more focused. Avoid overly complex multi-concept descriptions.\n"
        
        if not should_include_technical_details(image_model_name):
            model_guidance += "\nIMPORTANT: Simplify or remove specific camera/lens technical details. Use natural descriptions instead (e.g., 'close-up portrait' instead of 'Canon EOS R5, 85mm f/1.2 lens').\n"
        
        system_prompt = system_prompt + model_guidance
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        enhanced = response.choices[0].message.content.strip()
        return enhanced
        
    except Exception as e:
        logger.error(f"Cinematographer enhancement failed: {e}")
        raise


async def _prompt_engineer_critique(prompt: str, model: str = "gpt-4-turbo") -> Dict:
    """Agent 2: Prompt Engineer critiques and scores the prompt."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PROMPT_ENGINEER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Evaluate this image prompt:\n\n{prompt}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent scoring
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate structure
        if "scores" not in result or "critique" not in result or "improvements" not in result:
            raise ValueError("Invalid critique response structure")
        
        # Calculate overall score if not provided
        if "overall" not in result["scores"]:
            scores = result["scores"]
            result["scores"]["overall"] = (
                scores.get("completeness", 0) * 0.25 +
                scores.get("specificity", 0) * 0.25 +
                scores.get("professionalism", 0) * 0.20 +
                scores.get("cinematography", 0) * 0.15 +
                scores.get("brand_alignment", 0) * 0.15
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Prompt Engineer critique failed: {e}")
        raise


def _quick_score_prompt(prompt: str) -> Dict[str, float]:
    """
    Fast rule-based prompt scoring (no LLM call).
    Used for initial assessment to decide if enhancement is needed.
    """
    prompt_lower = prompt.lower()
    
    # Rule-based checks for image prompts (general-purpose, not product-specific)
    has_subject = any(word in prompt_lower for word in ["product", "service", "item", "person", "object", "subject", "character", "model", "portrait", "thing", "item"])
    has_visual = any(word in prompt_lower for word in ["image", "photo", "picture", "visual", "scene", "shot", "camera", "cinematic", "view"])
    has_style = any(word in prompt_lower for word in ["style", "mood", "tone", "aesthetic", "look", "feel", "atmosphere", "grading", "color"])
    has_details = len(prompt.split()) > 10  # Has some detail
    
    # Calculate completeness
    completeness = (
        (1.0 if has_subject else 0.0) * 0.4 +
        (1.0 if has_visual else 0.0) * 0.3 +
        (1.0 if has_style else 0.0) * 0.2 +
        (1.0 if has_details else 0.0) * 0.1
    ) * 100
    
    # Specificity: more words = more specific, but cap at reasonable level
    word_count = len(prompt.split())
    specificity = min(word_count / 25.0, 1.0) * 100  # Adjusted threshold
    
    # Professionalism: check for professional language patterns
    # Look for awkward phrasing patterns that indicate unprofessional language
    awkward_patterns = ["framed by a", "using a", "all in a", "to evoke"]  # These suggest less natural flow
    has_awkward = any(pattern in prompt_lower for pattern in awkward_patterns)
    has_professional_terms = any(word in prompt_lower for word in ["cinematic", "professional", "elegant", "sophisticated", "polished", "refined"])
    
    # Professionalism score: base on completeness, but penalize awkward phrasing
    professionalism_base = completeness * 0.9
    if has_awkward and not has_professional_terms:
        professionalism = max(professionalism_base - 20, 40)  # Penalize awkward phrasing
    elif has_awkward:
        professionalism = max(professionalism_base - 10, 50)  # Less penalty if has professional terms
    else:
        professionalism = professionalism_base
    
    # Cinematography: check for camera/lighting details
    has_camera = any(word in prompt_lower for word in ["camera", "lens", "canon", "sony", "eos", "f/", "mm"])
    has_shot_type = any(word in prompt_lower for word in ["angle", "shot", "framing", "aerial", "close-up", "closeup", "telephoto", "macro", "portrait", "wide"])
    has_lighting = any(word in prompt_lower for word in ["lighting", "light", "glow", "illumination", "diffused", "dramatic", "soft", "harsh", "golden", "neon"])
    
    cinematography = (
        (1.0 if has_camera else 0.0) * 0.4 +
        (1.0 if has_shot_type else 0.0) * 0.35 +
        (1.0 if has_lighting else 0.0) * 0.25
    ) * 100
    
    # Brand alignment: check for brand/style coherence (general, not product-specific)
    # If brand terms mentioned, they should be coherent; if not, score based on style consistency
    has_brand_terms = any(word in prompt_lower for word in ["brand", "logo", "identity", "guidelines"])
    has_style_coherence = any(word in prompt_lower for word in ["color", "palette", "aesthetic", "style", "mood", "tone"])
    brand_alignment = (1.0 if (has_brand_terms or has_style_coherence) else 0.5) * 100
    
    overall = (
        completeness * 0.25 +
        specificity * 0.25 +
        professionalism * 0.20 +
        cinematography * 0.15 +
        brand_alignment * 0.15
    )
    
    return {
        "completeness": round(completeness, 1),
        "specificity": round(specificity, 1),
        "professionalism": round(professionalism, 1),
        "cinematography": round(cinematography, 1),
        "brand_alignment": round(brand_alignment, 1),
        "overall": round(overall, 1)
    }


VARIATION_AGENT_SYSTEM_PROMPT = """You are a Prompt Strategist specializing in creating diverse prompt variations for image generation.

Your role:
- Analyze feedback from image quality scores
- Create multiple distinct prompt strategies that address the feedback in different ways
- Each variation should try a different approach to solving the same problem
- Return N complete, ready-to-use prompt variations

When creating variations, you should:
1. Try different strategies: simplification, detail addition, composition changes, style adjustments
2. Each variation should be a complete, standalone prompt
3. Variations should be meaningfully different (not just minor word changes)
4. Address the feedback from different angles

Example: If feedback says "Low CLIP-Score - image doesn't align well with prompt semantics"
- Variation 1: Simplify to core subject, remove abstract concepts
- Variation 2: Add very specific visual details and concrete descriptions
- Variation 3: Change composition/camera angle to be more standard
- Variation 4: Adjust style descriptors to be more model-friendly

Return your response as JSON:
{
  "variations": [
    "First complete prompt variation",
    "Second complete prompt variation",
    "Third complete prompt variation",
    ...
  ],
  "strategies": [
    "Brief description of strategy for variation 1",
    "Brief description of strategy for variation 2",
    ...
  ]
}

Each variation must be a complete, natural language prompt ready for image generation."""


NEGATIVE_PROMPT_SYSTEM_PROMPT = """You are an expert at creating negative prompts for image generation models.

Your role:
- Generate effective negative prompts that help avoid common image generation artifacts
- Focus on quality issues, unwanted elements, and common model failures
- Keep negative prompts concise and keyword-focused (comma-separated)
- Base negative prompts on the positive prompt to avoid contradictions

Guidelines:
- Use comma-separated keywords, not full sentences
- Focus on: quality issues (blurry, low quality), anatomical errors (deformed, extra limbs), unwanted elements (text, watermarks), style issues (oversaturated, distorted)
- DO NOT include things that contradict the positive prompt
- Keep it under 100 words typically
- Use common negative prompt terms that models understand

Return ONLY the negative prompt text, no explanations, no labels."""


async def _generate_negative_prompt(
    positive_prompt: str,
    original_prompt: str,
    image_model_name: str,
    model: str = "gpt-4-turbo"
) -> str:
    """Generate a negative prompt based on the positive prompt and model."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    # Get model-specific defaults
    default_negatives = get_default_negative_prompt(image_model_name)
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    user_message = f"""Positive prompt:
{positive_prompt}

Original user prompt:
{original_prompt}

Generate a negative prompt that will help avoid common quality issues and artifacts while not contradicting the positive prompt.

Model: {image_model_name}

Default negative terms for this model: {default_negatives}

Focus on quality issues, anatomical errors, unwanted elements, and style problems that are NOT part of the desired image."""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": NEGATIVE_PROMPT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=200
        )
        
        negative = response.choices[0].message.content.strip()
        # Clean up any labels or explanations
        if "negative prompt:" in negative.lower():
            negative = negative.split(":", 1)[-1].strip()
        negative = negative.strip('"').strip("'")
        
        return negative
        
    except Exception as e:
        logger.error(f"Negative prompt generation failed: {e}")
        # Fallback to defaults
        return default_negatives


async def _variation_agent_create_strategies(
    current_prompt: str,
    feedback: str,
    num_variations: int,
    image_model_name: Optional[str],
    model: str = "gpt-4-turbo"
) -> List[str]:
    """
    Variation Agent creates multiple distinct prompt strategies.
    
    Args:
        current_prompt: Current prompt to vary
        feedback: Feedback from image scores (what's not working)
        num_variations: Number of variations to create
        image_model_name: Target image generation model
        model: LLM model for variation agent
    
    Returns:
        List of prompt variations (strings)
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    # Get model-specific strategy info
    model_info = ""
    if image_model_name:
        strategy = get_model_strategy(image_model_name)
        model_info = f"""
Target model: {strategy['name']} ({strategy['description']})
Model preferences:
- Style: {strategy['preferences']['style']}
- Length: {strategy['preferences']['length']}
- Technical details: {strategy['preferences']['technical_details']}

Keep these preferences in mind when creating variations.
"""
    
    system_prompt = VARIATION_AGENT_SYSTEM_PROMPT
    if image_model_name:
        system_prompt += f"\n\nMODEL-SPECIFIC GUIDANCE:\n{model_info}"
    
    user_message = f"""Current prompt:
{current_prompt}

Feedback from image quality scores:
{feedback}

Create {num_variations} distinct prompt variations that address this feedback using different strategies.

Each variation should:
- Be a complete, ready-to-use prompt
- Try a different approach to solving the problem
- Be meaningfully different from the others
- Follow model-specific preferences if provided

Return as JSON with 'variations' and 'strategies' arrays."""
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,  # Higher temperature for more diverse variations
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate and extract variations
        if "variations" not in result:
            raise ValueError("Variation agent response missing 'variations' field")
        
        variations = result["variations"]
        if not isinstance(variations, list):
            raise ValueError("Variations must be a list")
        
        if len(variations) < num_variations:
            logger.warning(f"Requested {num_variations} variations but got {len(variations)}")
        
        # Return requested number (or all if fewer)
        return variations[:num_variations]
        
    except Exception as e:
        logger.error(f"Variation agent failed: {e}")
        # Fallback: return original prompt repeated
        logger.warning("Falling back to original prompt for all variations")
        return [current_prompt] * num_variations


async def enhance_prompt_with_parallel_exploration(
    user_prompt: str,
    image_model_name: str,
    num_variations: int = 6,  # Increased default from 4 to 6 for better exploration
    max_iterations: int = 3,
    score_threshold: float = 70.0,
    creative_model: str = "gpt-4-turbo",
    trace_dir: Optional[Path] = None,
    generate_negative: bool = True,
    aspect_ratio: str = "16:9",
    seed: Optional[int] = None
) -> ImagePromptEnhancementResult:
    """
    Parallel exploration: Create multiple prompt variations → generate → score → select best.
    
    This method creates N distinct prompt strategies per iteration, generates one image per
    variation, scores them all, and uses the best-performing variation as the base for
    the next iteration.
    
    Args:
        user_prompt: Original user prompt
        image_model_name: Target image generation model
        num_variations: Number of prompt variations to test per iteration (default: 6, increased for better exploration)
        max_iterations: Maximum number of iteration rounds (default: 3)
        score_threshold: Stop if overall image score >= this (default: 70.0)
        creative_model: Model for Variation Agent
        trace_dir: Optional directory to save trace files
        generate_negative: Whether to generate negative prompt
        aspect_ratio: Aspect ratio for test images
        seed: Optional seed for reproducibility
    
    Returns:
        ImagePromptEnhancementResult with best prompt from parallel exploration
    """
    from app.services.image_generation import generate_images
    from app.services.pipeline.image_quality_scoring import score_image
    
    logger.info(f"Starting parallel exploration (max_iterations={max_iterations}, variations={num_variations})")
    
    if trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)
        (trace_dir / "00_original_prompt.txt").write_text(user_prompt, encoding="utf-8")
    
    current_prompt = user_prompt
    iteration_history = []
    best_prompt = user_prompt
    best_score = 0.0
    best_variation_index = 0
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n=== Parallel Exploration Iteration {iteration}/{max_iterations} ===")
        
        # Step 1: Generate feedback from previous iteration (if not first)
        feedback = ""
        if iteration == 1:
            # First iteration: enhance the original prompt first
            logger.info("Enhancing initial prompt...")
            enhanced_base = await _cinematographer_enhance(
                current_prompt,
                model=creative_model,
                image_model_name=image_model_name
            )
            current_prompt = enhanced_base
            feedback = "Initial exploration - test different prompt strategies"
        else:
            # Subsequent iterations: create feedback from previous results
            prev_iteration = iteration_history[-1]
            if prev_iteration.get("variation_results"):
                best_prev = max(
                    prev_iteration["variation_results"],
                    key=lambda v: v.get("overall_score", 0)
                )
                feedback_parts = []
                if best_prev.get("overall_score", 0) < 50:
                    feedback_parts.append("Image scores still low - need significant improvements")
                if best_prev.get("pickscore", 0) < 30:
                    feedback_parts.append("Low PickScore - images don't match human preferences")
                if best_prev.get("clip_score", 0) < 30:
                    feedback_parts.append("Low CLIP-Score - images don't align with prompt semantics")
                if best_prev.get("aesthetic", 0) < 40:
                    feedback_parts.append("Low aesthetic - images lack visual appeal")
                
                feedback = "; ".join(feedback_parts) if feedback_parts else "Continue improving based on best variation"
                current_prompt = best_prev["prompt"]  # Start from best previous variation
        
        # Step 2: Variation Agent creates N distinct prompt strategies
        logger.info(f"Variation Agent: Creating {num_variations} distinct prompt strategies...")
        prompt_variations = await _variation_agent_create_strategies(
            current_prompt=current_prompt,
            feedback=feedback,
            num_variations=num_variations,
            image_model_name=image_model_name,
            model=creative_model
        )
        
        logger.info(f"Created {len(prompt_variations)} prompt variations")
        if trace_dir:
            variations_file = trace_dir / f"iteration_{iteration}_variations.json"
            variations_data = {
                "iteration": iteration,
                "base_prompt": current_prompt,
                "feedback": feedback,
                "variations": prompt_variations,
                "timestamp": datetime.now().isoformat()
            }
            variations_file.write_text(json.dumps(variations_data, indent=2), encoding="utf-8")
        
        # Step 3: Generate one image per variation (in parallel)
        logger.info(f"Generating 1 image per variation ({len(prompt_variations)} images total)...")
        variation_results = []
        
        for var_idx, variation_prompt in enumerate(prompt_variations):
            var_output_dir = trace_dir / f"iteration_{iteration}_variation_{var_idx+1}" if trace_dir else None
            if var_output_dir:
                var_output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Generate single image for this variation
                gen_results = await generate_images(
                    prompt=variation_prompt,
                    num_variations=1,  # One image per variation
                    aspect_ratio=aspect_ratio,
                    seed=seed,
                    model_name=image_model_name,
                    output_dir=var_output_dir
                )
                
                if gen_results and gen_results[0].image_path:
                    # Score the image
                    scores = await score_image(gen_results[0].image_path, variation_prompt)
                    
                    variation_results.append({
                        "variation_index": var_idx + 1,
                        "prompt": variation_prompt,
                        "image_path": gen_results[0].image_path,
                        "scores": scores,
                        "overall_score": scores["overall"],
                        "pickscore": scores.get("pickscore", 0),
                        "clip_score": scores.get("clip_score", 0),
                        "aesthetic": scores.get("aesthetic", 0)
                    })
                    
                    logger.info(f"  Variation {var_idx+1}: Score {scores['overall']:.1f}/100")
                else:
                    logger.warning(f"  Variation {var_idx+1}: Failed to generate image")
                    variation_results.append({
                        "variation_index": var_idx + 1,
                        "prompt": variation_prompt,
                        "error": "Image generation failed",
                        "overall_score": 0.0
                    })
            except Exception as e:
                logger.error(f"  Variation {var_idx+1}: Error - {e}")
                variation_results.append({
                    "variation_index": var_idx + 1,
                    "prompt": variation_prompt,
                    "error": str(e),
                    "overall_score": 0.0
                })
        
        # Step 4: Analyze results and select best
        best_var = None
        successful_variations = []
        avg_score = 0.0
        
        if variation_results:
            # Find best variation
            successful_variations = [v for v in variation_results if "error" not in v]
            if successful_variations:
                best_var = max(successful_variations, key=lambda v: v["overall_score"])
                avg_score = sum(v["overall_score"] for v in successful_variations) / len(successful_variations)
                
                logger.info(f"\nBest variation: #{best_var['variation_index']} (Score: {best_var['overall_score']:.1f}/100)")
                logger.info(f"Average score: {avg_score:.1f}/100")
                
                # Track overall best
                if best_var["overall_score"] > best_score:
                    best_score = best_var["overall_score"]
                    best_prompt = best_var["prompt"]
                    best_variation_index = best_var["variation_index"]
                
                # Early stopping
                if best_var["overall_score"] >= score_threshold:
                    logger.info(f"Score threshold ({score_threshold}) reached, stopping early")
                    break
            else:
                logger.warning("All variations failed - cannot continue")
                break
        
        # Step 5: Save iteration data
        iteration_data = {
            "iteration": iteration,
            "base_prompt": current_prompt,
            "feedback": feedback,
            "variation_results": variation_results,
            "best_variation": best_var if best_var else None,
            "average_score": avg_score,
            "best_score": best_var["overall_score"] if best_var else 0.0,
            "timestamp": datetime.now().isoformat()
        }
        iteration_history.append(iteration_data)
        
        if trace_dir:
            (trace_dir / f"iteration_{iteration}_summary.json").write_text(
                json.dumps(iteration_data, indent=2), encoding="utf-8"
            )
    
    # Generate negative prompt for best prompt
    negative_prompt = None
    if generate_negative and supports_negative_prompts(image_model_name):
        logger.info("Generating negative prompt for best prompt...")
        negative_prompt = await _generate_negative_prompt(
            best_prompt,
            user_prompt,
            image_model_name,
            model=creative_model
        )
    
    # Create final score
    final_score = {
        "overall": best_score if best_score > 0 else 50.0,
        "image_based": True,
        "best_image_score": best_score,
        "best_variation_index": best_variation_index
    }
    
    if trace_dir:
        (trace_dir / "05_final_enhanced_prompt.txt").write_text(best_prompt, encoding="utf-8")
        if negative_prompt:
            (trace_dir / "06_negative_prompt.txt").write_text(negative_prompt, encoding="utf-8")
        
        summary = {
            "original_prompt": user_prompt,
            "final_prompt": best_prompt,
            "negative_prompt": negative_prompt,
            "model_name": image_model_name,
            "final_score": final_score,
            "total_iterations": len(iteration_history),
            "iterations": iteration_history,
            "timestamp": datetime.now().isoformat()
        }
        (trace_dir / "prompt_trace_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    
    logger.info(f"\n=== Parallel Exploration Complete ===")
    logger.info(f"Best variation: #{best_variation_index} (Score: {best_score:.1f}/100)")
    logger.info(f"Total iterations: {len(iteration_history)}")
    
    return ImagePromptEnhancementResult(
        original_prompt=user_prompt,
        final_prompt=best_prompt,
        iterations=iteration_history,
        final_score=final_score,
        total_iterations=len(iteration_history),
        negative_prompt=negative_prompt,
        model_name=image_model_name
    )


async def enhance_prompt_with_image_feedback(
    user_prompt: str,
    image_model_name: str,
    num_test_images: int = 2,
    max_iterations: int = 3,
    score_threshold: float = 70.0,
    creative_model: str = "gpt-4-turbo",
    critique_model: str = "gpt-4-turbo",
    trace_dir: Optional[Path] = None,
    generate_negative: bool = True,
    aspect_ratio: str = "16:9",
    seed: Optional[int] = None
) -> ImagePromptEnhancementResult:
    """
    Image score feedback loop: generate → score → refine prompt based on actual image quality.
    
    This is more expensive than prompt-only enhancement but provides better results by
    using actual image quality scores to guide prompt refinement.
    
    Args:
        user_prompt: Original user prompt
        image_model_name: Target image generation model
        num_test_images: Number of test images to generate per iteration (default: 2)
        max_iterations: Maximum number of iteration rounds (default: 3)
        score_threshold: Stop if overall image score >= this (default: 70.0)
        creative_model: Model for Cinematographer agent
        critique_model: Model for Prompt Engineer agent
        trace_dir: Optional directory to save trace files
        generate_negative: Whether to generate negative prompt
        aspect_ratio: Aspect ratio for test images
        seed: Optional seed for reproducibility
    
    Returns:
        ImagePromptEnhancementResult with enhanced prompt based on image feedback
    """
    from app.services.image_generation import generate_images
    from app.services.pipeline.image_quality_scoring import score_image
    
    logger.info(f"Starting image feedback loop (max_iterations={max_iterations}, test_images={num_test_images})")
    
    if trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)
        (trace_dir / "00_original_prompt.txt").write_text(user_prompt, encoding="utf-8")
    
    current_prompt = user_prompt
    iteration_history = []
    best_prompt = user_prompt
    best_score = 0.0
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n=== Image Feedback Iteration {iteration}/{max_iterations} ===")
        
        # Step 1: Enhance prompt (model-specific)
        logger.info("Enhancing prompt with model-specific guidance...")
        enhanced_prompt = await _cinematographer_enhance(
            current_prompt,
            model=creative_model,
            image_model_name=image_model_name
        )
        
        # Step 2: Generate test images
        logger.info(f"Generating {num_test_images} test images...")
        test_output_dir = trace_dir / f"iteration_{iteration}_images" if trace_dir else None
        if test_output_dir:
            test_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            test_results = await generate_images(
                prompt=enhanced_prompt,
                num_variations=num_test_images,
                aspect_ratio=aspect_ratio,
                seed=seed,
                model_name=image_model_name,
                output_dir=test_output_dir
            )
        except Exception as e:
            logger.error(f"Image generation failed in iteration {iteration}: {e}")
            # Continue with prompt-only enhancement
            test_results = []
        
        # Step 3: Score images
        image_scores = []
        for result in test_results:
            if result.image_path:
                try:
                    scores = await score_image(result.image_path, enhanced_prompt)
                    image_scores.append({
                        "image_path": result.image_path,
                        "scores": scores
                    })
                except Exception as e:
                    logger.warning(f"Failed to score image {result.image_path}: {e}")
        
        # Step 4: Analyze scores and generate feedback
        if image_scores:
            avg_score = sum(s["scores"]["overall"] for s in image_scores) / len(image_scores)
            best_image_score = max(s["scores"]["overall"] for s in image_scores)
            
            logger.info(f"Average image score: {avg_score:.1f}/100")
            logger.info(f"Best image score: {best_image_score:.1f}/100")
            
            # Track best prompt
            if best_image_score > best_score:
                best_score = best_image_score
                best_prompt = enhanced_prompt
            
            # Analyze what's working/not working
            feedback_parts = []
            for img_data in image_scores:
                scores = img_data["scores"]
                if scores["pickscore"] < 30:
                    feedback_parts.append("Low PickScore - image doesn't match human preferences for this prompt")
                if scores["clip_score"] < 30:
                    feedback_parts.append("Low CLIP-Score - image doesn't align well with prompt semantics")
                if scores["aesthetic"] < 40:
                    feedback_parts.append("Low aesthetic score - image lacks visual appeal")
            
            feedback = "; ".join(feedback_parts) if feedback_parts else "Images are reasonable but could be improved"
            
            # Early stopping if threshold met
            if best_image_score >= score_threshold:
                logger.info(f"Score threshold ({score_threshold}) reached, stopping early")
                break
        else:
            avg_score = 0.0
            best_image_score = 0.0
            feedback = "No images generated successfully"
        
        iteration_data = {
            "iteration": iteration,
            "enhanced_prompt": enhanced_prompt,
            "test_images": len(test_results),
            "image_scores": image_scores,
            "average_score": avg_score,
            "best_score": best_image_score,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        iteration_history.append(iteration_data)
        
        if trace_dir:
            (trace_dir / f"iteration_{iteration}_summary.json").write_text(
                json.dumps(iteration_data, indent=2), encoding="utf-8"
            )
        
        # Step 5: Refine prompt based on feedback
        if iteration < max_iterations:
            refinement_context = f"""
Previous iteration results:
- Average image score: {avg_score:.1f}/100
- Best image score: {best_image_score:.1f}/100
- Feedback: {feedback}

Refine the prompt to improve image quality scores. Focus on:
1. Better alignment with what the model can generate well
2. Clearer visual descriptions
3. Model-specific optimizations for {image_model_name}
"""
            current_prompt = f"{enhanced_prompt}\n\n[Refinement needed: {refinement_context}]"
    
    # Generate negative prompt for final best prompt
    negative_prompt = None
    if generate_negative and supports_negative_prompts(image_model_name):
        logger.info("Generating negative prompt for best prompt...")
        negative_prompt = await _generate_negative_prompt(
            best_prompt,
            user_prompt,
            image_model_name,
            model=creative_model
        )
    
    # Create final score (use best image score if available, otherwise prompt score)
    final_score = {
        "overall": best_score if best_score > 0 else 50.0,
        "image_based": True,
        "best_image_score": best_score
    }
    
    if trace_dir:
        (trace_dir / "05_final_enhanced_prompt.txt").write_text(best_prompt, encoding="utf-8")
        if negative_prompt:
            (trace_dir / "06_negative_prompt.txt").write_text(negative_prompt, encoding="utf-8")
        
        summary = {
            "original_prompt": user_prompt,
            "final_prompt": best_prompt,
            "negative_prompt": negative_prompt,
            "model_name": image_model_name,
            "final_score": final_score,
            "total_iterations": len(iteration_history),
            "iterations": iteration_history,
            "timestamp": datetime.now().isoformat()
        }
        (trace_dir / "prompt_trace_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    
    logger.info(f"\n=== Image Feedback Loop Complete ===")
    logger.info(f"Best image score achieved: {best_score:.1f}/100")
    logger.info(f"Total iterations: {len(iteration_history)}")
    
    return ImagePromptEnhancementResult(
        original_prompt=user_prompt,
        final_prompt=best_prompt,
        iterations=iteration_history,
        final_score=final_score,
        total_iterations=len(iteration_history),
        negative_prompt=negative_prompt,
        model_name=image_model_name
    )


# Alias for backward compatibility with interactive pipeline
async def enhance_image_prompt(
    base_prompt: str,
    story_context: str = "",
    target_style: str = "cinematic",
    max_iterations: int = 1,
    **kwargs
) -> Dict[str, any]:
    """
    Simple wrapper for interactive pipeline compatibility.
    Returns a dict with 'enhanced_prompt' key.
    """
    # Combine prompt with story context
    full_prompt = f"{base_prompt}"
    if story_context:
        full_prompt = f"{full_prompt}. Context: {story_context}"
    if target_style:
        full_prompt = f"{full_prompt}. Style: {target_style}"

    # Use the iterative enhancement but with minimal iterations for speed
    result = await enhance_prompt_iterative(
        user_prompt=full_prompt,
        max_iterations=max_iterations,
        score_threshold=100.0,  # Never stop early
        **kwargs
    )

    return {
        "enhanced_prompt": result.final_prompt,
        "negative_prompt": result.negative_prompt,
        "score": result.final_score
    }
