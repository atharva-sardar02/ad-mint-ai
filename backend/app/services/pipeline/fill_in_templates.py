"""
Structured Fill-in-the-Blank Templates for Story-Driven Video Generation

Each template is a structured form with explicit fields that the LLM must fill.
No creative freedom - just fill the blanks with appropriate content.
"""

from typing import Dict, Any, List

# Base template structure that all story templates inherit
BASE_TEMPLATE_STRUCTURE = {
    # ============================================
    # PART 1: STORY & NARRATIVE
    # ============================================
    "story": {
        "title": "__FILL__",  # Short catchy title (3-5 words)
        "logline": "__FILL__",  # One sentence summary (max 20 words)
        "genre": "__FILL__",  # e.g., "inspirational", "dramatic", "playful", "mysterious"
        "tone": "__FILL__",  # e.g., "warm and intimate", "bold and energetic", "sophisticated"
        
        "narrative_structure": {
            "setup": "__FILL__",  # What is the initial situation? (2-3 sentences)
            "conflict_or_need": "__FILL__",  # What problem/desire drives the story? (1-2 sentences)
            "turning_point": "__FILL__",  # What changes? Product/solution introduced (1-2 sentences)
            "resolution": "__FILL__",  # How does it end? New reality (1-2 sentences)
        },
        
        "emotional_journey": {
            "starting_emotion": "__FILL__",  # e.g., "frustrated", "tired", "curious"
            "middle_emotion": "__FILL__",  # e.g., "hopeful", "intrigued", "excited"
            "ending_emotion": "__FILL__",  # e.g., "satisfied", "empowered", "joyful"
        },
        
        "key_message": "__FILL__",  # Core message in one sentence (max 15 words)
    },
    
    # ============================================
    # PART 2: SCRIPT & VOICE-OVER
    # ============================================
    "script": {
        "style": "__FILL__",  # e.g., "conversational first-person", "poetic narrator", "direct address"
        "pacing": "__FILL__",  # e.g., "slow and contemplative", "energetic and fast", "moderate"
        
        "lines": [
            {
                "scene_number": 1,
                "text": "__FILL__",  # Exact voice-over text (5-15 words)
                "delivery": "__FILL__",  # e.g., "soft and reflective", "bold and confident"
                "timing": "__FILL__",  # e.g., "0-3 seconds", "throughout scene"
                "emphasis_words": "__FILL__",  # Words to emphasize, comma-separated
            },
            {
                "scene_number": 2,
                "text": "__FILL__",
                "delivery": "__FILL__",
                "timing": "__FILL__",
                "emphasis_words": "__FILL__",
            },
            {
                "scene_number": 3,
                "text": "__FILL__",
                "delivery": "__FILL__",
                "timing": "__FILL__",
                "emphasis_words": "__FILL__",
            },
            {
                "scene_number": 4,
                "text": "__FILL__",
                "delivery": "__FILL__",
                "timing": "__FILL__",
                "emphasis_words": "__FILL__",
            }
        ],
        
        "music_direction": {
            "genre": "__FILL__",  # e.g., "ambient piano", "upbeat electronic", "acoustic guitar"
            "tempo": "__FILL__",  # e.g., "slow 60-80 BPM", "moderate 90-110 BPM", "fast 120+ BPM"
            "mood": "__FILL__",  # e.g., "peaceful", "energizing", "dramatic"
            "volume_levels": "__FILL__",  # e.g., "soft background throughout", "builds in intensity"
        }
    },
    
    # ============================================
    # PART 3: CHARACTER IDENTITY (If applicable)
    # ============================================
    "character": {
        "present": "__FILL__",  # true/false
        
        # PHYSICAL ATTRIBUTES (Police description level)
        "demographics": {
            "gender": "__FILL__",  # e.g., "woman", "man", "non-binary"
            "age_exact": "__FILL__",  # Exact age, e.g., "32"
            "ethnicity": "__FILL__",  # e.g., "East Asian", "Latin American", "Caucasian"
        },
        
        "body": {
            "height_feet": "__FILL__",  # e.g., "5"
            "height_inches": "__FILL__",  # e.g., "6"
            "build_type": "__FILL__",  # e.g., "athletic", "slender", "medium", "heavyset"
            "weight_approximate": "__FILL__",  # e.g., "130 pounds"
        },
        
        "hair": {
            "length": "__FILL__",  # e.g., "mid-back length", "shoulder-length", "short cropped"
            "color": "__FILL__",  # Specific, e.g., "chestnut brown", "platinum blonde", "jet black"
            "style": "__FILL__",  # e.g., "subtle waves", "straight", "tight curls", "dreadlocks"
            "part": "__FILL__",  # e.g., "side-parted on left", "center part", "no part"
            "texture": "__FILL__",  # e.g., "fine and silky", "coarse", "thick"
        },
        
        "face": {
            "shape": "__FILL__",  # e.g., "oval", "round", "square", "heart-shaped", "angular"
            "cheekbones": "__FILL__",  # e.g., "high and defined", "soft", "prominent"
            "jawline": "__FILL__",  # e.g., "soft", "defined", "strong and angular"
            "nose": "__FILL__",  # e.g., "straight", "slightly upturned", "broad"
            "lips": "__FILL__",  # e.g., "full", "thin", "medium"
        },
        
        "eyes": {
            "color": "__FILL__",  # Specific, e.g., "emerald green", "dark brown", "ice blue"
            "shape": "__FILL__",  # e.g., "almond-shaped", "round", "hooded", "upturned"
            "size": "__FILL__",  # e.g., "large", "medium", "small"
        },
        
        "skin": {
            "tone": "__FILL__",  # e.g., "warm beige", "deep brown", "pale porcelain"
            "fitzpatrick_type": "__FILL__",  # e.g., "Type III", "Type V"
            "texture": "__FILL__",  # e.g., "smooth", "freckled", "with visible pores"
        },
        
        "distinguishing_features": {
            "marks_or_scars": "__FILL__",  # e.g., "small beauty mark near left eye above cheekbone"
            "tattoos": "__FILL__",  # e.g., "none" or description
            "piercings": "__FILL__",  # e.g., "none", "small diamond nose stud on right nostril"
            "unique_traits": "__FILL__",  # e.g., "dimples when smiling", "gap between front teeth"
        },
        
        "clothing": {
            "top": "__FILL__",  # e.g., "ivory silk blouse with pearl buttons and pointed collar"
            "bottom": "__FILL__",  # e.g., "dark gray fitted trousers"
            "accessories": "__FILL__",  # e.g., "thin gold watch on left wrist"
            "style": "__FILL__",  # e.g., "professional minimalist", "casual bohemian"
        },
        
        "expression_and_demeanor": {
            "default_expression": "__FILL__",  # e.g., "warm confident expression with subtle smile"
            "body_language": "__FILL__",  # e.g., "relaxed posture", "energetic movements"
            "overall_vibe": "__FILL__",  # e.g., "approachable and professional", "mysterious and elegant"
        },
        
        # CHARACTER BACKSTORY (for context)
        "backstory": {
            "occupation": "__FILL__",  # e.g., "marketing executive", "yoga instructor"
            "lifestyle": "__FILL__",  # e.g., "busy urban professional", "health-conscious parent"
            "personality": "__FILL__",  # e.g., "driven and ambitious", "calm and mindful"
            "goal_or_desire": "__FILL__",  # e.g., "find balance in hectic mornings"
        }
    },
    
    # ============================================
    # PART 4: PRODUCT IDENTITY (If applicable)
    # ============================================
    "product": {
        "present": "__FILL__",  # true/false
        
        "type": "__FILL__",  # e.g., "coffee mug", "perfume bottle", "smartphone"
        "brand_name": "__FILL__",  # e.g., "Lumière", "NRG Coffee", or "none"
        
        "dimensions": {
            "height_inches": "__FILL__",  # e.g., "4"
            "width_inches": "__FILL__",  # e.g., "3.5"
            "depth_inches": "__FILL__",  # e.g., "3.5"
            "weight_ounces": "__FILL__",  # e.g., "8"
        },
        
        "material": {
            "primary": "__FILL__",  # e.g., "white ceramic", "frosted glass", "brushed aluminum"
            "secondary": "__FILL__",  # e.g., "gold metal rim", "plastic cap", or "none"
            "texture": "__FILL__",  # e.g., "matte finish", "glossy", "smooth with subtle grain"
        },
        
        "colors": {
            "primary_color": "__FILL__",  # e.g., "white", "matte black", "rose gold"
            "secondary_color": "__FILL__",  # e.g., "gold", "silver", or "none"
            "accent_color": "__FILL__",  # e.g., "pearl white", or "none"
        },
        
        "branding": {
            "logo_present": "__FILL__",  # true/false
            "logo_description": "__FILL__",  # e.g., "small embossed text 'NRG' in sans-serif"
            "logo_position": "__FILL__",  # e.g., "centered on front", "bottom right corner"
            "label_present": "__FILL__",  # true/false
            "label_description": "__FILL__",  # e.g., "thin gold rectangular label with embossed text"
        },
        
        "unique_features": {
            "shape_details": "__FILL__",  # e.g., "cylindrical with slight taper", "hexagonal facets"
            "cap_or_lid": "__FILL__",  # e.g., "gold metallic screw cap 1 inch diameter"
            "handle_or_grip": "__FILL__",  # e.g., "ergonomic C-shaped handle", or "none"
            "special_elements": "__FILL__",  # e.g., "thin gold rim at top edge", "frosted bottom half"
        },
        
        "contents": {
            "visible": "__FILL__",  # true/false
            "description": "__FILL__",  # e.g., "steaming dark roast coffee", "amber liquid"
        }
    },
    
    # ============================================
    # PART 5: PRODUCTION STYLE
    # ============================================
    "production": {
        "visual_style": {
            "overall_aesthetic": "__FILL__",  # e.g., "cinematic photorealistic", "stylized modern"
            "reference_films_or_ads": "__FILL__",  # e.g., "Apple commercial aesthetic", "Wes Anderson symmetry"
            "color_grading": "__FILL__",  # e.g., "warm with lifted shadows", "cool desaturated"
        },
        
        "color_palette": {
            "primary_colors": "__FILL__",  # e.g., "warm earth tones", "cool blues and whites"
            "accent_colors": "__FILL__",  # e.g., "gold highlights", "pops of red"
            "overall_mood": "__FILL__",  # e.g., "warm and inviting", "cool and sophisticated"
        },
        
        "lighting_approach": {
            "style": "__FILL__",  # e.g., "natural soft window light", "dramatic studio lighting"
            "color_temperature": "__FILL__",  # e.g., "warm 3200K", "neutral 5600K", "cool 7000K"
            "contrast_level": "__FILL__",  # e.g., "low contrast soft shadows", "high contrast dramatic"
        },
        
        "camera_style": {
            "movement_preference": "__FILL__",  # e.g., "slow deliberate movements", "dynamic handheld"
            "shot_preference": "__FILL__",  # e.g., "intimate close-ups", "wide establishing shots"
            "lens_character": "__FILL__",  # e.g., "shallow depth of field", "deep focus throughout"
        },
        
        "pacing": {
            "overall_tempo": "__FILL__",  # e.g., "slow and contemplative", "energetic and dynamic"
            "transition_style": "__FILL__",  # e.g., "smooth dissolves", "quick cuts", "match cuts"
        }
    },
    
    # ============================================
    # PART 6: SCENE-BY-SCENE BREAKDOWN (4 scenes)
    # ============================================
    "scenes": [
        {
            "scene_number": 1,
            "beat_name": "__FILL__",  # e.g., "Attention", "Quiet Moment", "Problem"
            "duration_seconds": "__FILL__",  # 3-7 seconds
            
            "environment": {
                "location_type": "__FILL__",  # e.g., "interior", "exterior", "studio"
                "specific_location": "__FILL__",  # e.g., "modern kitchen", "city park", "minimalist room"
                "time_of_day": "__FILL__",  # e.g., "early morning", "golden hour", "midnight"
                "weather": "__FILL__",  # e.g., "clear", "overcast", "N/A for interior"
                "season": "__FILL__",  # e.g., "spring", "winter", or "N/A"
                "background_description": "__FILL__",  # e.g., "large window with white curtains, morning light"
                "foreground_elements": "__FILL__",  # e.g., "white marble counter, minimalist decor"
                "props": "__FILL__",  # e.g., "coffee mug, newspaper, smartphone", or "none"
            },
            
            "camera": {
                "angle": "__FILL__",  # e.g., "eye-level", "low angle", "overhead", "dutch tilt"
                "height": "__FILL__",  # e.g., "eye-level", "above", "below"
                "movement": "__FILL__",  # e.g., "static", "slow dolly in", "pan left to right", "orbit"
                "shot_size": "__FILL__",  # e.g., "medium shot", "close-up", "wide shot", "extreme close-up"
                "lens_type": "__FILL__",  # e.g., "50mm", "wide angle 24mm", "telephoto 85mm"
                "depth_of_field": "__FILL__",  # e.g., "shallow (f/1.8)", "deep (f/8)", "medium"
                "frame_composition": "__FILL__",  # e.g., "rule of thirds subject right", "centered symmetrical"
            },
            
            "lighting": {
                "primary_light_source": "__FILL__",  # e.g., "natural window light", "overhead pendant"
                "primary_direction": "__FILL__",  # e.g., "from left", "from behind", "overhead"
                "secondary_light_source": "__FILL__",  # e.g., "soft fill from right", or "none"
                "color_temperature": "__FILL__",  # e.g., "warm 3200K", "cool 6500K", "mixed"
                "contrast": "__FILL__",  # e.g., "soft low contrast", "dramatic high contrast"
                "shadows": "__FILL__",  # e.g., "soft and subtle", "hard and defined", "minimal"
                "highlights": "__FILL__",  # e.g., "gentle on face", "strong rim light", "none"
                "overall_mood": "__FILL__",  # e.g., "soft and intimate", "bright and airy", "moody"
            },
            
            "character_details": {
                "present_in_scene": "__FILL__",  # true/false
                "position": "__FILL__",  # e.g., "centered in frame", "left third", "background"
                "posture": "__FILL__",  # e.g., "sitting relaxed", "standing confident", "leaning forward"
                "action": "__FILL__",  # e.g., "reaching towards coffee mug", "looking out window"
                "specific_gesture": "__FILL__",  # e.g., "both hands cradling mug", "one hand on counter"
                "facial_expression": "__FILL__",  # e.g., "peaceful contemplative", "eyes closed smiling"
                "eye_direction": "__FILL__",  # e.g., "looking at product", "gazing off camera", "at camera"
                "clothing_visible": "__FILL__",  # e.g., "top half visible", "full outfit", "partial"
            },
            
            "product_details": {
                "present_in_scene": "__FILL__",  # true/false
                "position": "__FILL__",  # e.g., "on counter in foreground", "in character's hands"
                "orientation": "__FILL__",  # e.g., "upright facing camera", "tilted 45 degrees"
                "prominence": "__FILL__",  # e.g., "hero shot centered", "subtle background", "held by character"
                "interaction": "__FILL__",  # e.g., "character about to grasp", "sitting alone", "being poured"
                "branding_visible": "__FILL__",  # e.g., "logo clearly visible", "label facing camera", "not visible"
            },
            
            "action_and_motion": {
                "primary_action": "__FILL__",  # e.g., "character reaching for mug", "product rotating"
                "secondary_action": "__FILL__",  # e.g., "steam rising from mug", or "none"
                "camera_motion": "__FILL__",  # e.g., "slowly pushing in", "static", "orbiting"
                "motion_speed": "__FILL__",  # e.g., "slow and deliberate", "moderate", "quick"
            },
            
            "mood_and_emotion": {
                "emotional_tone": "__FILL__",  # e.g., "contemplative calm", "energized excitement"
                "energy_level": "__FILL__",  # e.g., "low peaceful", "moderate", "high intense"
                "atmosphere": "__FILL__",  # e.g., "intimate and quiet", "vibrant and lively"
            },
            
            "special_effects": {
                "effects_present": "__FILL__",  # true/false
                "description": "__FILL__",  # e.g., "steam wisps rising", "light rays", or "none"
            }
        },
        # Scenes 2, 3, 4 follow same structure
        # (In actual implementation, these would be separate entries)
    ]
}


# Template-specific structures (each inherits BASE_TEMPLATE_STRUCTURE and adds specific beat names)

AIDA_TEMPLATE = {
    "template_id": "aida",
    "template_name": "AIDA Framework",
    "beats": ["Attention", "Interest", "Desire", "Action"],
    "structure": BASE_TEMPLATE_STRUCTURE
}

PROBLEM_AGITATE_SOLVE_TEMPLATE = {
    "template_id": "problem-agitate-solve",
    "template_name": "Problem-Agitate-Solve",
    "beats": ["Problem", "Agitate", "Solve", "Relief"],
    "structure": BASE_TEMPLATE_STRUCTURE
}

BEFORE_AFTER_BRIDGE_TEMPLATE = {
    "template_id": "before-after-bridge",
    "template_name": "Before-After-Bridge",
    "beats": ["Before", "After", "Bridge", "Celebration"],
    "structure": BASE_TEMPLATE_STRUCTURE
}

HERO_JOURNEY_TEMPLATE = {
    "template_id": "hero-journey",
    "template_name": "Hero's Journey",
    "beats": ["Ordinary World", "Call to Adventure", "Transformation", "Return Triumphant"],
    "structure": BASE_TEMPLATE_STRUCTURE
}

EMOTIONAL_ARC_TEMPLATE = {
    "template_id": "emotional-arc",
    "template_name": "Emotional Arc",
    "beats": ["Quiet Moment", "Surprise/Delight", "Joy", "Connection"],
    "structure": BASE_TEMPLATE_STRUCTURE
}

TEASER_REVEAL_TEMPLATE = {
    "template_id": "teaser-reveal",
    "template_name": "Teaser-Reveal",
    "beats": ["Mystery", "Build", "Reveal", "Showcase"],
    "structure": BASE_TEMPLATE_STRUCTURE
}

SOCIAL_PROOF_TEMPLATE = {
    "template_id": "social-proof",
    "template_name": "Social Proof",
    "beats": ["Community", "Testimonial Moment", "Results", "Join Us"],
    "structure": BASE_TEMPLATE_STRUCTURE
}

SENSORY_EXPERIENCE_TEMPLATE = {
    "template_id": "sensory-experience",
    "template_name": "Sensory Experience",
    "beats": ["First Sense", "Second Sense", "Immersion", "Satisfaction"],
    "structure": BASE_TEMPLATE_STRUCTURE
}


# All templates registry
FILL_IN_TEMPLATES = {
    "aida": AIDA_TEMPLATE,
    "problem-agitate-solve": PROBLEM_AGITATE_SOLVE_TEMPLATE,
    "before-after-bridge": BEFORE_AFTER_BRIDGE_TEMPLATE,
    "hero-journey": HERO_JOURNEY_TEMPLATE,
    "emotional-arc": EMOTIONAL_ARC_TEMPLATE,
    "teaser-reveal": TEASER_REVEAL_TEMPLATE,
    "social-proof": SOCIAL_PROOF_TEMPLATE,
    "sensory-experience": SENSORY_EXPERIENCE_TEMPLATE
}


def get_fill_in_template(template_id: str) -> Dict[str, Any]:
    """Get a specific fill-in template by ID."""
    return FILL_IN_TEMPLATES.get(template_id)


def get_all_fill_in_templates() -> Dict[str, Dict[str, Any]]:
    """Get all fill-in templates."""
    return FILL_IN_TEMPLATES

