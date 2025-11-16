"""
Text overlay service for adding styled text overlays to video clips.
"""
import logging
import platform
from pathlib import Path
from typing import Optional

from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.FadeIn import FadeIn
from moviepy.video.fx.FadeOut import FadeOut

from app.schemas.generation import TextOverlay

logger = logging.getLogger(__name__)


def add_text_overlay(
    video_path: str,
    text_overlay: TextOverlay,
    output_path: str
) -> str:
    """
    Add styled text overlay to a video clip.
    
    Args:
        video_path: Path to input video clip
        text_overlay: TextOverlay specification with text, position, style, animation
        output_path: Path to save output video with overlay
    
    Returns:
        str: Path to output video file
    
    Raises:
        RuntimeError: If overlay addition fails
    """
    logger.info(f"Adding text overlay to video: {video_path}")
    logger.debug(
        f"Text: '{text_overlay.text}', Position: {text_overlay.position}, "
        f"Color: {text_overlay.color}, Animation: {text_overlay.animation}"
    )
    
    try:
        # Load video clip
        video = VideoFileClip(video_path)
        video_duration = video.duration
        
        # Create text clip
        text_clip = _create_text_clip(
            text_overlay=text_overlay,
            video_size=video.size,
            duration=video_duration
        )
        
        # Apply animation
        text_clip = _apply_animation(text_clip, text_overlay.animation)
        
        # Position text clip
        positioned_text = _position_text_clip(
            text_clip=text_clip,
            position=text_overlay.position,
            video_size=video.size
        )
        
        # Composite text onto video
        final_video = CompositeVideoClip([video, positioned_text])
        
        # Write output video
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Writing output video to {output_path}")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=video.fps,
            preset='medium',
            logger=None  # Suppress MoviePy progress logs
        )
        
        # Clean up
        video.close()
        text_clip.close()
        positioned_text.close()
        final_video.close()
        
        logger.info(f"Text overlay added successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to add text overlay: {e}", exc_info=True)
        raise RuntimeError(f"Text overlay addition failed: {e}")


def _create_text_clip(
    text_overlay: TextOverlay,
    video_size: tuple,
    duration: float
) -> TextClip:
    """
    Create a TextClip with brand styling.
    
    Args:
        text_overlay: TextOverlay specification
        video_size: Video dimensions (width, height)
        duration: Duration of text clip in seconds
    
    Returns:
        TextClip: Styled text clip
    """
    font_path = _get_font_path()
    
    # Calculate text width (90% of video width, must be integer)
    text_width = int(video_size[0] * 0.9)
    
    # Create text clip
    text_clip = TextClip(
        text=text_overlay.text,
        font=font_path,
        font_size=text_overlay.font_size,
        color=text_overlay.color,
        size=(text_width, None),  # 90% of video width
        method='caption',  # Auto-wrap text
        text_align='center'
    ).with_duration(duration).with_position((0, 0))  # Position at origin within composite
    
    # Add text shadow for readability
    # Create shadow clip (slightly offset, darker color)
    shadow_color = _get_shadow_color(text_overlay.color)
    shadow_clip = TextClip(
        text=text_overlay.text,
        font=font_path,
        font_size=text_overlay.font_size,
        color=shadow_color,
        size=(text_width, None),
        method='caption',
        text_align='center'
    ).with_duration(duration).with_position((2, 2))  # Slight offset for shadow
    
    # Composite shadow and text (shadow behind text)
    text_with_shadow = CompositeVideoClip([shadow_clip, text_clip])
    
    return text_with_shadow


def _get_font_path() -> Optional[str]:
    """
    Locate a system font to ensure consistent rendering across platforms.
    
    Returns:
        Optional[str]: Path to a bold font file if available, None otherwise.
    """
    system = platform.system()
    
    font_candidates = []
    if system == "Windows":
        font_candidates = [
            Path("C:/Windows/Fonts/arialbd.ttf"),
            Path("C:/Windows/Fonts/ARIALBD.TTF"),
            Path("C:/Windows/Fonts/Arial Bold.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ]
    elif system == "Darwin":  # macOS
        font_candidates = [
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Helvetica.ttc"),
            Path("/Library/Fonts/Arial Bold.ttf"),
        ]
    else:  # Linux and others
        font_candidates = [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
        ]
    
    for font_path in font_candidates:
        if font_path.exists():
            return str(font_path)
    
    logger.warning(
        "No bold system font found in known locations. Falling back to MoviePy default font."
    )
    return None


def _get_shadow_color(text_color: str) -> str:
    """
    Get shadow color for text (dark shadow behind light text).
    
    Args:
        text_color: Text color (hex code)
    
    Returns:
        str: Shadow color (hex code)
    """
    # Simple heuristic: if text is light, use dark shadow; if dark, use light shadow
    # For MVP, default to black shadow with opacity
    # MoviePy doesn't support opacity directly, so we'll use a dark gray
    return "black"


def _apply_animation(text_clip: TextClip, animation: str) -> TextClip:
    """
    Apply animation to text clip.
    
    **MVP Limitation:** For MVP, `slide_up` and `scale` animations are simplified
    to `fade_in` for faster implementation. Full slide and scale animations can be
    added in future iterations using MoviePy's position and resize functions with
    time-based lambda functions.
    
    Args:
        text_clip: Text clip to animate
        animation: Animation type (fade_in, slide_up, scale, none)
    
    Returns:
        TextClip: Animated text clip
    """
    if animation == "fade_in":
        # Fade in over first 0.5 seconds
        return FadeIn(duration=0.5).apply(text_clip)
    
    elif animation == "slide_up":
        # MVP LIMITATION: slide_up is simplified to fade_in
        # Full implementation would use: text_clip.set_position(lambda t: ('center', y_start - t * speed))
        # where y_start is off-screen bottom and speed calculates movement over duration
        # For MVP, we use fade_in as a simplified version
        return FadeIn(duration=0.5).apply(text_clip)
    
    elif animation == "scale":
        # MVP LIMITATION: scale is simplified to fade_in
        # Full implementation would use: text_clip.resize(lambda t: start_scale + (1 - start_scale) * (t / duration))
        # where start_scale is 0.5 and duration is 0.5 seconds
        # For MVP, we use fade_in as a simplified version
        return FadeIn(duration=0.5).apply(text_clip)
    
    else:
        # No animation
        return text_clip


def _position_text_clip(
    text_clip: TextClip,
    position: str,
    video_size: tuple
) -> TextClip:
    """
    Position text clip based on specification (top, center, or bottom).
    
    Args:
        text_clip: Text clip to position
        position: Position specification (top, center, bottom)
        video_size: Video dimensions (width, height)
    
    Returns:
        TextClip: Positioned text clip
    """
    width, height = video_size
    text_height = getattr(text_clip, "h", None)
    
    # Ensure text_height is usable (handle CompositeVideoClip/mocks)
    invalid_height = False
    if text_height is None:
        invalid_height = True
    else:
        try:
            invalid_height = text_height <= 0
        except TypeError:
            invalid_height = True
    
    if invalid_height:
        logger.debug(
            f"Text height not available ({text_height}), falling back to 10% of video height"
        )
        text_height = max(int(height * 0.1), 10)
    
    if position == "top":
        # Position at top with margin
        y_pos = int(height * 0.1)  # 10% from top
        return text_clip.with_position(('center', y_pos))
    
    elif position == "center":
        # Center vertically
        y_pos = int((height - text_height) / 2)
        return text_clip.with_position(('center', y_pos))
    
    elif position == "bottom":
        # Position at bottom with margin - ensure text is fully visible
        # Calculate margin (10% of video height, minimum 20 pixels)
        margin = max(int(height * 0.1), 20)
        # Position so bottom of text is at (height - margin)
        # y_pos is the top edge of the text, so: y_pos + text_height = height - margin
        y_pos = int(height - text_height - margin)
        # Safety check: ensure text doesn't go off-screen
        if y_pos < 0:
            logger.warning(f"Text height ({text_height}) exceeds available space, positioning at minimum margin")
            y_pos = max(0, int(height - text_height - 10))  # Minimum 10px margin
        return text_clip.with_position(('center', y_pos))
    
    else:
        # Default to center
        logger.warning(f"Unknown position '{position}', defaulting to center")
        y_pos = int((height - text_height) / 2)
        return text_clip.with_position(('center', y_pos))


def add_overlays_to_clips(
    clip_paths: list[str],
    scene_plan: "ScenePlan",
    output_dir: str
) -> list[str]:
    """
    Add text overlays to multiple video clips.
    
    Args:
        clip_paths: List of input video clip paths
        scene_plan: ScenePlan with text overlay specifications
        output_dir: Directory to save output clips
    
    Returns:
        list[str]: List of output video clip paths with overlays
    
    Raises:
        RuntimeError: If overlay addition fails
    """
    if len(clip_paths) != len(scene_plan.scenes):
        raise ValueError(
            f"Mismatch: {len(clip_paths)} clips but {len(scene_plan.scenes)} scenes"
        )
    
    logger.info(f"Adding text overlays to {len(clip_paths)} video clips")
    
    output_paths = []
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    for i, (clip_path, scene) in enumerate(zip(clip_paths, scene_plan.scenes), start=1):
        try:
            # Generate output path
            output_filename = f"overlay_{i}.mp4"
            output_path = output_dir_path / output_filename
            
            # Add overlay
            result_path = add_text_overlay(
                video_path=clip_path,
                text_overlay=scene.text_overlay,
                output_path=str(output_path)
            )
            
            output_paths.append(result_path)
            logger.info(f"Overlay added to clip {i}/{len(clip_paths)}")
            
        except Exception as e:
            logger.error(f"Failed to add overlay to clip {i}: {e}")
            raise RuntimeError(f"Text overlay addition failed for clip {i}: {e}")
    
    logger.info(f"All {len(output_paths)} text overlays added successfully")
    return output_paths

