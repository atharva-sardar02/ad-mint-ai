"""
Vision Analysis for Reference Images.

Uses GPT-4 Vision to extract forensic-level character and product details
from reference images to ensure consistency across all video scenes.
"""
import base64
import logging
from pathlib import Path
from typing import List, Dict, Optional

import openai

from app.core.config import settings

logger = logging.getLogger(__name__)


CHAR_ANALYSIS_PROMPT = """Analyze this person in FORENSIC detail for character consistency across multiple video scenes.

Your analysis will be copied VERBATIM into prompts for 3-8 video scenes. Every detail matters for ensuring the EXACT SAME person appears in all scenes.

Provide ULTRA-SPECIFIC descriptions of:

**FACIAL FEATURES** (copy these exact details to all scenes):
- Face shape: oval/square/round/heart-shaped with specific structural notes
- Eye color: exact shade (e.g., "deep brown with amber flecks radiating from pupil")
- Eye shape: almond/round/hooded, precise spacing, distinctive characteristics
- Eyebrow shape: arc height, thickness (mm), natural growth pattern, color
- Nose: bridge height, nostril width, tip shape, exact profile characteristics
- Lips: exact fullness of upper and lower, cupid's bow definition, natural color tone
- Cheekbone: height, prominence level, how they catch light
- Jawline: angle (sharp/soft), chin shape (cleft/rounded/pointed), definition
- Facial hair: exact stubble length if present, coverage pattern, precise color including any grays
- Skin tone: exact undertone (warm/cool/neutral), specific descriptive shade
- Distinguishing marks: moles, freckles, scars, birthmarks with EXACT facial location
- Age indicators: specific line patterns, under-eye characteristics, skin texture

**HAIR CHARACTERISTICS** (exact matching details):
- Exact color: base color with any highlights, lowlights, or natural variation (e.g., "dark brown #2B1B17 with subtle caramel streaks")
- Precise length: measurements or clear length description (e.g., "cropped short, 1 inch on sides, 2.5 inches on top")
- Specific style: parting location (e.g., "side part at 2 o'clock position"), wave/curl pattern, texture (straight/wavy/curly/coily)
- Hairline: shape, recession if any, temple density
- Overall volume and density characteristics

**BODY CHARACTERISTICS** (key physical traits):
- Height estimation: specific (e.g., "approximately 5'10" tall")
- Build: slim/athletic/stocky/muscular with shoulder width, overall proportions
- Posture: natural shoulder position, stance characteristics
- Hand details if visible: finger proportions, skin characteristics

**CURRENT CLOTHING** (exact outfit details):
- Garment colors: exact shades with descriptive names (e.g., "charcoal gray #36454F")
- Material: type and visible texture (e.g., "merino wool with visible fine weave")
- Fit: how it drapes on body, where natural wrinkles form
- Specific details: collar type, button style and placement, any visible logos or patterns, sleeve length

**DISTINCTIVE FEATURES** (unique identifiers):
- Any unique physical characteristics that make this person recognizable
- Expressions: natural resting face characteristics
- Any accessories: glasses, jewelry, watches with specific details

**REMEMBER**: Be SO specific that if you read this description back, you could identify this exact person. These details will be used to generate 3-8 video scenes and must result in the IDENTICAL person appearing in every single scene.

Output as a flowing descriptive paragraph (200-300 words) that can be directly inserted into video generation prompts."""


PRODUCT_ANALYSIS_PROMPT = """Analyze this product in FORENSIC detail for product consistency across multiple video scenes.

Your analysis will be copied VERBATIM into prompts for 3-8 video scenes. Every detail matters for ensuring the EXACT SAME product appears in all scenes.

Provide ULTRA-SPECIFIC descriptions of:

**PRODUCT SHAPE & DIMENSIONS**:
- Exact shape description (e.g., "cylindrical bottle, 5 inches tall, 1.5 inches diameter")
- Proportions and distinctive silhouette characteristics
- Cap/lid/closure: exact shape, size, how it attaches

**COLORS & FINISHES**:
- Exact colors: specific shades (e.g., "deep amber glass with 85% transparency")
- Material finishes: matte/glossy/metallic with reflectivity characteristics
- Any color gradients, transitions, or multi-tone elements

**BRANDING & TEXT**:
- Brand name: exact text, font characteristics, placement, size
- Logo: detailed description, exact position, colors
- Any other text: ingredients, taglines, batch numbers if visible

**MATERIALS & TEXTURES**:
- Primary material: glass/plastic/metal with specific characteristics
- Surface texture: smooth/textured/faceted with exact details
- How light interacts: reflections, refractions, transparency levels

**DISTINCTIVE FEATURES**:
- Unique design elements that make this product recognizable
- Caps, pumps, spray mechanisms: exact mechanical details
- Labels: placement, colors, text, any wear or characteristics
- Any distinctive marks, engravings, or embellishments

**REMEMBER**: Be SO specific that this exact product could be identified from thousands of similar products. These details will ensure the IDENTICAL product appears in every video scene.

Output as a flowing descriptive paragraph (150-250 words) that can be directly inserted into video generation prompts."""


async def analyze_reference_images_for_consistency(
    reference_image_paths: List[str],
    brand_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Use GPT-4 Vision to extract forensic-level details from reference images.
    
    This ensures the EXACT same characters and products appear consistently
    across all video scenes by providing a single source of truth description.
    
    Args:
        reference_image_paths: List of paths to reference images (typically 3)
        brand_name: Optional brand name for context
        
    Returns:
        Dictionary with keys:
        - "character": Forensic character description (if person detected)
        - "product": Forensic product description (if product detected)
        - "scene": General scene/environment description
    """
    logger.info(f"[Vision Analysis] Analyzing {len(reference_image_paths)} reference images for consistency")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    character_description = None
    product_description = None
    scene_description = None
    
    # Analyze each image
    for idx, img_path in enumerate(reference_image_paths, 1):
        try:
            logger.info(f"[Vision Analysis] Processing image {idx}/{len(reference_image_paths)}: {Path(img_path).name}")
            
            # Read and encode image
            with open(img_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Determine image type
            img_ext = Path(img_path).suffix.lower()
            mime_type = "image/jpeg" if img_ext in [".jpg", ".jpeg"] else "image/png"
            
            # First, detect what's in the image
            detect_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Analyze this image and identify what it contains. Respond with a JSON object:
{{"has_person": true/false, "has_product": true/false, "description": "brief description"}}

Product context: This is a reference image for a {brand_name if brand_name else 'product'} advertisement."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{img_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            detection = detect_response.choices[0].message.content
            logger.info(f"[Vision Analysis] Image {idx} detection: {detection}")
            
            # Parse detection (simple string check since we don't need perfect JSON parsing)
            has_person = "true" in detection.lower() and "person" in detection.lower()
            has_product = "true" in detection.lower() and "product" in detection.lower()
            
            # Analyze character if person detected and we don't have character description yet
            if has_person and not character_description:
                logger.info(f"[Vision Analysis] Extracting character details from image {idx}")
                char_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": CHAR_ANALYSIS_PROMPT},
                                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_data}"}}
                            ]
                        }
                    ],
                    max_tokens=800,
                    temperature=0.2  # Low temperature for consistency
                )
                character_description = char_response.choices[0].message.content.strip()
                logger.info(f"[Vision Analysis] ✅ Character description extracted ({len(character_description)} chars)")
            
            # Analyze product if detected and we don't have product description yet
            if has_product and not product_description:
                logger.info(f"[Vision Analysis] Extracting product details from image {idx}")
                prod_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": PRODUCT_ANALYSIS_PROMPT},
                                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{img_data}"}}
                            ]
                        }
                    ],
                    max_tokens=600,
                    temperature=0.2  # Low temperature for consistency
                )
                product_description = prod_response.choices[0].message.content.strip()
                logger.info(f"[Vision Analysis] ✅ Product description extracted ({len(product_description)} chars)")
            
        except Exception as e:
            logger.error(f"[Vision Analysis] Error analyzing image {idx}: {e}")
            continue
    
    # Create result dictionary
    result = {}
    
    if character_description:
        result["character"] = character_description
        logger.info(f"[Vision Analysis] Final character description: {len(character_description)} chars")
    
    if product_description:
        result["product"] = product_description
        logger.info(f"[Vision Analysis] Final product description: {len(product_description)} chars")
    
    if not result:
        logger.warning("[Vision Analysis] No character or product detected in reference images")
    else:
        logger.info(f"[Vision Analysis] ✅ Analysis complete: {list(result.keys())}")
    
    return result

