"""
Prompt Generator from Filled Templates

Takes a filled template (all fields filled) and generates image/video prompts
by concatenating the filled fields into coherent sentences.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_character_description(character: Dict[str, Any]) -> str:
    """
    Generate complete character description from filled fields.
    
    Args:
        character: Filled character dict
    
    Returns:
        str: Complete character description (police description level)
    """
    if character.get("present") != "true":
        return ""
    
    demographics = character.get("demographics", {})
    body = character.get("body", {})
    hair = character.get("hair", {})
    face = character.get("face", {})
    eyes = character.get("eyes", {})
    skin = character.get("skin", {})
    features = character.get("distinguishing_features", {})
    clothing = character.get("clothing", {})
    expression = character.get("expression_and_demeanor", {})
    
    parts = []
    
    # Demographics
    parts.append(f"{demographics.get('gender', 'Person').capitalize()}, {demographics.get('age_exact', '')} years old")
    
    # Body
    parts.append(f"{body.get('height_feet', '')} feet {body.get('height_inches', '')} inches tall")
    parts.append(f"{body.get('build_type', '')} build")
    if body.get('weight_approximate'):
        parts.append(f"approximately {body.get('weight_approximate')}")
    
    # Hair
    hair_desc = f"{hair.get('length', '')} {hair.get('color', '')} hair"
    if hair.get('style'):
        hair_desc += f" with {hair.get('style')}"
    if hair.get('part'):
        hair_desc += f", {hair.get('part')}"
    if hair.get('texture'):
        hair_desc += f", {hair.get('texture')} texture"
    parts.append(hair_desc)
    
    # Face
    face_desc = f"{face.get('shape', '')} face"
    if face.get('cheekbones'):
        face_desc += f" with {face.get('cheekbones')} cheekbones"
    if face.get('jawline'):
        face_desc += f", {face.get('jawline')} jawline"
    parts.append(face_desc)
    
    # Eyes
    eye_desc = f"{eyes.get('shape', '')} {eyes.get('color', '')} eyes"
    if eyes.get('size'):
        eye_desc += f", {eyes.get('size')} size"
    parts.append(eye_desc)
    
    # Skin
    skin_desc = f"{skin.get('tone', '')} skin"
    if skin.get('fitzpatrick_type'):
        skin_desc += f" (Fitzpatrick {skin.get('fitzpatrick_type')})"
    if skin.get('texture'):
        skin_desc += f", {skin.get('texture')}"
    parts.append(skin_desc)
    
    # Distinguishing features
    if features.get('marks_or_scars') and features.get('marks_or_scars') != "none":
        parts.append(features.get('marks_or_scars'))
    if features.get('tattoos') and features.get('tattoos') != "none":
        parts.append(f"Tattoos: {features.get('tattoos')}")
    if features.get('piercings') and features.get('piercings') != "none":
        parts.append(f"Piercings: {features.get('piercings')}")
    
    # Clothing
    if clothing.get('top'):
        parts.append(f"Wearing {clothing.get('top')}")
    if clothing.get('accessories') and clothing.get('accessories') != "none":
        parts.append(clothing.get('accessories'))
    
    # Expression
    if expression.get('default_expression'):
        parts.append(expression.get('default_expression'))
    
    return ". ".join(parts) + "."


def generate_product_description(product: Dict[str, Any]) -> str:
    """
    Generate complete product description from filled fields.
    
    Args:
        product: Filled product dict
    
    Returns:
        str: Complete product description
    """
    if product.get("present") != "true":
        return ""
    
    dims = product.get("dimensions", {})
    material = product.get("material", {})
    colors = product.get("colors", {})
    branding = product.get("branding", {})
    features = product.get("unique_features", {})
    contents = product.get("contents", {})
    
    parts = []
    
    # Type and brand
    prod_desc = product.get("type", "product")
    if product.get("brand_name") and product.get("brand_name") != "none":
        prod_desc = f"{product.get('brand_name')} {prod_desc}"
    parts.append(prod_desc)
    
    # Dimensions
    if dims.get('height_inches'):
        parts.append(f"{dims.get('height_inches')} inches tall")
    if dims.get('width_inches'):
        parts.append(f"{dims.get('width_inches')} inches wide")
    
    # Material and colors
    material_desc = f"{colors.get('primary_color', '')} {material.get('primary', '')}"
    if material.get('texture'):
        material_desc += f", {material.get('texture')}"
    parts.append(material_desc)
    
    if colors.get('secondary_color') and colors.get('secondary_color') != "none":
        parts.append(f"with {colors.get('secondary_color')} accents")
    
    # Unique features
    if features.get('shape_details'):
        parts.append(features.get('shape_details'))
    if features.get('cap_or_lid') and features.get('cap_or_lid') != "none":
        parts.append(features.get('cap_or_lid'))
    if features.get('special_elements') and features.get('special_elements') != "none":
        parts.append(features.get('special_elements'))
    
    # Branding
    if branding.get('logo_present') == "true" and branding.get('logo_description'):
        parts.append(f"Logo: {branding.get('logo_description')}")
    if branding.get('label_present') == "true" and branding.get('label_description'):
        parts.append(f"Label: {branding.get('label_description')}")
    
    # Contents
    if contents.get('visible') == "true" and contents.get('description'):
        parts.append(f"Contains: {contents.get('description')}")
    
    return ". ".join(parts) + "."


def generate_scene_prompt(
    scene: Dict[str, Any],
    character_desc: str,
    product_desc: str,
    is_first_scene: bool = False
) -> str:
    """
    Generate complete image generation prompt for a scene.
    
    Args:
        scene: Filled scene dict
        character_desc: Pre-generated character description (identical for all scenes)
        product_desc: Pre-generated product description (identical for all scenes)
        is_first_scene: Whether this is scene 1 (includes full descriptions)
    
    Returns:
        str: Complete detailed image generation prompt (80-150 words)
    """
    parts = []
    
    # Character (if present)
    if scene.get("character_details", {}).get("present_in_scene") == "true":
        if is_first_scene:
            parts.append(character_desc)
        else:
            # Reference Scene 1
            char_name = character_desc.split(",")[0]  # e.g., "Woman"
            parts.append(f"The EXACT SAME {char_name.lower()} from Scene 1 ({character_desc})")
        
        # Character details in this scene
        char_details = scene.get("character_details", {})
        if char_details.get("action"):
            parts.append(char_details.get("action"))
        if char_details.get("position"):
            parts.append(char_details.get("position"))
        if char_details.get("posture"):
            parts.append(char_details.get("posture"))
        if char_details.get("facial_expression"):
            parts.append(char_details.get("facial_expression"))
    
    # Product (if present)
    if scene.get("product_details", {}).get("present_in_scene") == "true":
        if is_first_scene:
            parts.append(product_desc)
        else:
            # Reference Scene 1
            prod_type = product_desc.split()[0] if product_desc else "product"
            parts.append(f"The EXACT SAME {prod_type.lower()} from Scene 1 ({product_desc})")
        
        # Product details in this scene
        prod_details = scene.get("product_details", {})
        if prod_details.get("position"):
            parts.append(f"Product positioned: {prod_details.get('position')}")
        if prod_details.get("orientation"):
            parts.append(prod_details.get("orientation"))
    
    # Environment
    env = scene.get("environment", {})
    if env.get("specific_location"):
        parts.append(env.get("specific_location"))
    if env.get("background_description"):
        parts.append(env.get("background_description"))
    if env.get("time_of_day"):
        parts.append(env.get("time_of_day"))
    
    # Camera
    camera = scene.get("camera", {})
    camera_desc = []
    if camera.get("angle"):
        camera_desc.append(camera.get("angle"))
    if camera.get("shot_size"):
        camera_desc.append(camera.get("shot_size"))
    if camera.get("depth_of_field"):
        camera_desc.append(camera.get("depth_of_field"))
    if camera_desc:
        parts.append(f"Camera: {', '.join(camera_desc)}")
    
    # Lighting
    lighting = scene.get("lighting", {})
    lighting_desc = []
    if lighting.get("primary_light_source"):
        lighting_desc.append(f"{lighting.get('primary_light_source')} from {lighting.get('primary_direction', '')}")
    if lighting.get("color_temperature"):
        lighting_desc.append(lighting.get("color_temperature"))
    if lighting.get("overall_mood"):
        lighting_desc.append(f"{lighting.get('overall_mood')} mood")
    if lighting_desc:
        parts.append(f"Lighting: {', '.join(lighting_desc)}")
    
    # Special effects
    if scene.get("special_effects", {}).get("effects_present") == "true":
        parts.append(scene.get("special_effects", {}).get("description", ""))
    
    return ". ".join(parts) + "."


def generate_storyboard_from_filled_template(filled_template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert filled template into storyboard format compatible with existing pipeline.
    
    Args:
        filled_template: Completely filled template
    
    Returns:
        dict: Storyboard plan in format expected by image/video generation pipeline
    """
    logger.info("[Prompt Generator] Converting filled template to storyboard format")
    
    # Generate character and product descriptions (used across all scenes)
    character_desc = generate_character_description(filled_template.get("character", {}))
    product_desc = generate_product_description(filled_template.get("product", {}))
    
    logger.info(f"[Prompt Generator] Character description: {len(character_desc)} chars")
    logger.info(f"[Prompt Generator] Product description: {len(product_desc)} chars")
    
    # Build consistency markers
    production = filled_template.get("production", {})
    consistency_markers = {
        "subject_description": character_desc if character_desc else product_desc,
        "style": production.get("visual_style", {}).get("overall_aesthetic", "cinematic photorealistic"),
        "color_palette": production.get("color_palette", {}).get("primary_colors", "natural tones"),
        "lighting": production.get("lighting_approach", {}).get("style", "natural soft lighting"),
        "composition": production.get("camera_style", {}).get("shot_preference", "balanced composition"),
        "mood": filled_template.get("story", {}).get("tone", "engaging")
    }
    
    # Build scenes
    storyboard_scenes = []
    scenes = filled_template.get("scenes", [])
    
    for idx, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", idx + 1)
        is_first = (scene_num == 1)
        
        # Generate image generation prompt
        image_gen_prompt = generate_scene_prompt(scene, character_desc, product_desc, is_first)
        
        # Build storyboard scene
        storyboard_scene = {
            "scene_number": scene_num,
            "aida_stage": scene.get("beat_name", f"Beat {scene_num}"),
            "duration_seconds": int(scene.get("duration_seconds", 4)),
            
            # Main prompts
            "detailed_prompt": scene.get("action_and_motion", {}).get("primary_action", image_gen_prompt[:80]),
            "image_generation_prompt": image_gen_prompt,
            "start_image_prompt": image_gen_prompt,  # Simplified - same as main for now
            "end_image_prompt": image_gen_prompt,    # Simplified - same as main for now
            
            # Metadata
            "subject_presence": "full" if (scene.get("character_details", {}).get("present_in_scene") == "true" or 
                                          scene.get("product_details", {}).get("present_in_scene") == "true") else "none",
            
            "scene_description": {
                "environment": scene.get("environment", {}).get("specific_location", ""),
                "character_action": scene.get("character_details", {}).get("action", ""),
                "camera_angle": scene.get("camera", {}).get("angle", ""),
                "composition": scene.get("camera", {}).get("frame_composition", ""),
                "visual_elements": scene.get("environment", {}).get("foreground_elements", "")
            }
        }
        
        storyboard_scenes.append(storyboard_scene)
    
    # Build complete storyboard
    storyboard = {
        "consistency_markers": consistency_markers,
        "scenes": storyboard_scenes,
        
        # Additional metadata from filled template
        "story_metadata": {
            "title": filled_template.get("story", {}).get("title", ""),
            "logline": filled_template.get("story", {}).get("logline", ""),
            "template_used": filled_template.get("_metadata", {}).get("template_id", ""),
            "voice_over_script": filled_template.get("script", {}).get("lines", [])
        }
    }
    
    logger.info(f"✅ Storyboard generated: {len(storyboard_scenes)} scenes")
    
    return storyboard

