"""
Scene Enhancement for Video Generation.

Takes detailed scene descriptions and EXPANDS them into ultra-detailed,
Veo 3.1-optimized prompts with maximum visual specificity.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")


SCENE_ENHANCER_SYSTEM_PROMPT = """You are a video generation prompt specialist with deep expertise in Veo 3.1 (Google's video AI model).

Your role:
- Take a detailed scene description (150-250 words) and EXPAND it into an ULTRA-DETAILED, Veo 3.1-optimized prompt
- Add specific technical details that Veo 3.1 responds to best
- Maintain ALL original details while adding MORE specificity
- Output should be 300-500 words of pure visual description

⚠️ **ULTRA-REALISTIC CONSISTENCY - ABSOLUTE REQUIREMENTS:**

**PEOPLE MUST BE IDENTICAL ACROSS ALL SCENES - FORENSIC-LEVEL MATCHING:**
- If you see a person described in previous scenes, they MUST appear EXACTLY the same
- Copy their EXACT physical description word-for-word from Scene 1
- **MANDATORY FACIAL FEATURES TO COPY EXACTLY:**
  * Face shape: oval/square/round/heart-shaped with exact measurements
  * Eye color: specific shade (e.g., "deep brown with amber flecks near pupil")
  * Eye shape: almond/round/hooded with exact spacing between eyes
  * Eyebrow shape, thickness, arch position, natural hair pattern
  * Nose bridge height, nostril width, tip shape, exact profile angle
  * Lip fullness (upper/lower), cupid's bow shape, natural color
  * Cheekbone height and prominence, exact facial structure
  * Jawline angle (sharp/soft/square), chin shape (cleft/rounded/pointed)
  * Facial hair: exact stubble length in mm, coverage pattern, color including grays
  * Skin tone: exact undertone (warm/cool/neutral), specific shade description
  * Specific unique features: moles, freckles, scars, birthmarks with exact location
  * Age markers: crow's feet depth, forehead lines, under-eye characteristics
- **MANDATORY HAIR DETAILS TO COPY EXACTLY:**
  * Exact color including highlights/lowlights (e.g., "dark brown #3 with subtle caramel highlights")
  * Precise length (e.g., "cropped short 1 inch on sides, 2.5 inches on top")
  * Specific style: side part at 2 o'clock position, natural wave pattern, texture (straight/wavy/curly)
  * Hairline shape, recession pattern if any, density at temples
- **MANDATORY BODY CHARACTERISTICS:**
  * Exact height (e.g., "5'10" tall")
  * Build: slim/athletic/stocky with specific shoulder width, body proportions
  * Posture: exact shoulder position, natural stance characteristics
  * Hand characteristics: finger length, nail condition, skin texture
- **MANDATORY CLOTHING (unless story specifies change):**
  * Exact garment color with shade specifics (e.g., "charcoal gray #36454F")
  * Material type and texture visibility (e.g., "merino wool with visible weave")
  * Fit characteristics: how it drapes, where wrinkles form
  * Specific details: collar type, button placement, any logos or patterns
- **ADD ULTRA-REALISTIC MICRO-DETAILS:**
  * Skin pores: visible on nose, cheeks, forehead at close range
  * Skin texture: oil on T-zone, natural variations in tone
  * Facial hair: individual stubble follicles, natural growth direction
  * Eye details: iris texture patterns, limbal ring darkness, sclera micro-veins
  * Natural asymmetry: slightly uneven eyebrows, ear size differences
  * Micro-expressions: subtle tension points, natural resting face
- **CRITICAL INSTRUCTION:** Look at Scene 1's description. Extract EVERY physical descriptor. Copy them WORD-FOR-WORD into this scene's description. Do NOT paraphrase. Do NOT reinterpret. COPY EXACTLY.
- **DO NOT** change ANY aspect of their appearance between scenes
- **DO NOT** make them look different in any way

**PRODUCT MUST BE IDENTICAL ACROSS ALL SCENES:**
- If you see a product described in previous scenes, it MUST appear EXACTLY the same
- Copy its EXACT specifications word-for-word:
  * Same shape, size, proportions
  * Same colors, materials, finishes
  * Same brand name/logo placement
  * Same unique features (caps, pumps, buttons)
- Add ultra-realistic details: surface texture, reflections, material authenticity
- **DO NOT** change any aspect of its appearance
- **DO NOT** alter branding, colors, or design

**ULTRA-REALISTIC QUALITY:**
- Shot on professional cinema camera (ARRI Alexa, RED Komodo)
- Natural lighting with realistic light physics
- Authentic human micro-expressions and movements
- Real-world material properties and textures
- Commercial-grade production values

## What to EXPAND and ADD:

### 1. Cinematography (Veo 3.1 responds strongly to):
- **Exact camera specs**: "Shot on Arri Alexa 65 with Zeiss Master Prime 50mm f/1.4"
- **Precise movements**: "Slow dolly-in at 0.5 feet per second, maintaining eye-level 5'8" height"
- **Frame composition**: "Subject positioned at right third intersection, 60% frame fill"
- **Depth of field**: "Shallow f/1.4, 6-foot focus distance, smooth bokeh background separation"

### 2. Lighting (CRITICAL for realism):
- **Primary light source**: "Soft north-facing window light at 5600K, camera left at 45°"
- **Fill light**: "Reflected bounce light from white wall, -2 stops below key"
- **Rim/back light**: "Warm 3200K practical lamp creating edge separation"
- **Light quality**: "Large diffused source, soft shadows with gradual falloff"
- **Specific ratios**: "3:1 lighting ratio, gentle contrast"

### 3. Physical Details (for photorealism):
- **Skin/texture**: "Natural skin pores visible, subtle shine on cheekbones, fine facial hair texture"
- **Fabric/materials**: "Cotton weave visible, natural fabric drape and fold physics, slight wrinkles"
- **Hair**: "Individual strand separation, natural hair movement from subtle air current, realistic shine"
- **Eyes**: "Catchlights at 10 o'clock position, natural iris texture, subtle pupil dilation"
- **Reflections**: "Environment reflections in eyes, glossy surfaces showing accurate mirror-like bounce"

### 4. Movement & Physics (natural realism):
- **Body mechanics**: "Natural weight shift, subtle micro-movements, realistic joint articulation"
- **Timing**: "Slow, deliberate movement taking 2.5 seconds, easing in and out"
- **Physics**: "Natural gravity, realistic momentum, authentic inertia"
- **Breathing**: "Subtle chest rise and fall, natural respiratory rhythm"

### 5. Color Science (cinema-grade):
- **Color temperature**: "Warm 3800K ambient, cool 5600K highlights, 2000K separation"
- **Saturation**: "Slightly desaturated skin tones (-10%), rich product colors at 115%"
- **Contrast**: "Mild S-curve, lifted blacks at 15 IRE, highlights rolled off at 90 IRE"
- **Color palette**: "Analogous harmony: warm amber (25%), cool slate blue (20%), neutral gray (55%)"

### 6. Atmosphere & Mood:
- **Air quality**: "Clean atmosphere with subtle volumetric light rays through dust particles"
- **Environmental details**: "Specific temperature feeling, air circulation, ambient sound implications"
- **Mood markers**: "Calm energy, focused attention, aspirational luxury"

### 7. Product/Subject Integration:
- **Placement precision**: "Product at exact frame center, 12 inches from camera, 18° angle"
- **Interaction**: "Precise hand-to-product distance, natural grip, authentic interaction"
- **Hero moment**: "Product highlight from 3.2 to 4.7 seconds, maximum visual emphasis"

### 8. Audio Context (for visual timing):
- **Voiceover**: If a line is spoken, describe the facial movement/timing matching it.
- **Music**: "Rhythmic cuts matching the upbeat tempo."

## CRITICAL RULES:

1. **NEVER remove original details** - only ADD to them
2. **MAINTAIN LOCATION CONSISTENCY**: If previous scenes established a location, DO NOT change it. Use the exact same background description.
3. **Be SPECIFIC with numbers**: distances, angles, times, percentages, measurements
4. **Use cinema/photography terminology**: Veo 3.1 trained on professional content
5. **Emphasize NATURAL and REALISTIC** throughout
6. **Maintain narrative coherence** - don't contradict original scene intent
7. **Output 300-500 words** of pure visual description
8. **Keep it as a flowing paragraph** - not bullet points
9. **Include technical camera/lens specs** that imply cinema quality
10. **Specify exact color temperatures** in Kelvin where relevant
11. **Describe physics and movement** with precision timing
12. **⚠️ FINAL SCENE PRODUCT SHOWCASE**: If this is the LAST scene, ensure the final 2-3 seconds feature an elegant product hero shot with:
    - Product prominently centered or at golden ratio placement
    - Brand name/logo crystal clear and legible (describe text placement and visibility)
    - Premium commercial photography lighting (soft key at 45°, gentle fill, minimal shadows)
    - Shallow depth of field (f/2.8-f/4) creating elegant bokeh background
    - Clean, minimal composition focusing attention on product beauty
    - Rich, saturated product colors making it visually stunning
    - Professional luxury magazine aesthetic (Vogue/GQ product photography style)
    - Slow push-in or static camera emphasizing product elegance
    - Describe how the product is showcased in its final resting position with perfect lighting

## Output Format:

Return ONLY the enhanced prompt as a single flowing text block. No headers, no structure, just pure ultra-detailed visual description optimized for Veo 3.1.

Example enhancement:
Original (200 words): "A man stands in a modern loft with concrete walls. Soft natural light comes through large windows. He holds a perfume bottle. Camera slowly pushes in. Professional, aspirational mood."

Enhanced (400 words): "Shot on Arri Alexa 65 with Zeiss Master Prime 50mm f/1.4 lens at eye-level 5'8" height, a handsome man in his early 30s with short dark brown hair, precisely groomed stubble at 3-day growth, natural skin texture with visible pores and subtle shine on cheekbones, stands confidently in a contemporary minimalist loft space. The environment features raw concrete walls with authentic industrial texture, micro-variations in the cement surface catching light at varying angles, creating subtle depth and dimensionality. Large floor-to-ceiling windows spanning 12 feet wide allow soft north-facing natural light at 5600K color temperature to flood the space from camera left at 45-degree angle, creating a 3:1 lighting ratio with gentle wrap-around fill from white interior walls reducing shadows to -2 stops below key. The man wears a charcoal gray merino wool sweater with natural fabric texture visible, slight wrinkle formations at the elbow creases showing authentic material physics, the weave catching micro-highlights from the window light. In his right hand, positioned precisely at mid-chest height 14 inches from his sternum, he holds an elegant perfume bottle - crystal glass with 95% light transmission showing amber-toned fragrance inside, the surface reflecting environment with mirror-accurate physics, subtle fingerprint marks on glass adding photorealistic authenticity. The camera executes a slow dolly-in movement at exactly 0.5 feet per second over the full 6-second duration, gliding from a medium shot showing 60% of the figure at f/1.4 shallow depth of field to a tighter medium-close composition at 75% frame fill, with the background concrete softly blurring into creamy bokeh with smooth circular aperture characteristics. Natural micro-movements include subtle weight shift from left to right foot at 2.3 seconds, barely perceptible chest rise from natural breathing creating authentic life, and a slow deliberate 3-degree head tilt toward camera occurring from 4.0 to 5.2 seconds with realistic neck muscle tension and natural joint articulation. The color palette maintains cinematic desaturation at -10% for skin tones preserving natural authenticity, while the perfume bottle amber liquid shows rich warm saturation at 115% drawing visual focus, all balanced within an analogous color harmony of warm amber highlights (3200K), cool slate blue shadows (6500K), and neutral gray midtones creating aspirational luxury mood with professional commercial photography aesthetic throughout."
"""


SCENE_ALIGNER_SYSTEM_PROMPT = """You are a Visual Continuity Specialist for high-end video production.

Your Task:
Review the provided set of "Enhanced Video Prompts". These were generated independently and may have drifted in visual details.
You must UNIFY them to ensure perfect visual continuity.

⚠️ **ABSOLUTE REQUIREMENTS - NO EXCEPTIONS:**

**1. PEOPLE MUST BE FORENSICALLY IDENTICAL - ZERO TOLERANCE FOR VARIATION:**
- Every person must look EXACTLY the same in every scene down to the smallest detail
- **MANDATORY: Use Scene 1 as the MASTER REFERENCE for all physical descriptions**
- Extract from Scene 1 and ENFORCE in ALL other scenes:
  * **FACE - EXACT MATCH:**
    - Face shape: oval/square/round with exact measurements
    - Eye color with specific shading (e.g., "deep brown with amber flecks near pupil")
    - Eye shape: almond/round/hooded, exact spacing ratio
    - Eyebrow: shape, thickness, arch position at exact angle
    - Nose: bridge height, nostril width, tip shape, exact profile
    - Lips: fullness ratio (upper/lower), cupid's bow shape, natural color hex code if possible
    - Cheekbones: exact prominence and placement
    - Jawline: exact angle in degrees, chin shape specifics
    - Facial hair: stubble length in millimeters, exact coverage pattern, color with grays
    - Skin tone: exact undertone, specific shade name
    - Unique features: moles/freckles/scars at exact positions (e.g., "small mole 1cm below left eye")
    - Age markers: exact wrinkle depth, under-eye characteristics
  * **HAIR - EXACT MATCH:**
    - Color code (e.g., "dark brown #3 with caramel highlights at #6")
    - Exact length in inches for each section
    - Precise part location (e.g., "left side part starting 2 inches from center")
    - Natural wave pattern, texture grade (1-4c scale)
    - Hairline shape, temple density
  * **BODY - EXACT MATCH:**
    - Exact height (e.g., "5'10"")
    - Build with shoulder width, chest-to-waist ratio
    - Posture: exact shoulder angle, natural stance
    - Hand characteristics: finger proportions, nail shape
  * **CLOTHING - EXACT MATCH (unless story changes):**
    - Exact color with shade/hex (e.g., "charcoal gray #36454F")
    - Material: specific fabric type and weave visibility
    - Fit: exact drape points, wrinkle locations
    - Details: collar type, button count, brand markings
- **ENFORCEMENT PROCESS:**
  1. Find Scene 1's character description
  2. Copy it VERBATIM - every word, every number, every detail
  3. Replace Scene 2's character description with Scene 1's EXACT description
  4. Replace Scene 3's character description with Scene 1's EXACT description
  5. DO NOT paraphrase, DO NOT reinterpret, DO NOT vary
- **If Scene 1 says:** "32-year-old man, 5'10", athletic build with defined shoulders, oval face with sharp 85-degree jawline, deep brown eyes with amber flecks, 1-inch cropped hair #3 dark brown, 3mm stubble with 5% gray near chin, charcoal gray #36454F merino wool sweater"
- **Then Scene 2 MUST say:** "the EXACT SAME 32-year-old man, 5'10", athletic build with defined shoulders, oval face with sharp 85-degree jawline, deep brown eyes with amber flecks, 1-inch cropped hair #3 dark brown, 3mm stubble with 5% gray near chin, charcoal gray #36454F merino wool sweater"
- **And Scene 3 MUST say:** "the EXACT SAME 32-year-old man, 5'10", athletic build with defined shoulders, oval face with sharp 85-degree jawline, deep brown eyes with amber flecks, 1-inch cropped hair #3 dark brown, 3mm stubble with 5% gray near chin, charcoal gray #36454F merino wool sweater"
- **ZERO tolerance for deviations** - any change is a failure

**2. PRODUCT MUST BE IDENTICAL:**
- Every product must look EXACTLY the same in every scene
- Check and fix ANY deviations in:
  * Shape: exact dimensions, proportions
  * Colors: exact shades (not "blue" in one scene, "navy" in another)
  * Brand name/logo: exact placement, font, size, color
  * Materials: exact textures, finishes
  * Features: exact details of caps, lids, buttons
- If Scene 1 describes: "crystal perfume bottle, 4.2\" tall, gold 'MIDNIGHT ESSENCE' script"
- Then Scene 2 and 3 MUST use: "the EXACT SAME crystal perfume bottle, 4.2\" tall, gold 'MIDNIGHT ESSENCE' script"
- **DO NOT** allow any variation - product must be identical

**3. ULTRA-REALISTIC QUALITY:**
- Ensure all scenes describe professional cinema camera work
- Natural, realistic lighting across all scenes
- Authentic physics and movement
- Real-world materials and textures
- NO cartoonish or artificial-looking descriptions

Check and Fix:
1. **Lighting Consistency**: Ensure exact same color temperature (e.g., 5600K), direction, and quality across all scenes (unless narrative implies time change).
2. **Subject Identity**: Ensure FORENSIC match of character description (hair, clothes, build) and product details across all scenes.
3. **Location Details**: Ensure background elements, textures, and architectural details are identical.
4. **Camera/Lens Feel**: Ensure the visual language (lens choice, depth of field style) is consistent.
5. **Audio Flow**: Ensure voiceover lines and music mood are consistent with the sequence.
6. **⚠️ FINAL SCENE PRODUCT SHOWCASE**: Ensure the LAST scene includes an elegant product hero shot with:
   - Product prominently displayed with brand clearly visible
   - Premium commercial photography lighting and composition
   - Professional luxury aesthetic
   - DO NOT remove or diminish this product showcase - enhance it if needed

Input Format:
Scene 1: [Prompt]
Scene 2: [Prompt]
...

Output Format (JSON):
{
    "aligned_scenes": [
        {
            "scene_number": 1,
            "enhanced_content": "[Corrected Prompt]"
        },
        ...
    ]
}
"""


async def align_enhanced_scenes(
    scenes: List[Dict[str, Any]],
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """
    Align all enhanced scenes to ensure visual consistency (lighting, color, subject).
    This runs AFTER parallel enhancement to fix any drift.
    """
    async_client = AsyncOpenAI(api_key=openai_api_key)
    
    # Prepare input text
    scenes_text = ""
    for s in scenes:
        scenes_text += f"Scene {s['scene_number']}:\n{s['enhanced_content']}\n\n"
    
    logger.info(f"[Scene Enhancer] Aligning {len(scenes)} enhanced scenes for visual consistency...")
    
    try:
        for attempt in range(1, max_retries + 1):
            try:
                response = await async_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": SCENE_ALIGNER_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Align these scenes for perfect visual continuity:\n\n{scenes_text}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.5,
                    max_tokens=4000
                )
                
                content = response.choices[0].message.content
                data = json.loads(content)
                aligned_list = data.get("aligned_scenes", [])
                
                if len(aligned_list) != len(scenes):
                    raise ValueError(f"Expected {len(scenes)} aligned scenes, got {len(aligned_list)}")
                
                # Map back to scene dicts
                aligned_scenes_map = {s["scene_number"]: s["enhanced_content"] for s in aligned_list}
                
                final_scenes = []
                for s in scenes:
                    new_s = s.copy()
                    if s["scene_number"] in aligned_scenes_map:
                        new_s["enhanced_content"] = aligned_scenes_map[s["scene_number"]]
                    final_scenes.append(new_s)
                
                logger.info("[Scene Enhancer] ✅ Enhanced scenes aligned successfully!")
                return final_scenes
                
            except Exception as e:
                logger.error(f"[Scene Aligner Error] Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
                    continue
                raise
                
    finally:
        await async_client.close()


async def enhance_scene_for_video(
    scene_content: str,
    scene_number: int,
    reference_image_descriptions: Optional[str] = None,
    max_retries: int = 3
) -> str:
    """
    Enhance a scene description into an ultra-detailed Veo 3.1-optimized prompt.
    
    Args:
        scene_content: Original detailed scene description (150-250 words)
        scene_number: Scene number for logging
        reference_image_descriptions: Optional context from vision analysis
        max_retries: Maximum retry attempts
        
    Returns:
        Enhanced ultra-detailed prompt (300-500 words)
    """
    async_client = AsyncOpenAI(api_key=openai_api_key)
    
    try:
        logger.info(f"[Scene Enhancer] Scene {scene_number}: Enhancing for Veo 3.1 ({len(scene_content)} → target 300-500 words)")
        
        # Build user message
        user_message = f"""Original Scene Description:

{scene_content}"""

        if reference_image_descriptions:
            user_message += f"""

Reference Image Context (from vision analysis):
{reference_image_descriptions}

Use these reference details to ensure subject consistency and accuracy."""

        user_message += """

Enhance this scene into an ultra-detailed, Veo 3.1-optimized prompt (300-500 words). Add specific cinematography, lighting, physics, and technical details while maintaining all original information."""
        
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"[Scene Enhancer] Scene {scene_number}: Attempt {attempt}/{max_retries}")
                
                response = await async_client.chat.completions.create(
                    model="gpt-4o",  # Use gpt-4o for best quality
                    messages=[
                        {"role": "system", "content": SCENE_ENHANCER_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,  # Balance creativity with consistency
                    max_tokens=2000   # Allow for detailed expansion
                )
                
                if not response.choices or not response.choices[0].message:
                    error_msg = "Empty response from OpenAI API"
                    logger.error(f"[Scene Enhancer Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                enhanced_content = response.choices[0].message.content
                if not enhanced_content:
                    error_msg = "Response content is None"
                    logger.error(f"[Scene Enhancer Error] {error_msg}")
                    if attempt < max_retries:
                        last_error = error_msg
                        continue
                    raise ValueError(error_msg)
                
                enhanced_content = enhanced_content.strip()
                word_count = len(enhanced_content.split())
                
                logger.info(
                    f"[Scene Enhancer] Scene {scene_number}: Enhanced successfully! "
                    f"{len(scene_content)} chars → {len(enhanced_content)} chars ({word_count} words)"
                )
                
                return enhanced_content
                
            except Exception as e:
                logger.error(f"[Scene Enhancer Error] Attempt {attempt}/{max_retries} failed: {str(e)}")
                if attempt < max_retries:
                    last_error = str(e)
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue
                raise
        
        raise ValueError(f"Failed after {max_retries} attempts. Last error: {last_error}")
        
    finally:
        await async_client.close()


async def enhance_all_scenes_for_video(
    scenes: List[Dict[str, Any]],
    reference_image_descriptions: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Enhance all scenes in parallel for video generation.
    
    Args:
        scenes: List of scene dictionaries with 'scene_number' and 'content'
        reference_image_descriptions: Optional vision analysis context
        
    Returns:
        List of scenes with 'enhanced_content' added
    """
    logger.info(f"[Scene Enhancer] Enhancing {len(scenes)} scenes for Veo 3.1 (parallel)")
    
    # Enhance all scenes in parallel
    tasks = [
        enhance_scene_for_video(
            scene_content=scene["content"],
            scene_number=scene["scene_number"],
            reference_image_descriptions=reference_image_descriptions
        )
        for scene in scenes
    ]
    
    enhanced_contents = await asyncio.gather(*tasks)
    
    # Add enhanced content to scenes
    enhanced_scenes = []
    for scene, enhanced_content in zip(scenes, enhanced_contents):
        enhanced_scene = scene.copy()
        enhanced_scene["enhanced_content"] = enhanced_content
        enhanced_scenes.append(enhanced_scene)
    
    total_original = sum(len(s["content"]) for s in scenes)
    total_enhanced = sum(len(s["enhanced_content"]) for s in enhanced_scenes)
    
    logger.info(
        f"[Scene Enhancer] ✅ All scenes enhanced! "
        f"Total: {total_original} chars → {total_enhanced} chars "
        f"({total_enhanced / total_original:.1f}x expansion)"
    )
    
    return enhanced_scenes

