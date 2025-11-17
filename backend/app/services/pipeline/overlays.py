"""
Text overlay service for adding styled text overlays to video clips.
"""
import logging
import os
import platform
import re
import tempfile
from pathlib import Path
from typing import Optional

from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
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
        
        # Position text clip (pass font_size for accurate descender margin calculation)
        positioned_text = _position_text_clip(
            text_clip=text_clip,
            position=text_overlay.position,
            video_size=video.size,
            font_size=text_overlay.font_size
        )
        
        # Composite text onto video
        final_video = CompositeVideoClip([video, positioned_text])
        
        # Set temp directory for MoviePy to use (ensures temp files are created in writable location)
        # Get original working directory BEFORE changing directories
        original_cwd = os.getcwd()
        
        # Convert output_path to absolute BEFORE changing directory
        if not Path(output_path).is_absolute():
            output_path_abs = str(Path(original_cwd) / output_path)
        else:
            output_path_abs = output_path
        output_path_abs = str(Path(output_path_abs).resolve())
        
        # Set temp directory
        temp_dir = os.environ.get('TMPDIR', '/tmp')
        temp_dir_path = Path(temp_dir)
        if not temp_dir_path.exists():
            temp_dir_path.mkdir(parents=True, exist_ok=True)
        # Set tempfile's tempdir to ensure MoviePy uses it
        tempfile.tempdir = str(temp_dir_path.absolute())
        # Also set TMPDIR in environment for FFmpeg and other subprocesses
        os.environ['TMPDIR'] = str(temp_dir_path.absolute())
        
        # Change to temp directory so MoviePy creates temp files there
        try:
            os.chdir(str(temp_dir_path.absolute()))
        except OSError as e:
            logger.warning(f"Could not change to temp directory {temp_dir_path}: {e}. Continuing with current directory.")
        
        # Write output video
        output_path_obj = Path(output_path_abs)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Writing output video to {output_path_abs}")
        try:
            final_video.write_videofile(
                output_path_abs,
                codec='libx264',
                audio_codec='aac',
                fps=video.fps,
                preset='medium',
                logger=None  # Suppress MoviePy progress logs
            )
        finally:
            # Restore original working directory
            try:
                os.chdir(original_cwd)
            except OSError:
                pass  # Ignore errors when restoring directory
        
        # Clean up
        video.close()
        text_clip.close()
        positioned_text.close()
        final_video.close()
        
        logger.info(f"Text overlay added successfully: {output_path_abs}")
        return output_path_abs
        
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
    
    # First, create a temporary clip to get the actual rendered height
    # This helps us calculate proper padding
    temp_clip = TextClip(
        text=text_overlay.text,
        font=font_path,
        font_size=text_overlay.font_size,
        color=text_overlay.color,
        size=(text_width, None),
        method='caption',
        text_align='center'
    )
    actual_text_height = temp_clip.h
    temp_clip.close()
    
    # Add padding to account for:
    # 1. Descenders (p, y, g, q, j) - can extend ~30% of font size below baseline
    # 2. Line spacing in multi-line text - extra space between lines
    # 3. Shadow offset - shadow extends 2px in each direction
    # 4. Safety margin - extra padding to prevent any clipping
    descender_padding = int(text_overlay.font_size * 0.3)  # 30% for descenders
    line_spacing_padding = int(text_overlay.font_size * 0.2)  # 20% for line spacing
    shadow_padding = 4  # 2px shadow offset on each side
    safety_margin = 10  # Extra safety margin
    
    # Calculate total padding (add to both top and bottom for safety)
    total_padding = descender_padding + line_spacing_padding + shadow_padding + safety_margin
    padded_height = actual_text_height + (total_padding * 2)  # Padding on top and bottom
    
    # Create text clip with explicit height that includes padding
    # Note: When using explicit height with method='caption', the text may not fill
    # the entire height, but the clip will be the specified size, preventing clipping
    text_clip = TextClip(
        text=text_overlay.text,
        font=font_path,
        font_size=text_overlay.font_size,
        color=text_overlay.color,
        size=(text_width, padded_height),  # Explicit height with padding
        method='caption',
        text_align='center'
    ).with_duration(duration).with_position((0, 0))  # Position at origin within composite
    
    # Add text shadow for readability
    shadow_color = _get_shadow_color(text_overlay.color)
    shadow_clip = TextClip(
        text=text_overlay.text,
        font=font_path,
        font_size=text_overlay.font_size,
        color=shadow_color,
        size=(text_width, padded_height),
        method='caption',
        text_align='center'
    ).with_duration(duration).with_position((2, 2))  # Shadow offset
    
    # Composite shadow and text
    # The composite will be sized to fit both clips including shadow offset
    # The padded height ensures descenders and multi-line text have room
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
    video_size: tuple,
    font_size: int = 48
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
        # Position at bottom with generous margin for descenders and multi-line text
        # Descenders (p, y, g, q, j) can extend ~30-40% of font size below baseline
        # TextClip's calculated height doesn't always account for descenders properly
        # Multi-line text needs extra vertical space
        # Use a large, safe margin to ensure nothing gets clipped
        descender_margin = int(font_size * 0.4)  # 40% of font size for descenders
        base_margin = max(int(height * 0.08), 25)  # Base margin from bottom
        multi_line_margin = 20  # Extra margin for multi-line text
        total_margin = base_margin + descender_margin + multi_line_margin
        
        # Position so the text clip (including descenders) stays well within bounds
        y_pos = int(height - text_height - total_margin)
        
        # Safety check: ensure text doesn't go off-screen
        if y_pos < 0:
            logger.warning(f"Text height ({text_height}) + margins exceed video height, using minimum safe margin")
            y_pos = max(0, int(height - text_height - 30))  # Minimum 30px margin
        
        logger.debug(f"Bottom positioning: text_height={text_height}, font_size={font_size}, margin={total_margin}, y_pos={y_pos}")
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
            # Skip overlay if text_overlay is None
            if scene.text_overlay is None:
                logger.info(f"No text overlay for clip {i}, skipping overlay addition")
                output_paths.append(clip_path)  # Use original clip without overlay
                continue
            
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


def extract_brand_name(prompt: str) -> Optional[str]:
    """
    Extract brand name from user prompt using common patterns.
    
    Args:
        prompt: User's prompt text
    
    Returns:
        Optional[str]: Extracted brand name or None if not found
    """
    if not prompt:
        return None
    
    # Common brand patterns (case-insensitive)
    # Look for capitalized words that might be brands
    # Common brand names
    common_brands = [
        "nike", "adidas", "puma", "reebok", "converse", "vans",
        "apple", "samsung", "google", "microsoft", "amazon",
        "coca-cola", "pepsi", "starbucks", "mcdonald's",
        "tesla", "ford", "toyota", "bmw", "mercedes",
        "gucci", "prada", "versace", "louis vuitton",
        "sony", "lg", "dell", "hp", "lenovo"
    ]
    
    prompt_lower = prompt.lower()
    
    # Check for common brands first
    for brand in common_brands:
        if brand in prompt_lower:
            # Return capitalized version
            return brand.capitalize()
    
    # Look for capitalized words that might be brand names
    # Pattern: word(s) that are capitalized and might be a brand
    words = re.findall(r'\b[A-Z][a-z]+\b', prompt)
    
    # Filter out common words that aren't brands
    common_words = {"The", "This", "That", "These", "Those", "A", "An", "And", "Or", "But", "For", "With", "From", "About"}
    potential_brands = [w for w in words if w not in common_words]
    
    # Return first potential brand, or None
    if potential_brands:
        return potential_brands[0]
    
    return None


def add_brand_overlay_to_final_video(
    video_path: str,
    brand_name: Optional[str],
    output_path: str,
    duration: float = 2.0
) -> str:
    """
    Add a brand name overlay at the end of the final video.
    
    Args:
        video_path: Path to input video file
        brand_name: Brand name to display (if None, will try to extract from prompt)
        output_path: Path to save output video with brand overlay
        duration: Duration of brand overlay in seconds (default: 2.0)
    
    Returns:
        str: Path to output video file
    
    Raises:
        RuntimeError: If overlay addition fails
    """
    logger.info(f"Adding brand overlay to final video: {video_path}")
    
    try:
        # Load video clip
        video = VideoFileClip(video_path)
        video_duration = video.duration
        
        # If no brand name provided, skip overlay
        if not brand_name:
            logger.info("No brand name provided, skipping brand overlay")
            video.close()
            return video_path
        
        # Create brand overlay text
        brand_text = brand_name.upper()  # Display brand in uppercase
        
        # Create text overlay for brand (appears at the end, centered)
        brand_overlay = TextOverlay(
            text=brand_text,
            position="center",  # Center position
            font_size=72,  # Larger font for brand
            color="#FFFFFF",  # White text
            animation="fade_in"  # Fade in animation
        )
        
        # Calculate when to show brand overlay (last N seconds)
        overlay_start_time = max(0, video_duration - duration)
        overlay_end_time = video_duration
        
        # Create text clip for brand
        text_clip = _create_text_clip(
            text_overlay=brand_overlay,
            video_size=video.size,
            duration=duration
        )
        
        # Apply fade in animation
        text_clip = _apply_animation(text_clip, brand_overlay.animation)
        
        # Get text dimensions for background sizing
        text_width = text_clip.w
        text_height = text_clip.h
        
        # Create background with padding (semi-transparent black)
        padding_x = int(text_width * 0.3)  # 30% padding on each side
        padding_y = int(text_height * 0.4)  # 40% padding on top/bottom
        background_width = int(text_width + (padding_x * 2))
        background_height = int(text_height + (padding_y * 2))
        
        # Create semi-transparent black background (RGBA: black with 80% opacity)
        # MoviePy ColorClip uses RGB, so we'll use a dark gray/black
        # For semi-transparency, we'll use a darker background that provides contrast
        background_color = (0, 0, 0)  # Black
        background_clip = ColorClip(
            size=(background_width, background_height),
            color=background_color,
            duration=duration
        ).with_opacity(0.7)  # 70% opacity for semi-transparency
        
        # Position text on background (centered)
        text_on_bg = text_clip.with_position(('center', 'center'))
        
        # Composite text on background
        brand_composite = CompositeVideoClip(
            [background_clip, text_on_bg],
            size=(background_width, background_height)
        )
        
        # Center the brand composite on the video
        video_width, video_height = video.size
        x_pos = (video_width - background_width) // 2
        y_pos = (video_height - background_height) // 2
        
        # Position the brand composite in the center of the video
        positioned_brand = brand_composite.with_position((x_pos, y_pos))
        
        # Set the brand composite to appear at the end of the video
        positioned_brand = positioned_brand.with_start(overlay_start_time)
        
        # Composite brand overlay onto video
        final_video = CompositeVideoClip([video, positioned_brand])
        
        # Set temp directory for MoviePy to use
        original_cwd = os.getcwd()
        
        # Convert output_path to absolute BEFORE changing directory
        if not Path(output_path).is_absolute():
            output_path_abs = str(Path(original_cwd) / output_path)
        else:
            output_path_abs = output_path
        output_path_abs = str(Path(output_path_abs).resolve())
        
        # Set temp directory
        temp_dir = os.environ.get('TMPDIR', '/tmp')
        temp_dir_path = Path(temp_dir)
        if not temp_dir_path.exists():
            temp_dir_path.mkdir(parents=True, exist_ok=True)
        tempfile.tempdir = str(temp_dir_path.absolute())
        os.environ['TMPDIR'] = str(temp_dir_path.absolute())
        
        # Change to temp directory
        try:
            os.chdir(str(temp_dir_path.absolute()))
        except OSError as e:
            logger.warning(f"Could not change to temp directory {temp_dir_path}: {e}. Continuing with current directory.")
        
        # Write output video
        output_path_obj = Path(output_path_abs)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Writing video with brand overlay to {output_path_abs}")
        try:
            final_video.write_videofile(
                output_path_abs,
                codec='libx264',
                audio_codec='aac',
                fps=24,
                preset='medium',
                logger=None  # Suppress MoviePy progress logs
            )
        finally:
            # Restore original working directory
            try:
                os.chdir(original_cwd)
            except OSError:
                pass
        
        # Clean up
        video.close()
        text_clip.close()
        background_clip.close()
        brand_composite.close()
        positioned_brand.close()
        final_video.close()
        
        logger.info(f"Brand overlay added successfully: {output_path_abs}")
        return output_path_abs
        
    except Exception as e:
        logger.error(f"Failed to add brand overlay: {e}", exc_info=True)
        raise RuntimeError(f"Brand overlay addition failed: {e}")

