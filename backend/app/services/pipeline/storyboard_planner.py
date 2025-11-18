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

def get_storyboard_system_prompt(target_duration: int = 15) -> str:
    """Generate system prompt based on target duration."""
    # Calculate optimal scene structure based on target duration
    # Maximum duration per scene is 7 seconds
    # Minimum duration per scene is 3 seconds
    # LLM will decide the number of scenes and duration per scene
    
    # Suggest a framework based on duration
    if target_duration <= 12:
        framework_suggestion = "3-act structure (Setup → Confrontation → Resolution)"
        suggested_scenes = 3
    elif target_duration <= 20:
        framework_suggestion = "AIDA (Attention → Interest → Desire → Action)"
        suggested_scenes = 4
    elif target_duration <= 30:
        framework_suggestion = "5-act narrative structure"
        suggested_scenes = 5
    else:
        framework_suggestion = "Extended narrative structure"
        suggested_scenes = max(5, target_duration // 6)  # Rough estimate
    
    # Calculate average duration per scene
    avg_duration = target_duration / suggested_scenes if suggested_scenes > 0 else 5
    
    return f"""You are a professional video creative director and storyboard artist working on a legitimate creative video production project. Your job is to create a compelling, detailed storyboard for a creative video project with a target total duration of {target_duration} seconds. This is for educational and creative purposes, helping visualize concepts through video storytelling.

IMPORTANT DURATION RULES:
- The target total duration is {target_duration} seconds
- **CRITICAL**: Each scene MUST be between 3 and 7 seconds long. MINIMUM is 3 seconds, MAXIMUM is 7 seconds.
- DO NOT create scenes shorter than 3 seconds or longer than 7 seconds
- You must decide how many scenes to create and the duration of each scene
- The sum of all scene durations should be as close as possible to {target_duration} seconds
- If the target duration is longer, you can use longer individual scenes (up to 7 seconds) or more scenes
- Suggested framework: {framework_suggestion} (approximately {suggested_scenes} scenes)
- You have creative freedom to adjust the number of scenes and their durations to best tell the story, but each scene must be 3-7 seconds

Think of this like you're briefing a cinematographer and visual effects team. You need to paint a vivid picture with words so they can bring your vision to life. This is a creative storytelling task focused on visual narrative and cinematography.

Here's what I need from you:

First, decide on the storyboard structure:
- Determine the optimal number of scenes (based on the story needs and target duration of {target_duration} seconds)
- Assign a duration to each scene - **MUST be between 3-7 seconds (MINIMUM 3, MAXIMUM 7)**
- Ensure the total duration is close to {target_duration} seconds
- Use longer scenes (up to 7 seconds) when the narrative requires more time, or create more scenes if the story benefits from more moments
- **NEVER assign a scene duration less than 3 seconds or more than 7 seconds**

Then, establish the visual language. Think about the overall style, color palette, lighting approach, composition style, and mood that will tie all scenes together. This creates visual consistency throughout the entire video.

**CRITICAL: SUBJECT IDENTITY CONSISTENCY**
This is the #1 priority when the subject appears. If your storyboard features a main subject (product, character, object):
- The subject does NOT need to appear in every scene - use your creative judgment
- Some scenes might be establishing shots, close-ups of other elements, environmental shots, etc. WITHOUT the subject
- HOWEVER: When the subject DOES appear (in any scene), it must be the EXACT SAME subject with IDENTICAL appearance
- If it's a perfume bottle: the SAME bottle design (shape, color, label, material, size) in every scene where it appears
- If it's a character: the SAME person (face, clothing, hair, features) in every scene where they appear
- If it's a product: the SAME product (exact design, branding, proportions) in every scene where it appears
- DO NOT allow the subject to change, morph, or vary between scenes where it appears
- Treat the subject like a real physical object that remains identical whenever it's shown
- In your detailed prompts for Scene 1 where the subject first appears, explicitly describe the subject's characteristics in detail
- In subsequent scenes where the subject appears, reference "the same [subject] from Scene 1" to maintain consistency
- For scenes where the subject does NOT appear, use `subject_presence: "none"` and focus on other visual elements

Then, for each scene you create, you need to create MULTIPLE types of prompts for different purposes:

**CRITICAL: Subject Presence Control** - For each scene, you must decide:
- Whether the main subject (product/character) appears in this scene
- If yes, when does the subject appear? (throughout, at start, at end, appears mid-scene, disappears mid-scene)
- How long is the subject visible? (full scene duration, partial duration with specific timing)
- This gives you creative control: some scenes might be establishing shots without the subject, some might focus entirely on the subject, some might have the subject enter or exit

**1. Main Scene Prompt (detailed_prompt)** - This is your primary description for video generation. Write it like you're describing a scene to a director. Be specific about what we see: the environment, the action happening, how the camera frames it, the lighting, the mood. IMPORTANT: If the subject should NOT appear in this scene, make that clear. If the subject appears only partway through, describe when it appears. If the subject is present throughout, describe it naturally. Aim for 40-80 words that capture the essence of the scene. This prompt will be used for video generation.

**2. Detailed Image Generation Prompt (image_generation_prompt)** - This is CRITICAL for maintaining visual cohesion, especially SUBJECT IDENTITY. This is a much more detailed, image-specific prompt (80-150 words) that explicitly describes:
   - **THE EXACT SAME SUBJECT**: For scenes 2+, start with "The EXACT SAME [subject type] from Scene 1" (e.g., "The EXACT SAME frosted glass perfume bottle from Scene 1")
   - **Subject's precise physical characteristics**: In Scene 1, establish detailed specs (e.g., "8-inch tall perfume bottle, frosted matte glass, silver metallic cap, thin rectangular label, rose gold liquid inside")
   - **For scenes 2+**: Reference these exact specs and state "maintaining identical appearance"
   - Exact visual details: colors, textures, materials, shapes, proportions
   - Specific visual characteristics that must remain the same across ALL scenes
   - Lighting specifics: direction, intensity, color temperature, shadows
   - Composition details: exact positioning, framing, depth of field
   - Style specifics: rendering style, level of detail, visual treatment
   - How this image should visually connect to previous scenes (for scenes 2+)
   
   This prompt is specifically crafted for image generation models to ensure maximum visual consistency, ESPECIALLY FOR THE SUBJECT. Be extremely detailed about the subject's appearance and explicitly state it must be identical across scenes.

**3. Image Continuity Notes (image_continuity_notes)** - For scenes 2 and beyond, describe how this image should visually relate to the previous scene(s):
   - **IF SUBJECT APPEARS**: Explicitly state "The EXACT SAME [subject] from Scene X must appear with IDENTICAL appearance" (where X is the first scene the subject appeared in)
   - **IF SUBJECT DOES NOT APPEAR**: Describe how this scene relates visually to the overall video without the subject
   - What elements carry over from the previous scene?
   - How should colors, lighting, or style transition?
   - What visual elements should remain IDENTICAL (e.g., "the EXACT SAME perfume bottle from scene 1 with identical frosted glass, silver cap, and label" - but only if subject appears in this scene)
   - Any visual progression or evolution that should occur
   - For scene 1, describe what visual foundation is being established (especially the subject's defining characteristics if it appears, or the overall visual world if it doesn't)

**4. Visual Consistency Guidelines (visual_consistency_guidelines)** - Per-scene specific instructions for maintaining visual consistency:
   - Exact specifications for recurring elements (dimensions, colors, materials, textures)
   - Camera style consistency (lens type, focal length, depth of field)
   - Color grading consistency (specific color values, saturation levels)
   - Lighting consistency (same light sources, shadows, highlights)
   - Style consistency (rendering approach, level of realism, visual treatment)

**5. Scene Transition Notes (scene_transition_notes)** - For scenes 2+, describe how this scene visually transitions from the previous one:
   - Visual flow: how does the camera move or the scene change?
   - Element continuity: what stays the same, what changes?
   - Color/lighting transition: how does the visual mood shift?
   - Spatial relationship: how does this scene relate spatially to the previous one?

**6. Start Frame Prompt (start_image_prompt)** - CRITICAL: Describe exactly what the FIRST FRAME looks like when THIS SPECIFIC SCENE begins. This must be a DIFFERENT moment/pose/position from other scenes, BUT maintain the SAME subject, style, colors, lighting, and visual characteristics when the subject IS present. IMPORTANT: 
- If the subject appears in this scene from the start, describe the subject at the opening moment (e.g., "person standing, about to start")
- If the subject does NOT appear at the start (e.g., appears mid-scene), describe the scene WITHOUT the subject (e.g., "empty elegant room, camera slowly panning")
- If the subject appears later, the start frame should show the scene before the subject enters
- They are UNIQUE moments but VERY SIMILAR visually when subject IS present (same subject, same style, same colors, same lighting)
- Be extremely detailed about visual consistency: exact same subject appearance, same colors, same lighting direction, same style (when subject is present)
- Include detailed visual specifications for image generation

**7. End Frame Prompt (end_image_prompt)** - CRITICAL: Describe the final frame, the last moment of THIS SPECIFIC SCENE's clip. This must be a DIFFERENT moment/pose/position from other scenes, BUT maintain the SAME subject, style, colors, lighting, and visual characteristics when the subject IS present. IMPORTANT:
- If the subject is present at the end of this scene, describe the subject at the closing moment (e.g., "person in specific pose")
- If the subject has exited or is not present at the end, describe the scene WITHOUT the subject (e.g., "empty space where subject was, camera lingering")
- If the subject appears at the end, the end frame should show the subject entering or present
- They are UNIQUE moments but VERY SIMILAR visually when subject IS present (same subject, same style, same colors, same lighting)
- Be extremely detailed about visual consistency: exact same subject appearance, same colors, same lighting direction, same style (when subject is present)
- Include detailed visual specifications for image generation

The key difference: The `image_generation_prompt` is MUCH more detailed and explicit about visual consistency than the `detailed_prompt`. It's specifically designed to help image generation models create cohesive visuals that maintain consistency across all scenes.

For the video generation, we're using advanced AI models that can work with reference images, start images, and end images. The detailed image generation prompts create the reference images (ensuring visual consistency), while the start and end prompts help create precise frame control for models like Kling 2.5 Turbo.

Remember: Write all prompts in natural, descriptive language. Think like a filmmaker describing a shot, not like filling out a form. Be creative, be specific, and make it come alive. The image generation prompts should be especially detailed to ensure visual cohesion.

Now, I need you to return this in a structured JSON format so we can process it programmatically. Here's the structure:

{{
  "consistency_markers": {{
    "style": "Describe the overall visual style in natural language",
    "color_palette": "Describe the color scheme naturally",
    "lighting": "Describe the lighting approach",
    "composition": "Describe the composition style",
    "mood": "Describe the emotional tone",
    "subject_description": "CRITICAL: Provide an EXTREMELY detailed description of the main subject (product/character/object) for when it appears in scenes. This is used to ensure the subject looks IDENTICAL in every scene where it appears. Include EXACT specifications: dimensions, colors, materials, textures, shapes, branding, labels, proportions, distinctive features. This description must be so detailed that an artist could recreate the exact same subject. Example for perfume: '8-inch tall perfume bottle with frosted matte glass body, silver metallic cap (1-inch diameter), thin rose gold metallic rectangular label with embossed text, rose gold liquid visible inside, subtle hexagonal facets on bottle sides, narrow neck transitioning to rounded shoulders'. Note: The subject does NOT need to appear in every scene, but this description ensures it's identical whenever it DOES appear."
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "aida_stage": "Attention",
      "detailed_prompt": "Your natural, descriptive main scene prompt here (40-80 words) - for video generation",
      "image_generation_prompt": "Your EXTREMELY detailed image generation prompt here (80-150 words) - explicitly describe visual details, exact colors, textures, materials, lighting specifics, composition details, and style. This is critical for visual consistency.",
      "image_continuity_notes": "For scene 1: Describe what visual foundation is being established. What key elements are introduced that must remain consistent?",
      "visual_consistency_guidelines": "Specific per-scene instructions: exact specifications for recurring elements, camera style, color grading, lighting, and rendering style that must be maintained.",
      "scene_transition_notes": "For scene 1: This is the opening scene, establishing the visual world.",
      "start_image_prompt": "Your detailed description of the first frame with visual specifications",
      "end_image_prompt": "Your detailed description of the last frame with visual specifications",
      "subject_presence": "full" | "partial" | "none" | "appears_at_start" | "appears_at_end" | "appears_mid_scene" | "disappears_mid_scene",
      "subject_appearance_timing": "Detailed description of when and how the subject appears in this scene. If 'full', describe that subject is present throughout. If 'partial', specify exact timing (e.g., 'subject enters at 2 seconds and remains until end', 'subject visible for first 3 seconds then camera moves away'). If 'none', describe why the subject is not present (e.g., 'establishing shot of environment', 'focus on supporting elements').",
      "subject_duration_in_scene": <NUMBER>,  // Duration in seconds that the subject is visible in this scene. If subject_presence is 'full', this equals duration_seconds. If 'partial', specify the actual duration (e.g., if scene is 6 seconds but subject appears for 3 seconds, put 3). If 'none', put 0.
      "scene_description": {{
        "environment": "Natural description of where this takes place",
        "character_action": "Natural description of what's happening",
        "camera_angle": "Natural description of the camera perspective",
        "composition": "Natural description of how the frame is composed",
        "visual_elements": "Natural description of key visual elements"
      }},
      "duration_seconds": <YOUR_CHOSEN_DURATION>  // **CRITICAL**: MUST be between 3 and 7 seconds (MINIMUM 3, MAXIMUM 7). Choose the duration that best fits this scene's narrative needs.
    }}
    // ... continue for all scenes you create
    // IMPORTANT: The sum of all "duration_seconds" should be close to {target_duration} seconds
    // **CRITICAL**: Every scene's duration_seconds MUST be at least 3 and at most 7
    // For scenes 2+, make sure image_continuity_notes and scene_transition_notes reference previous scenes
  ]
}}

Key points:
- Write all prompts in natural, conversational language - like you're describing a scene to a colleague
- The `image_generation_prompt` should be MUCH more detailed than `detailed_prompt` - it's specifically for ensuring visual cohesion
- Be extremely specific about visual elements that must remain consistent across scenes
- For scenes 2+, explicitly reference how elements from previous scenes should appear
- Maintain consistency across all scenes using the same visual markers
- **CRITICAL**: Each scene duration MUST be YOUR CHOICE between 3-7 seconds (MINIMUM 3, MAXIMUM 7)
- The total duration of all scenes should be close to {target_duration} seconds
- Follow the {framework_suggestion} progression as a guide, but adapt it to fit the story and target duration
- You decide the number of scenes and duration per scene based on what best serves the narrative
"""


async def plan_storyboard(
    user_prompt: str,
    reference_image_path: Optional[str] = None,
    target_duration: int = 15,
    max_retries: int = 3,
) -> dict:
    """
    Create a detailed storyboard plan using LLM.
    
    Args:
        user_prompt: User's original prompt
        reference_image_path: Optional reference image path (if user provided one)
        target_duration: Target total duration in seconds (default: 15). LLM will decide number of scenes and duration per scene (max 7s per scene)
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Storyboard plan with detailed prompts for each scene
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    # Use best available OpenAI model with vision if reference image provided
    model = "gpt-4o"  # Best model with vision capabilities
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Get system prompt based on target duration
    system_prompt = get_storyboard_system_prompt(target_duration)
    
    # Build user message in natural language - make it clear this is for creative/educational purposes
    if reference_image_path:
        user_content = f"I'm working on a creative video production project and need help creating a video storyboard with a target duration of {target_duration} seconds. This is for legitimate creative and educational purposes. Here's the concept I want to visualize: {user_prompt}\n\nI've also provided a reference image that shows the style and subject matter I want. Please analyze it and use it to inform your storyboard. Decide how many scenes to create and the duration of each scene (each scene can be 3-7 seconds, maximum 7 seconds per scene). The total duration should be close to {target_duration} seconds. Create detailed, natural language prompts for each scene that will bring this creative vision to life."
    else:
        user_content = f"I'm working on a creative video production project and need help creating a video storyboard with a target duration of {target_duration} seconds. This is for legitimate creative and educational purposes. Here's the concept I want to visualize: {user_prompt}\n\nPlease decide how many scenes to create and the duration of each scene (each scene can be 3-7 seconds, maximum 7 seconds per scene). The total duration should be close to {target_duration} seconds. Create a detailed storyboard with rich, cinematic descriptions for each scene. Write the prompts naturally, like you're describing shots to a film crew."
    
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
                            max_tokens=6000,  # Increased for detailed image generation prompts
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
                        max_tokens=6000,  # Increased for detailed image generation prompts
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
                # Validate scene count is reasonable (at least 1, not too many)
                if len(scenes) < 1:
                    if attempt < max_retries:
                        logger.warning(f"Got {len(scenes)} scenes, expected at least 1, retrying...")
                        continue
                    raise ValueError(f"Expected at least 1 scene, got {len(scenes)}")
                
                # Validate each scene duration is within limits (3-7 seconds)
                total_duration = 0
                for scene in scenes:
                    scene_duration = scene.get("duration_seconds", 4)
                    if scene_duration < 3 or scene_duration > 7:
                        if attempt < max_retries:
                            logger.warning(f"Scene {scene.get('scene_number')} has invalid duration {scene_duration}s (must be 3-7s), retrying...")
                            continue
                        raise ValueError(f"Scene {scene.get('scene_number')} has invalid duration {scene_duration}s (must be between 3 and 7 seconds)")
                    total_duration += scene_duration
                
                logger.info(f"✅ Storyboard has {len(scenes)} scenes with total duration {total_duration}s (target: {target_duration}s)")
                
                # Validate each scene has required fields
                for scene in scenes:
                    if "detailed_prompt" not in scene:
                        if attempt < max_retries:
                            logger.warning(f"Scene {scene.get('scene_number')} missing detailed_prompt, retrying...")
                            continue
                        raise ValueError(f"Scene {scene.get('scene_number')} missing detailed_prompt")
                    # Validate image_generation_prompt (critical for visual cohesion)
                    if "image_generation_prompt" not in scene:
                        logger.warning(f"Scene {scene.get('scene_number')} missing image_generation_prompt - will fallback to detailed_prompt")
                        # Fallback: use detailed_prompt if image_generation_prompt is missing
                        scene["image_generation_prompt"] = scene.get("detailed_prompt", "")
                    # Validate optional but recommended fields
                    if "image_continuity_notes" not in scene:
                        logger.warning(f"Scene {scene.get('scene_number')} missing image_continuity_notes (optional but recommended)")
                    if "visual_consistency_guidelines" not in scene:
                        logger.warning(f"Scene {scene.get('scene_number')} missing visual_consistency_guidelines (optional but recommended)")
                    if "scene_transition_notes" not in scene:
                        logger.warning(f"Scene {scene.get('scene_number')} missing scene_transition_notes (optional but recommended)")
                    # Validate start_image_prompt and end_image_prompt (for Kling 2.5 Turbo Pro)
                    if "start_image_prompt" not in scene:
                        logger.warning(f"Scene {scene.get('scene_number')} missing start_image_prompt (optional for Kling 2.5 Turbo Pro)")
                    if "end_image_prompt" not in scene:
                        logger.warning(f"Scene {scene.get('scene_number')} missing end_image_prompt (optional for Kling 2.5 Turbo Pro)")
                
                logger.info(f"✅ Storyboard plan generated with {len(scenes)} detailed scenes")
                logger.debug(f"Consistency markers: {storyboard_plan.get('consistency_markers', {})}")
                
                # Store LLM input and output for complete flow tracking
                storyboard_plan["llm_input"] = {
                    "system_prompt": system_prompt,
                    "user_message": user_content if not reference_image_path or not use_reference_image else "User message with reference image (see image attachment)",
                    "model": model,
                    "target_duration": target_duration,
                    "num_scenes": len(scenes),  # Actual number of scenes decided by LLM
                    "total_duration": sum(s.get("duration_seconds", 4) for s in scenes),  # Actual total duration
                    "reference_image_provided": reference_image_path is not None and use_reference_image,
                }
                storyboard_plan["llm_output"] = {
                    "raw_response": content,  # Store the raw JSON response from LLM
                    "model_used": model,
                    "finish_reason": finish_reason,
                }
                
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


async def refine_storyboard_scene(
    storyboard_plan: dict,
    scene_number: int,
    refinement_instruction: str,
    max_retries: int = 2,
) -> dict:
    """
    Refine a specific scene in the storyboard plan by sending it back to the LLM with refinement instructions.
    
    This allows fine-tuning specific scenes or prompts before generating images/videos.
    
    Args:
        storyboard_plan: The complete storyboard plan dictionary
        scene_number: The scene number to refine (1-indexed)
        refinement_instruction: Natural language instruction for what to refine (e.g., "make the lighting more dramatic", "add more detail about the product appearance")
        max_retries: Maximum retry attempts
    
    Returns:
        dict: Updated storyboard plan with the refined scene
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    model = "gpt-4o"
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    scenes = storyboard_plan.get("scenes", [])
    consistency_markers = storyboard_plan.get("consistency_markers", {})
    
    # Find the scene to refine
    scene_to_refine = None
    for scene in scenes:
        if scene.get("scene_number") == scene_number:
            scene_to_refine = scene
            break
    
    if not scene_to_refine:
        raise ValueError(f"Scene {scene_number} not found in storyboard plan")
    
    system_prompt = """You are a professional video creative director refining a specific scene in a storyboard. Your job is to improve the scene based on the refinement instruction while maintaining consistency with the overall storyboard.

You will receive:
1. The current scene details (all prompts and descriptions)
2. The consistency markers that apply to all scenes
3. A refinement instruction describing what needs to be improved

Your task is to refine the scene by updating the relevant prompts and descriptions according to the instruction. Make sure to:
- Keep the scene_number and aida_stage unchanged
- Maintain consistency with the consistency_markers
- Update the prompts to incorporate the refinement
- Ensure all prompts remain natural and descriptive
- If refining image_generation_prompt, make it even more detailed and explicit about visual elements

Return the refined scene in the same JSON structure as the original scene."""
    
    user_content = f"""I need to refine Scene {scene_number} in my storyboard. Here's the current scene:

{{
  "scene_number": {scene_to_refine.get("scene_number")},
  "aida_stage": "{scene_to_refine.get("aida_stage", "")}",
  "detailed_prompt": "{scene_to_refine.get("detailed_prompt", "")}",
  "image_generation_prompt": "{scene_to_refine.get("image_generation_prompt", scene_to_refine.get("detailed_prompt", ""))}",
  "image_continuity_notes": "{scene_to_refine.get("image_continuity_notes", "")}",
  "visual_consistency_guidelines": "{scene_to_refine.get("visual_consistency_guidelines", "")}",
  "scene_transition_notes": "{scene_to_refine.get("scene_transition_notes", "")}",
  "start_image_prompt": "{scene_to_refine.get("start_image_prompt", "")}",
  "end_image_prompt": "{scene_to_refine.get("end_image_prompt", "")}",
  "scene_description": {scene_to_refine.get("scene_description", {})}
}}

The consistency markers that apply to all scenes are:
{consistency_markers}

Refinement instruction: {refinement_instruction}

Please refine this scene according to the instruction. Return the complete refined scene in JSON format with all fields updated as needed."""
    
    last_error = None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Storyboard Refinement] Refining scene {scene_number}, attempt {attempt}/{max_retries}")
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=2000,
                )
                
                if not response.choices or not response.choices[0].message:
                    error_msg = f"Empty response from OpenAI API for scene refinement"
                    logger.error(f"[Storyboard Refinement Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                content = response.choices[0].message.content
                if not content:
                    error_msg = f"Response content is None for scene refinement"
                    logger.error(f"[Storyboard Refinement Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Parse JSON - handle both raw JSON and JSON in markdown code blocks
                try:
                    refined_scene = json.loads(content)
                except json.JSONDecodeError:
                    import re
                    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
                    if json_match:
                        try:
                            refined_scene = json.loads(json_match.group(1))
                            logger.info("[Storyboard Refinement] Extracted JSON from markdown code block")
                        except json.JSONDecodeError as e:
                            error_msg = f"Invalid JSON in code block: {e}"
                            logger.warning(f"[Storyboard Refinement Error] {error_msg}")
                            if attempt < max_retries:
                                last_error = error_msg
                                continue
                            raise ValueError(error_msg)
                    else:
                        error_msg = f"Could not find valid JSON in response. Content: {content[:500]}"
                        logger.warning(f"[Storyboard Refinement Error] {error_msg}")
                        if attempt < max_retries:
                            last_error = error_msg
                            continue
                        raise ValueError(error_msg)
                
                # Validate refined scene has required fields
                if "scene_number" not in refined_scene:
                    refined_scene["scene_number"] = scene_number
                if "detailed_prompt" not in refined_scene:
                    raise ValueError("Refined scene missing required field: detailed_prompt")
                
                # Update the scene in the storyboard plan
                for idx, scene in enumerate(scenes):
                    if scene.get("scene_number") == scene_number:
                        scenes[idx] = refined_scene
                        break
                
                storyboard_plan["scenes"] = scenes
                
                logger.info(f"✅ Scene {scene_number} refined successfully")
                return storyboard_plan
                
            except Exception as e:
                last_error = e
                logger.warning(f"[Storyboard Refinement Error] {e}")
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(min(2 ** attempt, 5))
                    continue
        
        raise RuntimeError(f"Scene refinement failed after retries: {last_error}")
    
    finally:
        await async_client.close()


async def refine_storyboard_prompts(
    storyboard_plan: dict,
    refinement_instructions: dict,
    max_retries: int = 2,
) -> dict:
    """
    Refine multiple scenes or specific prompts in the storyboard plan.
    
    Args:
        storyboard_plan: The complete storyboard plan dictionary
        refinement_instructions: Dict mapping scene_number to refinement instruction, or "all" to refine all scenes
                                Example: {1: "make lighting more dramatic", 2: "add more product details", "all": "increase visual detail"}
        max_retries: Maximum retry attempts per scene
    
    Returns:
        dict: Updated storyboard plan with refined scenes
    """
    if "all" in refinement_instructions:
        # Refine all scenes with the same instruction
        instruction = refinement_instructions["all"]
        scenes = storyboard_plan.get("scenes", [])
        for scene in scenes:
            scene_number = scene.get("scene_number")
            if scene_number:
                storyboard_plan = await refine_storyboard_scene(
                    storyboard_plan=storyboard_plan,
                    scene_number=scene_number,
                    refinement_instruction=instruction,
                    max_retries=max_retries,
                )
    else:
        # Refine specific scenes
        for scene_number, instruction in refinement_instructions.items():
            if isinstance(scene_number, int):
                storyboard_plan = await refine_storyboard_scene(
                    storyboard_plan=storyboard_plan,
                    scene_number=scene_number,
                    refinement_instruction=instruction,
                    max_retries=max_retries,
                )
    
    return storyboard_plan

