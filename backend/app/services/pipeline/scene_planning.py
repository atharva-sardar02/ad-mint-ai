"""
Scene planning module that processes LLM output and generates enriched scene plans.
"""
import logging
from typing import Dict, List, Optional

from app.schemas.generation import AdSpecification, Scene, ScenePlan, TextOverlay

logger = logging.getLogger(__name__)

# Framework-specific scene structure templates
FRAMEWORK_TEMPLATES: Dict[str, List[Dict[str, any]]] = {
    "PAS": [
        {"type": "Problem", "duration": 5, "description": "Highlight the problem or pain point"},
        {"type": "Agitation", "duration": 5, "description": "Intensify the problem's impact"},
        {"type": "Solution", "duration": 5, "description": "Present the product as the solution"}
    ],
    "BAB": [
        {"type": "Before", "duration": 5, "description": "Show the state before using the product"},
        {"type": "After", "duration": 5, "description": "Show the improved state after using the product"},
        {"type": "Bridge", "duration": 5, "description": "Show how the product bridges the gap"}
    ],
    "AIDA": [
        {"type": "Attention", "duration": 4, "description": "Grab attention with compelling visuals"},
        {"type": "Interest", "duration": 4, "description": "Build interest with product features"},
        {"type": "Desire", "duration": 4, "description": "Create desire through benefits"},
        {"type": "Action", "duration": 4, "description": "Prompt action with clear CTA"}
    ]
}


def plan_scenes(ad_spec: AdSpecification, target_duration: int = 15) -> ScenePlan:
    """
    Process AdSpecification and generate enriched ScenePlan with visual prompts and text overlays.
    
    Args:
        ad_spec: AdSpecification from LLM enhancement
        target_duration: Target total duration in seconds (default: 15 for MVP)
    
    Returns:
        ScenePlan: Enriched scene plan with visual prompts and durations
    """
    framework = ad_spec.framework
    logger.info(f"Planning scenes for framework: {framework}, target duration: {target_duration}s")
    
    # Get framework template
    if framework not in FRAMEWORK_TEMPLATES:
        logger.warning(f"Unknown framework {framework}, defaulting to AIDA")
        framework = "AIDA"
    
    template = FRAMEWORK_TEMPLATES[framework]
    
    # Use scenes from LLM if available and valid, otherwise generate from template
    if ad_spec.scenes and len(ad_spec.scenes) >= 3:
        logger.info(f"Using {len(ad_spec.scenes)} scenes from LLM response")
        scenes = ad_spec.scenes
    else:
        logger.info(f"Generating scenes from {framework} template")
        scenes = _generate_scenes_from_template(ad_spec, template)
    
    # Enrich visual prompts with brand keywords
    enriched_scenes = []
    for i, scene in enumerate(scenes):
        enriched_scene = _enrich_scene(scene, ad_spec, i)
        enriched_scenes.append(enriched_scene)
    
    # Adjust durations to match target
    total_duration = sum(scene.duration for scene in enriched_scenes)
    if total_duration != target_duration:
        logger.info(f"Adjusting scene durations: {total_duration}s -> {target_duration}s")
        enriched_scenes = _adjust_durations(enriched_scenes, target_duration)
    
    scene_plan = ScenePlan(
        scenes=enriched_scenes,
        total_duration=sum(scene.duration for scene in enriched_scenes),
        framework=framework
    )
    
    logger.info(f"Scene plan created: {len(enriched_scenes)} scenes, {scene_plan.total_duration}s total")
    return scene_plan


def _generate_scenes_from_template(
    ad_spec: AdSpecification, template: List[Dict[str, any]]
) -> List[Scene]:
    """Generate scenes from framework template."""
    scenes = []
    for i, template_scene in enumerate(template, start=1):
        scene = Scene(
            scene_number=i,
            scene_type=template_scene["type"],
            visual_prompt=f"{template_scene['description']}. {ad_spec.product_description}. Style: {ad_spec.brand_guidelines.visual_style_keywords}, Mood: {ad_spec.brand_guidelines.mood}",
            text_overlay={
                "text": ad_spec.ad_specifications.call_to_action if i == len(template) else "",
                "position": "center" if i == len(template) else "bottom",
                "font_size": 48,
                "color": ad_spec.brand_guidelines.brand_colors[0] if ad_spec.brand_guidelines.brand_colors else "#FFFFFF",
                "animation": "fade_in"
            },
            duration=template_scene["duration"]
        )
        scenes.append(scene)
    return scenes


def _enrich_scene(scene: Scene, ad_spec: AdSpecification, index: int) -> Scene:
    """
    Enrich scene visual prompt with brand keywords and context.
    
    Note: The scene.visual_prompt is already built from compact fragments (3-7 words each)
    by _build_sora_scene_prompt(). This function adds style/mood guidance as post-processing
    to help Sora-2 understand the overall aesthetic without modifying the core scene fragments.
    """
    # Enhance visual prompt with brand guidelines
    brand_keywords = ad_spec.brand_guidelines.visual_style_keywords
    mood = ad_spec.brand_guidelines.mood

    # Start with the compact fragment-based prompt from LLM
    enriched_parts = [scene.visual_prompt]

    # Add style/mood guidance (these are style hints, not scene description fragments)
    # They help Sora-2 understand the overall aesthetic
    if brand_keywords:
        enriched_parts.append(f"The overall visual style feels {brand_keywords}.")

    if mood:
        enriched_parts.append(f"The mood is {mood}.")

    enriched_prompt = "\n".join(enriched_parts)
    
    # Ensure text overlay uses brand colors
    text_overlay = scene.text_overlay
    if not text_overlay.color or text_overlay.color == "#000000":
        text_overlay.color = ad_spec.brand_guidelines.brand_colors[0] if ad_spec.brand_guidelines.brand_colors else "#FFFFFF"
    
    return Scene(
        scene_number=scene.scene_number,
        scene_type=scene.scene_type,
        visual_prompt=enriched_prompt,
        text_overlay=text_overlay,
        duration=scene.duration
    )


def _adjust_durations(scenes: List[Scene], target_duration: int) -> List[Scene]:
    """Adjust scene durations to match target duration."""
    current_total = sum(scene.duration for scene in scenes)
    if current_total == target_duration:
        return scenes
    
    # Calculate adjustment factor
    factor = target_duration / current_total
    
    adjusted_scenes = []
    remaining = target_duration
    
    for i, scene in enumerate(scenes):
        if i == len(scenes) - 1:
            # Last scene gets remaining duration
            adjusted_duration = remaining
        else:
            # Calculate proportional duration
            adjusted_duration = max(3, min(7, round(scene.duration * factor)))
            remaining -= adjusted_duration
        
        adjusted_scenes.append(Scene(
            scene_number=scene.scene_number,
            scene_type=scene.scene_type,
            visual_prompt=scene.visual_prompt,
            text_overlay=scene.text_overlay,
            duration=adjusted_duration
        ))
    
    return adjusted_scenes


def create_basic_scene_plan_from_prompt(
    prompt: str, 
    target_duration: int = 15,
    num_scenes: Optional[int] = None
) -> ScenePlan:
    """
    Create a basic scene plan directly from user prompt without LLM enhancement.
    Used when LLM layer is disabled.
    
    Args:
        prompt: User's text prompt
        target_duration: Target total duration in seconds (default: 15)
        num_scenes: Number of scenes to create (optional, will be calculated from target_duration if None)
    
    Returns:
        ScenePlan: Basic scene plan with scenes generated from prompt
    """
    logger.info(f"Creating basic scene plan from prompt (no LLM): {prompt[:100]}...")
    
    # If num_scenes not provided, calculate based on target_duration
    # Aim for 4-5 seconds per scene on average, but respect max 7s per scene
    if num_scenes is None:
        # Calculate optimal number of scenes
        # Try to use 4-5 seconds per scene, but can go up to 7s if needed
        avg_duration = 4.5  # Target average duration per scene
        num_scenes = max(3, min(8, round(target_duration / avg_duration)))
        logger.info(f"Calculated {num_scenes} scenes for target duration {target_duration}s")
    
    # Limit num_scenes to valid range
    num_scenes = max(3, min(8, num_scenes))
    
    # Calculate duration per scene (max 7 seconds per scene)
    duration_per_scene = max(3, min(7, target_duration // num_scenes))
    remaining_duration = target_duration - (duration_per_scene * (num_scenes - 1))
    
    # Create simple scenes from prompt
    scenes = []
    for i in range(1, num_scenes + 1):
        # Use the prompt as visual prompt, with slight variations
        if i == 1:
            visual_prompt = f"{prompt}. Opening scene, establishing shot, cinematic quality"
        elif i == num_scenes:
            visual_prompt = f"{prompt}. Closing scene, call to action, professional finish"
        else:
            visual_prompt = f"{prompt}. Scene {i}, dynamic composition, engaging visuals"
        
        # Determine duration (last scene gets remaining duration)
        scene_duration = remaining_duration if i == num_scenes else duration_per_scene
        
        scene = Scene(
            scene_number=i,
            scene_type=f"Scene {i}",
            visual_prompt=visual_prompt,
            text_overlay=TextOverlay(
                text="" if i < num_scenes else "Learn More",
                position="bottom" if i < num_scenes else "center",
                font_size=48,
                color="#FFFFFF",
                animation="fade_in"
            ),
            duration=scene_duration
        )
        scenes.append(scene)
    
    scene_plan = ScenePlan(
        scenes=scenes,
        total_duration=sum(scene.duration for scene in scenes),
        framework="AIDA"  # Default framework when LLM is disabled
    )
    
    logger.info(f"Basic scene plan created: {len(scenes)} scenes, {scene_plan.total_duration}s total")
    return scene_plan


# ScenePlan is imported from app.schemas.generation

