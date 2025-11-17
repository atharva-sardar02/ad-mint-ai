"""
Storyboard planner that creates detailed scene-by-scene plan using LLM.
Generates detailed prompts for each scene that will be used for both image and video generation.
"""
import json
import logging
from typing import List, Optional

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_storyboard_system_prompt(num_scenes: int = 4) -> str:
    """Generate system prompt based on number of scenes."""
    if num_scenes == 4:
        framework = "AIDA (Attention → Interest → Desire → Action)"
        scene_structure = "Attention, Interest, Desire, Action"
        first_scene_stage = "Attention"
    elif num_scenes == 3:
        framework = "3-act structure (Setup → Confrontation → Resolution)"
        scene_structure = "Setup, Confrontation, Resolution"
        first_scene_stage = "Setup"
    else:
        framework = f"{num_scenes}-scene narrative structure"
        scene_structure = f"Scene 1, Scene 2, ... Scene {num_scenes}"
        first_scene_stage = "Scene 1"
    
    return f"""You are a professional video creative director and storyboard artist working on a legitimate creative video production project. Your job is to create a compelling, detailed storyboard for a {num_scenes}-scene creative video project following the {framework} structure. This is for educational and creative purposes, helping visualize concepts through video storytelling.

Think of this like you're briefing a cinematographer and visual effects team. You need to paint a vivid picture with words so they can bring your vision to life. This is a creative storytelling task focused on visual narrative and cinematography.

Here's what I need from you:

First, establish the visual language. Think about the overall style, color palette, lighting approach, composition style, and mood that will tie all {num_scenes} scenes together. This creates visual consistency throughout the entire video.

Then, for each of the {num_scenes} scenes, craft three natural, descriptive prompts:

1. **Main Scene Prompt** - This is your primary description. Write it like you're describing a scene to a director. Be specific about what we see: the environment, the action happening, how the camera frames it, the lighting, the mood. Make it vivid and cinematic. Aim for 40-80 words that capture the essence of the scene. This prompt will be used to generate both the reference image and the video clip.

2. **Start Frame Prompt** - Describe exactly what the first frame looks like when the video begins. What's the initial pose? Where is everything positioned? What's the setup before any action happens? Be specific about the opening moment.

3. **End Frame Prompt** - Describe the final frame, the last moment of the 4-second clip. How does the scene conclude? What's the final position or state? What does the viewer see as the clip ends?

For the video generation, we're using advanced AI models that can work with reference images, start images, and end images. The main scene prompt creates the reference image (the representative frame), while the start and end prompts help create precise frame control for models like Kling 2.5 Turbo.

Remember: Write these prompts in natural, descriptive language. Think like a filmmaker describing a shot, not like filling out a form. Be creative, be specific, and make it come alive.

Now, I need you to return this in a structured JSON format so we can process it programmatically. Here's the structure:

{{
  "consistency_markers": {{
    "style": "Describe the overall visual style in natural language",
    "color_palette": "Describe the color scheme naturally",
    "lighting": "Describe the lighting approach",
    "composition": "Describe the composition style",
    "mood": "Describe the emotional tone"
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "aida_stage": "{first_scene_stage}",
      "detailed_prompt": "Your natural, descriptive main scene prompt here - write it like you're describing a shot to a cinematographer",
      "start_image_prompt": "Your natural description of the first frame",
      "end_image_prompt": "Your natural description of the last frame",
      "scene_description": {{
        "environment": "Natural description of where this takes place",
        "character_action": "Natural description of what's happening",
        "camera_angle": "Natural description of the camera perspective",
        "composition": "Natural description of how the frame is composed",
        "visual_elements": "Natural description of key visual elements"
      }},
      "duration_seconds": 4
    }}
    // ... continue for all {num_scenes} scenes
  ]
}}

Key points:
- Write all prompts in natural, conversational language - like you're describing a scene to a colleague
- Be specific and vivid - the more detail, the better the generated visuals
- Maintain consistency across all scenes using the same visual markers
- Each scene is exactly 4 seconds long
- Follow the {framework} progression: {scene_structure}
"""


async def plan_storyboard(
    user_prompt: str,
    reference_image_path: Optional[str] = None,
    num_scenes: int = 4,
    max_retries: int = 3,
) -> dict:
    """
    Create a detailed storyboard plan using LLM.
    
    Args:
        user_prompt: User's original prompt
        reference_image_path: Optional reference image path (if user provided one)
        num_scenes: Number of scenes to generate (default: 4 for AIDA)
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Storyboard plan with detailed prompts for each scene
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    # Use best available OpenAI model with vision if reference image provided
    model = "gpt-4o"  # Best model with vision capabilities
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Get system prompt based on number of scenes
    system_prompt = get_storyboard_system_prompt(num_scenes)
    
    # Build user message in natural language - make it clear this is for creative/educational purposes
    if reference_image_path:
        user_content = f"I'm working on a creative video production project and need help creating a {num_scenes}-scene video storyboard. This is for legitimate creative and educational purposes. Here's the concept I want to visualize: {user_prompt}\n\nI've also provided a reference image that shows the style and subject matter I want. Please analyze it and use it to inform your storyboard. Create detailed, natural language prompts for each scene that will bring this creative vision to life."
    else:
        user_content = f"I'm working on a creative video production project and need help creating a {num_scenes}-scene video storyboard. This is for legitimate creative and educational purposes. Here's the concept I want to visualize: {user_prompt}\n\nPlease create a detailed storyboard with rich, cinematic descriptions for each scene. Write the prompts naturally, like you're describing shots to a film crew."
    
    # Prepare messages - will be modified on retries if needed
    messages = []
    if reference_image_path:
        from app.services.pipeline.storyboard_generator import _encode_image, _prepare_image_messages
        messages = _prepare_image_messages(user_content, [reference_image_path])
    else:
        messages = [{"role": "user", "content": user_content}]
    
    last_error = None
    use_reference_image = reference_image_path is not None  # Track if we should use image
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Storyboard Planner] Attempt {attempt}/{max_retries} using {model}")
                
                # On attempt 2+, try without reference image if it exists (might be triggering filters)
                if attempt >= 2 and reference_image_path and use_reference_image:
                    logger.warning(f"[Storyboard Planner] Attempt {attempt}: Retrying without reference image (may be causing content filter issues)")
                    # Use text-only message without image
                    messages = [{"role": "user", "content": user_content.replace("I've also provided a reference image", "I have a reference image available but will describe the concept")}]
                    use_reference_image = False  # Don't try with image again
                
                # Try with JSON mode, but skip it if we had issues in previous attempts
                use_json_mode = attempt == 1  # Only use JSON mode on first attempt
                
                if use_json_mode:
                    try:
                        response = await async_client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                *messages
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.7,
                            max_tokens=4000,  # Increased for detailed prompts
                        )
                    except Exception as e:
                        logger.warning(f"[Storyboard Planner] JSON mode failed, trying without JSON constraint: {e}")
                        use_json_mode = False
                
                if not use_json_mode:
                    # Retry without JSON mode constraint
                    response = await async_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *messages
                        ],
                        temperature=0.7,
                        max_tokens=4000,
                    )
                
                # Log full response for debugging
                try:
                    logger.debug(f"[Storyboard Planner] Full response structure: {response.model_dump_json(indent=2) if hasattr(response, 'model_dump_json') else 'No model_dump_json method'}")
                    if hasattr(response, 'choices') and response.choices:
                        choice = response.choices[0]
                        logger.debug(f"[Storyboard Planner] Choice details: finish_reason={choice.finish_reason}, message_type={type(choice.message)}, has_content={hasattr(choice.message, 'content')}")
                        if hasattr(choice.message, 'content'):
                            logger.debug(f"[Storyboard Planner] Content preview: {str(choice.message.content)[:200] if choice.message.content else 'None'}")
                except Exception as e:
                    logger.warning(f"[Storyboard Planner] Could not log response details: {e}")
                
                # Check if response has content
                if not response.choices or not response.choices[0].message:
                    error_msg = f"Empty response from OpenAI API. Response: {response}"
                    logger.error(f"[Storyboard Planner Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Check finish_reason to understand why content might be missing
                finish_reason = response.choices[0].finish_reason
                if finish_reason != "stop":
                    error_msg = f"Unexpected finish_reason: {finish_reason}. This might indicate content filtering, length limits, or API issues."
                    logger.warning(f"[Storyboard Planner Warning] {error_msg}")
                
                # Get content - check multiple possible locations
                message = response.choices[0].message
                content = message.content
                
                # Check if content is None - this might happen with JSON mode and vision API
                if not content:
                    # Check for refusal message
                    refusal = getattr(message, 'refusal', None)
                    if refusal:
                        logger.error(f"[Storyboard Planner] OpenAI refused the request: {refusal}")
                        # If it's a refusal, we should provide a clearer error message
                        if attempt < max_retries:
                            # Try with a modified prompt that's more explicit about creative/educational use
                            logger.info(f"[Storyboard Planner] Request was refused. Retrying with modified prompt on attempt {attempt + 1}")
                            last_error = f"OpenAI API refused the request: {refusal}. This may be due to content filtering. Retrying with modified prompt."
                            continue
                        else:
                            raise ValueError(f"OpenAI API refused the request after {max_retries} attempts: {refusal}. This may be due to content filtering. Please try a different prompt or contact support.")
                    
                    # Log the entire message object to see what we have
                    logger.error(f"[Storyboard Planner] Content is None. Message object: {message}")
                    
                    # Log detailed response info for debugging
                    response_info = {
                        "finish_reason": finish_reason,
                        "model": response.model if hasattr(response, 'model') else 'unknown',
                        "usage": response.usage.model_dump() if hasattr(response, 'usage') and response.usage else None,
                        "message_role": message.role if hasattr(message, 'role') else 'unknown',
                        "message_refusal": refusal,
                    }
                    error_msg = f"Response content is None or empty. Finish reason: {finish_reason}. Response info: {response_info}"
                    logger.error(f"[Storyboard Planner Error] {error_msg}")
                    
                    # If we're using JSON mode and getting empty content, try without it on next attempt
                    if attempt < max_retries:
                        last_error = error_msg
                        logger.info(f"[Storyboard Planner] Retrying without JSON mode constraint on attempt {attempt + 1}")
                        continue
                    raise ValueError(f"OpenAI API returned empty content. Finish reason: {finish_reason}. This might indicate the response was filtered, truncated, or the model refused to respond.")
                
                # Parse JSON - handle both raw JSON and JSON in markdown code blocks
                try:
                    # Try parsing directly first
                    storyboard_plan = json.loads(content)
                except json.JSONDecodeError:
                    # If that fails, try extracting JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            storyboard_plan = json.loads(json_match.group(1))
                            logger.info("[Storyboard Planner] Extracted JSON from markdown code block")
                        except json.JSONDecodeError as e:
                            error_msg = f"Invalid JSON in code block: {e}. Content preview: {content[:500]}"
                            logger.warning(f"[Storyboard Planner Error] {error_msg}")
                            if attempt < max_retries:
                                last_error = error_msg
                                continue
                            raise ValueError(error_msg)
                    else:
                        error_msg = f"Could not find valid JSON in response. Content preview: {content[:500]}"
                        logger.warning(f"[Storyboard Planner Error] {error_msg}")
                        if attempt < max_retries:
                            last_error = error_msg
                            continue
                        raise ValueError(error_msg)
                except TypeError as e:
                    error_msg = f"Type error parsing JSON: {e}. Content type: {type(content)}"
                    logger.error(f"[Storyboard Planner Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Validate structure
                scenes = storyboard_plan.get("scenes", [])
                if len(scenes) != num_scenes:
                    if attempt < max_retries:
                        logger.warning(f"Expected {num_scenes} scenes, got {len(scenes)}, retrying...")
                        continue
                    raise ValueError(f"Expected {num_scenes} scenes, got {len(scenes)}")
                
                # Validate each scene has required fields
                for scene in scenes:
                    if "detailed_prompt" not in scene:
                        if attempt < max_retries:
                            logger.warning(f"Scene {scene.get('scene_number')} missing detailed_prompt, retrying...")
                            continue
                        raise ValueError(f"Scene {scene.get('scene_number')} missing detailed_prompt")
                    # Validate start_image_prompt and end_image_prompt (for Kling 2.5 Turbo Pro)
                    if "start_image_prompt" not in scene:
                        logger.warning(f"Scene {scene.get('scene_number')} missing start_image_prompt (optional for Kling 2.5 Turbo Pro)")
                    if "end_image_prompt" not in scene:
                        logger.warning(f"Scene {scene.get('scene_number')} missing end_image_prompt (optional for Kling 2.5 Turbo Pro)")
                
                logger.info(f"✅ Storyboard plan generated with {len(scenes)} detailed scenes")
                logger.debug(f"Consistency markers: {storyboard_plan.get('consistency_markers', {})}")
                
                return storyboard_plan
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Storyboard Planner Error] {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 20))
                    continue
        
        raise RuntimeError(f"Storyboard planning failed after retries: {last_error}")
    
    finally:
        await async_client.close()

