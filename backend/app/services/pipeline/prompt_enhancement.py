"""
Two-agent iterative prompt enhancement service.

This service uses two specialized LLM agents to iteratively refine user prompts:
- Agent 1 (Creative Director): Enhances prompts with cinematography, brand elements, professional language
- Agent 2 (Prompt Engineer): Critiques and scores prompts for technical quality

The agents iterate until a quality threshold is met or convergence is detected.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import openai

from app.core.config import settings

logger = logging.getLogger(__name__)

# Agent system prompts
CREATIVE_DIRECTOR_SYSTEM_PROMPT = """You are an award-winning creative director and cinematographer specializing in professional video advertisements.

Your role:
- Transform basic prompts into cinematic, professional ad specifications
- Add missing cinematography details (camera angles, lighting, composition)
- Enhance visual descriptions with film-grade terminology
- Fill gaps in brand identity, mood, and style
- Ensure prompts are production-ready for video generation

When enhancing prompts, you MUST:
1. Add specific camera details (lens, angle, movement)
2. Specify lighting conditions and mood
3. Include composition and framing details
4. Enhance product descriptions with visual richness
5. Add brand-appropriate style keywords
6. Ensure professional advertising language

Be creative but precise. Your enhanced prompts will directly impact video quality.

Return ONLY the enhanced prompt text, no explanations or metadata."""

PROMPT_ENGINEER_SYSTEM_PROMPT = """You are an expert prompt engineer specializing in video generation models (Stable Video Diffusion, AnimateDiff, Sora, etc.).

Your role:
- Critique prompts for technical quality and generation effectiveness
- Identify gaps that will cause poor video outputs
- Score prompts on multiple dimensions
- Provide specific, actionable feedback for improvement

Evaluation criteria:
1. Completeness (0-100): Does it have all necessary elements (product, brand, style, target audience)?
2. Specificity (0-100): Are visual details clear and unambiguous?
3. Professionalism (0-100): Is it ad-quality language?
4. Cinematography (0-100): Does it include camera/composition details?
5. Brand alignment (0-100): Are brand guidelines present and clear?

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

Be specific and actionable in your feedback."""


class PromptEnhancementResult:
    """Result of prompt enhancement process."""
    
    def __init__(
        self,
        original_prompt: str,
        final_prompt: str,
        iterations: List[Dict],
        final_score: Dict[str, float],
        total_iterations: int
    ):
        self.original_prompt = original_prompt
        self.final_prompt = final_prompt
        self.iterations = iterations
        self.final_score = final_score
        self.total_iterations = total_iterations


async def enhance_prompt_iterative(
    user_prompt: str,
    max_iterations: int = 3,
    score_threshold: float = 85.0,
    creative_model: str = "gpt-4-turbo",
    critique_model: str = "gpt-4-turbo",
    trace_dir: Optional[Path] = None
) -> PromptEnhancementResult:
    """
    Two-agent iterative prompt enhancement.
    
    Args:
        user_prompt: Original user prompt
        max_iterations: Maximum number of iteration rounds (default: 3)
        score_threshold: Stop if overall score >= this (default: 85.0)
        creative_model: Model for Creative Director agent (default: gpt-4-turbo)
        critique_model: Model for Prompt Engineer agent (default: gpt-4-turbo)
        trace_dir: Optional directory to save trace files
    
    Returns:
        PromptEnhancementResult with enhanced prompt and iteration history
    """
    logger.info(f"Starting iterative prompt enhancement (max_iterations={max_iterations}, threshold={score_threshold})")
    
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
    
    # If already good, skip enhancement
    if initial_score['overall'] >= 75.0:
        logger.info("Prompt already good quality, skipping enhancement")
        return PromptEnhancementResult(
            original_prompt=user_prompt,
            final_prompt=user_prompt,
            iterations=[],
            final_score=initial_score,
            total_iterations=0
        )
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n=== Iteration {iteration}/{max_iterations} ===")
        
        # Agent 1: Creative Director - Enhance
        logger.info("Agent 1 (Creative Director): Enhancing prompt...")
        enhanced_prompt = await _creative_director_enhance(
            current_prompt,
            model=creative_model
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
    
    if trace_dir:
        (trace_dir / "05_final_enhanced_prompt.txt").write_text(final_prompt, encoding="utf-8")
        
        # Save summary
        summary = {
            "original_prompt": user_prompt,
            "final_prompt": final_prompt,
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
    
    return PromptEnhancementResult(
        original_prompt=user_prompt,
        final_prompt=final_prompt,
        iterations=iteration_history,
        final_score=final_score,
        total_iterations=len(iteration_history)
    )


async def _creative_director_enhance(prompt: str, model: str = "gpt-4-turbo") -> str:
    """Agent 1: Creative Director enhances the prompt."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": CREATIVE_DIRECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        enhanced = response.choices[0].message.content.strip()
        return enhanced
        
    except Exception as e:
        logger.error(f"Creative Director enhancement failed: {e}")
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
                {"role": "user", "content": f"Evaluate this prompt:\n\n{prompt}"}
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
    
    # Rule-based checks
    has_product = any(word in prompt_lower for word in ["product", "service", "item", "brand", "ad", "advertisement"])
    has_visual = any(word in prompt_lower for word in ["video", "visual", "scene", "shot", "camera", "cinematic"])
    has_style = any(word in prompt_lower for word in ["style", "mood", "tone", "aesthetic", "look", "feel"])
    has_details = len(prompt.split()) > 10  # Has some detail
    
    # Calculate scores
    completeness = (
        (1.0 if has_product else 0.0) * 0.4 +
        (1.0 if has_visual else 0.0) * 0.3 +
        (1.0 if has_style else 0.0) * 0.2 +
        (1.0 if has_details else 0.0) * 0.1
    ) * 100
    
    specificity = min(len(prompt.split()) / 30.0, 1.0) * 100  # More words = more specific
    
    # Rough estimates for other dimensions
    professionalism = completeness * 0.8  # Rough estimate
    cinematography = (1.0 if any(word in prompt_lower for word in ["camera", "lens", "angle", "shot", "framing"]) else 0.3) * 100
    brand_alignment = (1.0 if any(word in prompt_lower for word in ["brand", "logo", "color", "identity"]) else 0.5) * 100
    
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

