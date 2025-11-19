# Fill-in-the-Blank Template System

## Overview

This system uses **structured templates with explicit fields** that the LLM must fill. Think of it like a detailed form or Mad Libs - the LLM doesn't create freely, it fills in specific blanks.

---

## Complete Template Structure

### Template Contains:

1. **Story & Narrative** (15 fields)
2. **Script & Voice-Over** (20+ fields)
3. **Character Identity** (50+ fields)
4. **Product Identity** (30+ fields)
5. **Production Style** (15 fields)
6. **Scene-by-Scene Breakdown** (40+ fields per scene × 4 scenes = 160 fields)

**Total: ~290 fields to fill per video**

---

## Example: Coffee Ad Template Filling

### Input to LLM:

```json
{
  "user_prompt": "Artisan coffee that starts your morning right",
  "template_id": "emotional-arc",
  "template_to_fill": {
    "story": {
      "title": "__FILL__",
      "logline": "__FILL__",
      "genre": "__FILL__",
      ...
    },
    "character": {
      "age_exact": "__FILL__",
      "height_feet": "__FILL__",
      "height_inches": "__FILL__",
      "hair.color": "__FILL__",
      "hair.length": "__FILL__",
      "hair.style": "__FILL__",
      ...
    },
    "scenes": [
      {
        "scene_number": 1,
        "environment.location_type": "__FILL__",
        "environment.specific_location": "__FILL__",
        "environment.background_description": "__FILL__",
        "camera.angle": "__FILL__",
        "camera.shot_size": "__FILL__",
        "lighting.primary_light_source": "__FILL__",
        "character_details.action": "__FILL__",
        ...
      }
    ]
  }
}
```

---

### LLM Output (All Fields Filled):

```json
{
  "story": {
    "title": "Morning Ritual",
    "logline": "A busy professional discovers peace in her sacred morning coffee ritual",
    "genre": "inspirational lifestyle",
    "tone": "warm and intimate",
    
    "narrative_structure": {
      "setup": "Sarah wakes up to another hectic morning. Her alarm has been ringing for ten minutes. The day already feels overwhelming before it begins.",
      "conflict_or_need": "She craves a moment of calm and intention before the chaos starts. Something to ground her.",
      "turning_point": "She discovers the ritual of brewing artisan coffee. The process itself becomes meditative. The first sip brings clarity.",
      "resolution": "Now every morning begins with this sacred moment. She owns her mornings instead of rushing through them. The day starts with intention, not chaos."
    },
    
    "emotional_journey": {
      "starting_emotion": "overwhelmed and rushed",
      "middle_emotion": "curious and present",
      "ending_emotion": "calm and empowered"
    },
    
    "key_message": "Your morning ritual sets the tone for your entire day"
  },
  
  "script": {
    "style": "intimate first-person reflection",
    "pacing": "slow and contemplative",
    
    "lines": [
      {
        "scene_number": 1,
        "text": "Mornings used to be chaos.",
        "delivery": "soft and reflective, slightly weary",
        "timing": "0-3 seconds",
        "emphasis_words": "chaos"
      },
      {
        "scene_number": 2,
        "text": "Until I discovered this.",
        "delivery": "gentle with building curiosity",
        "timing": "throughout scene",
        "emphasis_words": "discovered, this"
      },
      {
        "scene_number": 3,
        "text": "Now every morning starts with intention.",
        "delivery": "warm and confident",
        "timing": "1-5 seconds",
        "emphasis_words": "intention"
      },
      {
        "scene_number": 4,
        "text": "My moment of calm before the world wakes up.",
        "delivery": "peaceful and satisfied",
        "timing": "throughout scene",
        "emphasis_words": "moment, calm"
      }
    ],
    
    "music_direction": {
      "genre": "ambient acoustic piano",
      "tempo": "slow 65 BPM",
      "mood": "peaceful and contemplative",
      "volume_levels": "soft background, gradually fades to silence at end"
    }
  },
  
  "character": {
    "present": "true",
    
    "demographics": {
      "gender": "woman",
      "age_exact": "32",
      "ethnicity": "Caucasian"
    },
    
    "body": {
      "height_feet": "5",
      "height_inches": "6",
      "build_type": "medium",
      "weight_approximate": "130 pounds"
    },
    
    "hair": {
      "length": "mid-back length",
      "color": "chestnut brown",
      "style": "subtle natural waves",
      "part": "side-parted on left",
      "texture": "fine and silky"
    },
    
    "face": {
      "shape": "oval",
      "cheekbones": "high and defined",
      "jawline": "soft and feminine",
      "nose": "straight and proportional",
      "lips": "medium fullness"
    },
    
    "eyes": {
      "color": "emerald green",
      "shape": "almond-shaped",
      "size": "medium to large"
    },
    
    "skin": {
      "tone": "warm beige",
      "fitzpatrick_type": "Type III",
      "texture": "smooth with natural glow"
    },
    
    "distinguishing_features": {
      "marks_or_scars": "small beauty mark near left eye, positioned just above cheekbone",
      "tattoos": "none",
      "piercings": "none",
      "unique_traits": "subtle dimples when smiling"
    },
    
    "clothing": {
      "top": "ivory silk blouse with pearl buttons and pointed collar",
      "bottom": "not visible in frame",
      "accessories": "thin gold watch on left wrist",
      "style": "elegant professional minimalist"
    },
    
    "expression_and_demeanor": {
      "default_expression": "warm confident expression with subtle smile",
      "body_language": "relaxed and present posture",
      "overall_vibe": "calm and approachable professional"
    },
    
    "backstory": {
      "occupation": "marketing executive",
      "lifestyle": "busy urban professional balancing career and wellness",
      "personality": "driven but seeking balance, values quality over speed",
      "goal_or_desire": "find moments of peace and intention in a hectic schedule"
    }
  },
  
  "product": {
    "present": "true",
    
    "type": "coffee mug",
    "brand_name": "none visible",
    
    "dimensions": {
      "height_inches": "4",
      "width_inches": "3.5",
      "depth_inches": "3.5",
      "weight_ounces": "12"
    },
    
    "material": {
      "primary": "white ceramic",
      "secondary": "none",
      "texture": "matte smooth finish"
    },
    
    "colors": {
      "primary_color": "pure white",
      "secondary_color": "gold",
      "accent_color": "none"
    },
    
    "branding": {
      "logo_present": "false",
      "logo_description": "none",
      "logo_position": "none",
      "label_present": "false",
      "label_description": "none"
    },
    
    "unique_features": {
      "shape_details": "cylindrical with slight inward curve at top, modern minimalist design",
      "cap_or_lid": "none",
      "handle_or_grip": "C-shaped handle with comfortable grip",
      "special_elements": "thin gold rim at top edge, exactly 2mm width"
    },
    
    "contents": {
      "visible": "true",
      "description": "steaming dark roast coffee, rich brown color, visible steam wisps rising"
    }
  },
  
  "production": {
    "visual_style": {
      "overall_aesthetic": "cinematic photorealistic with soft intimate quality",
      "reference_films_or_ads": "Apple lifestyle commercials, Kinfolk magazine aesthetic",
      "color_grading": "warm with slightly lifted shadows, gentle fade on highlights"
    },
    
    "color_palette": {
      "primary_colors": "warm earth tones, soft beiges and creams",
      "accent_colors": "subtle gold highlights, deep coffee browns",
      "overall_mood": "warm inviting and calming"
    },
    
    "lighting_approach": {
      "style": "natural soft window light with gentle fill",
      "color_temperature": "warm 3200K morning glow",
      "contrast_level": "low contrast with soft shadows"
    },
    
    "camera_style": {
      "movement_preference": "slow deliberate movements, gentle push-ins",
      "shot_preference": "intimate medium close-ups and close-ups",
      "lens_character": "shallow depth of field (f/1.8-2.8), soft bokeh"
    },
    
    "pacing": {
      "overall_tempo": "slow and contemplative, letting moments breathe",
      "transition_style": "smooth dissolves, gentle fades"
    }
  },
  
  "scenes": [
    {
      "scene_number": 1,
      "beat_name": "Quiet Moment",
      "duration_seconds": "4",
      
      "environment": {
        "location_type": "interior",
        "specific_location": "modern minimalist kitchen",
        "time_of_day": "early morning, around 6:30 AM",
        "weather": "clear morning",
        "season": "spring",
        "background_description": "large window with soft white semi-sheer curtains, morning light filtering through, white walls, minimal decor",
        "foreground_elements": "white marble counter with natural veining, clean and uncluttered surface",
        "props": "white coffee mug with gold rim, folded newspaper edge visible"
      },
      
      "camera": {
        "angle": "eye-level",
        "height": "slightly above subject's eye level",
        "movement": "slow dolly in, pushing closer to subject",
        "shot_size": "medium shot transitioning to medium close-up",
        "lens_type": "50mm prime lens",
        "depth_of_field": "shallow f/1.8, soft bokeh background",
        "frame_composition": "rule of thirds, subject positioned in right third, negative space left"
      },
      
      "lighting": {
        "primary_light_source": "natural window light",
        "primary_direction": "from left side at 45 degree angle",
        "secondary_light_source": "soft white bounce fill from right",
        "color_temperature": "warm 3200K morning glow",
        "contrast": "soft and low, gentle shadows",
        "shadows": "subtle and soft, barely visible under cheekbones",
        "highlights": "gentle on face and hair, natural glow",
        "overall_mood": "soft intimate and peaceful"
      },
      
      "character_details": {
        "present_in_scene": "true",
        "position": "centered in frame, seated at counter",
        "posture": "relaxed, leaning slightly forward towards counter",
        "action": "reaching towards coffee mug with both hands, about to grasp handle",
        "specific_gesture": "hands moving from lap towards mug, palms open and relaxed",
        "facial_expression": "peaceful contemplative, eyes soft and downward gazing",
        "eye_direction": "looking down at coffee mug",
        "clothing_visible": "top half visible, ivory silk blouse with collar"
      },
      
      "product_details": {
        "present_in_scene": "true",
        "position": "on counter directly in front of character, slightly left of center",
        "orientation": "upright facing camera, handle on right side",
        "prominence": "prominent in foreground, sharp focus",
        "interaction": "character about to grasp, hands approaching",
        "branding_visible": "gold rim clearly visible, catching morning light"
      },
      
      "action_and_motion": {
        "primary_action": "character's hands slowly reaching towards coffee mug",
        "secondary_action": "steam gently rising from coffee in delicate wisps",
        "camera_motion": "slow push in at 0.5 inches per second",
        "motion_speed": "slow and deliberate, contemplative pace"
      },
      
      "mood_and_emotion": {
        "emotional_tone": "contemplative calm with hint of anticipation",
        "energy_level": "low peaceful, quiet morning energy",
        "atmosphere": "intimate and serene, almost meditative"
      },
      
      "special_effects": {
        "effects_present": "true",
        "description": "subtle steam wisps rising from coffee, catching morning light, moving slowly upward"
      }
    }
    // Scenes 2, 3, 4 would follow with similar detail...
  ]
}
```

---

## How It Works: 3-Step Process

### Step 1: Load Template
```python
template = get_fill_in_template("emotional-arc")
# Returns template with all __FILL__ placeholders
```

### Step 2: LLM Fills Template
```python
filled_template = await fill_template_with_llm(
    template=template,
    user_prompt="Artisan coffee that starts your morning right"
)
# LLM fills every __FILL__ field
```

### Step 3: Generate Prompts from Filled Template
```python
# Concatenate filled fields into sentences
image_prompt = generate_image_prompt_from_filled_fields(filled_template)

# Example output:
"Woman, 32 years old, 5 feet 6 inches tall, medium build approximately 130 pounds. 
Mid-back length chestnut brown hair with subtle natural waves, side-parted on left, 
fine and silky texture. Oval face with high and defined cheekbones, soft and feminine 
jawline. Almond-shaped emerald green eyes, medium to large size. Warm beige skin tone, 
Fitzpatrick Type III, smooth with natural glow. Small beauty mark near left eye positioned 
just above cheekbone. Ivory silk blouse with pearl buttons and pointed collar. Warm 
confident expression with subtle smile. Sitting at modern minimalist kitchen counter, 
reaching towards coffee mug with both hands. White ceramic coffee mug 4 inches tall with 
thin gold rim at top edge. Natural window light from left at 45 degrees, warm 3200K morning 
glow, soft intimate mood. Eye-level camera, 50mm lens, shallow f/1.8 depth of field. 
Cinematic photorealistic aesthetic."
```

---

## Benefits of Fill-in-the-Blank Approach

### ✅ **Complete Control**
- Every single detail is explicitly specified
- No ambiguity, no creative interpretation
- LLM is just a form-filler, not a creative writer

### ✅ **Perfect Consistency**
- Character description built from exact filled fields
- Same fields copied to every scene
- No chance of hallucination or variation

### ✅ **Validation & Quality Control**
- Can check if all fields are filled
- Can validate field types (numbers, enums)
- Can enforce constraints (e.g., height must be "X feet Y inches")

### ✅ **Structured Output**
- Easy to parse and validate
- Easy to store in database
- Easy to modify specific fields

### ✅ **Granular Editing**
- User can edit individual fields
- Can regenerate just one field
- Can A/B test different values

---

## Template Fields Summary

### Story (15 fields)
- Title, logline, genre, tone
- Setup, conflict, turning point, resolution
- Emotional journey (start → middle → end)

### Script (20+ fields)
- Voice-over style and pacing
- 4 lines (text, delivery, timing, emphasis)
- Music direction (genre, tempo, mood)

### Character (50+ fields)
- Demographics (gender, age, ethnicity)
- Body (height, build, weight)
- Hair (length, color, style, part, texture)
- Face (shape, cheekbones, jaw, nose, lips)
- Eyes (color, shape, size)
- Skin (tone, Fitzpatrick type, texture)
- Distinguishing features (marks, tattoos, piercings)
- Clothing (top, bottom, accessories, style)
- Expression and demeanor
- Backstory (occupation, lifestyle, personality)

### Product (30+ fields)
- Type, brand, dimensions, weight
- Materials (primary, secondary, texture)
- Colors (primary, secondary, accent)
- Branding (logo, label descriptions)
- Unique features (shape, cap, handle)
- Contents (visible, description)

### Production (15 fields)
- Visual style, references, color grading
- Color palette (primary, accent, mood)
- Lighting (style, temperature, contrast)
- Camera style (movement, shots, lens)
- Pacing (tempo, transitions)

### Per Scene (40+ fields × 4 scenes = 160 fields)
- Beat name, duration
- Environment (location, time, weather, background, props)
- Camera (angle, movement, shot size, lens, composition)
- Lighting (sources, direction, temperature, shadows, mood)
- Character details (position, posture, action, expression)
- Product details (position, orientation, interaction)
- Action and motion
- Mood and emotion
- Special effects

**Total: ~290 structured fields per video**

---

## Next Steps

This is the **fill-in-the-blank template system**. Every detail is a slot that the LLM fills based on your prompt.

Should I implement this structured approach to replace the current creative story generation? 🎯

