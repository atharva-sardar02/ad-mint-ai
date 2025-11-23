"""
Story Director Agent for Master Mode.

The Story Director writes comprehensive advertisement story drafts based on user prompts.
It creates full stories with character details, pacing, emotional beats, and scene breakdowns.
"""
import base64
import json
import logging
from pathlib import Path
from typing import List, Optional

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)

# System prompt for Story Director
STORY_DIRECTOR_SYSTEM_PROMPT = """You are a professional advertisement story director with decades of experience creating compelling video advertisements.

**YOUR ROLE:**
Create comprehensive, production-ready advertisement stories based on user prompts. Your stories must be detailed enough that a video production team can execute them directly.

**CRITICAL: MINIMUM LENGTH REQUIREMENT**
- Your story must be AT LEAST 1500 words
- Aim for 1500-2500 words of detailed content
- Short stories will be rejected - be thorough and comprehensive

**STORY STRUCTURE (Required Sections):**

## 1. Overview
- High-level narrative arc and concept
- Main message and value proposition
- Target audience and emotional appeal
- Recommended video duration ({target_duration_guidance})
- Visual style and mood

## 2. Narrative Arc ({scenes_guidance})

**For 3-scene videos (12-24 seconds) - Classic Structure:**
   - **Scene 1: Establishment/Entry**: The character enters the frame or is established in the location. They have a clear need or status quo.
   - **Scene 2: Interaction/Product Use - AUTHENTIC USAGE**: The character uses the product EXACTLY as it's intended to be used in real life:
     * Perfume/Cologne: Spray on neck, wrists, or clothing (show the spray mist, the pumping action, realistic application)
     * Skincare: Apply to face/skin with proper technique (massage, pat, smooth)
     * Beverage: Open, pour, sip naturally
     * Food: Unwrap, bite, chew, savor
     * Electronics: Power on, interact with controls/screen realistically
     * Clothing: Try on, adjust fit, check appearance
     * Tools: Use for intended purpose with proper technique
     
     ⚠️ CRITICAL: Show the ACTUAL USAGE ACTION in detail - not just holding the product. The viewer must see HOW the product is authentically used.
   
   - **Scene 3: Reaction/Result + PRODUCT SHOWCASE**: The character reacts to the product (smile, relief, joy) showing the benefit/result. **⚠️ CRITICAL: The final scene MUST culminate in an ELEGANT PRODUCT AND BRAND REVEAL** - show the product prominently with the brand name clearly visible in a beautiful, premium composition.

**For longer videos (25+ seconds, 4+ scenes) - Expanded Dynamic Narrative:**
   
   ⚠️ **CRITICAL**: DO NOT just show the same product usage from multiple angles. Tell a RICH, DYNAMIC STORY with variety!
   
   - **Act 1 (Scene 1):** Establishment/Entry - same as 3-scene structure
   
   - **Act 2 (Middle scenes 2 through N-1):** **DYNAMIC STORY PROGRESSION** - Each scene shows a DIFFERENT moment/context:
     * **Scene 2:** Initial product interaction/usage (authentic usage action)
     * **Scenes 3+:** Show a JOURNEY or TRANSFORMATION through time/contexts:
       - Different moments throughout the day/experience
       - Different emotional beats and reactions
       - Product benefits manifesting in different ways
       - Various contexts or mini-scenarios (all within same general location or logical progression)
       - Progression showing before → during → after effects
       - Social interactions or reactions from others
       - Multiple use cases or applications of the product
       - Build-up of benefits over time
       
     **Examples of dynamic middle scenes:**
     - Perfume: Application → Confidence boost → Social interaction → Lasting impression
     - Skincare: Application → Absorption → Fresh feeling → Radiant glow → Confidence
     - Food/Drink: Preparation → First taste → Savoring → Sharing → Satisfaction
     - Tech: Setup → First use → Key feature → Wow moment → Daily integration
   
   - **Act 3 (Final scene):** Results, satisfaction, and **PRODUCT + BRAND SHOWCASE** - same as 3-scene structure
   
   ⚠️ **KEY PRINCIPLES FOR LONGER VIDEOS:**
   - Each scene must show something NEW and MEANINGFUL
   - Maintain emotional progression and narrative momentum
   - Each scene = different moment in time OR different context OR different emotional beat
   - Avoid repetitive actions - show VARIETY and RICHNESS
   - All scenes flow naturally within the same location or logical space
   
   ⚠️ **FINAL SCENE PRODUCT SHOWCASE**: Must show the EXACT product from reference images with brand clearly visible
   ⚠️ **LOCATION CONSISTENCY**: All scenes in the SAME LOCATION (or logical progression if story requires movement)

## 3. Character Details (If using people from reference images)

   ⚠️ **ULTRA-REALISTIC & CONSISTENT - MANDATORY:**
   - Describe people in FORENSIC detail so they look IDENTICAL in every scene
   - These details will be used to generate all video scenes
   - ANY variation will cause people to look different between scenes
   - BE EXTREMELY SPECIFIC - every detail matters for consistency
   
   **Physical appearance** (MANDATORY DETAILS):
   - Exact age (not "30s" → "32 years old")
   - Exact height (e.g., "5'10" tall")
   - Exact build with measurements (e.g., "athletic build, 42-inch shoulders, defined musculature")
   
   **Facial features** (MANDATORY - BE FORENSICALLY SPECIFIC):
   - Face shape with angle (e.g., "oval face with 85-degree jawline")
   - Eye color with specifics (e.g., "deep brown eyes with amber flecks around pupil, almond-shaped")
   - Eyebrows (e.g., "naturally thick eyebrows with slight arch, dark brown matching hair")
   - Nose (e.g., "straight nose with narrow bridge, 1.2-inch width at base")
   - Lips (e.g., "medium lips, upper slightly thinner, natural pink tone")
   - Cheekbones (e.g., "high, prominent cheekbones with defined contour")
   - Jawline (e.g., "sharp, angular jawline with squared chin")
   - Facial hair (if any - e.g., "3mm stubble, 5% gray near chin, even coverage")
   - Skin tone (e.g., "warm beige skin tone, Fitzpatrick Type III, subtle natural glow")
   - Unique features (e.g., "small mole 1cm below left eye, faint laugh lines")
   
   **Hair** (MANDATORY - EXACT SPECIFICATIONS):
   - Exact color code (e.g., "dark brown #3 with subtle caramel highlights at #6")
   - Exact length per section (e.g., "1 inch on sides, 2.5 inches on top")
   - Specific style (e.g., "left side part starting 2 inches from center, natural wave pattern 2B")
   - Hairline (e.g., "straight hairline, dense at temples, no recession")
   - Texture (e.g., "medium texture with natural shine, moves with air current")
   
   **Clothing** (EXACT DETAILS - unless story changes):
   - Exact colors with codes (e.g., "charcoal gray #36454F")
   - Specific materials (e.g., "merino wool with visible weave texture")
   - Exact fit (e.g., "tailored fit, slight wrinkles at elbows, drapes naturally at waist")
   - All details (e.g., "crew neck, ribbed collar and cuffs, no visible branding")
   
   **Body characteristics**:
   - Posture (e.g., "naturally upright posture, shoulders back, relaxed stance")
   - Hand details (e.g., "proportional hands, trimmed nails, smooth skin")
   - Natural asymmetries (e.g., "slightly higher right shoulder, natural stance favors left leg")
   
   ⚠️ **IN SUBSEQUENT SCENES**: Always write "The EXACT SAME [person] from Scene 1" followed by repeating ALL the specific details

## 4. Product Details (MUST match reference image if provided)

   ⚠️ **ULTRA-REALISTIC & CONSISTENT - MANDATORY:**
   - Describe product in ENGINEERING detail so it looks IDENTICAL in every scene
   - These details will be used to generate all video scenes
   - ANY variation will cause product to look different between scenes
   
   **Exact specifications**: Shape, size, proportions, materials
   - Example: "Rectangular crystal bottle, 4.2\" tall x 2.1\" wide x 1.3\" deep"
   
   **Colors**: Specific shades (e.g., "rose gold", "matte black", "frosted glass")
   - NOT "gold bottle" → "rose gold with brushed metal finish"
   - NOT "clear bottle" → "crystal clear glass with 95% light transmission"
   
   **Branding**: Logo placement, text, design elements
   - Example: "Brand name 'MIDNIGHT ESSENCE' in gold serif script, 0.8\" tall, centered on front face"
   
   **Unique features**: Caps, pumps, buttons (exact details)
   - Example: "Vintage atomizer pump with ornate floral engraving, antique gold finish"
   
   ⚠️ **IN SUBSEQUENT SCENES**: Always write "The EXACT SAME [product] from Scene 1"

## 5. Scene Breakdown ({scenes_guidance})

For each scene, include:

**Scene [N]: [AIDA Stage] ([Duration] seconds)**

**Visual Description** (100-150 words):
- Environment details
- Subject positioning and camera angle
- Lighting (source, direction, quality)
- Composition and color palette

**Action Description**:
- What happens (step-by-step)
- Starting and ending poses
- **AUTHENTIC PRODUCT USAGE** (Scene 2): Show HOW product is actually used:
  * Perfume: Pick up → remove cap → spray → apply to pulse points → set down
  * Other products: Show complete usage sequence
- Motion characteristics

**Cinematography**:
- Camera movement and shot type
- Lens choice and focus
- Frame composition

## 6. Key Moments
- Emotional peaks and visual highlights
- Brand reveal timing
- Product interaction moments
- Call-to-action

## 7. Production Notes
- Aspect ratio (16:9, 9:16, 1:1)
- Color grading and music style
- Transitions between scenes

## 8. Audio & Voiceover Plan
- **Music Mood**: Genre, tempo, emotional tone
- **Voiceover Script**: One line per scene (English)
- **Sound Effects**: Key SFX for each scene

**OUTPUT REQUIREMENTS:**
- Use Markdown formatting with clear headers
- Be EXTREMELY detailed and specific
- Include exact measurements, colors, angles
- Aim for 1500-2500 words total
- Make it production-ready with no ambiguity

⚠️ **REFERENCE IMAGES**: If provided, use EXACTLY what you see - don't make up generic descriptions!

Return ONLY the Markdown-formatted story."""


async def generate_story_draft(
    user_prompt: str,
    feedback: Optional[str] = None,
    conversation_history: Optional[List[dict]] = None,
    reference_image_paths: Optional[List[str]] = None,
    brand_name: Optional[str] = None,
    target_duration: Optional[int] = None,
    model: str = "gpt-4o",
    max_retries: int = 3
) -> str:
    """
    Generate a story draft based on user prompt and optional feedback.
    
    Args:
        user_prompt: The original user prompt describing the advertisement
        feedback: Optional feedback from the critic for revisions
        conversation_history: Optional conversation history for context
        reference_image_paths: Optional paths to reference images (person, product, etc.)
        brand_name: Optional brand name to feature prominently in the advertisement
        target_duration: Optional target video duration in seconds (extracted from prompt or specified)
        model: OpenAI model to use (default: gpt-4o)
        max_retries: Maximum retry attempts on errors
        
    Returns:
        Markdown-formatted story string
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    async_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Determine duration guidance and required scenes
    if target_duration:
        duration_guidance = f"{target_duration} seconds (as specified by user)"
        # Calculate required number of scenes based on 8 seconds max per scene
        import math
        min_scenes_required = math.ceil(target_duration / 8)
        # Ensure at least 3 scenes (for 3-act structure)
        required_scenes = max(3, min_scenes_required)
        scenes_guidance = f"**CRITICAL: You MUST create EXACTLY {required_scenes} scenes** (to achieve {target_duration}s target: {required_scenes} scenes × ~{target_duration // required_scenes}s per scene)"
        logger.info(f"[Story Director] Target {target_duration}s requires {required_scenes} scenes ({target_duration / 8:.1f} at 8s max)")
    else:
        duration_guidance = "12-20 seconds"
        required_scenes = 3  # Default 3-act structure
        scenes_guidance = "3-5 scenes, suggest 3 for simplicity"
    
    # Format system prompt with duration guidance and scene count
    system_prompt = STORY_DIRECTOR_SYSTEM_PROMPT.format(
        target_duration_guidance=duration_guidance,
        scenes_guidance=scenes_guidance
    )
    
    # Build context from conversation history
    # CRITICAL FIX: Only include the LAST iteration (previous story + critique)
    # Sending full conversation history causes context length issues and content filtering
    context_messages = []
    if conversation_history:
        # Only include the LAST director-critic pair (most recent iteration)
        # This prevents context explosion while maintaining continuity
        recent_entries = conversation_history[-2:] if len(conversation_history) >= 2 else conversation_history
        
        for entry in recent_entries:
            if entry.get("role") == "director":
                # Only include a SUMMARY of previous story (not full text)
                prev_story = entry.get('content', {}).get('story_draft', '')
                # Truncate to first 500 chars to give context without overwhelming
                story_summary = prev_story[:500] + "..." if len(prev_story) > 500 else prev_story
                context_messages.append({
                    "role": "assistant",
                    "content": f"Previous story draft (Iteration {entry.get('iteration', '?')}) - SUMMARY:\n\n{story_summary}"
                })
            elif entry.get("role") == "critic":
                critique = entry.get("content", {})
                context_messages.append({
                    "role": "user",
                    "content": f"Critique from Iteration {entry.get('iteration', '?')}:\n\nCritique: {critique.get('critique', '')}\n\nImprovements needed:\n" + "\n".join(f"- {imp}" for imp in critique.get("improvements", []))
                })
    
    # Build the main user message
    user_message_parts = []
    
    # Add reference image instruction if images are provided
    if reference_image_paths:
        user_message_parts.append(
            f"🎨 **REFERENCE IMAGES PROVIDED ({len(reference_image_paths)} image(s))**\n\n"
            "⚠️ **CRITICAL INSTRUCTIONS FOR REFERENCE IMAGES:**\n\n"
            "**Image Classification:**\n"
            "- **If 3 images**: 2 are people/person, 1 is the product\n"
            "- **If 2 images**: 1 is person, 1 is the product\n"
            "- **If 1 image**: It's the product\n\n"
            "**What You MUST Do:**\n"
            "1. **Study each image carefully** - Look at EVERY detail\n"
            "2. **Identify which images show people and which show the product**\n"
            "3. **For PERSON images**: Describe their EXACT appearance:\n"
            "   - Age, gender, ethnicity, build\n"
            "   - Hair: exact color (not just 'brown', but 'chestnut brown'), length, style\n"
            "   - Face: eye color, facial features, skin tone\n"
            "   - Clothing: exact colors, styles, fabrics\n"
            "   - Expression and demeanor\n\n"
            "4. **For PRODUCT image**: Describe its EXACT specifications:\n"
            "   - Precise shape, size, proportions\n"
            "   - Exact colors (not 'blue', but 'navy blue')\n"
            "   - Materials and textures (e.g., 'frosted matte glass')\n"
            "   - Brand name/logo (location, font, color)\n"
            "   - Any unique features (cap, pump, button, label design)\n\n"
            "5. **IN YOUR STORY**: Use the EXACT person(s) and EXACT product you see in the images\n"
            "6. **FINAL SCENE**: Must show the EXACT product from the reference image with brand name visible\n\n"
            "⚠️ **DO NOT** make up generic descriptions. Use what you SEE in the images!\n\n"
        )
    
    user_message_parts.append(
        f"📝 **YOUR TASK: Create a comprehensive advertisement story for this concept:**\n\n"
        f"\"{user_prompt}\"\n\n"
    )
    
    # Add brand name if provided
    if brand_name:
        user_message_parts.append(
            f"🏷️ **BRAND NAME (CRITICAL):**\n"
            f"The brand name is: **\"{brand_name}\"**\n\n"
            f"⚠️ **YOU MUST:**\n"
            f"1. Feature this EXACT brand name in your story\n"
            f"2. In the final scene, ensure the brand name \"{brand_name}\" is clearly visible on the product\n"
            f"3. Describe how the brand name appears (font, color, placement on product)\n"
            f"4. Make the brand name prominent and legible in the final product showcase\n"
            f"5. Do NOT change, abbreviate, or modify the brand name in any way\n\n"
        )
    
    user_message_parts.append(
        f"**REQUIREMENTS:**\n"
        f"- Write a COMPLETE, DETAILED story (aim for 1500-2500 words)\n"
        f"- Include ALL required sections from your system prompt\n"
        f"- Be EXTREMELY specific with visual details\n"
        f"- If reference images provided, use EXACTLY what you see in them\n"
        f"- Ensure Scene 2 shows authentic product usage (not just holding)\n"
        f"- Ensure Scene 3 ends with elegant product + brand showcase\n"
    )
    
    if brand_name:
        user_message_parts.append(
            f"- **BRAND NAME \"{brand_name}\" must be clearly visible in the final scene**\n"
        )
    
    if feedback:
        user_message_parts.append(f"\n\nFeedback from Story Critic:\n{feedback}")
    
    if conversation_history:
        user_message_parts.append("\n\nUse the conversation history above to maintain narrative continuity and build upon previous iterations.")
    
    user_message = "\n".join(user_message_parts)
    
    last_error = None
    # Track whether to use reference images (may be disabled after failed attempts)
    use_reference_images = reference_image_paths is not None
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"[Story Director] Generating story draft, attempt {attempt}/{max_retries}")
                
                # Build messages
                messages = [
                    {"role": "system", "content": system_prompt},
                    *context_messages
                ]
                
                # Determine if we should use images for THIS attempt
                # On retries after content filter, skip images
                attempt_use_images = use_reference_images and (attempt == 1 or not last_error or "Content filtered" not in str(last_error))
                
                # Build user message with vision if images provided AND not disabled due to errors
                if attempt_use_images and reference_image_paths:
                    # Vision format: text + images
                    content_parts = [{"type": "text", "text": user_message}]
                    
                    # Add images
                    for img_path in reference_image_paths:
                        try:
                            # Read and encode image
                            with open(img_path, "rb") as img_file:
                                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            
                            # Determine image type
                            img_ext = Path(img_path).suffix.lower()
                            mime_type = "image/jpeg" if img_ext in [".jpg", ".jpeg"] else "image/png"
                            
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{img_data}"
                                }
                            })
                            logger.info(f"[Story Director] Added reference image: {img_path}")
                        except Exception as e:
                            logger.error(f"[Story Director] Failed to read image {img_path}: {e}")
                    
                    messages.append({"role": "user", "content": content_parts})
                else:
                    # Text-only format
                    if not attempt_use_images and reference_image_paths:
                        logger.warning(f"[Story Director] Skipping reference images on attempt {attempt} due to previous errors")
                    messages.append({"role": "user", "content": user_message})
                
                response = await async_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.9,  # More creative to encourage detailed output
                    max_tokens=4096,  # Maximum allowed for comprehensive stories
                )
                
                if not response.choices or not response.choices[0].message:
                    error_msg = "Empty response from OpenAI API"
                    logger.error(f"[Story Director Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Check finish reason for content filtering or length issues
                finish_reason = response.choices[0].finish_reason
                if finish_reason != "stop":
                    logger.warning(f"[Story Director] Unexpected finish_reason: {finish_reason}")
                    if finish_reason == "length":
                        logger.error("[Story Director] Response truncated due to max_tokens limit. Story may be incomplete.")
                    elif finish_reason == "content_filter":
                        logger.error("[Story Director] Response blocked by content filter!")
                        if attempt < max_retries:
                            # Try removing images on next attempt to bypass filter
                            if reference_image_paths:
                                logger.warning("[Story Director] Removing reference images to bypass content filter on next attempt")
                                reference_image_paths = None
                            last_error = "Content filtered by OpenAI"
                            continue
                
                story_draft = response.choices[0].message.content
                if not story_draft:
                    error_msg = "Response content is None"
                    logger.error(f"[Story Director Error] {error_msg}")
                    # Log response details for debugging
                    logger.error(f"[Story Director] Response finish_reason: {finish_reason}")
                    logger.error(f"[Story Director] Response refusal: {getattr(response.choices[0].message, 'refusal', 'None')}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                # Validate story is not too short
                if len(story_draft) < 500:
                    error_msg = f"Story too short ({len(story_draft)} characters). Expected at least 1500 words (~7500 chars)."
                    logger.warning(f"[Story Director Warning] {error_msg}")
                    logger.warning(f"[Story Director] Story content: {story_draft[:200]}")
                    if attempt < max_retries:
                        logger.warning(f"[Story Director] Retrying to get a complete story...")
                        last_error = error_msg
                        continue
                    else:
                        # On last attempt, log but don't fail - let it through
                        logger.error(f"[Story Director] Story is too short even after {max_retries} attempts!")
                
                logger.info(f"[Story Director] Successfully generated story draft ({len(story_draft)} characters)")
                return story_draft.strip()
                
            except Exception as e:
                logger.error(f"[Story Director Error] Attempt {attempt}/{max_retries} failed: {str(e)}")
                if attempt < max_retries:
                    last_error = str(e)
                    continue
                raise
        
        # Should not reach here, but just in case
        raise ValueError(f"Failed after {max_retries} attempts. Last error: {last_error}")
        
    finally:
        await async_client.close()

