"""
Text converters for the 3-stage pipeline (Option C).

- Stage 1 → Stage 3: full blueprint text
- Stage 2 → Stage 3: cinematic physics text
- Stage 1 → Stage 2: compact summary (moods + lightings + style_tone)
"""

from app.services.pipeline.llm_schemas import Stage1Blueprint, ScentProfile


def stage1_to_text(stage1: Stage1Blueprint) -> str:
    """
    Convert Stage 1 blueprint into a readable plaintext format
    (used by Stage 3 Scene Assembler).
    """
    lines = ["STAGE 1 BLUEPRINT"]

    for scene in stage1.scenes:
        lines.append(f"\nScene {scene.scene_number}: {scene.stage}")
        lines.append(f"visual: {scene.scene_description.visual}")
        lines.append(f"action: {scene.scene_description.action}")
        lines.append(f"camera: {scene.scene_description.camera}")
        lines.append(f"lighting: {scene.scene_description.lighting}")
        lines.append(f"mood: {scene.scene_description.mood}")
        lines.append(f"product_usage: {scene.scene_description.product_usage}")

    return "\n".join(lines)


def stage2_to_text(stage2: ScentProfile) -> str:
    """
    Convert Stage 2 scent profile into readable plaintext format
    (used by Stage 3 Scene Assembler).
    """
    return (
        "STAGE 2 CINEMATIC PROFILE\n"
        f"lighting_cues: {stage2.lighting_cues}\n"
        f"color_palette: {stage2.color_palette}\n"
        f"motion_physics: {stage2.motion_physics}\n"
        f"surface_textures: {stage2.surface_textures}\n"
        f"atmosphere_density: {stage2.atmosphere_density}\n"
        f"sound_motifs: {stage2.sound_motifs}\n"
        f"emotional_register: {stage2.emotional_register}\n"
    )


def stage1_to_stage2_summary(stage1: Stage1Blueprint) -> dict:
    """
    Extract ONLY the fields Stage 2 is allowed to use:

    - mood words from each scene
    - lighting fragments from each scene
    - global style_tone

    This keeps Stage 2 focused on emotional & lighting arcs,
    not specific environments or compositions.
    """
    moods = []
    lightings = []

    for scene in stage1.scenes:
        moods.append(scene.scene_description.mood)
        lightings.append(scene.scene_description.lighting)

    return {
        "moods": moods,
        "lightings": lightings,
        "style_tone": stage1.style_tone,
    }