"""
Two-agent iterative video prompt enhancement service.

This service uses two specialized LLM agents to iteratively refine video prompts:
- Agent 1 (Video Director/Creative Director): Enhances prompts with motion, temporal coherence, cinematography
- Agent 2 (Prompt Engineer): Critiques and scores prompts for technical quality

The agents iterate until a quality threshold is met or convergence is detected.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import openai
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)

# Agent system prompts - adapted for video generation
VIDEO_DIRECTOR_SYSTEM_PROMPT = """You are an award-winning video director and cinematographer specializing in professional video generation for advertisements.

Your role:
- Transform basic video prompts into cinematic, professional specifications optimized for video generation models (Stable Video Diffusion, AnimateDiff, Sora, etc.)
- Write prompts as ONE flowing sentence (or maximum TWO sentences) in natural language, following the "one-sentence screenplay" style: subject → action → setting → style → mood
- Add missing cinematography details seamlessly woven into the description
- Enhance visual descriptions with film-grade terminology
- Ensure prompts are specific enough for clarity but not overly constrained
- **CRITICAL FOR VIDEO**: Include motion, temporal continuity, and camera movement details

CRITICAL: Write your enhanced prompt as a SINGLE, FLOWING SENTENCE in natural language. DO NOT use structured sections, labels, or bullet points. DO NOT write "Scene:", "Camera:", "Lighting:" etc. Write it as if describing the scene to an artist in one continuous sentence, following the Prompt Scoring Guide best practices.

When enhancing prompts, you MUST include (but weave naturally into the sentence):
1. Camera framing and movement (e.g., "wide aerial shot", "steady tracking shot", "low-angle view", "slow dolly forward", "smooth pan left")
2. Action beats and timing cues (e.g., "gradual reveal", "smooth transition", "dynamic motion")
3. Lighting and color palette (e.g., "soft golden morning light", "dramatic side lighting", "harsh neon glow", "soft, diffused lighting")
4. Motion intensity and style (e.g., "subtle motion", "dynamic movement", "smooth, fluid motion")
5. Temporal continuity hints (e.g., "seamless transition", "continuous motion", "smooth progression")
6. Frame rate considerations if relevant (e.g., "24fps cinematic motion", "smooth 30fps")

Structure your enhanced prompt following the Prompt Scoring Guide pattern:
[Who/what is the focus] [what action or state] [where/when it's happening] [style, mood, and cinematography modifiers all woven together] [motion and temporal details]

Example of GOOD format (video prompt):
"A sleek modern smartphone displayed on a minimalist white surface, Canon EOS R5 50mm f/1.4 lens, close-up portrait, soft diffused lighting creating gentle shadows, shallow depth of field with softly blurred background, cinematic color grading with cool tones, clean professional atmosphere, 16:9 aspect ratio, slow dolly forward with subtle zoom, smooth 24fps cinematic motion, seamless transition from product reveal to lifestyle context."

Example of BAD format (DO NOT DO THIS):
"Scene: A smartphone...
Camera: Canon EOS R5...
Lighting: Soft diffused...
Motion: Slow dolly forward..."

Key principles from Prompt Scoring Guide:
- Use natural language, not keyword stuffing
- Limit to one scene or action per prompt
- Write in 1-2 well-formed sentences maximum
- Be specific but avoid overly constrained prompts
- Structure like a scene description (who/what → action → where/when → style → motion)
- **For video**: Always include motion and temporal continuity details

Camera movement cues to use: "wide aerial shot", "steady tracking shot", "low-angle view", "slow dolly forward", "smooth pan left", "static shot", "tracking movement", "push in", "pull back"

Motion intensity cues: "subtle motion", "moderate movement", "dynamic motion", "smooth, fluid motion", "gentle movement"

Temporal continuity cues: "seamless transition", "continuous motion", "smooth progression", "temporal coherence", "consistent motion"

Be creative but precise. Your enhanced prompts will directly impact video quality.

Return ONLY the enhanced prompt text as a single flowing sentence (or two at most), no explanations, no metadata, no structured sections."""

PROMPT_ENGINEER_SYSTEM_PROMPT = """You are an expert prompt engineer specializing in video generation models (Stable Video Diffusion, AnimateDiff, Sora, etc.).

Your role:
- Critique prompts for technical quality and generation effectiveness based on Prompt Scoring Guide best practices
- Identify gaps that will cause poor video outputs
- Score prompts on multiple dimensions aligned with industry standards
- Provide specific, actionable feedback for improvement

Evaluation criteria (based on Prompt Scoring Guide):
1. Completeness (0-100): Does it have all necessary elements (subject, scene/action, setting/context, style, motion)? Does it follow the structure: who/what → action → where/when → style → motion?
2. Specificity (0-100): Are visual and motion details clear and unambiguous? Can the model generate this without ambiguity? Is it specific enough but not overly constrained?
3. Professionalism (0-100): Is it ad-quality language? Does it use professional terminology? Does it read like a one-sentence screenplay?
4. Cinematography (0-100): Does it include camera/composition details? Are lighting cues present? Does it specify framing, depth of field, or perspective?
5. Temporal Coherence (0-100): Does it describe smooth, plausible motion? Are temporal continuity hints present? Does it avoid conflicting motion descriptions?
6. Brand alignment (0-100): If brand elements are mentioned in the original prompt, are they preserved and enhanced? If no brand mentioned, score based on general style coherence.

Provide your response as JSON:
{
  "scores": {
    "completeness": 85,
    "specificity": 72,
    "professionalism": 90,
    "cinematography": 65,
    "temporal_coherence": 70,
    "brand_alignment": 80,
    "overall": 77.0
  },
  "critique": "Specific feedback on what's good and what needs improvement",
  "improvements": ["List of specific improvements needed", "Another improvement"]
}

Be specific and actionable in your feedback. Evaluate against Prompt Scoring Guide principles:
- Does the prompt follow scene description structure (who/what → action → where/when → style → motion)?
- Is it written as ONE flowing sentence (or maximum TWO sentences) in natural language?
- CRITICAL: Does it avoid structured sections, labels, or bullet points (e.g., "Scene:", "Camera:", "Lighting:")? If it has these, mark it down significantly - video generation models need natural language prompts, not structured metadata.
- Are camera cues included naturally within the sentence (wide aerial shot, steady tracking shot, low-angle view, slow dolly forward, smooth pan left)?
- Are lighting cues included naturally within the sentence (soft golden morning light, harsh neon glow, soft diffused lighting, dramatic side lighting)?
- **CRITICAL FOR VIDEO**: Are motion and temporal continuity details present? (motion intensity, camera movement, temporal coherence hints)
- Is it limited to one scene or action (not multiple unrelated scenes)?
- Does it use natural language (not keyword stuffing or comma-separated lists)?
- Is it specific enough for clarity but not overly constrained?
"""


class VideoPromptEnhancementResult:
    """Result of video prompt enhancement process."""
    
    def __init__(
        self,
        original_prompt: str,
        final_prompt: str,
        iterations: List[Dict],
        final_score: Dict[str, float],
        total_iterations: int,
        videodirectorgpt_plan: Optional[Dict] = None,
        motion_prompt: Optional[str] = None
    ):
        self.original_prompt = original_prompt
        self.final_prompt = final_prompt
        self.iterations = iterations
        self.final_score = final_score
        self.total_iterations = total_iterations
        self.videodirectorgpt_plan = videodirectorgpt_plan
        self.motion_prompt = motion_prompt


class StoryboardMotionEnhancementResult:
    """Result of storyboard motion prompt enhancement process."""
    
    def __init__(
        self,
        storyboard_path: Path,
        unified_narrative_path: Path,
        clips: List[Dict],
        clip_results: List[VideoPromptEnhancementResult],
        clip_frame_paths: Dict[int, Dict[str, str]],
        summary: Dict
    ):
        self.storyboard_path = storyboard_path
        self.unified_narrative_path = unified_narrative_path
        self.clips = clips
        self.clip_results = clip_results
        self.clip_frame_paths = clip_frame_paths
        self.summary = summary


async def enhance_video_prompt_iterative(
    user_prompt: str,
    max_iterations: int = 3,
    score_threshold: float = 85.0,
    creative_model: str = "gpt-4-turbo",
    critique_model: str = "gpt-4-turbo",
    trace_dir: Optional[Path] = None,
    video_mode: bool = True,
    image_to_video: bool = False
) -> VideoPromptEnhancementResult:
    """
    Two-agent iterative video prompt enhancement.
    
    Args:
        user_prompt: Original user prompt
        max_iterations: Maximum number of iteration rounds (default: 3)
        score_threshold: Stop if overall score >= this (default: 85.0)
        creative_model: Model for Video Director agent (default: gpt-4-turbo)
        critique_model: Model for Prompt Engineer agent (default: gpt-4-turbo)
        trace_dir: Optional directory to save trace files
        video_mode: Enable video-specific enhancement (default: True)
        image_to_video: Enable image-to-video motion prompt mode (default: False)
    
    Returns:
        VideoPromptEnhancementResult with enhanced prompt and iteration history
    """
    logger.info(f"Starting iterative video prompt enhancement (max_iterations={max_iterations}, threshold={score_threshold}, image_to_video={image_to_video})")
    
    # Initialize trace directory if provided
    if trace_dir:
        trace_dir.mkdir(parents=True, exist_ok=True)
        # Save original prompt
        (trace_dir / "00_original_prompt.txt").write_text(user_prompt, encoding="utf-8")
    
    current_prompt = user_prompt
    iteration_history = []
    
    # Quick initial assessment (rule-based, fast)
    initial_score = _quick_score_prompt(user_prompt, video_mode=video_mode)
    logger.info(f"Initial prompt score: {initial_score['overall']:.1f}")
    
    # Check if any individual dimension is below threshold (more accurate than overall score)
    min_dimension_threshold = 70.0
    any_dimension_low = any(
        initial_score.get(dim, 0) < min_dimension_threshold 
        for dim in ["completeness", "specificity", "professionalism", "cinematography", "temporal_coherence", "brand_alignment"]
    )
    
    # If already good (high overall AND all dimensions good), skip enhancement
    if initial_score['overall'] >= 80.0 and not any_dimension_low:
        logger.info("Prompt already good quality, skipping enhancement")
        return VideoPromptEnhancementResult(
            original_prompt=user_prompt,
            final_prompt=user_prompt,
            iterations=[],
            final_score=initial_score,
            total_iterations=0
        )
    
    # VideoDirectorGPT planning (optional, if available)
    # Story 7.3 Phase 2 is in backlog, so this is optional
    videodirectorgpt_plan = None
    try:
        # Try to get VideoDirectorGPT planning from scene_planning service
        # For now, we'll create a basic plan structure
        # When Story 7.3 Phase 2 is available, this will be enhanced
        from app.services.pipeline.scene_planning import create_basic_scene_plan_from_prompt
        scene_plan = create_basic_scene_plan_from_prompt(user_prompt, target_duration=15, num_scenes=1)
        if scene_plan and scene_plan.scenes:
            # Extract basic planning info from scene plan
            videodirectorgpt_plan = {
                "shot_list": [{
                    "scene_number": scene.scene_number,
                    "camera_movement": "static",
                    "shot_size": "medium",
                    "perspective": "eye level",
                    "lens_type": "standard"
                } for scene in scene_plan.scenes],
                "scene_dependencies": [],
                "narrative_flow": f"{len(scene_plan.scenes)}_scene_plan",
                "consistency_groupings": [],
                "framework": scene_plan.framework
            }
            logger.info(f"Basic scene planning applied: {len(scene_plan.scenes)} scene(s) (VideoDirectorGPT Phase 2 not available)")
    except Exception as e:
        logger.debug(f"VideoDirectorGPT planning not available: {e}")
        # Continue without planning - tool still works
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n=== Iteration {iteration}/{max_iterations} ===")
        
        # Agent 1: Video Director - Enhance
        logger.info("Agent 1 (Video Director): Enhancing prompt...")
        enhanced_prompt = await _video_director_enhance(
            current_prompt,
            model=creative_model,
            image_to_video=image_to_video
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
    
    # Generate motion prompt for image-to-video mode
    motion_prompt = None
    if image_to_video:
        motion_prompt = await _generate_motion_prompt(final_prompt, creative_model)
        if trace_dir and motion_prompt:
            (trace_dir / "motion_prompt.txt").write_text(motion_prompt, encoding="utf-8")
    
    if trace_dir:
        (trace_dir / "05_final_enhanced_prompt.txt").write_text(final_prompt, encoding="utf-8")
        
        # Save VideoDirectorGPT plan if available
        if videodirectorgpt_plan:
            (trace_dir / "06_videodirectorgpt_plan.json").write_text(
                json.dumps(videodirectorgpt_plan, indent=2), encoding="utf-8"
            )
        
        # Save summary
        summary = {
            "original_prompt": user_prompt,
            "final_prompt": final_prompt,
            "motion_prompt": motion_prompt,
            "initial_score": initial_score,
            "final_score": final_score,
            "total_iterations": len(iteration_history),
            "iterations": iteration_history,
            "videodirectorgpt_plan": videodirectorgpt_plan,
            "timestamp": datetime.now().isoformat()
        }
        (trace_dir / "prompt_trace_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    
    logger.info(f"\n=== Enhancement Complete ===")
    logger.info(f"Final score: {final_score['overall']:.1f} (improvement: {final_score['overall'] - initial_score['overall']:.1f} points)")
    logger.info(f"Total iterations: {len(iteration_history)}")
    
    return VideoPromptEnhancementResult(
        original_prompt=user_prompt,
        final_prompt=final_prompt,
        iterations=iteration_history,
        final_score=final_score,
        total_iterations=len(iteration_history),
        videodirectorgpt_plan=videodirectorgpt_plan,
        motion_prompt=motion_prompt
    )


async def _video_director_enhance(
    prompt: str,
    model: str = "gpt-4-turbo",
    image_to_video: bool = False
) -> str:
    """Agent 1: Video Director enhances the prompt."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Add image-to-video specific instructions
    user_prompt_text = prompt
    if image_to_video:
        user_prompt_text = f"""{prompt}

IMPORTANT: This is for image-to-video generation. Focus on enhancing MOTION descriptions:
- Camera movement (pan, tilt, dolly, static, tracking)
- Motion intensity (subtle, moderate, dynamic)
- Frame rate considerations
- Temporal continuity
- Negative prompts for unwanted motion (e.g., "jerky, flicker, inconsistent")
"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": VIDEO_DIRECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt_text}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        enhanced = response.choices[0].message.content.strip()
        return enhanced
        
    except Exception as e:
        logger.error(f"Video Director enhancement failed: {e}")
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
                {"role": "user", "content": f"Evaluate this video prompt:\n\n{prompt}"}
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
                scores.get("completeness", 0) * 0.20 +
                scores.get("specificity", 0) * 0.20 +
                scores.get("professionalism", 0) * 0.15 +
                scores.get("cinematography", 0) * 0.15 +
                scores.get("temporal_coherence", 0) * 0.15 +
                scores.get("brand_alignment", 0) * 0.15
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Prompt Engineer critique failed: {e}")
        raise


def _quick_score_prompt(prompt: str, video_mode: bool = True) -> Dict[str, float]:
    """
    Fast rule-based prompt scoring (no LLM call).
    Used for initial assessment to decide if enhancement is needed.
    """
    prompt_lower = prompt.lower()
    
    # Rule-based checks for video prompts
    has_subject = any(word in prompt_lower for word in ["product", "service", "item", "person", "object", "subject", "character", "model", "portrait", "thing", "item"])
    has_visual = any(word in prompt_lower for word in ["image", "photo", "picture", "visual", "scene", "shot", "camera", "cinematic", "view", "video"])
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
    specificity = min(word_count / 25.0, 1.0) * 100
    
    # Professionalism: check for professional language patterns
    awkward_patterns = ["framed by a", "using a", "all in a", "to evoke"]
    has_awkward = any(pattern in prompt_lower for pattern in awkward_patterns)
    has_professional_terms = any(word in prompt_lower for word in ["cinematic", "professional", "elegant", "sophisticated", "polished", "refined"])
    
    professionalism_base = completeness * 0.9
    if has_awkward and not has_professional_terms:
        professionalism = max(professionalism_base - 20, 40)
    elif has_awkward:
        professionalism = max(professionalism_base - 10, 50)
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
    
    # Temporal coherence: check for motion/temporal details (VIDEO-SPECIFIC)
    has_motion = any(word in prompt_lower for word in ["motion", "movement", "move", "transition", "dolly", "pan", "tilt", "tracking", "push", "pull"])
    has_temporal = any(word in prompt_lower for word in ["smooth", "continuous", "seamless", "temporal", "coherence", "progression", "flow"])
    has_frame_rate = any(word in prompt_lower for word in ["fps", "frame rate", "24fps", "30fps", "60fps"])
    
    temporal_coherence = (
        (1.0 if has_motion else 0.0) * 0.5 +
        (1.0 if has_temporal else 0.0) * 0.3 +
        (1.0 if has_frame_rate else 0.0) * 0.2
    ) * 100 if video_mode else 50.0  # Default to 50 if not video mode
    
    # Brand alignment: check for brand/style coherence
    has_brand_terms = any(word in prompt_lower for word in ["brand", "logo", "identity", "guidelines"])
    has_style_coherence = any(word in prompt_lower for word in ["color", "palette", "aesthetic", "style", "mood", "tone"])
    brand_alignment = (1.0 if (has_brand_terms or has_style_coherence) else 0.5) * 100
    
    overall = (
        completeness * 0.20 +
        specificity * 0.20 +
        professionalism * 0.15 +
        cinematography * 0.15 +
        temporal_coherence * 0.15 +
        brand_alignment * 0.15
    )
    
    return {
        "completeness": round(completeness, 1),
        "specificity": round(specificity, 1),
        "professionalism": round(professionalism, 1),
        "cinematography": round(cinematography, 1),
        "temporal_coherence": round(temporal_coherence, 1),
        "brand_alignment": round(brand_alignment, 1),
        "overall": round(overall, 1)
    }


async def _generate_motion_prompt(enhanced_prompt: str, model: str = "gpt-4-turbo") -> str:
    """
    Generate motion prompt for image-to-video generation.
    Extracts and enhances motion descriptions from the enhanced prompt.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    motion_system_prompt = """You are a motion design specialist for image-to-video generation.

Extract and enhance motion descriptions from the given prompt. Focus on:
- Camera movement (pan, tilt, dolly, static, tracking)
- Motion intensity (subtle, moderate, dynamic)
- Frame rate considerations
- Temporal continuity
- Negative prompts for unwanted motion (e.g., "jerky, flicker, inconsistent")

Return ONLY the motion description as a concise sentence, no explanations."""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": motion_system_prompt},
                {"role": "user", "content": f"Extract motion description from this prompt:\n\n{enhanced_prompt}"}
            ],
            temperature=0.5,
            max_tokens=300
        )
        
        motion_prompt = response.choices[0].message.content.strip()
        return motion_prompt
        
    except Exception as e:
        logger.error(f"Motion prompt generation failed: {e}")
        return "smooth, subtle motion, 24fps cinematic quality"


async def enhance_storyboard_motion_prompts(
    storyboard_path: Path,
    max_iterations: int = 3,
    score_threshold: float = 85.0,
    creative_model: str = "gpt-4-turbo",
    critique_model: str = "gpt-4-turbo",
    trace_dir: Optional[Path] = None
) -> StoryboardMotionEnhancementResult:
    """
    Enhance motion prompts for all clips in a storyboard.
    
    Args:
        storyboard_path: Path to storyboard_metadata.json file
        max_iterations: Maximum iteration rounds per clip (default: 3)
        score_threshold: Stop if overall score >= this (default: 85.0)
        creative_model: Model for Video Director agent (default: gpt-4-turbo)
        critique_model: Model for Prompt Engineer agent (default: gpt-4-turbo)
        trace_dir: Optional directory to save trace files (default: output/video_prompt_traces/{timestamp})
    
    Returns:
        StoryboardMotionEnhancementResult with enhanced motion prompts for all clips
    """
    logger.info(f"Starting storyboard motion prompt enhancement: {storyboard_path}")
    
    storyboard_path = Path(storyboard_path)
    if not storyboard_path.exists():
        raise FileNotFoundError(f"Storyboard file not found: {storyboard_path}")
    
    # Load storyboard JSON
    with open(storyboard_path, "r", encoding="utf-8") as f:
        storyboard_data = json.load(f)
    
    # Validate structure
    if "clips" not in storyboard_data:
        raise ValueError("Invalid storyboard JSON: missing 'clips' array")
    
    # Load unified narrative document (REQUIRED)
    unified_narrative_path = storyboard_data.get("unified_narrative_path")
    if not unified_narrative_path:
        raise ValueError("Storyboard missing unified_narrative_path - required for narrative context")
    
    unified_narrative_path = Path(unified_narrative_path)
    if not unified_narrative_path.exists():
        raise FileNotFoundError(f"Unified narrative document not found: {unified_narrative_path}")
    
    # Load unified narrative JSON
    unified_narrative_json = None
    if unified_narrative_path.suffix == ".json":
        with open(unified_narrative_path, "r", encoding="utf-8") as f:
            unified_narrative_json = json.load(f)
    elif unified_narrative_path.suffix == ".md":
        # Try to find corresponding JSON file
        json_path = unified_narrative_path.with_suffix(".json")
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                unified_narrative_json = json.load(f)
        else:
            logger.warning(f"Unified narrative JSON not found at {json_path}, proceeding without JSON structure")
    
    # Setup output directory
    if trace_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_dir = Path("output") / "video_prompt_traces" / timestamp
    trace_dir = Path(trace_dir)
    trace_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each clip
    clips = []
    clip_results = []
    clip_frame_paths = {}
    
    for clip_data in storyboard_data["clips"]:
        clip_number = clip_data.get("clip_number", len(clips) + 1)
        motion_description = clip_data.get("motion_description", "")
        start_frame_path = clip_data.get("start_frame_path")
        end_frame_path = clip_data.get("end_frame_path")
        
        # Validate frame paths exist
        if start_frame_path:
            start_path = Path(start_frame_path)
            if not start_path.exists():
                logger.warning(f"Start frame not found: {start_frame_path}")
            else:
                # Validate image is readable
                try:
                    Image.open(start_path).verify()
                except Exception as e:
                    logger.warning(f"Start frame image not readable: {start_frame_path}, {e}")
        
        if end_frame_path:
            end_path = Path(end_frame_path)
            if not end_path.exists():
                logger.warning(f"End frame not found: {end_frame_path}")
            else:
                # Validate image is readable
                try:
                    Image.open(end_path).verify()
                except Exception as e:
                    logger.warning(f"End frame image not readable: {end_frame_path}, {e}")
        
        # Store frame paths
        clip_frame_paths[clip_number] = {
            "start_frame_path": start_frame_path,
            "end_frame_path": end_frame_path
        }
        
        logger.info(f"\n=== Processing Clip {clip_number} ===")
        
        # Create per-clip trace directory
        clip_trace_dir = trace_dir / f"clip_{clip_number:03d}"
        clip_trace_dir.mkdir(parents=True, exist_ok=True)
        
        # Build narrative context for enhancement
        narrative_context = ""
        if unified_narrative_json:
            narrative_context = f"""
UNIFIED NARRATIVE CONTEXT:
- Overall Story: {unified_narrative_json.get('overall_story', {}).get('narrative', 'N/A')}
- Emotional Arc: {json.dumps(unified_narrative_json.get('emotional_arc', {}), indent=2)}
- Visual Progression: {json.dumps(unified_narrative_json.get('visual_progression', {}), indent=2)}
- Scene Connections: {json.dumps(unified_narrative_json.get('scene_connections', {}), indent=2)}
- Product Reveal Strategy: {json.dumps(unified_narrative_json.get('product_reveal_strategy', {}), indent=2)}
"""
        
        # Build visual context from start/end frames
        visual_context = ""
        if start_frame_path and end_frame_path:
            visual_context = f"""
VISUAL CONTEXT (for image-to-video generation):
- Start Frame: {start_frame_path}
- End Frame: {end_frame_path}
- Motion should transition smoothly from start to end frame
"""
        
        # Enhance motion prompt with narrative and visual context
        enhanced_motion_prompt = f"""{motion_description}

{narrative_context}

{visual_context}

Enhance this motion description to:
- Maintain story coherence with overall narrative
- Follow the emotional arc progression from the narrative
- Apply consistent visual progression strategy
- Create smooth narrative transitions between clips
- Align with scene connections and product reveal strategy
- Reference start/end frames for image-to-video generation
"""
        
        # Enhance using two-agent loop
        result = await enhance_video_prompt_iterative(
            user_prompt=enhanced_motion_prompt,
            max_iterations=max_iterations,
            score_threshold=score_threshold,
            creative_model=creative_model,
            critique_model=critique_model,
            trace_dir=clip_trace_dir,
            video_mode=True,
            image_to_video=True  # Storyboard mode is always image-to-video
        )
        
        clip_results.append(result)
        
        # Save enhanced motion prompt
        enhanced_motion_file = trace_dir / f"clip_{clip_number:03d}_enhanced_motion_prompt.txt"
        enhanced_motion_file.write_text(result.final_prompt, encoding="utf-8")
        
        # Build clip output data
        clip_output = {
            "clip_number": clip_number,
            "original_motion_description": motion_description,
            "enhanced_motion_prompt": result.final_prompt,
            "motion_prompt": result.motion_prompt,
            "scores": result.final_score,
            "iterations": result.total_iterations,
            "camera_movement": clip_data.get("camera_movement"),
            "shot_size": clip_data.get("shot_size"),
            "perspective": clip_data.get("perspective"),
            "lens_type": clip_data.get("lens_type"),
            "start_frame_path": start_frame_path,
            "end_frame_path": end_frame_path
        }
        clips.append(clip_output)
    
    # Generate summary
    all_scores = [r.final_score["overall"] for r in clip_results]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    
    summary = {
        "total_clips": len(clips),
        "average_score": round(avg_score, 1),
        "min_score": round(min(all_scores), 1) if all_scores else 0.0,
        "max_score": round(max(all_scores), 1) if all_scores else 0.0,
        "total_iterations": sum(r.total_iterations for r in clip_results),
        "timestamp": datetime.now().isoformat()
    }
    
    # Save summary JSON
    summary_data = {
        "storyboard_path": str(storyboard_path),
        "unified_narrative_path": str(unified_narrative_path),
        "clips": clips,
        "clip_frame_paths": clip_frame_paths,
        "summary": summary
    }
    
    summary_file = trace_dir / "storyboard_enhanced_motion_prompts.json"
    summary_file.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    
    logger.info(f"\n=== Storyboard Enhancement Complete ===")
    logger.info(f"Processed {len(clips)} clips, average score: {avg_score:.1f}")
    
    return StoryboardMotionEnhancementResult(
        storyboard_path=storyboard_path,
        unified_narrative_path=unified_narrative_path,
        clips=clips,
        clip_results=clip_results,
        clip_frame_paths=clip_frame_paths,
        summary=summary
    )

