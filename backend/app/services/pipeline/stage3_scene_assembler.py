"""
Stage 3: Video Scene Assembler (Option C — Final, Anti-Hang v10.0)
"""

import re
from typing import List, Dict, Any, Optional

from app.services.pipeline.llm_client import call_chat_model
from app.services.pipeline.llm_schemas import ScentProfile, Stage1Blueprint
from app.services.pipeline.prompts import STAGE3_SCENE_ASSEMBLER_PROMPT

# NOTE: directly import your text converters
from app.services.pipeline.text_converters import (
    stage1_to_text,
    stage2_to_text
)

DEFAULT_MODEL = "gpt-5"


def _split_scenes(raw: str) -> List[str]:
    """
    More robust scene splitting:
    - Prefer "Scene X:" markers.
    - Fallback to double-newline.
    """
    lines = raw.splitlines()
    scenes: List[str] = []
    current: List[str] = []

    for line in lines:
        if re.match(r"^\s*Scene\s+\d+:", line):
            if current:
                scenes.append("\n".join(current).strip())
                current = []
            current.append(line)
        else:
            current.append(line)

    if current:
        scenes.append("\n".join(current).strip())

    scenes = [s for s in scenes if s.strip()]

    if len(scenes) == 5:
        return scenes

    # fallback
    fallback = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    return fallback


async def run_stage3_scene_assembler(
    stage1_blueprint: Stage1Blueprint,
    scent_profile: ScentProfile,
    brand_style_json: Optional[Dict[str, Any]] = None,
    product_style_json: Optional[Dict[str, Any]] = None,
    model: str = DEFAULT_MODEL,
) -> List[str]:
    """
    Stage 3 (Option C):
    - ONE system message only
    - ONE combined user message containing both Stage 1 + Stage 2
    - Shorter plaintext format to avoid GPT-5 stalls
    - Optional brand style JSON and product style JSON for brand-aware scene generation

    Args:
        stage1_blueprint: Stage 1 blueprint with 5 scenes
        scent_profile: Stage 2 scent profile with cinematic characteristics
        brand_style_json: Optional brand style JSON extracted from brand style images (Story 10.2)
        product_style_json: Optional product style JSON extracted from product images (Story 10.2)
        model: LLM model to use (default: gpt-5)

    Returns:
        List of 5 cinematic scene paragraphs (video-ready)
    """

    if len(stage1_blueprint.scenes) != 5:
        raise ValueError(
            f"Stage 1 must contain exactly 5 scenes, got {len(stage1_blueprint.scenes)}"
        )

    # =========================================================
    # Compact the inputs (EXTREMELY IMPORTANT to avoid hanging)
    # =========================================================
    stage1_text = stage1_to_text(stage1_blueprint)
    stage2_text = stage2_to_text(scent_profile)

    # Format brand style JSON if provided
    brand_style_text = ""
    if brand_style_json:
        brand_style_text = _format_brand_style_json(brand_style_json)

    # Format product style JSON if provided
    product_style_text = ""
    if product_style_json:
        product_style_text = _format_product_style_json(product_style_json)

    # ONE merged user message — fastest, most stable
    user_message_parts = [
        "STAGE 1 BLUEPRINT BELOW:",
        stage1_text,
        "",
        "STAGE 2 CINEMATIC PROFILE BELOW:",
        stage2_text,
    ]

    # Add brand style information if available
    if brand_style_text:
        user_message_parts.extend([
            "",
            "BRAND STYLE INFORMATION BELOW:",
            brand_style_text,
        ])

    # Add product style information if available
    if product_style_text:
        user_message_parts.extend([
            "",
            "PRODUCT STYLE INFORMATION BELOW:",
            product_style_text,
        ])

    user_message_parts.extend([
        "---------------------------",
        "Produce the 5 cinematic scenes now.",
    ])

    user_message = "\n".join(user_message_parts)

    # =========================================================
    # FIXED MESSAGE SHAPE (NO DUPLICATE SYSTEM PROMPTS)
    # =========================================================
    messages = [
        {"role": "system", "content": STAGE3_SCENE_ASSEMBLER_PROMPT},
        {"role": "user", "content": user_message},
    ]

    # =========================================================
    # GPT-5 call — MUST NOT stream, MUST NOT send two systems
    # =========================================================
    raw = await call_chat_model(
        messages=messages,
        model=model,
        max_output_tokens=6000,   # lowered for stability
    )

    raw = raw.strip()
    scenes = _split_scenes(raw)

    if len(scenes) != 5:
        raise ValueError(
            f"Stage 3 expected 5 scenes, got {len(scenes)}.\n\nRaw:\n{raw}"
        )

    return scenes


def _format_brand_style_json(brand_style_json: Dict[str, Any]) -> str:
    """
    Format brand style JSON as readable text for LLM consumption.

    Args:
        brand_style_json: Brand style JSON dictionary

    Returns:
        Formatted text string
    """
    lines = []

    # Brand identity
    if "brand_identity" in brand_style_json:
        identity = brand_style_json["brand_identity"]
        if isinstance(identity, dict):
            if identity.get("brand_name"):
                lines.append(f"Brand Name: {identity['brand_name']}")
            if identity.get("brand_personality"):
                lines.append(f"Brand Personality: {identity['brand_personality']}")

    # Color palette
    if "color_palette" in brand_style_json:
        color_palette = brand_style_json["color_palette"]
        lines.append("Color Palette:")
        if isinstance(color_palette, dict):
            if color_palette.get("primary"):
                lines.append(f"  Primary colors: {', '.join(color_palette['primary'])}")
            if color_palette.get("secondary"):
                lines.append(f"  Secondary colors: {', '.join(color_palette['secondary'])}")
            if color_palette.get("accent"):
                lines.append(f"  Accent colors: {', '.join(color_palette['accent'])}")
            if color_palette.get("forbidden_colors"):
                lines.append(f"  Forbidden colors: {', '.join(color_palette['forbidden_colors'])}")

    # Lighting style
    if "lighting_style" in brand_style_json:
        lighting = brand_style_json["lighting_style"]
        lines.append("Lighting Style:")
        if isinstance(lighting, dict):
            if lighting.get("primary_lighting"):
                lines.append(f"  Primary lighting: {lighting['primary_lighting']}")
            if lighting.get("secondary_lighting"):
                lines.append(f"  Secondary lighting: {lighting['secondary_lighting']}")
            if lighting.get("avoid_lighting"):
                lines.append(f"  Avoid lighting: {', '.join(lighting['avoid_lighting'])}")

    # Composition rules
    if "composition_rules" in brand_style_json:
        composition = brand_style_json["composition_rules"]
        lines.append("Composition Rules:")
        if isinstance(composition, dict):
            if composition.get("framing"):
                lines.append(f"  Framing: {composition['framing']}")
            if composition.get("negative_space"):
                lines.append(f"  Negative space: {composition['negative_space']}")
            if composition.get("camera_language"):
                lines.append(f"  Camera language: {', '.join(composition['camera_language'])}")
            if composition.get("forbidden_angles"):
                lines.append(f"  Forbidden angles: {', '.join(composition['forbidden_angles'])}")

    # Atmosphere
    if "atmosphere" in brand_style_json:
        atmosphere = brand_style_json["atmosphere"]
        lines.append("Atmosphere:")
        if isinstance(atmosphere, dict):
            if atmosphere.get("mood"):
                lines.append(f"  Mood: {atmosphere['mood']}")
            if atmosphere.get("texture"):
                lines.append(f"  Texture: {atmosphere['texture']}")
            if atmosphere.get("depth_of_field"):
                lines.append(f"  Depth of field: {atmosphere['depth_of_field']}")

    # Brand markers
    if brand_style_json.get("brand_markers"):
        markers = brand_style_json["brand_markers"]
        if isinstance(markers, list) and markers:
            lines.append(f"Brand markers: {', '.join(markers)}")

    return "\n".join(lines) if lines else ""


def _format_product_style_json(product_style_json: Dict[str, Any]) -> str:
    """
    Format product style JSON as readable text for LLM consumption.

    Args:
        product_style_json: Product style JSON dictionary

    Returns:
        Formatted text string
    """
    lines = []

    # Product identity
    if "product_identity" in product_style_json:
        identity = product_style_json["product_identity"]
        lines.append("Product Identity:")
        if isinstance(identity, dict):
            if identity.get("name"):
                lines.append(f"  Name: {identity['name']}")
            if identity.get("category"):
                lines.append(f"  Category: {identity['category']}")
            if identity.get("brand"):
                lines.append(f"  Brand: {identity['brand']}")

    # Product geometry
    if "product_geometry" in product_style_json:
        geometry = product_style_json["product_geometry"]
        lines.append("Product Geometry:")
        if isinstance(geometry, dict):
            if geometry.get("silhouette"):
                lines.append(f"  Silhouette: {geometry['silhouette']}")
            if geometry.get("cap_shape"):
                lines.append(f"  Cap shape: {geometry['cap_shape']}")
            if geometry.get("label_shape"):
                lines.append(f"  Label shape: {geometry['label_shape']}")
            if geometry.get("proportions"):
                lines.append(f"  Proportions: {geometry['proportions']}")
            if geometry.get("beveling_details"):
                lines.append(f"  Beveling details: {geometry['beveling_details']}")
            if geometry.get("angles_to_preserve"):
                lines.append(f"  Angles to preserve: {', '.join(geometry['angles_to_preserve'])}")

    # Materials
    if "materials" in product_style_json:
        materials = product_style_json["materials"]
        lines.append("Materials:")
        if isinstance(materials, dict):
            if materials.get("body_material"):
                lines.append(f"  Body material: {materials['body_material']}")
            if materials.get("cap_material"):
                lines.append(f"  Cap material: {materials['cap_material']}")
            if materials.get("reflectivity"):
                lines.append(f"  Reflectivity: {materials['reflectivity']}")
            if materials.get("liquid_color"):
                lines.append(f"  Liquid color: {materials['liquid_color']}")

    # Visual style
    if "visual_style" in product_style_json:
        visual_style = product_style_json["visual_style"]
        lines.append("Visual Style:")
        if isinstance(visual_style, dict):
            if visual_style.get("default_composition"):
                lines.append(f"  Default composition: {visual_style['default_composition']}")
            if visual_style.get("recommended_backgrounds"):
                lines.append(f"  Recommended backgrounds: {', '.join(visual_style['recommended_backgrounds'])}")
            if visual_style.get("forbidden_backgrounds"):
                lines.append(f"  Forbidden backgrounds: {', '.join(visual_style['forbidden_backgrounds'])}")
            if visual_style.get("perspective"):
                lines.append(f"  Perspective: {visual_style['perspective']}")
            if visual_style.get("product_scale"):
                lines.append(f"  Product scale: {visual_style['product_scale']}")

    # Color profile
    if "color_profile" in product_style_json:
        color_profile = product_style_json["color_profile"]
        lines.append("Color Profile:")
        if isinstance(color_profile, dict):
            if color_profile.get("dominant_colors"):
                lines.append(f"  Dominant colors: {', '.join(color_profile['dominant_colors'])}")
            if color_profile.get("contrast_level"):
                lines.append(f"  Contrast level: {color_profile['contrast_level']}")
            if color_profile.get("avoid_colors"):
                lines.append(f"  Avoid colors: {', '.join(color_profile['avoid_colors'])}")

    return "\n".join(lines) if lines else ""