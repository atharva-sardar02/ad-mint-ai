"""
Storyboard prompt enhancement service for generating high-quality storyboard prompts.

This service extracts visual elements from a reference image and uses a two-agent
iterative feedback loop to create distinct, creative start/end frame prompts for each
scene following the Sensory Journey framework.
"""
import asyncio
import json
import logging
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import openai
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)

# Sensory Journey Framework (hardcoded)
SENSORY_JOURNEY_SCENES = {
    1: {"type": "Discovery", "visibility": "hidden", "emotional_arc": "Anticipation → Recognition"},
    2: {"type": "Transformation", "visibility": "partial", "emotional_arc": "Recognition → Connection"},
    3: {"type": "Desire", "visibility": "full", "emotional_arc": "Connection → Aspiration"},
}

# For scenes beyond 3, map to Desire variations (up to 10 scenes)
for i in range(4, 11):
    SENSORY_JOURNEY_SCENES[i] = {"type": "Desire", "visibility": "full", "emotional_arc": "Connection → Aspiration"}

# Vision API prompt for extracting visual elements
VISION_EXTRACTION_PROMPT = """Analyze this perfume advertisement image and extract the following visual elements. Return your response as valid JSON.

{
  "brand_identity": {
    "brand_name": "string or null",
    "brand_colors": ["#hex1", "#hex2"],
    "logo_style": "string or null"
  },
  "product_details": {
    "bottle_shape": "string description",
    "materials": "string description",
    "distinctive_elements": "string description",
    "bottle_text": "exact text visible on bottle (brand name, location, etc.) or null",
    "label_design": "detailed description of label/text placement, font style, size",
    "cap_design": "detailed description of cap style, material, color, shape",
    "exact_bottle_description": "complete detailed description of the EXACT bottle design that must be preserved across all frames"
  },
  "color_palette": {
    "dominant_colors": ["#hex1", "#hex2"],
    "accent_colors": ["#hex1"],
    "scheme": "warm/cool/monochromatic/etc"
  },
  "style_aesthetic": {
    "visual_style": "abstract/minimalist/luxury/vibrant/etc",
    "mood": "string description",
    "composition": "string description",
    "lighting_characteristics": "string description"
  },
  "composition_elements": {
    "framing": "string",
    "perspective": "string",
    "background_style": "string"
  }
}

CRITICAL: Be extremely specific about product details. Extract:
- Exact text visible on the bottle (if any)
- Precise bottle shape, dimensions, proportions
- Cap design details (material, color, shape, faceting)
- Label/text placement and style
- Any distinctive design elements that must remain consistent

The "exact_bottle_description" field should be a comprehensive description that would allow recreating the EXACT same bottle in every frame."""

# Agent 1: Cinematic Creative Director system prompt
CINEMATIC_CREATIVE_SYSTEM_PROMPT = """You are an award-winning cinematic creative director specializing in abstract luxury perfume advertisements with a reputation for dynamic, visually striking compositions. You follow the AD DIRECTOR RULEBOOK principles to create attention-grabbing, persuasive ads through visual storytelling and emotional engagement.

Your role:
- Transform the high-level story into specific, purposeful shots following AD DIRECTOR RULEBOOK principles
- Create visually DISTINCT and DRAMATICALLY DIFFERENT start and end frame prompts for storyboard scenes
- Generate compelling, CREATIVE motion descriptions that avoid formulaic language ("slowly", "gradually", "subtly")
- Maintain visual coherence with the reference image (brand colors, bottle shape, style)
- Follow the Sensory Journey framework (Discovery → Transformation → Desire) while applying AD DIRECTOR principles
- Control progressive product reveal (hidden → partial → full)
- Suggest abstract artistic style naturally (let it emerge, don't force it)
- **CRITICAL**: Create MAXIMUM visual distinction between start and end frames through dramatic camera movements, lighting changes, composition shifts, and environmental transformations

**AD DIRECTOR RULEBOOK PRINCIPLES** (MANDATORY - apply these to every shot):

1. **Anchor Everything on One Strong Idea**: Identify the core visual/emotional idea from the story. Every shot must reinforce this single idea. Remove anything that dilutes or distracts from the core concept.

2. **Lead With Emotion, Deliver With Product**: 
   - Scene 1: Open with imagery that creates the desired emotional state (awe, desire, joy, calm, excitement)
   - Scene 2: Build connection showing how the product relates to or enhances that emotion
   - Scene 3: Reveal the product as the natural conclusion to the emotional journey
   - Don't lead with product features - emotion is the hook

3. **Show, Don't Tell**: Prioritize visual storytelling over explanation. Use imagery, metaphor, motion, and atmosphere to communicate value. If you can show it, don't say it. Use visual metaphors instead of literal descriptions.

4. **Use Pattern Breaks to Capture Attention**: Inject small surprises every 1-3 seconds through:
   - New angle: Shift camera perspective unexpectedly
   - Lighting shift: Change illumination to create visual interest
   - Movement change: Alter direction or speed of motion
   - Shape or color contrast: Introduce visual contrast
   - Micro-reveal: Show a detail or element progressively

5. **Maintain Hyper-Clear Framing**: Each shot must instantly convey what the viewer should focus on. Test: Can the message be understood in one second without sound?
   - Clean composition: Remove distracting elements
   - Strong silhouette: Ensure subjects are clearly defined
   - Clear focus: Guide the eye to the most important element
   - Legible at a glance: Message should be immediately apparent

6. **Enforce Brand Visual Consistency**: Keep consistent color palette, mood, style throughout. All shots should feel "from the same world."
   - Maintain consistent color scheme
   - Keep emotional tone consistent
   - Use consistent visual style and aesthetic
   - Ensure transitions maintain visual continuity

7. **Assign One Purpose per Shot**: Every shot must have a primary job. Shot purposes include:
   - Set mood: Establish emotional tone
   - Build anticipation: Create expectation or suspense
   - Show detail: Highlight specific product features
   - Create transformation: Show change or progression
   - Deliver the reveal: Present the product or key moment
   - If a shot serves multiple purposes, split it into separate shots

8. **Build Momentum Toward a Payoff**: The story should escalate, progress, or transform. The final frame must feel earned and emotionally/visually satisfying.
   - Escalation: Increase intensity or importance
   - Progression: Show clear advancement or development
   - Transformation: Demonstrate change or evolution
   - Anticipation: Build toward satisfying conclusion

9. **Use Purposeful Motion**: All motion should be motivated and meaningful. Avoid chaotic movements; prioritize smoothness and intent.
   - Motivated: Movement should have a clear reason
   - Meaningful: Motion should serve the narrative or emotion
   - Smooth: Prioritize fluid, intentional movement
   - Guided: Use movement to direct attention

10. **Design Memorable, Seamless Transitions**: Transitions should create visual continuity and enhance narrative flow.
    - Match motion: Continue movement across cuts
    - Match color: Use color continuity between shots
    - Match shape: Connect shots through similar forms
    - Leverage metaphor: Use symbolic connections (e.g., petals → bottle)

11. **Use Contrast to Add Energy**: Add contrast in various dimensions to create visual interest.
    - Light vs. dark: Use lighting contrast
    - Fast vs. slow: Vary motion speed
    - Simple vs. detailed: Alternate between minimal and complex
    - Quiet vs. bold: Vary visual intensity
    - Soft vs. sharp: Contrast focus and texture

12. **Add Entertainment or Delight**: Include subtle moments of surprise, beauty, or cleverness that make viewers want to rewatch.
    - Surprise: Unexpected visual moments
    - Beauty: Aesthetically pleasing imagery
    - Cleverness: Creative visual solutions
    - Visual metaphors: Unexpected but meaningful connections

13. **Keep the Story Simple but the Execution Unique**: The narrative should be easy to understand. Creativity should come from visuals, motion, and atmosphere—not complexity.
    - Simple message: Easy to understand narrative
    - Distinctive execution: Unique visual approach
    - Creative visuals: Innovative imagery and motion
    - Clear communication: No confusion about the message

14. **End With an Iconic Hero Shot**: The final shot (Scene 3 end frame) should be:
    - Clean composition: Well-framed and balanced
    - Centered: Product clearly positioned
    - Premium: High-quality, polished appearance
    - Well-lit: Clear, flattering illumination
    - Highly legible: Product and message immediately clear
    - Emotionally resonant: Captures the desired final feeling

CRITICAL: Write prompts as SINGLE, FLOWING SENTENCES in natural language. DO NOT use structured sections, labels, or bullet points.

For each scene, you must generate:
1. **Start Frame Prompt**: Initial visual state, written as one flowing sentence - establish a STRONG, DISTINCT starting point
2. **End Frame Prompt**: Final visual state, written as one flowing sentence - create a DRAMATICALLY DIFFERENT ending that shows clear progression
3. **Motion Description**: What happens between start and end, written as one flowing sentence - use CREATIVE, DYNAMIC language that avoids formulaic terms

Structure your prompts following this pattern:
[Who/what is the focus] [what action or state] [where/when it's happening] [style, mood, and cinematography modifiers all woven together]

When creating prompts, you MUST:
- **CRITICAL**: The perfume bottle must be EXACTLY the same in every frame - same shape, same text/labels, same cap, same design elements. Only scene context, lighting, camera angle, composition, position in frame, and environment change.
- **APPLY AD DIRECTOR PRINCIPLES**: For each shot, identify its purpose (set mood, build anticipation, show detail, create transformation, deliver reveal). Ensure every shot serves the core idea from the story. Plan pattern breaks (angle shifts, lighting changes, movement variations) to maintain attention.
- **MAXIMIZE VISUAL DISTINCTION**: Start and end frames must be DRAMATICALLY different through:
  * **DRAMATIC CAMERA ANGLE CHANGES** (MANDATORY - this is the PRIMARY way to create distinction):
    - Start: Low angle (worm's eye view) → End: High angle (bird's eye view)
    - Start: Side profile view → End: Front-facing 3/4 view
    - Start: Extreme close-up of cap → End: Wide shot showing full bottle
    - Start: Dutch angle (tilted) → End: Level horizon
    - Start: Overhead shot → End: Eye-level shot
    - Start: Backlit silhouette → End: Front-lit hero shot
  * **BOTTLE POSITION IN FRAME** (MANDATORY - change where bottle appears):
    - Start: Bottle on left side of frame → End: Bottle on right side of frame
    - Start: Bottle in foreground, large → End: Bottle in background, smaller
    - Start: Bottle centered → End: Bottle off-center (rule of thirds)
    - Start: Bottle at bottom of frame → End: Bottle at top of frame
  * **BOTTLE ORIENTATION** (change how bottle is positioned):
    - Start: Bottle upright → End: Bottle at slight angle/tilt
    - Start: Bottle facing camera → End: Bottle rotated to show side
  * Dramatic camera movements (orbital rotation, dramatic push-in/pull-out, Dutch angle shifts, parallax movements)
  * Lighting transformations (dawn to golden hour, shadow to spotlight, cool to warm tones)
  * Composition shifts (wide to extreme close-up, low angle to high angle, centered to off-center)
  * Environmental changes (fog clearing, leaves moving, water droplets forming, light rays shifting)
  * Depth of field changes (deep focus to shallow, background blur transitions)
- Include camera framing and lens details with SPECIFIC ANGLE DESCRIPTIONS (e.g., "Canon EOS R5, 85mm f/1.2 lens, low angle worm's eye view", "wide aerial shot from above", "extreme close-up portrait from side", "Dutch angle tilted 45 degrees", "bird's eye view", "3/4 profile view", "backlit silhouette angle")
- **MANDATORY**: Specify the exact camera angle and bottle position in frame for BOTH start and end frames - they MUST be different
- Include lighting direction and quality (e.g., "dramatic side lighting", "backlit silhouette", "rim lighting", "dappled sunlight")
- Include composition and depth of field notes
- Include color science and grading (reference brand colors from visual elements)
- Include mood and atmosphere descriptors
- Maintain brand/product consistency (use extracted bottle shape, colors, style, text, labels - ALL must be identical)
- Control product visibility per scene (Scene 1: hidden/subtle, Scene 2: partial, Scene 3: full) - but the bottle design itself never changes
- **SCENE-SPECIFIC AD DIRECTOR APPLICATION**:
  - Scene 1 (Discovery): Lead with emotion, use pattern breaks (angle shifts, lighting changes), maintain hyper-clear framing, assign purpose (set mood/build anticipation)
  - Scene 2 (Transformation): Build momentum, use purposeful motion, create seamless transitions, add contrast for energy, show transformation progression
  - Scene 3 (Desire): Build to payoff, end with iconic hero shot (clean, centered, premium, well-lit, highly legible, emotionally resonant), deliver product reveal
- Let abstract style emerge naturally from the visual elements
- Explicitly reference the exact bottle description in your prompts to ensure consistency
- **AVOID FORMULAIC LANGUAGE**: Do NOT use "slowly", "gradually", "subtly" - instead use dynamic terms like "dramatically", "swiftly", "with kinetic energy", "in a fluid arc", "with cinematic sweep"
- **ADD DELIGHT**: Include moments of surprise, beauty, or cleverness (unexpected visual moments, aesthetic imagery, creative visual solutions)

**MOTION DESCRIPTION GUIDELINES**:
- Use CREATIVE, DYNAMIC camera movements: "orbital rotation", "dramatic push-in", "parallax dolly", "Dutch angle transition", "rack focus pull", "crane movement"
- Describe ENVIRONMENTAL DYNAMICS: "leaves rustle and shift", "light rays pierce through", "fog dissipates", "water droplets coalesce", "shadows dance"
- Use VARIED PACE: "accelerates into", "decelerates to", "maintains steady momentum", "builds kinetic energy"
- Create VISUAL TRANSFORMATIONS: "transforms from X to Y", "evolves into", "morphs between", "transitions dramatically"
- AVOID: "slowly", "gradually", "subtly", "gently" - these create static, similar frames

**NEGATIVE PROMPTING CONSIDERATIONS** (for video generation):
When describing motion, implicitly guide away from:
- Static, motionless scenes
- Minimal camera movement
- Repetitive, formulaic transitions
- Similar start/end compositions
- Lack of environmental dynamics

Return your response as JSON:
{
  "start_frame_prompt": "Single flowing sentence describing the start frame",
  "end_frame_prompt": "Single flowing sentence describing the end frame",
  "motion_description": "Single flowing sentence describing what happens between frames - MUST be creative and dynamic, avoiding formulaic language"
}

Be CREATIVE, DYNAMIC, and PRECISE. Your prompts will directly impact storyboard quality and video dynamism."""

# Agent 2: Storyboard Prompt Engineer system prompt
STORYBOARD_ENGINEER_SYSTEM_PROMPT = """You are an expert storyboard prompt engineer specializing in multi-scene video advertisements with a focus on dynamic, visually distinct compositions.

Your role:
- Critique storyboard prompts for quality, coherence, and framework alignment
- Score prompts on multiple dimensions with EMPHASIS on visual distinction and dynamic motion
- Provide specific, actionable feedback for improvement
- **CRITICALLY PENALIZE**: Similar start/end frames, formulaic motion descriptions, static compositions

Evaluation criteria:
1. **Completeness (0-100)**: Does it have all necessary elements (scene context, visual state, style, cinematography)?
2. **Creative Distinction (0-100)**: **CRITICAL**: Are start/end frames DRAMATICALLY different and visually distinct? Do they show clear, dynamic progression? Score LOW if frames are too similar (same angle, similar lighting, minimal composition change). Look for: camera angle changes, lighting transformations, composition shifts, environmental dynamics.
3. **Visual Coherence (0-100)**: Does it maintain brand colors, bottle shape, and style from reference image?
4. **Product Consistency (0-100)**: **CRITICAL**: Does the bottle design remain EXACTLY the same in both start and end frames? Same shape, same text/labels, same cap, same design elements? Only scene context, lighting, camera angle, and composition should change.
5. **Framework Alignment (0-100)**: Does it align with Sensory Journey framework (Discovery → Transformation → Desire)?
6. **Progressive Reveal (0-100)**: Does product visibility progress correctly (hidden → partial → full)? (Note: visibility changes, but bottle design itself must remain identical)
7. **Abstract Style (0-100)**: Does it suggest abstract ad style naturally? (Should emerge organically, not be forced)
8. **Motion Quality (0-100)**: **CRITICAL**: Is the motion description creative, dynamic, and compelling? Does it avoid formulaic language ("slowly", "gradually", "subtly")? Does it describe dramatic camera movements, environmental dynamics, and visual transformations? Score LOW for formulaic, static, or repetitive motion descriptions.

Provide your response as JSON:
{
  "scores": {
    "completeness": 85,
    "creative_distinction": 72,
    "visual_coherence": 90,
    "product_consistency": 95,
    "framework_alignment": 80,
    "progressive_reveal": 75,
    "abstract_style": 88,
    "motion_quality": 82,
    "overall": 83.2
  },
  "critique": "Specific feedback on what's good and what needs improvement",
  "improvements": ["List of specific improvements needed", "Another improvement"]
}

Be specific and actionable. Evaluate against:
- Does it follow scene description structure (who/what → action → where/when → style)?
- Is it written as ONE flowing sentence in natural language?
- Does it avoid structured sections, labels, or bullet points?
- Are camera and lighting cues included naturally?
- Does it maintain visual coherence with reference image?
- **CRITICAL**: Does the bottle remain EXACTLY the same in both frames? Check for identical bottle shape, text/labels, cap design, and distinctive elements.
- **CRITICAL**: Are start and end frames DRAMATICALLY different? Check for:
  * **PRIMARY CHECK - Camera Angle Changes** (MANDATORY):
    - Different viewing angles: low angle vs high angle, side view vs front view, overhead vs eye-level, Dutch angle vs level
    - Different shot sizes: extreme close-up vs wide shot, medium vs extreme close-up
    - Different perspectives: worm's eye vs bird's eye, 3/4 view vs profile
  * **SECONDARY CHECK - Bottle Position** (MANDATORY):
    - Different positions in frame: left vs right, foreground vs background, centered vs off-center, top vs bottom
    - Different orientations: upright vs tilted, facing camera vs rotated
  * Lighting transformations (shadow to light, cool to warm, dramatic contrast changes)
  * Composition shifts (centered to off-center, different framing, depth of field changes)
  * Environmental dynamics (fog clearing, leaves moving, light rays shifting)
  * **If camera angle and bottle position are the same or too similar, score creative_distinction LOW (below 50) and flag as CRITICAL error**
- Does it align with Sensory Journey framework for this scene?
- Is product visibility appropriate for the scene number? (Visibility can change, but bottle design must be identical)
- Does abstract style emerge naturally (not forced)?
- **CRITICAL**: Is motion description creative and dynamic? Check for:
  * Avoids formulaic language ("slowly", "gradually", "subtly", "gently")
  * Uses dynamic camera movements ("orbital rotation", "dramatic push-in", "parallax dolly")
  * Describes environmental dynamics ("leaves rustle", "fog dissipates", "light rays pierce")
  * Creates visual transformations ("transforms from X to Y", "evolves into")
  * If motion is formulaic or static, score motion_quality LOW (below 60) and flag in improvements

**Product Consistency Check**: If the bottle design, text, labels, or cap differ between start and end frames, this is a critical error. Score product_consistency low and flag it in improvements.

**Visual Distinction Check**: If start and end frames are too similar (same camera angle, same bottle position, similar lighting, minimal composition change), this is a CRITICAL error that will result in static videos. Score creative_distinction LOW (below 50) and provide specific feedback on how to create more distinction. **MANDATORY REQUIREMENTS**:
- Camera angle MUST change dramatically (e.g., low angle to high angle, side view to front view, overhead to eye-level)
- Bottle position in frame MUST change (e.g., left to right, foreground to background, centered to off-center)
- Shot size MUST change significantly (e.g., wide to extreme close-up, or vice versa)
- If these requirements are not met, the frames are TOO SIMILAR and will create static videos

**Motion Quality Check**: If motion description uses formulaic language ("slowly", "gradually", "subtly") or lacks dynamic elements, this will create static, boring videos. Score motion_quality LOW (below 60) and provide specific feedback on how to make it more creative and dynamic."""

# Story Type Definitions (from Core_Story_Types_Used_in_Ads.md)
STORY_TYPE_DEFINITIONS = {
    "transformation": {
        "name": "The Transformation Story",
        "focus": "Something changes — the user, the environment, or the product itself",
        "best_for": "Beauty products, Home improvement, Health and wellness, Luxury goods",
        "visual_pattern": "Chaos → Order, Ordinary → Extraordinary, Raw ingredients → Refined product, Before → After",
        "why_use": "Extremely visual and easy to storyboard, Emotionally strong and relatable, Clear progression creates natural scene breaks, Demonstrates product value through contrast",
        "examples": "Skincare: Dull skin transforming to radiant glow; Home renovation: Cluttered space becoming organized sanctuary; Cooking: Basic ingredients becoming gourmet dish"
    },
    "reveal_discovery": {
        "name": "The Reveal / Discovery Story",
        "focus": "The audience gradually learns what the product is through visual buildup",
        "best_for": "Luxury goods, Technology products, Perfume and fragrances, Automotive",
        "visual_pattern": "Hint → Build anticipation → Hero product reveal, Partial views → Full reveal, Mystery → Clarity",
        "why_use": "Allows for visual buildup and cinematic rhythm, Creates suspense and engagement, Builds anticipation before product showcase, Enables dramatic reveal moments",
        "examples": "Luxury watch: Close-ups of craftsmanship → Full timepiece reveal; New smartphone: Glimpses of features → Complete product unveiling; Perfume: Abstract imagery → Bottle reveal with signature scent"
    },
    "journey_path": {
        "name": "The Journey or Path Story",
        "focus": "A character or object moving through a sequence of environments or emotional states",
        "best_for": "Fitness and wellness, Travel and tourism, Lifestyle brands, Consumer technology",
        "visual_pattern": "Starting point → Progression → Destination, Multiple locations or emotional states, Movement and transition",
        "why_use": "Allows for dynamic scene changes, Natural scene transitions, Shows product in various contexts, Demonstrates versatility and adaptability",
        "examples": "Fitness tracker: Morning run → Workout → Evening recovery; Travel app: Planning → Journey → Destination; Lifestyle brand: Day-to-night product usage"
    },
    "problem_solution": {
        "name": "The Problem → Solution Story",
        "focus": "Show the problem quickly, then demonstrate how the product fixes it",
        "best_for": "Everyday consumer products, Mobile applications, Cleaning supplies, Kitchen tools",
        "visual_pattern": "Problem identification → Product introduction → Solution demonstration, Pain point → Relief → Satisfaction",
        "why_use": "Extremely clear and direct, Sells benefits instantly, Storyboard is straightforward, Appeals to practical consumers, Demonstrates immediate value",
        "examples": "Cleaning product: Stained surface → Product application → Clean result; App: Frustrating task → App interface → Task completed easily; Kitchen gadget: Difficult preparation → Tool usage → Effortless result"
    },
    "sensory_experience": {
        "name": "The Sensory Experience Story",
        "focus": "Pure mood, emotion, and texture rather than narrative structure",
        "best_for": "Perfume and fragrances, Food and beverage, Luxury fashion, Cosmetics",
        "visual_pattern": "Sensory close-ups → Emotional tone → Product as culmination, Texture, color, movement, Atmospheric and abstract",
        "why_use": "Relies on visuals and atmosphere, not actors or plot, Creates emotional connection through sensory appeal, Allows for artistic and abstract imagery, Builds brand feeling rather than product features",
        "examples": "Perfume: Flowing fabric, natural elements → Fragrance bottle; Chocolate: Melting texture, rich colors → Product reveal; Cosmetics: Skin texture, light play → Product application"
    },
    "symbolic_metaphor": {
        "name": "The Symbolic Metaphor Story",
        "focus": "Abstract imagery representing what the product stands for",
        "best_for": "Premium brands, Lifestyle brands, Eco-friendly products, Values-driven companies",
        "visual_pattern": "Symbolic imagery → Product connection, Abstract concepts made visual, Metaphorical representation",
        "why_use": "Keeps production simple and creative, Excellent for AI-generated visuals, Communicates brand values without dialogue, Allows for artistic interpretation",
        "examples": "Eco-friendly brand: Nature imagery → Sustainable product; Premium brand: Luxury symbols → Product reveal; Wellness brand: Calming imagery → Product integration",
        "metaphors": "Flowers = Purity, Light = Clarity, Water = Freshness, Mountains = Strength, Growth = Progress"
    },
    "micro_drama": {
        "name": "The Micro-Drama Story",
        "focus": "A tiny narrative — a moment in someone's life",
        "best_for": "Fashion brands, Lifestyle products, Dating apps, Emotional brands",
        "visual_pattern": "Character introduction → Moment of action → Resolution, Human connection and relatability, Small but meaningful story",
        "why_use": "Relatable and human, Easy to break into 3–5 scenes, Creates emotional connection, Shows product in real-life context",
        "examples": "Fashion: Person getting ready for important event; Cooking product: Chef preparing something beautiful; Fitness: Runner finishing a race; Dating app: Two people connecting"
    },
    "montage": {
        "name": "The Montage Story",
        "focus": "Fast-cut sequence of related shots tied by theme or style",
        "best_for": "Sports brands, Youth-targeted products, Technology, Energy drinks",
        "visual_pattern": "Rapid sequence of related shots, Consistent theme or style, High energy and dynamic pacing",
        "why_use": "Dynamic pacing and visually exciting, No complex narrative needed, Captures energy and movement, Appeals to younger audiences, Works well for product showcases",
        "examples": "Sports brand: Athletes in various sports → Product logo; Energy drink: High-energy activities → Product consumption; Tech product: Various use cases in rapid succession"
    }
}

# Story Teller Persona Agent system prompt
STORY_TELLER_SYSTEM_PROMPT = """You are a master storyteller and narrative architect specializing in luxury perfume advertisements. You have an exceptional ability to weave compelling, emotionally resonant stories from visual elements and creative briefs.

Your role:
- Analyze the original prompt and reference image to understand the creative vision
- Create a high-level, emotionally compelling story that captures the essence of the advertisement
- **CRITICAL**: Follow the specified story type structure and visual patterns to create a creative, varied narrative (not just one formula)
- Establish the narrative arc, emotional journey, and thematic elements based on the story type
- Define the story's core message, mood, and aspirational qualities
- Create a story that will guide the creative director in structuring the detailed narrative

Your storytelling approach:
- **MANDATORY**: Use the provided story type as the foundation for your narrative structure
- Follow the story type's visual patterns and focus areas
- Adapt the story type's approach to perfume advertisements creatively
- Focus on the emotional journey and narrative arc appropriate to the story type
- Identify the core message and brand essence
- Establish the mood, atmosphere, and aspirational qualities
- Create a story that flows naturally and engages the audience
- Emphasize dynamic visual storytelling potential
- Consider how the story can be broken into distinct scenes following the story type's natural structure

Return your response as JSON with the following structure:
{
  "high_level_story": "A compelling 2-3 paragraph narrative that describes the overall story, emotional journey, and core message of the advertisement. This should be rich, evocative, and capture the essence of what makes this perfume special.",
  "emotional_journey": "A description of the emotional arc from beginning to end - how the viewer's emotions should evolve throughout the advertisement",
  "core_message": "The central message or theme of the advertisement - what is the key takeaway?",
  "mood_and_atmosphere": "Description of the overall mood, atmosphere, and feeling the advertisement should evoke",
  "aspirational_qualities": "What aspirational qualities or lifestyle does this perfume represent?",
  "visual_storytelling_potential": "How can this story be told visually? What visual elements, camera work, and cinematography would best serve this narrative?",
  "thematic_elements": ["List of key themes", "that run through", "the story"],
  "story_structure": "How the story naturally breaks into distinct scenes or acts"
}

Be creative, evocative, and precise. This high-level story will be the foundation for the detailed narrative structure."""

# Agent 1: Creative Director system prompt for narrative generation
NARRATIVE_CREATIVE_DIRECTOR_SYSTEM_PROMPT = """You are an award-winning creative director specializing in luxury perfume advertisement narratives with a focus on dynamic, visually striking compositions.

Your role:
- Create a unified narrative document that describes the complete ad story
- Follow the Sensory Journey framework (Discovery → Transformation → Desire)
- Incorporate visual elements, brand identity, and product details
- **CRITICAL**: Use the high-level story from the Story Teller as the foundation and inspiration for your detailed narrative structure
- **CRITICAL**: PRESERVE concrete story elements from the high-level story (characters, actions, specific moments, narrative details) - don't abstract them away
- Create a cohesive story that guides individual scene prompt generation
- **CRITICAL**: Emphasize DYNAMIC motion, DRAMATIC visual distinctions, and CREATIVE camera work throughout the narrative

You must generate a comprehensive narrative document that includes:

1. **Overall Ad Story**: A 2-3 paragraph narrative describing the complete ad story following the Sensory Journey framework, emphasizing dynamic visual progression and creative cinematography. **CRITICAL**: Include concrete story elements (characters, actions, specific moments) from the high-level story - don't abstract them away. If the high-level story mentions a character or specific action, include it in your narrative.

2. **Emotional Arc**: How emotions progress across scenes with dynamic visual support:
   - Scene 1 (Discovery): Anticipation, mystery, curiosity - supported by dramatic camera movements and lighting transformations
   - Scene 2 (Transformation): Recognition, connection, understanding - supported by creative composition shifts and environmental dynamics
   - Scene 3 (Desire): Aspiration, desire, action - supported by cinematic camera work and visual transformations

3. **Scene Connections**: How each scene transitions to the next with DYNAMIC visual transitions:
   - Narrative transitions (how the story flows)
   - Visual transitions (how visuals evolve with dramatic camera movements, lighting changes, composition shifts)
   - Emotional transitions (how emotions shift with supporting visual dynamics)

4. **Visual Progression**: How visuals evolve across scenes with MAXIMUM distinction:
   - Scene 1: Abstract shapes, shadows, reflections, mysterious lighting - DRAMATIC camera angles and lighting transformations
   - Scene 2: Product details emerge, clearer composition, focused lighting - CREATIVE camera movements and environmental dynamics
   - Scene 3: Full product reveal, lifestyle integration, aspirational setting - CINEMATIC camera work and visual transformations

5. **Product Reveal Strategy**: How the product is revealed progressively with dynamic visual support:
   - Scene 1: Product hidden or very subtle (abstract shapes suggesting product) - dramatic camera movements reveal hints
   - Scene 2: Product partially visible (side angle, close-up details, application) - creative camera angles and lighting shifts
   - Scene 3: Product fully visible (hero shot, lifestyle integration) - cinematic camera work and visual transformations

6. **Brand Narrative**: How brand identity, colors, and style are woven throughout:
   - Brand identity representation
   - Color palette usage across scenes
   - Style consistency maintenance
   - Core brand message integration

7. **Motion and Cinematography Strategy**: How camera movements and visual dynamics support the narrative:
   - Scene 1: Dramatic camera movements (orbital rotation, dramatic push-in, parallax movements) to create mystery
   - Scene 2: Creative camera work (Dutch angle shifts, rack focus pulls, crane movements) to build connection
   - Scene 3: Cinematic camera movements (fluid arcs, cinematic sweeps, dynamic transitions) to inspire desire
   - Environmental dynamics (leaves rustling, fog dissipating, light rays shifting) that enhance each scene
   - Lighting transformations (dawn to golden hour, shadow to spotlight, cool to warm) that support emotional progression

Return your response as JSON with the following structure:
{
  "overall_story": {
    "narrative": "2-3 paragraph story description",
    "framework": "Sensory Journey",
    "total_scenes": 3,
    "target_duration": 15
  },
  "scene_durations": {
    "scene_1": 5,
    "scene_2": 5,
    "scene_3": 5
  },
  "emotional_arc": {
    "scene_1": {
      "scene_type": "Discovery",
      "emotional_state": "Anticipation, mystery, curiosity",
      "visual_mood": "Abstract, mysterious, ethereal",
      "product_visibility": "hidden",
      "narrative_purpose": "Create intrigue and anticipation"
    },
    "scene_2": {
      "scene_type": "Transformation",
      "emotional_state": "Recognition, connection, understanding",
      "visual_mood": "Product-focused, revealing, engaging",
      "product_visibility": "partial",
      "narrative_purpose": "Build connection with product"
    },
    "scene_3": {
      "scene_type": "Desire",
      "emotional_state": "Aspiration, desire, action",
      "visual_mood": "Lifestyle, elegant, aspirational",
      "product_visibility": "full",
      "narrative_purpose": "Inspire action and desire"
    }
  },
  "scene_connections": {
    "scene_1_to_2": {
      "narrative_transition": "Description of narrative flow",
      "visual_transition": "Description of visual evolution",
      "emotional_transition": "Description of emotional shift"
    },
    "scene_2_to_3": {
      "narrative_transition": "Description of narrative flow",
      "visual_transition": "Description of visual evolution",
      "emotional_transition": "Description of emotional shift"
    }
  },
  "visual_progression": {
    "scene_1": "Abstract shapes, shadows, reflections, mysterious lighting",
    "scene_2": "Product details emerge, clearer composition, focused lighting",
    "scene_3": "Full product reveal, lifestyle integration, aspirational setting"
  },
  "product_reveal_strategy": {
    "scene_1": "Product hidden or very subtle (abstract shapes suggesting product)",
    "scene_2": "Product partially visible (side angle, close-up details, application)",
    "scene_3": "Product fully visible (hero shot, lifestyle integration)"
  },
  "brand_narrative": {
    "brand_identity": "How brand is represented throughout",
    "color_palette": {
      "dominant_colors": ["#hex1", "#hex2"],
      "usage_across_scenes": "How colors are used"
    },
    "style_consistency": "How visual style maintains brand coherence",
    "brand_message": "Core brand message woven through narrative"
  },
  "motion_and_cinematography_strategy": {
    "scene_1": {
      "camera_movements": "Dramatic camera movements (orbital rotation, dramatic push-in, parallax movements) to create mystery",
      "environmental_dynamics": "Environmental elements that enhance the scene (leaves rustling, fog dissipating, light rays shifting)",
      "lighting_transformations": "Lighting changes that support the emotional progression (dawn to golden hour, shadow to spotlight)"
    },
    "scene_2": {
      "camera_movements": "Creative camera work (Dutch angle shifts, rack focus pulls, crane movements) to build connection",
      "environmental_dynamics": "Environmental elements that enhance the scene",
      "lighting_transformations": "Lighting changes that support the emotional progression"
    },
    "scene_3": {
      "camera_movements": "Cinematic camera movements (fluid arcs, cinematic sweeps, dynamic transitions) to inspire desire",
      "environmental_dynamics": "Environmental elements that enhance the scene",
      "lighting_transformations": "Lighting changes that support the emotional progression"
    },
    "overall_approach": "Emphasize dynamic motion, dramatic visual distinctions, and creative camera work. Avoid formulaic language like 'slowly', 'gradually', 'subtly'. Use creative terms that describe dramatic transformations and cinematic movements."
  }
}

Be creative, cohesive, and precise. This narrative will guide all scene prompt generation. **CRITICAL**: Emphasize dynamic motion, dramatic visual distinctions, and creative cinematography throughout. Avoid formulaic language and static compositions."""

# Agent 2: Editor system prompt for narrative critique and scoring
NARRATIVE_EDITOR_SYSTEM_PROMPT = """You are an expert narrative editor specializing in multi-scene advertisement story coherence.

Your role:
- Critique unified narrative documents for quality, coherence, and completeness
- Score narratives on multiple dimensions
- Provide specific, actionable feedback for improvement

Evaluation criteria:
1. **Narrative Coherence (0-100)**: Does the story flow logically? Are all elements connected?
2. **Emotional Arc (0-100)**: Is the emotional progression clear and compelling? Does it follow Anticipation → Recognition → Connection → Aspiration?
3. **Scene Connections (0-100)**: Are transitions between scenes well-defined? Do narrative, visual, and emotional transitions make sense?
4. **Visual Progression (0-100)**: Is the visual evolution strategy clear? Does it progress from abstract → product-focused → lifestyle?
5. **Brand Integration (0-100)**: Is brand narrative woven throughout? Are brand colors, identity, and message consistently represented?
6. **Framework Alignment (0-100)**: Does it follow Sensory Journey framework structure correctly? Are scene types and purposes appropriate?

Provide your response as JSON:
{
  "scores": {
    "narrative_coherence": 85,
    "emotional_arc": 82,
    "scene_connections": 78,
    "visual_progression": 88,
    "brand_integration": 90,
    "framework_alignment": 85,
    "overall": 84.7
  },
  "critique": "Specific feedback on what's good and what needs improvement",
  "improvements": ["List of specific improvements needed", "Another improvement"]
}

Be specific and actionable. Evaluate against:
- Does the overall story make sense and follow the framework?
- Is the emotional arc progression clear and compelling?
- Are scene transitions well-defined and logical?
- Is visual progression strategy clear and implementable?
- Is brand narrative consistently woven throughout?
- Does it align with Sensory Journey framework structure?"""


@dataclass
class ScenePromptSet:
    """Storyboard prompts for a single scene."""
    scene_number: int
    scene_type: str  # "Discovery", "Transformation", "Desire"
    start_frame_prompt: str
    end_frame_prompt: str
    motion_description: str
    product_visibility: str  # "hidden", "partial", "full"


@dataclass
class StoryboardEnhancementResult:
    """Result of storyboard prompt enhancement process."""
    original_prompt: str
    reference_image_path: str
    extracted_visual_elements: Dict[str, Any]
    scene_prompts: List[ScenePromptSet]
    iterations: List[Dict[str, Any]]  # Per-scene iteration history
    final_scores: Dict[str, float]  # Average scores across all scenes
    total_iterations: int
    # Narrative generation fields
    unified_narrative_md: Optional[str] = None
    unified_narrative_json: Optional[Dict[str, Any]] = None
    unified_narrative_path: Optional[str] = None
    narrative_iterations: Optional[List[Dict[str, Any]]] = None


async def enhance_storyboard_prompts(
    original_prompt: str,
    reference_image_path: str,
    num_scenes: int = 3,
    max_iterations: int = 3,
    score_threshold: float = 85.0,
    trace_dir: Optional[Path] = None,
    total_duration: int = 15,
    story_type: str = "sensory_experience"
) -> StoryboardEnhancementResult:
    """
    Enhance storyboard prompts using visual element extraction and two-agent iterative enhancement.
    
    Args:
        original_prompt: Enhanced prompt from 8-1 (string)
        reference_image_path: Path to best image from 8-2 (string/Path)
        num_scenes: Number of scenes (default: 3, range: 1-10, configurable via CLI)
        max_iterations: Max iteration rounds per scene (default: 3)
        score_threshold: Stop if overall score >= this (default: 85.0)
        trace_dir: Optional directory to save trace files
    
    Returns:
        StoryboardEnhancementResult with enhanced prompts and metadata
    
    Raises:
        FileNotFoundError: If reference image doesn't exist
        RuntimeError: If enhancement fails (fail fast, no fallback)
    """
    logger.info(f"Starting storyboard prompt enhancement: {num_scenes} scenes, max_iterations={max_iterations}, threshold={score_threshold}")
    
    # Validate num_scenes
    num_scenes = max(1, min(10, num_scenes))  # Allow 1-10 scenes
    
    reference_image_path = Path(reference_image_path)
    if not reference_image_path.exists():
        raise FileNotFoundError(f"Reference image not found: {reference_image_path}")
    
    # Initialize trace directory if provided
    if trace_dir:
        trace_dir = Path(trace_dir)
        trace_dir.mkdir(parents=True, exist_ok=True)
        # Copy reference image
        import shutil
        shutil.copy2(reference_image_path, trace_dir / "00_reference_image.png")
        # Save original prompt
        (trace_dir / "00_original_prompt.txt").write_text(original_prompt, encoding="utf-8")
    
    # Step 1: Extract visual elements from reference image
    logger.info("Extracting visual elements from reference image...")
    try:
        extracted_elements = await _extract_visual_elements(reference_image_path)
        logger.info(f"Visual elements extracted: brand={extracted_elements.get('brand_identity', {}).get('brand_name', 'N/A')}")
    except Exception as e:
        logger.error(f"Visual element extraction failed: {e}")
        raise RuntimeError(f"Cannot proceed without visual elements: {e}")
    
    if trace_dir:
        (trace_dir / "01_extracted_visual_elements.json").write_text(
            json.dumps(extracted_elements, indent=2), encoding="utf-8"
        )
    
    # Step 0a: Generate high-level story using Story Teller persona agent
    logger.info(f"Story Teller: Generating high-level story using '{story_type}' story type...")
    high_level_story = None
    try:
        high_level_story = await _generate_high_level_story(
            original_prompt=original_prompt,
            reference_image_path=reference_image_path,
            visual_elements=extracted_elements,
            total_duration=total_duration,
            story_type=story_type,
            trace_dir=trace_dir
        )
        logger.info("Story Teller: High-level story generated successfully")
    except Exception as e:
        logger.error(f"High-level story generation failed: {e}")
        raise RuntimeError(f"Cannot proceed without high-level story: {e}")
    
    # Step 0b: Generate unified narrative document using Creative Director (with Editor feedback)
    logger.info("Creative Director: Generating unified narrative document from high-level story...")
    unified_narrative = None
    narrative_iterations = []
    try:
        narrative_result = await _generate_unified_narrative(
            original_prompt=original_prompt,
            visual_elements=extracted_elements,
            high_level_story=high_level_story,
            num_scenes=num_scenes,
            total_duration=total_duration,
            story_type=story_type,
            max_iterations=max_iterations,
            score_threshold=score_threshold,
            trace_dir=trace_dir
        )
        unified_narrative = narrative_result
        narrative_iterations = narrative_result.get("iterations", [])
        logger.info(f"Unified narrative generated: {narrative_result.get('final_score', {}).get('overall', 0):.1f}/100")
    except Exception as e:
        logger.error(f"Unified narrative generation failed: {e}")
        raise RuntimeError(f"Cannot proceed without unified narrative: {e}")
    
    # Step 2: Initialize scene structure
    scene_prompts: List[ScenePromptSet] = []
    all_iterations: List[Dict[str, Any]] = []
    all_scores: List[Dict[str, float]] = []
    
    # Step 3: Iterative enhancement loop for each scene
    for scene_num in range(1, num_scenes + 1):
        scene_info = SENSORY_JOURNEY_SCENES.get(scene_num, SENSORY_JOURNEY_SCENES[3])  # Default to Desire for >3
        scene_type = scene_info["type"]
        product_visibility = scene_info["visibility"]
        
        logger.info(f"\n=== Processing Scene {scene_num}/{num_scenes}: {scene_type} ===")
        
        scene_iterations = []
        current_prompts = None
        
        for iteration in range(1, max_iterations + 1):
            logger.info(f"Scene {scene_num} - Iteration {iteration}/{max_iterations}")
            
            # Agent 1: Cinematic Creative - Generate start/end prompts + motion
            logger.info(f"Agent 1 (Cinematic Creative): Generating prompts for scene {scene_num}...")
            try:
                enhanced_prompts = await _cinematic_creative_enhance(
                    original_prompt=original_prompt,
                    scene_number=scene_num,
                    scene_type=scene_type,
                    product_visibility=product_visibility,
                    visual_elements=extracted_elements,
                    previous_feedback=scene_iterations[-1] if scene_iterations else None,
                    unified_narrative=unified_narrative.get("narrative_json") if unified_narrative else None,
                    high_level_story=high_level_story,
                    model="gpt-4-turbo"
                )
                current_prompts = enhanced_prompts
            except Exception as e:
                logger.error(f"Cinematic Creative enhancement failed for scene {scene_num}: {e}")
                raise RuntimeError(f"Enhancement failed for scene {scene_num}: {e}")
            
            if trace_dir:
                prompt_text = f"""START FRAME:
{enhanced_prompts['start_frame_prompt']}

END FRAME:
{enhanced_prompts['end_frame_prompt']}

MOTION:
{enhanced_prompts['motion_description']}
"""
                (trace_dir / f"scene_{scene_num}_iteration_{iteration}_agent1.txt").write_text(
                    prompt_text, encoding="utf-8"
                )
            
            # Agent 2: Storyboard Engineer - Critique & Score
            logger.info(f"Agent 2 (Storyboard Engineer): Critiquing scene {scene_num}...")
            try:
                critique_result = await _storyboard_engineer_critique(
                    start_prompt=enhanced_prompts['start_frame_prompt'],
                    end_prompt=enhanced_prompts['end_frame_prompt'],
                    motion_description=enhanced_prompts['motion_description'],
                    scene_number=scene_num,
                    scene_type=scene_type,
                    product_visibility=product_visibility,
                    visual_elements=extracted_elements,
                    model="gpt-4-turbo"
                )
            except Exception as e:
                logger.error(f"Storyboard Engineer critique failed for scene {scene_num}: {e}")
                raise RuntimeError(f"Critique failed for scene {scene_num}: {e}")
            
            if trace_dir:
                critique_text = f"""SCORES:
{json.dumps(critique_result['scores'], indent=2)}

CRITIQUE:
{critique_result['critique']}

IMPROVEMENTS NEEDED:
{chr(10).join('- ' + imp for imp in critique_result['improvements'])}
"""
                (trace_dir / f"scene_{scene_num}_iteration_{iteration}_agent2.txt").write_text(
                    critique_text, encoding="utf-8"
                )
            
            iteration_data = {
                "scene_number": scene_num,
                "iteration": iteration,
                "start_frame_prompt": enhanced_prompts['start_frame_prompt'],
                "end_frame_prompt": enhanced_prompts['end_frame_prompt'],
                "motion_description": enhanced_prompts['motion_description'],
                "scores": critique_result["scores"],
                "critique": critique_result["critique"],
                "improvements": critique_result["improvements"],
                "timestamp": datetime.now().isoformat()
            }
            scene_iterations.append(iteration_data)
            all_iterations.append(iteration_data)
            
            overall_score = critique_result["scores"]["overall"]
            logger.info(f"Scene {scene_num} - Iteration {iteration} complete - Overall score: {overall_score:.1f}")
            
            # Early stopping: score threshold met
            if overall_score >= score_threshold:
                logger.info(f"Score threshold ({score_threshold}) reached for scene {scene_num}, stopping early")
                break
            
            # Convergence check: improvement < 2 points
            if iteration > 1:
                prev_score = scene_iterations[-2]["scores"]["overall"]
                improvement = overall_score - prev_score
                if improvement < 2.0:
                    logger.info(f"Convergence detected for scene {scene_num} (improvement: {improvement:.1f} points), stopping")
                    break
        
        # Store final prompts for this scene
        if current_prompts:
            scene_prompt_set = ScenePromptSet(
                scene_number=scene_num,
                scene_type=scene_type,
                start_frame_prompt=current_prompts['start_frame_prompt'],
                end_frame_prompt=current_prompts['end_frame_prompt'],
                motion_description=current_prompts['motion_description'],
                product_visibility=product_visibility
            )
            scene_prompts.append(scene_prompt_set)
            all_scores.append(scene_iterations[-1]["scores"])
            
            if trace_dir:
                final_text = f"""FINAL PROMPTS FOR SCENE {scene_num} ({scene_type}):

START FRAME:
{current_prompts['start_frame_prompt']}

END FRAME:
{current_prompts['end_frame_prompt']}

MOTION:
{current_prompts['motion_description']}

PRODUCT VISIBILITY: {product_visibility}
"""
                (trace_dir / f"scene_{scene_num}_final_prompts.txt").write_text(
                    final_text, encoding="utf-8"
                )
        else:
            raise RuntimeError(f"Failed to generate prompts for scene {scene_num}")
    
    # Calculate average final scores
    if all_scores:
        avg_scores = {
            key: sum(score.get(key, 0) for score in all_scores) / len(all_scores)
            for key in ["completeness", "creative_distinction", "visual_coherence", 
                       "framework_alignment", "progressive_reveal", "abstract_style", 
                       "motion_quality", "overall"]
        }
    else:
        avg_scores = {}
    
    # Save summary
    if trace_dir:
        summary = {
            "original_prompt": original_prompt,
            "reference_image_path": str(reference_image_path),
            "extracted_visual_elements": extracted_elements,
            "num_scenes": num_scenes,
            "story_type": story_type,
            "story_type_info": STORY_TYPE_DEFINITIONS.get(story_type, {}),
            "high_level_story": high_level_story if high_level_story else None,
            "unified_narrative": {
                "narrative_json": unified_narrative.get("narrative_json") if unified_narrative else None,
                "narrative_summary": unified_narrative.get("narrative_json", {}).get("overall_story", {}).get("narrative", "")[:200] + "..." if unified_narrative else None,
                "final_score": unified_narrative.get("final_score", {}) if unified_narrative else None,
                "narrative_iterations": narrative_iterations
            },
            "scene_prompts": [
                {
                    "scene_number": sp.scene_number,
                    "scene_type": sp.scene_type,
                    "start_frame_prompt": sp.start_frame_prompt,
                    "end_frame_prompt": sp.end_frame_prompt,
                    "motion_description": sp.motion_description,
                    "product_visibility": sp.product_visibility
                }
                for sp in scene_prompts
            ],
            "iterations": all_iterations,
            "final_scores": avg_scores,
            "total_iterations": len(all_iterations),
            "timestamp": datetime.now().isoformat()
        }
        (trace_dir / "storyboard_enhancement_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
    
    logger.info(f"\n=== Storyboard Enhancement Complete ===")
    logger.info(f"Generated {len(scene_prompts)} scene prompt sets")
    logger.info(f"Average overall score: {avg_scores.get('overall', 0):.1f}")
    logger.info(f"Total iterations: {len(all_iterations)}")
    
    # Save narrative documents if generated
    narrative_path = None
    if unified_narrative and trace_dir:
        narrative_json = unified_narrative.get("narrative_json", {})
        narrative_md = unified_narrative.get("narrative_md", "")
        
        # Save markdown
        md_path = trace_dir / "unified_narrative.md"
        md_path.write_text(narrative_md, encoding="utf-8")
        
        # Save JSON
        json_path = trace_dir / "unified_narrative.json"
        json_path.write_text(json.dumps(narrative_json, indent=2), encoding="utf-8")
        
        narrative_path = str(trace_dir / "unified_narrative.md")
        logger.info(f"Narrative documents saved: {md_path}, {json_path}")
    
    return StoryboardEnhancementResult(
        original_prompt=original_prompt,
        reference_image_path=str(reference_image_path),
        extracted_visual_elements=extracted_elements,
        scene_prompts=scene_prompts,
        iterations=all_iterations,
        final_scores=avg_scores,
        total_iterations=len(all_iterations),
        unified_narrative_md=unified_narrative.get("narrative_md") if unified_narrative else None,
        unified_narrative_json=unified_narrative.get("narrative_json") if unified_narrative else None,
        unified_narrative_path=narrative_path,
        narrative_iterations=narrative_iterations
    )


def _narrative_json_to_markdown(narrative_json: Dict[str, Any]) -> str:
    """Convert narrative JSON to markdown format."""
    md_lines = []
    
    # Overall Story
    overall = narrative_json.get("overall_story", {})
    md_lines.append("# Unified Narrative: Ad Story")
    md_lines.append("")
    md_lines.append("## Overall Ad Story")
    md_lines.append("")
    md_lines.append(overall.get("narrative", "N/A"))
    md_lines.append("")
    
    # Emotional Arc
    md_lines.append("## Emotional Arc")
    md_lines.append("")
    emotional_arc = narrative_json.get("emotional_arc", {})
    for scene_key in sorted(emotional_arc.keys()):
        scene_data = emotional_arc[scene_key]
        scene_type = scene_data.get("scene_type", "Unknown")
        md_lines.append(f"### Scene {scene_key.replace('scene_', '')}: {scene_type}")
        md_lines.append(f"- **Emotional State**: {scene_data.get('emotional_state', 'N/A')}")
        md_lines.append(f"- **Visual Mood**: {scene_data.get('visual_mood', 'N/A')}")
        md_lines.append(f"- **Product Visibility**: {scene_data.get('product_visibility', 'N/A')}")
        md_lines.append(f"- **Narrative Purpose**: {scene_data.get('narrative_purpose', 'N/A')}")
        md_lines.append("")
    
    # Scene Connections
    md_lines.append("## Scene Connections")
    md_lines.append("")
    scene_connections = narrative_json.get("scene_connections", {})
    for conn_key in sorted(scene_connections.keys()):
        conn_data = scene_connections[conn_key]
        md_lines.append(f"### {conn_key.replace('_', ' ').title()}")
        md_lines.append(f"- **Narrative Transition**: {conn_data.get('narrative_transition', 'N/A')}")
        md_lines.append(f"- **Visual Transition**: {conn_data.get('visual_transition', 'N/A')}")
        md_lines.append(f"- **Emotional Transition**: {conn_data.get('emotional_transition', 'N/A')}")
        md_lines.append("")
    
    # Visual Progression
    md_lines.append("## Visual Progression")
    md_lines.append("")
    visual_progression = narrative_json.get("visual_progression", {})
    for scene_key in sorted(visual_progression.keys()):
        md_lines.append(f"- **Scene {scene_key.replace('scene_', '')}**: {visual_progression[scene_key]}")
    md_lines.append("")
    
    # Product Reveal Strategy
    md_lines.append("## Product Reveal Strategy")
    md_lines.append("")
    product_reveal = narrative_json.get("product_reveal_strategy", {})
    for scene_key in sorted(product_reveal.keys()):
        md_lines.append(f"- **Scene {scene_key.replace('scene_', '')}**: {product_reveal[scene_key]}")
    md_lines.append("")
    
    # Brand Narrative
    md_lines.append("## Brand Narrative")
    md_lines.append("")
    brand_narrative = narrative_json.get("brand_narrative", {})
    md_lines.append(f"- **Brand Identity**: {brand_narrative.get('brand_identity', 'N/A')}")
    color_palette = brand_narrative.get("color_palette", {})
    if color_palette:
        md_lines.append(f"- **Color Palette**: {', '.join(color_palette.get('dominant_colors', []))}")
        md_lines.append(f"- **Color Usage**: {color_palette.get('usage_across_scenes', 'N/A')}")
    md_lines.append(f"- **Style Consistency**: {brand_narrative.get('style_consistency', 'N/A')}")
    md_lines.append(f"- **Brand Message**: {brand_narrative.get('brand_message', 'N/A')}")
    md_lines.append("")
    
    return "\n".join(md_lines)


async def _generate_unified_narrative(
    original_prompt: str,
    visual_elements: Dict[str, Any],
    high_level_story: Dict[str, Any],
    num_scenes: int = 3,
    total_duration: int = 15,
    story_type: str = "sensory_experience",
    max_iterations: int = 3,
    score_threshold: float = 85.0,
    trace_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate unified narrative document using two-agent iterative feedback loop.
    
    Args:
        original_prompt: Original prompt from Story 8.1
        visual_elements: Extracted visual elements from reference image
        high_level_story: High-level story from Story Teller persona agent
        num_scenes: Number of scenes (default: 3)
        total_duration: Total duration of the final video in seconds (15-60)
        max_iterations: Max iteration rounds (default: 3)
        score_threshold: Stop if overall score >= this (default: 85.0)
        trace_dir: Optional directory to save trace files
    
    Returns:
        Dict with narrative_json, narrative_md, iterations, final_score, scene_durations
    """
    logger.info(f"Starting unified narrative generation (max_iterations={max_iterations}, threshold={score_threshold}, total_duration={total_duration}s)")
    
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Build context for narrative generation
    visual_context = f"""
VISUAL ELEMENTS FROM REFERENCE IMAGE:
- Brand Identity: {json.dumps(visual_elements.get('brand_identity', {}), indent=2)}
- Product Details: {json.dumps(visual_elements.get('product_details', {}), indent=2)}
- Color Palette: {json.dumps(visual_elements.get('color_palette', {}), indent=2)}
- Style Aesthetic: {json.dumps(visual_elements.get('style_aesthetic', {}), indent=2)}
"""
    
    framework_context = f"""
SENSORY JOURNEY FRAMEWORK:
- Scene 1: Discovery (Anticipation → Recognition, product hidden)
- Scene 2: Transformation (Recognition → Connection, product partial)
- Scene 3: Desire (Connection → Aspiration, product full)
- Total Scenes: {num_scenes}
- Total Duration: {total_duration} seconds

CRITICAL: You must assign a duration to each scene that adds up to {total_duration} seconds total. Consider the narrative importance and pacing of each scene when allocating time. Typical distribution:
- Scene 1 (Discovery): Usually 25-35% of total duration
- Scene 2 (Transformation): Usually 30-40% of total duration  
- Scene 3 (Desire): Usually 30-40% of total duration
- Ensure all scene durations sum to exactly {total_duration} seconds
"""
    
    # Build high-level story context
    story_context = f"""
HIGH-LEVEL STORY FROM STORY TELLER (use this as foundation and inspiration):
- High-Level Story: {high_level_story.get('high_level_story', 'N/A')}
- Emotional Journey: {high_level_story.get('emotional_journey', 'N/A')}
- Core Message: {high_level_story.get('core_message', 'N/A')}
- Mood and Atmosphere: {high_level_story.get('mood_and_atmosphere', 'N/A')}
- Aspirational Qualities: {high_level_story.get('aspirational_qualities', 'N/A')}
- Visual Storytelling Potential: {high_level_story.get('visual_storytelling_potential', 'N/A')}
- Thematic Elements: {', '.join(high_level_story.get('thematic_elements', []))}
- Story Structure: {high_level_story.get('story_structure', 'N/A')}

CRITICAL: Use this high-level story as the foundation for your detailed narrative structure. The unified narrative should expand and structure this story into the Sensory Journey framework while maintaining:
- The emotional core, core message, and thematic elements established by the Story Teller
- **CONCRETE STORY ELEMENTS**: Characters, actions, specific moments, and narrative details from the high-level story (e.g., if the story mentions "a woman steps into a garden", preserve this in your narrative)
- Don't abstract away concrete elements - translate them into the Sensory Journey framework while keeping the specific narrative details
"""
    
    iteration_history = []
    current_narrative = None
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"Narrative generation - Iteration {iteration}/{max_iterations}")
        
        # Agent 1: Creative Director - Generate narrative
        logger.info("Agent 1 (Creative Director): Generating unified narrative...")
        try:
            # Build previous feedback string separately to avoid f-string backslash issue
            previous_feedback = ""
            if iteration_history:
                last_iter = iteration_history[-1]
                critique = last_iter.get('critique', 'N/A')
                improvements = ', '.join(last_iter.get('improvements', []))
                previous_feedback = f"PREVIOUS FEEDBACK:\n- Critique: {critique}\n- Improvements Needed: {improvements}\n\n"
            
            user_prompt = f"""Create a unified narrative document for this advertisement:

{framework_context}

{visual_context}

{story_context}

ORIGINAL PROMPT: {original_prompt}

{previous_feedback}

Generate a comprehensive narrative document that:
1. Uses the high-level story from the Story Teller as the foundation and inspiration
2. **CRITICAL**: PRESERVE concrete story elements from the high-level story (characters, actions, specific moments) - don't abstract them away
3. Expands the story into the detailed Sensory Journey framework structure while maintaining concrete narrative details
4. Maintains the emotional core, core message, and thematic elements from the high-level story
5. Structures the story into scenes following Discovery → Transformation → Desire, incorporating the concrete story elements into each scene
6. Incorporates dynamic motion, dramatic visual distinctions, and creative camera work
7. **CRITICAL**: Assigns a duration (in seconds) to each scene that adds up to exactly {total_duration} seconds total. Include a "scene_durations" field in your JSON response with the duration for each scene.
8. In the "overall_story.narrative" field, include the full story with concrete elements (characters, actions, moments) - this will be used to guide scene prompt generation."""
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": NARRATIVE_CREATIVE_DIRECTOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            current_narrative = json.loads(content)
            
            # Validate structure
            required_keys = ["overall_story", "emotional_arc", "scene_connections", "visual_progression", 
                           "product_reveal_strategy", "brand_narrative", "scene_durations"]
            for key in required_keys:
                if key not in current_narrative:
                    raise ValueError(f"Missing required key in narrative: {key}")
            
            # Validate and adjust scene durations to sum to total_duration
            scene_durations = current_narrative.get("scene_durations", {})
            total_assigned = sum(scene_durations.get(f"scene_{i}", 0) for i in range(1, num_scenes + 1))
            if total_assigned != total_duration:
                logger.warning(f"Scene durations sum to {total_assigned}s, expected {total_duration}s. Adjusting...")
                # Adjust durations proportionally
                if total_assigned > 0:
                    scale_factor = total_duration / total_assigned
                    for i in range(1, num_scenes + 1):
                        scene_key = f"scene_{i}"
                        if scene_key in scene_durations:
                            scene_durations[scene_key] = round(scene_durations[scene_key] * scale_factor)
                    # Ensure exact sum by adjusting last scene
                    current_sum = sum(scene_durations.get(f"scene_{i}", 0) for i in range(1, num_scenes + 1))
                    if current_sum != total_duration:
                        last_scene_key = f"scene_{num_scenes}"
                        scene_durations[last_scene_key] = scene_durations.get(last_scene_key, 0) + (total_duration - current_sum)
                else:
                    # If no durations provided, distribute evenly
                    base_duration = total_duration // num_scenes
                    remainder = total_duration % num_scenes
                    for i in range(1, num_scenes + 1):
                        scene_durations[f"scene_{i}"] = base_duration + (1 if i <= remainder else 0)
                current_narrative["scene_durations"] = scene_durations
            
        except Exception as e:
            logger.error(f"Creative Director narrative generation failed: {e}")
            raise RuntimeError(f"Narrative generation failed: {e}")
        
        if trace_dir:
            (trace_dir / f"narrative_iteration_{iteration}_agent1.txt").write_text(
                json.dumps(current_narrative, indent=2), encoding="utf-8"
            )
        
        # Agent 2: Editor - Critique & Score
        logger.info("Agent 2 (Editor): Critiquing unified narrative...")
        try:
            evaluation_prompt = f"""Evaluate this unified narrative document:

{json.dumps(current_narrative, indent=2)}

Score on all dimensions and provide specific feedback."""
            
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": NARRATIVE_EDITOR_SYSTEM_PROMPT},
                    {"role": "user", "content": evaluation_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            critique_result = json.loads(content)
            
            # Validate structure
            if "scores" not in critique_result or "critique" not in critique_result or "improvements" not in critique_result:
                raise ValueError("Invalid critique response structure")
            
            # Calculate overall score if not provided
            if "overall" not in critique_result["scores"]:
                scores = critique_result["scores"]
                critique_result["scores"]["overall"] = (
                    scores.get("narrative_coherence", 0) * 0.20 +
                    scores.get("emotional_arc", 0) * 0.20 +
                    scores.get("scene_connections", 0) * 0.15 +
                    scores.get("visual_progression", 0) * 0.15 +
                    scores.get("brand_integration", 0) * 0.15 +
                    scores.get("framework_alignment", 0) * 0.15
                )
            
        except Exception as e:
            logger.error(f"Editor critique failed: {e}")
            raise RuntimeError(f"Narrative critique failed: {e}")
        
        if trace_dir:
            critique_text = f"""SCORES:
{json.dumps(critique_result['scores'], indent=2)}

CRITIQUE:
{critique_result['critique']}

IMPROVEMENTS NEEDED:
{chr(10).join('- ' + imp for imp in critique_result['improvements'])}
"""
            (trace_dir / f"narrative_iteration_{iteration}_agent2.txt").write_text(
                critique_text, encoding="utf-8"
            )
        
        iteration_data = {
            "iteration": iteration,
            "narrative_json": current_narrative,
            "scores": critique_result["scores"],
            "critique": critique_result["critique"],
            "improvements": critique_result["improvements"],
            "timestamp": datetime.now().isoformat()
        }
        iteration_history.append(iteration_data)
        
        overall_score = critique_result["scores"]["overall"]
        logger.info(f"Narrative iteration {iteration} complete - Overall score: {overall_score:.1f}")
        
        # Early stopping: score threshold met
        if overall_score >= score_threshold:
            logger.info(f"Score threshold ({score_threshold}) reached, stopping early")
            break
        
        # Convergence check: improvement < 2 points
        if iteration > 1:
            prev_score = iteration_history[-2]["scores"]["overall"]
            improvement = overall_score - prev_score
            if improvement < 2.0:
                logger.info(f"Convergence detected (improvement: {improvement:.1f} points), stopping")
                break
    
    # Use final narrative
    final_narrative = iteration_history[-1]["narrative_json"] if iteration_history else current_narrative
    final_score = iteration_history[-1]["scores"] if iteration_history else {}
    
    # Convert to markdown
    narrative_md = _narrative_json_to_markdown(final_narrative)
    
    logger.info(f"\n=== Unified Narrative Generation Complete ===")
    logger.info(f"Final score: {final_score.get('overall', 0):.1f}/100")
    logger.info(f"Total iterations: {len(iteration_history)}")
    
    return {
        "narrative_json": final_narrative,
        "narrative_md": narrative_md,
        "iterations": iteration_history,
        "final_score": final_score
    }


async def _generate_high_level_story(
    original_prompt: str,
    reference_image_path: Path,
    visual_elements: Dict[str, Any],
    total_duration: int = 15,
    story_type: str = "sensory_experience",
    trace_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate high-level story using Story Teller persona agent.
    
    Args:
        original_prompt: Original prompt from Story 8.1
        reference_image_path: Path to reference image
        visual_elements: Extracted visual elements from reference image
        total_duration: Total duration of the final video in seconds (15-60)
        story_type: Story type to use (transformation, reveal_discovery, journey_path, problem_solution, sensory_experience, symbolic_metaphor, micro_drama, montage)
        trace_dir: Optional directory to save trace files
    
    Returns:
        Dict with high-level story structure
    """
    logger.info(f"Story Teller: Generating high-level story for {total_duration}s video using '{story_type}' story type...")
    
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Get story type definition
    story_type_info = STORY_TYPE_DEFINITIONS.get(story_type, STORY_TYPE_DEFINITIONS["sensory_experience"])
    
    # Build visual context
    visual_context = f"""
VISUAL ELEMENTS FROM REFERENCE IMAGE:
- Brand Identity: {json.dumps(visual_elements.get('brand_identity', {}), indent=2)}
- Product Details: {json.dumps(visual_elements.get('product_details', {}), indent=2)}
- Color Palette: {json.dumps(visual_elements.get('color_palette', {}), indent=2)}
- Style Aesthetic: {json.dumps(visual_elements.get('style_aesthetic', {}), indent=2)}
"""
    
    # Build story type context
    story_type_context = f"""
STORY TYPE: {story_type_info['name']}

STORY TYPE FOCUS: {story_type_info['focus']}

BEST FOR: {story_type_info['best_for']}

VISUAL PATTERN: {story_type_info['visual_pattern']}

WHY DIRECTORS USE THIS TYPE: {story_type_info['why_use']}

EXAMPLE APPLICATIONS: {story_type_info['examples']}
"""
    
    if 'metaphors' in story_type_info:
        story_type_context += f"\nSYMBOLIC METAPHORS: {story_type_info['metaphors']}\n"
    
    # Read and encode image for vision
    with open(reference_image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode("utf-8")
    
    try:
        user_prompt = f"""Create a high-level, emotionally compelling story for this perfume advertisement:

ORIGINAL PROMPT: {original_prompt}

{visual_context}

{story_type_context}

TOTAL VIDEO DURATION: {total_duration} seconds

**CRITICAL INSTRUCTIONS**:
1. You MUST follow the "{story_type_info['name']}" story type structure and visual patterns provided above
2. Adapt this story type creatively to perfume advertisements - don't just follow a generic formula
3. Use the story type's visual pattern ({story_type_info['visual_pattern']}) as the foundation for your narrative arc
4. The story should be paced appropriately for a {total_duration}-second video - consider how the narrative arc, emotional journey, and story beats should unfold within this timeframe
5. Create a rich, evocative story that captures the essence of what makes this perfume special
6. The story should establish the emotional journey, core message, mood, and aspirational qualities that will guide the detailed narrative structure
7. **BE CREATIVE**: Don't just follow one formula - use the story type as inspiration to create a unique, compelling narrative that stands out

Analyze the prompt and reference image to understand the creative vision, then craft your story following the {story_type_info['name']} structure."""
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Use gpt-4o for vision capability
            messages=[
                {
                    "role": "system",
                    "content": STORY_TELLER_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.8,  # Higher temperature for more creative storytelling
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        high_level_story = json.loads(content)
        
        # Validate structure
        required_keys = ["high_level_story", "emotional_journey", "core_message", 
                        "mood_and_atmosphere", "aspirational_qualities", 
                        "visual_storytelling_potential", "thematic_elements", "story_structure"]
        for key in required_keys:
            if key not in high_level_story:
                raise ValueError(f"Missing required key in high-level story: {key}")
        
        if trace_dir:
            (trace_dir / "00_high_level_story.json").write_text(
                json.dumps(high_level_story, indent=2), encoding="utf-8"
            )
            logger.info(f"High-level story saved to {trace_dir / '00_high_level_story.json'}")
        
        logger.info("Story Teller: High-level story generated successfully")
        return high_level_story
        
    except Exception as e:
        logger.error(f"Story Teller story generation failed: {e}")
        raise RuntimeError(f"High-level story generation failed: {e}")


async def _extract_visual_elements(image_path: Path) -> Dict[str, Any]:
    """Extract visual elements from reference image using GPT-4 Vision."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    # Read and encode image
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode("utf-8")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Updated: gpt-4-vision-preview is deprecated, using gpt-4o for vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_EXTRACTION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate structure
        required_keys = ["brand_identity", "product_details", "color_palette", "style_aesthetic", "composition_elements"]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing required key in visual elements: {key}")
        
        return result
        
    except Exception as e:
        logger.error(f"Vision API extraction failed: {e}")
        raise RuntimeError(f"Visual element extraction failed: {e}")


async def _cinematic_creative_enhance(
    original_prompt: str,
    scene_number: int,
    scene_type: str,
    product_visibility: str,
    visual_elements: Dict[str, Any],
    previous_feedback: Optional[Dict[str, Any]],
    unified_narrative: Optional[Dict[str, Any]] = None,
    high_level_story: Optional[Dict[str, Any]] = None,
    model: str = "gpt-4-turbo"
) -> Dict[str, str]:
    """Agent 1: Cinematic Creative Director generates start/end prompts and motion description."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Build product consistency section with exact details
    product_details = visual_elements.get('product_details', {})
    exact_bottle = product_details.get('exact_bottle_description', product_details.get('bottle_shape', 'N/A'))
    bottle_text = product_details.get('bottle_text', 'N/A')
    label_design = product_details.get('label_design', 'N/A')
    cap_design = product_details.get('cap_design', 'N/A')
    
    product_consistency = f"""
CRITICAL PRODUCT CONSISTENCY REQUIREMENT:
The perfume bottle MUST be IDENTICAL across ALL frames. Use this EXACT description:
- Bottle Design: {exact_bottle}
- Bottle Text/Labels: {bottle_text if bottle_text != 'N/A' else 'No visible text'}
- Label Design: {label_design if label_design != 'N/A' else 'Standard label'}
- Cap Design: {cap_design if cap_design != 'N/A' else 'Standard cap'}
- Materials: {product_details.get('materials', 'N/A')}
- Distinctive Elements: {product_details.get('distinctive_elements', 'N/A')}

MANDATORY: Every frame must show the EXACT same bottle design, including:
- Same bottle shape and proportions
- Same text/labels (if visible) in the same position
- Same cap design and style
- Same materials and finish
- Same distinctive design elements

The bottle is the anchor element - it must remain visually identical while only the scene context, lighting, camera angle, bottle position in frame, and composition change.

CRITICAL: The bottle can appear in DIFFERENT positions in the frame and from DIFFERENT camera angles - this is MANDATORY for creating dynamic, non-static videos. The bottle design stays the same, but its position and viewing angle MUST change dramatically between start and end frames."""
    
    # Build context for the agent
    visual_context = f"""
VISUAL ELEMENTS FROM REFERENCE IMAGE:
- Brand Colors: {', '.join(visual_elements.get('brand_identity', {}).get('brand_colors', []))}
- Bottle Shape: {visual_elements.get('product_details', {}).get('bottle_shape', 'N/A')}
- Color Palette: {visual_elements.get('color_palette', {}).get('scheme', 'N/A')}
- Visual Style: {visual_elements.get('style_aesthetic', {}).get('visual_style', 'N/A')}
- Mood: {visual_elements.get('style_aesthetic', {}).get('mood', 'N/A')}

{product_consistency}
"""
    
    scene_context = f"""
SCENE CONTEXT:
- Scene Number: {scene_number}
- Scene Type: {scene_type}
- Product Visibility: {product_visibility}
- Emotional Arc: {SENSORY_JOURNEY_SCENES.get(scene_number, {}).get('emotional_arc', 'N/A')}
"""
    
    feedback_context = ""
    if previous_feedback:
        feedback_context = f"""
PREVIOUS FEEDBACK:
- Critique: {previous_feedback.get('critique', 'N/A')}
- Improvements Needed: {', '.join(previous_feedback.get('improvements', []))}
"""
    
    narrative_context = ""
    if unified_narrative or high_level_story:
        # Extract relevant narrative information for this scene
        overall_story = unified_narrative.get("overall_story", {}) if unified_narrative else {}
        core_idea = overall_story.get("core_message", overall_story.get("narrative", ""))
        if not core_idea and high_level_story:
            core_idea = high_level_story.get("core_message", "")
        
        # Get FULL story narratives (no truncation)
        full_overall_story = overall_story.get("narrative", "")
        high_level_story_text = high_level_story.get("high_level_story", "") if high_level_story else ""
        emotional_journey = high_level_story.get("emotional_journey", "") if high_level_story else ""
        visual_storytelling = high_level_story.get("visual_storytelling_potential", "") if high_level_story else ""
        thematic_elements = high_level_story.get("thematic_elements", []) if high_level_story else []
        story_structure = high_level_story.get("story_structure", "") if high_level_story else ""
        
        emotional_arc = unified_narrative.get("emotional_arc", {}) if unified_narrative else {}
        scene_key = f"scene_{scene_number}"
        scene_narrative = emotional_arc.get(scene_key, {})
        motion_strategy = unified_narrative.get("motion_and_cinematography_strategy", {}) if unified_narrative else {}
        scene_motion = motion_strategy.get(scene_key, {})
        
        narrative_context = f"""
**HIGH-LEVEL STORY** (CRITICAL - incorporate concrete story elements from this):
{high_level_story_text if high_level_story_text else 'N/A'}

**EMOTIONAL JOURNEY** (from high-level story):
{emotional_journey if emotional_journey else 'N/A'}

**VISUAL STORYTELLING POTENTIAL** (from high-level story):
{visual_storytelling if visual_storytelling else 'N/A'}

**THEMATIC ELEMENTS** (from high-level story):
{', '.join(thematic_elements) if thematic_elements else 'N/A'}

**STORY STRUCTURE** (from high-level story):
{story_structure if story_structure else 'N/A'}

**UNIFIED NARRATIVE CONTEXT** (use this to guide your prompts):
- **CORE IDEA** (Anchor everything on this): {core_idea if core_idea else 'N/A'}
- **FULL Overall Story** (from unified narrative): {full_overall_story if full_overall_story else 'N/A'}
- Scene Emotional State: {scene_narrative.get('emotional_state', 'N/A')}
- Scene Visual Mood: {scene_narrative.get('visual_mood', 'N/A')}
- Scene Narrative Purpose: {scene_narrative.get('narrative_purpose', 'N/A')}
- Visual Progression: {unified_narrative.get('visual_progression', {}).get(scene_key, 'N/A') if unified_narrative else 'N/A'}
- Product Reveal Strategy: {unified_narrative.get('product_reveal_strategy', {}).get(scene_key, 'N/A') if unified_narrative else 'N/A'}
- Brand Narrative: {unified_narrative.get('brand_narrative', {}).get('brand_message', 'N/A') if unified_narrative else 'N/A'}
- Motion Strategy: {scene_motion.get('camera_movements', 'N/A')}
- Environmental Dynamics: {scene_motion.get('environmental_dynamics', 'N/A')}
- Lighting Transformations: {scene_motion.get('lighting_transformations', 'N/A')}
- Overall Motion Approach: {motion_strategy.get('overall_approach', 'N/A')}

**CRITICAL INSTRUCTIONS**: 
- **MANDATORY**: Incorporate concrete story elements from the HIGH-LEVEL STORY above (characters, actions, specific moments, narrative details)
- If the high-level story mentions a character (e.g., "a woman steps into a garden"), your prompts MUST include that character and their actions
- If the high-level story describes specific moments or actions, translate those into visual shots
- Anchor every shot on the CORE IDEA - every element must reinforce this single idea
- Use the motion strategy to create dynamic, creative motion descriptions that avoid formulaic language
- Create maximum visual distinction between start and end frames
- Apply AD DIRECTOR PRINCIPLES to transform the story into specific, purposeful shots
- The high-level story provides the CONCRETE narrative - don't abstract it away, translate it visually
"""
    
    user_prompt = f"""Create storyboard prompts for this scene:

{scene_context}

{visual_context}

{narrative_context}

ORIGINAL PROMPT: {original_prompt}

{feedback_context}

Generate start frame prompt, end frame prompt, and motion description that:
1. **MANDATORY**: Use the EXACT bottle design described in the Product Consistency Requirement above - the bottle must be identical in every frame
2. **CRITICAL - INCORPORATE CONCRETE STORY ELEMENTS**: 
   - If the HIGH-LEVEL STORY mentions characters (e.g., "a woman", "a person"), include them in your prompts
   - If the HIGH-LEVEL STORY describes specific actions or moments, translate those into visual shots
   - Don't abstract away the story - preserve the concrete narrative elements (who, what, where, when)
   - The story provides the narrative - your job is to translate it visually, not replace it with abstract descriptions
3. Maintain visual coherence with the reference image (use brand colors, bottle shape, style)
4. **APPLY AD DIRECTOR PRINCIPLES**:
   - Identify the core idea from the story and ensure this shot reinforces it
   - Assign ONE clear purpose to this shot (set mood, build anticipation, show detail, create transformation, deliver reveal)
   - Lead with emotion (especially Scene 1), build connection (Scene 2), deliver product payoff (Scene 3)
   - Plan pattern breaks: Include angle shifts, lighting changes, or movement variations to maintain attention
   - Maintain hyper-clear framing: Shot must be instantly understandable in one second
   - Use purposeful motion: All movement must be motivated and meaningful
   - If Scene 3 end frame: Create iconic hero shot (clean, centered, premium, well-lit, highly legible, emotionally resonant)
4. **CRITICAL - MAXIMUM VISUAL DISTINCTION** (MANDATORY - this prevents static videos):
   - **PRIMARY - CAMERA ANGLE MUST CHANGE DRAMATICALLY**:
     * Start frame: Specify ONE specific camera angle (e.g., "low angle worm's eye view from ground level", "side profile shot from left", "overhead bird's eye view", "Dutch angle tilted 45 degrees", "extreme close-up of cap from front", "backlit silhouette from behind")
     * End frame: Specify a COMPLETELY DIFFERENT camera angle (e.g., "high angle bird's eye view from above", "3/4 front-facing view", "eye-level shot", "level horizon shot", "wide shot from side showing full bottle", "front-lit hero shot")
     * Examples of dramatic angle changes: low angle → high angle, side view → front view, overhead → eye-level, close-up → wide shot, Dutch angle → level, backlit → front-lit
   - **SECONDARY - BOTTLE POSITION IN FRAME MUST CHANGE**:
     * Start frame: Specify bottle position (e.g., "bottle on left side of frame", "bottle centered in foreground", "bottle at bottom of frame", "bottle in upper right corner")
     * End frame: Specify DIFFERENT position (e.g., "bottle on right side of frame", "bottle in background off-center", "bottle at top of frame", "bottle in lower left corner")
   - **TERTIARY - Other distinctions**:
     * Dramatic camera movements (orbital rotation, dramatic push-in/pull-out, Dutch angle shifts, parallax movements)
     * Lighting transformations (dawn to golden hour, shadow to spotlight, cool to warm tones)
     * Composition shifts (wide to extreme close-up, low angle to high angle, centered to off-center)
     * Environmental changes (fog clearing, leaves moving, water droplets forming, light rays shifting)
     * Depth of field changes (deep focus to shallow, background blur transitions)
4. Follow the Sensory Journey framework for {scene_type}
5. Control product visibility: {product_visibility} (but the bottle design itself must remain identical)
6. Let abstract style emerge naturally from the visual elements
7. Create compelling, DYNAMIC visual transitions with creative motion
8. Align with the unified narrative context provided above
9. **AVOID FORMULAIC LANGUAGE**: Do NOT use "slowly", "gradually", "subtly", "gently" in motion descriptions - use dynamic, creative terms instead
10. **MOTION MUST BE CREATIVE**: Use terms like "orbital rotation", "dramatic push-in", "parallax dolly", "Dutch angle transition", "rack focus pull", "crane movement", "leaves rustle and shift", "light rays pierce through", "fog dissipates", "transforms from X to Y", "evolves into", "with kinetic energy", "in a fluid arc", "with cinematic sweep"

CRITICAL: The bottle design (shape, text, labels, cap) must be EXACTLY the same in every frame. However, the bottle CAN and MUST appear in DIFFERENT positions in the frame and from DIFFERENT camera angles to create dynamic, non-static videos.

CRITICAL: Start and end frames MUST be DRAMATICALLY different - if they're too similar (same camera angle, same bottle position), the resulting video will be static and boring. **MANDATORY REQUIREMENTS**:
- Camera angle MUST change dramatically (e.g., low angle to high angle, side view to front view, overhead to eye-level)
- Bottle position in frame MUST change (e.g., left to right, foreground to background, centered to off-center)
- Shot size MUST change significantly (e.g., wide to extreme close-up, or vice versa)
- If these requirements are not met, the frames are TOO SIMILAR and will create static videos

Return as JSON with start_frame_prompt, end_frame_prompt, and motion_description."""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": CINEMATIC_CREATIVE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate structure
        required_keys = ["start_frame_prompt", "end_frame_prompt", "motion_description"]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing required key in creative response: {key}")
        
        return result
        
    except Exception as e:
        logger.error(f"Cinematic Creative enhancement failed: {e}")
        raise


async def _storyboard_engineer_critique(
    start_prompt: str,
    end_prompt: str,
    motion_description: str,
    scene_number: int,
    scene_type: str,
    product_visibility: str,
    visual_elements: Dict[str, Any],
    model: str = "gpt-4-turbo"
) -> Dict[str, Any]:
    """Agent 2: Storyboard Prompt Engineer critiques and scores the prompts."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Build product consistency context for critique
    product_details = visual_elements.get('product_details', {})
    exact_bottle = product_details.get('exact_bottle_description', product_details.get('bottle_shape', 'N/A'))
    bottle_text = product_details.get('bottle_text', 'N/A')
    label_design = product_details.get('label_design', 'N/A')
    cap_design = product_details.get('cap_design', 'N/A')
    
    product_consistency_check = f"""
CRITICAL PRODUCT CONSISTENCY REQUIREMENT:
The bottle MUST be IDENTICAL in both start and end frames:
- Exact Bottle Design: {exact_bottle}
- Bottle Text/Labels: {bottle_text if bottle_text != 'N/A' else 'No visible text'}
- Label Design: {label_design if label_design != 'N/A' else 'Standard label'}
- Cap Design: {cap_design if cap_design != 'N/A' else 'Standard cap'}

Check that both prompts reference the EXACT same bottle design, text, and labels."""
    
    # Build context
    visual_context = f"""
REFERENCE VISUAL ELEMENTS:
- Brand Colors: {', '.join(visual_elements.get('brand_identity', {}).get('brand_colors', []))}
- Bottle Shape: {visual_elements.get('product_details', {}).get('bottle_shape', 'N/A')}
- Visual Style: {visual_elements.get('style_aesthetic', {}).get('visual_style', 'N/A')}

{product_consistency_check}
"""
    
    scene_context = f"""
SCENE REQUIREMENTS:
- Scene Number: {scene_number}
- Scene Type: {scene_type}
- Expected Product Visibility: {product_visibility}
"""
    
    evaluation_prompt = f"""Evaluate these storyboard prompts:

{scene_context}

{visual_context}

START FRAME PROMPT:
{start_prompt}

END FRAME PROMPT:
{end_prompt}

MOTION DESCRIPTION:
{motion_description}

Score on all dimensions and provide specific feedback."""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": STORYBOARD_ENGINEER_SYSTEM_PROMPT},
                {"role": "user", "content": evaluation_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent scoring
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate structure
        if "scores" not in result or "critique" not in result or "improvements" not in result:
            raise ValueError("Invalid critique response structure")
        
        # Calculate overall score if not provided
        if "overall" not in result["scores"]:
            scores = result["scores"]
            result["scores"]["overall"] = (
                scores.get("completeness", 0) * 0.15 +
                scores.get("creative_distinction", 0) * 0.15 +
                scores.get("visual_coherence", 0) * 0.12 +
                scores.get("product_consistency", 0) * 0.20 +  # Higher weight for product consistency
                scores.get("framework_alignment", 0) * 0.12 +
                scores.get("progressive_reveal", 0) * 0.08 +
                scores.get("abstract_style", 0) * 0.10 +
                scores.get("motion_quality", 0) * 0.08
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Storyboard Engineer critique failed: {e}")
        raise

