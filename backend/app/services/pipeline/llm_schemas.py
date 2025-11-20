"""
Pydantic schemas for the 3-stage perfume ad pipeline (Option C) and Vision LLM style extraction.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import re


class SceneDescription(BaseModel):
    visual: str
    action: str
    camera: str
    lighting: str
    mood: str
    product_usage: str


class BlueprintScene(BaseModel):
    scene_number: int
    stage: str
    duration_seconds: int
    scene_description: SceneDescription
    sound_design: str
    voiceover: str
    overlay_text: str


class Stage1Blueprint(BaseModel):
    framework: str
    total_duration_seconds: int
    reference_image_path: str
    reference_image_usage: str
    style_tone: str
    scenes: List[BlueprintScene]
    music: Dict[str, str]


class ScentProfile(BaseModel):
    """
    Stage 2 output: olfactory + cinematic profile.

    Option C (full cinematic mode):
    - No strict word-count constraints on cinematic fields.
    - No color policing at schema level.
    - Light, ingredient-only validation on notes.
    """
    scent_profile_source: str = Field(..., pattern="^(inferred|user_provided|hybrid)$")

    top_notes: List[str]
    heart_notes: List[str]
    base_notes: List[str]

    lighting_cues: str
    color_palette: str
    motion_physics: str
    surface_textures: str
    atmosphere_density: str
    sound_motifs: str
    emotional_register: str

    @field_validator("top_notes", "heart_notes", "base_notes", mode="after")
    def validate_notes(cls, notes):
        """
        Enforce 'ingredients, not vibes/categories'.
        Delete this completely if you want maximum freedom.
        """
        forbidden_adjectives = [
            "fresh", "warm", "cool", "energetic", "uplifting", "grounded",
            "subtle", "zesty", "bright", "soft", "intense", "deep",
        ]
        forbidden_categories = ["citrus", "floral", "woody", "ambery", "green"]

        for n in notes:
            lower = n.lower()
            if any(adj in lower for adj in forbidden_adjectives):
                raise ValueError(
                    f"Invalid note '{n}'. Notes must be specific ingredients, not adjectives."
                )
            if lower in forbidden_categories:
                raise ValueError(
                    f"Invalid note '{n}'. Categories are not allowed as notes; use concrete ingredients."
                )
        return notes


# Vision LLM Style Extraction Schemas

def _validate_hex_colors(colors: List[str]) -> List[str]:
    """Validate that all colors are in hex format (#RRGGBB or #RGB)."""
    hex_pattern = re.compile(r'^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$')
    for color in colors:
        if not hex_pattern.match(color):
            raise ValueError(f"Invalid hex color format: {color}. Expected format: #RRGGBB or #RGB")
    return colors


# Product Style Schemas

class ProductIdentity(BaseModel):
    """Product identity information."""
    name: Optional[str] = Field(None, description="Product name (e.g., 'Chanel No. 5 Eau de Parfum')")
    category: Optional[str] = Field(None, description="Product category (e.g., 'fragrance', 'cosmetics', etc.)")
    brand: Optional[str] = Field(None, description="Brand name (e.g., 'Chanel')")


class ProductGeometry(BaseModel):
    """Geometric characteristics of the product."""
    silhouette: Optional[str] = Field(None, description="Product silhouette description (e.g., 'rectangular glass bottle with square shoulders')")
    cap_shape: Optional[str] = Field(None, description="Cap shape description (e.g., 'matte black square cap')")
    label_shape: Optional[str] = Field(None, description="Label shape and placement (e.g., 'rectangular label centered on the front')")
    proportions: Optional[str] = Field(None, description="Product proportions (e.g., 'tall, narrow bottle; cap width equals bottle neck width')")
    beveling_details: Optional[str] = Field(None, description="Beveling or edge details (e.g., 'subtle bevels along edges')")
    angles_to_preserve: List[str] = Field(default_factory=list, description="Camera angles to preserve (e.g., ['front-on', '3/4 angle'])")


class Materials(BaseModel):
    """Material characteristics of the product."""
    body_material: Optional[str] = Field(None, description="Body material (e.g., 'transparent glass', 'metal', etc.)")
    cap_material: Optional[str] = Field(None, description="Cap material (e.g., 'matte black plastic', 'metal', etc.)")
    reflectivity: Optional[str] = Field(None, description="Reflectivity description (e.g., 'body: glossy; cap: matte')")
    liquid_color: Optional[str] = Field(None, description="Liquid color if applicable (e.g., 'golden amber', 'clear', etc.)")


class ProductVisualStyle(BaseModel):
    """Visual style characteristics specific to product images."""
    default_composition: Optional[str] = Field(None, description="Default composition style (e.g., 'centered product on clean background')")
    recommended_backgrounds: List[str] = Field(default_factory=list, description="Recommended background styles (e.g., ['off-white', 'cream', 'soft gradient'])")
    forbidden_backgrounds: List[str] = Field(default_factory=list, description="Forbidden background styles (e.g., ['busy textures', 'neon colors', 'clutter'])")
    perspective: Optional[str] = Field(None, description="Recommended perspective (e.g., 'eye-level to slight high-angle')")
    product_scale: Optional[str] = Field(None, description="Product scale in frame (e.g., 'dominant in frame', 'small product shot', etc.)")


class ProductColorProfile(BaseModel):
    """Color profile extracted from product images."""
    dominant_colors: List[str] = Field(default_factory=list, description="Dominant colors in hex format")
    contrast_level: Optional[str] = Field(None, description="Contrast level: high, medium, low")
    avoid_colors: List[str] = Field(default_factory=list, description="Colors to avoid (e.g., ['neon green', 'deep red'])")

    @field_validator("dominant_colors", mode="after")
    def validate_hex_colors(cls, colors):
        """Validate that all colors are in hex format (#RRGGBB or #RGB)."""
        return _validate_hex_colors(colors)


class ProductStyleJSON(BaseModel):
    """Complete product style JSON extracted from product images."""
    product_identity: ProductIdentity = Field(..., description="Product identity information")
    product_geometry: ProductGeometry = Field(..., description="Product geometric characteristics")
    materials: Materials = Field(..., description="Material characteristics")
    visual_style: ProductVisualStyle = Field(..., description="Visual style characteristics")
    color_profile: ProductColorProfile = Field(..., description="Color profile")


# Brand Style Schemas

class BrandIdentity(BaseModel):
    """Brand identity information."""
    brand_name: Optional[str] = Field(None, description="Brand name (e.g., 'Chanel')")
    brand_personality: Optional[str] = Field(None, description="Brand personality description (e.g., 'timeless, elegant, Parisian minimalism')")


class BrandColorPalette(BaseModel):
    """Brand color palette."""
    primary: List[str] = Field(default_factory=list, description="Primary brand colors in hex format")
    secondary: List[str] = Field(default_factory=list, description="Secondary brand colors in hex format")
    accent: List[str] = Field(default_factory=list, description="Accent brand colors in hex format")
    forbidden_colors: List[str] = Field(default_factory=list, description="Colors to avoid (e.g., ['neon tones', 'excessive saturation'])")

    @field_validator("primary", "secondary", "accent", mode="after")
    def validate_hex_colors(cls, colors):
        """Validate that all colors are in hex format (#RRGGBB or #RGB)."""
        return _validate_hex_colors(colors)


class LightingStyle(BaseModel):
    """Lighting style characteristics."""
    primary_lighting: Optional[str] = Field(None, description="Primary lighting style (e.g., 'soft diffused studio light')")
    secondary_lighting: Optional[str] = Field(None, description="Secondary lighting style (e.g., 'subtle rim light for glass definition')")
    avoid_lighting: List[str] = Field(default_factory=list, description="Lighting styles to avoid (e.g., ['harsh shadows', 'colored lighting'])")


class CompositionRules(BaseModel):
    """Composition rules and guidelines."""
    framing: Optional[str] = Field(None, description="Framing style (e.g., 'centered and symmetrical')")
    negative_space: Optional[str] = Field(None, description="Negative space treatment (e.g., 'generous margin around product')")
    camera_language: List[str] = Field(default_factory=list, description="Camera movement styles (e.g., ['slow dolly', 'subtle parallax'])")
    forbidden_angles: List[str] = Field(default_factory=list, description="Forbidden camera angles (e.g., ['distorted wide-angle close-ups'])")


class Atmosphere(BaseModel):
    """Atmosphere characteristics."""
    mood: Optional[str] = Field(None, description="Mood description (e.g., 'sophisticated and calm')")
    texture: Optional[str] = Field(None, description="Texture style (e.g., 'clean, minimal surfaces')")
    depth_of_field: Optional[str] = Field(None, description="Depth of field preference (e.g., 'shallow (product in focus)')")


class BrandStyleJSON(BaseModel):
    """Complete brand style JSON extracted from brand style images."""
    brand_identity: BrandIdentity = Field(..., description="Brand identity information")
    color_palette: BrandColorPalette = Field(..., description="Brand color palette")
    lighting_style: LightingStyle = Field(..., description="Lighting style characteristics")
    composition_rules: CompositionRules = Field(..., description="Composition rules and guidelines")
    atmosphere: Atmosphere = Field(..., description="Atmosphere characteristics")
    brand_markers: List[str] = Field(default_factory=list, description="Brand markers (e.g., ['clean monochrome palette', 'minimalist set design'])")


# Stage 3 Scene Assembler Schemas

class Stage3Input(BaseModel):
    """Complete input schema for Stage 3 Scene Assembler."""
    stage1_blueprint: Stage1Blueprint = Field(..., description="Stage 1 blueprint with 5 scenes containing visual, action, camera, lighting, mood, and product_usage")
    scent_profile: ScentProfile = Field(..., description="Stage 2 scent profile with cinematic characteristics (lighting_cues, color_palette, motion_physics, surface_textures, atmosphere_density, sound_motifs, emotional_register)")
    brand_style_json: Optional[BrandStyleJSON] = Field(None, description="Optional brand style JSON extracted from brand style images. Includes brand identity, color palette, lighting style, composition rules, atmosphere, and brand markers.")
    product_style_json: Optional[ProductStyleJSON] = Field(None, description="Optional product style JSON extracted from product images. Includes product identity, geometry, materials, visual style, and color profile.")
    model: str = Field(default="gpt-5", description="LLM model to use for scene assembly (default: gpt-5)")


class Stage3Output(BaseModel):
    """Complete output schema for Stage 3 Scene Assembler."""
    scenes: List[str] = Field(..., min_length=5, max_length=5, description="List of 5 video-ready cinematic scene paragraphs. Each paragraph is 3-5 sentences describing a 3-4 second shot with environment, subject, camera motion, lighting, color, and emotional micro-beat.")


class Stage3Complete(BaseModel):
    """Complete Stage 3 pipeline result including inputs and outputs."""
    stage1_blueprint: Stage1Blueprint = Field(..., description="Stage 1 blueprint used as input")
    stage2_scent_profile: ScentProfile = Field(..., description="Stage 2 scent profile used as input")
    brand_style_json: Optional[BrandStyleJSON] = Field(None, description="Brand style JSON used as input (if provided)")
    product_style_json: Optional[ProductStyleJSON] = Field(None, description="Product style JSON used as input (if provided)")
    stage3_scenes: List[str] = Field(..., min_length=5, max_length=5, description="Stage 3 output: 5 video-ready cinematic scene paragraphs")