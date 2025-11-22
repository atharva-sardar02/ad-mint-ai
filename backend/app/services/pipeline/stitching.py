"""
Video stitching service for concatenating video clips with transitions.
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip, ColorClip
from moviepy.video.fx.FadeIn import FadeIn
from moviepy.video.fx.FadeOut import FadeOut
import numpy as np

logger = logging.getLogger(__name__)


def _validate_clip(clip: VideoFileClip, clip_name: str = "clip") -> bool:
    """
    Validate that a clip has valid dimensions and can be processed.

    Args:
        clip: Video clip to validate
        clip_name: Name for logging purposes

    Returns:
        bool: True if clip is valid, False otherwise
    """
    try:
        if not clip or not hasattr(clip, 'size') or not clip.size:
            logger.warning(f"{clip_name} has no size")
            return False

        try:
            size = clip.size
            if not isinstance(size, (tuple, list)) or len(size) != 2:
                logger.warning(f"{clip_name} has invalid size format: {size}")
                return False
            w, h = size
        except (TypeError, ValueError) as e:
            logger.warning(f"{clip_name} size cannot be unpacked: {e}")
            return False

        if w <= 0 or h <= 0:
            logger.warning(f"{clip_name} has invalid dimensions: {w}x{h}")
            return False

        if not hasattr(clip, 'duration') or not clip.duration or clip.duration <= 0:
            logger.warning(f"{clip_name} has invalid duration: {clip.duration if hasattr(clip, 'duration') else 'N/A'}")
            return False

        # Try to read first and last frames to verify clip is readable
        try:
            first_frame = clip.get_frame(0)
            if first_frame is None or first_frame.shape[0] <= 0 or first_frame.shape[1] <= 0:
                logger.warning(f"{clip_name} first frame has invalid shape")
                return False

            # Check last frame (or near end to avoid corrupted tail)
            last_frame_time = max(0, clip.duration - 0.1)
            last_frame = clip.get_frame(last_frame_time)
            if last_frame is None or last_frame.shape[0] <= 0 or last_frame.shape[1] <= 0:
                logger.warning(f"{clip_name} last frame has invalid shape")
                return False

        except Exception as e:
            logger.warning(f"{clip_name} cannot read frames: {e}")
            return False

        return True
    except Exception as e:
        logger.warning(f"Error validating {clip_name}: {e}")
        return False
def _apply_crossfade_transition(clip1: VideoFileClip, clip2: VideoFileClip, duration: float = 0.5) -> tuple:
    """Apply crossfade transition between two clips."""
    # Apply fade out to end of clip1
    clip1_with_fade = FadeOut(duration=duration).apply(clip1)
    # Apply fade in to start of clip2
    clip2_with_fade = FadeIn(duration=duration).apply(clip2)
    return clip1_with_fade, clip2_with_fade


def _apply_wipe_transition(clip1: VideoFileClip, clip2: VideoFileClip, direction: str = "left", duration: float = 0.5) -> tuple:
    """
    Apply wipe transition between two clips using CompositeVideoClip for true overlapping effect.
    Direction can be: left, right, up, down
    
    Returns:
        Tuple of (shortened_clip1, transition_composite, shortened_clip2)
    """
    w, h = clip1.size
    
    # Extract the overlapping sections
    clip1_end = clip1.subclipped(max(0, clip1.duration - duration), clip1.duration)
    clip2_start = clip2.subclipped(0, min(duration, clip2.duration))
    
    # Create animated position for clip2 during transition
    if direction == "left":
        # Clip2 wipes in from right
        clip2_animated = clip2_start.with_position(lambda t: (w - (w * (t / duration)), 0))
    elif direction == "right":
        # Clip2 wipes in from left
        clip2_animated = clip2_start.with_position(lambda t: (-w + (w * (t / duration)), 0))
    elif direction == "up":
        # Clip2 wipes in from bottom
        clip2_animated = clip2_start.with_position(lambda t: (0, h - (h * (t / duration))))
    elif direction == "down":
        # Clip2 wipes in from top
        clip2_animated = clip2_start.with_position(lambda t: (0, -h + (h * (t / duration))))
    else:
        # Default to left
        clip2_animated = clip2_start.with_position(lambda t: (w - (w * (t / duration)), 0))
    
    # Create composite clip with clip1 as background and clip2 wiping over it
    transition_composite = CompositeVideoClip([
        clip1_end.with_position((0, 0)),
        clip2_animated
    ], size=(w, h)).with_duration(duration)
    
    # Return shortened clips and the transition composite
    clip1_shortened = clip1.subclipped(0, max(0, clip1.duration - duration)) if clip1.duration > duration else clip1
    clip2_shortened = clip2.subclipped(min(duration, clip2.duration), clip2.duration) if clip2.duration > duration else clip2
    
    return clip1_shortened, transition_composite, clip2_shortened


def _apply_flash_transition(clip1: VideoFileClip, clip2: VideoFileClip, duration: float = 0.1) -> tuple:
    """
    Apply flash/whiteout transition - quick, attention-grabbing.
    Creates a brief white flash between clips.
    
    Returns:
        Tuple of (shortened_clip1, flash_composite, shortened_clip2)
    """
    w, h = clip1.size
    
    # Very short duration for flash (0.1s default, split into fade in/out)
    flash_duration = duration
    
    # Extract the overlapping sections
    clip1_end = clip1.subclipped(max(0, clip1.duration - flash_duration/2), clip1.duration)
    clip2_start = clip2.subclipped(0, min(flash_duration/2, clip2.duration))
    
    # Create white flash
    white_flash = ColorClip(size=(w, h), color=(255, 255, 255), duration=flash_duration)
    
    # Fade out clip1 to white
    clip1_fade = FadeOut(duration=flash_duration/2).apply(clip1_end)
    
    # Fade in clip2 from white
    clip2_fade = FadeIn(duration=flash_duration/2).apply(clip2_start)
    
    # Create composite with flash
    transition_composite = CompositeVideoClip([
        white_flash.with_position((0, 0)),
        clip1_fade.with_position((0, 0)).with_start(0),
        clip2_fade.with_position((0, 0)).with_start(flash_duration/2)
    ], size=(w, h)).with_duration(flash_duration)
    
    # Return shortened clips and the transition composite
    clip1_shortened = clip1.subclipped(0, max(0, clip1.duration - flash_duration/2)) if clip1.duration > flash_duration/2 else clip1
    clip2_shortened = clip2.subclipped(min(flash_duration/2, clip2.duration), clip2.duration) if clip2.duration > flash_duration/2 else clip2
    
    return clip1_shortened, transition_composite, clip2_shortened


def _apply_zoom_blur_transition(clip1: VideoFileClip, clip2: VideoFileClip, duration: float = 0.3) -> tuple:
    """
    Apply zoom blur transition - emphasizes product reveals.
    Aggressive zoom with motion blur effect.
    
    Returns:
        Tuple of (shortened_clip1, transition_composite, shortened_clip2)
    """
    w, h = clip1.size
    
    # Extract the overlapping sections
    clip1_end = clip1.subclipped(max(0, clip1.duration - duration), clip1.duration)
    clip2_start = clip2.subclipped(0, min(duration, clip2.duration))
    
    # Aggressive zoom into clip1 (2x zoom)
    clip1_zoomed = clip1_end.resized(lambda t: 1 + (1.0 * (t / duration)))
    clip1_faded = FadeOut(duration=duration * 0.8).apply(clip1_zoomed)
    
    # Zoom out from clip2 (start at 1.5x, zoom to 1x)
    clip2_zoomed = clip2_start.resized(lambda t: 1.5 - (0.5 * (t / duration)))
    clip2_faded = FadeIn(duration=duration * 0.8).apply(clip2_zoomed)
    
    # Create composite
    transition_composite = CompositeVideoClip([
        clip1_faded.with_position('center'),
        clip2_faded.with_position('center')
    ], size=(w, h)).with_duration(duration)
    
    # Return shortened clips and the transition composite
    clip1_shortened = clip1.subclipped(0, max(0, clip1.duration - duration)) if clip1.duration > duration else clip1
    clip2_shortened = clip2.subclipped(min(duration, clip2.duration), clip2.duration) if clip2.duration > duration else clip2
    
    return clip1_shortened, transition_composite, clip2_shortened


def _apply_whip_pan_transition(clip1: VideoFileClip, clip2: VideoFileClip, direction: str = "left", duration: float = 0.2) -> tuple:
    """
    Apply whip pan transition - high energy for lifestyle products.
    Fast horizontal movement that creates motion blur effect.
    
    Returns:
        Tuple of (shortened_clip1, transition_composite, shortened_clip2)
    """
    w, h = clip1.size
    
    # Very short duration for whip pan (fast movement)
    # Extract the overlapping sections
    clip1_end = clip1.subclipped(max(0, clip1.duration - duration), clip1.duration)
    clip2_start = clip2.subclipped(0, min(duration, clip2.duration))
    
    # Create fast movement animations
    if direction == "left":
        # Clip1 whips out to left, clip2 whips in from right
        clip1_animated = clip1_end.with_position(lambda t: (-w * 2 * (t / duration), 0))
        clip2_animated = clip2_start.with_position(lambda t: (w - (w * 2 * (t / duration)), 0) if t < duration/2 else (0, 0))
    elif direction == "right":
        # Clip1 whips out to right, clip2 whips in from left
        clip1_animated = clip1_end.with_position(lambda t: (w * 2 * (t / duration), 0))
        clip2_animated = clip2_start.with_position(lambda t: (-w + (w * 2 * (t / duration)), 0) if t < duration/2 else (0, 0))
    elif direction == "up":
        # Clip1 whips up, clip2 whips in from bottom
        clip1_animated = clip1_end.with_position(lambda t: (0, -h * 2 * (t / duration)))
        clip2_animated = clip2_start.with_position(lambda t: (0, h - (h * 2 * (t / duration))) if t < duration/2 else (0, 0))
    else:  # down
        # Clip1 whips down, clip2 whips in from top
        clip1_animated = clip1_end.with_position(lambda t: (0, h * 2 * (t / duration)))
        clip2_animated = clip2_start.with_position(lambda t: (0, -h + (h * 2 * (t / duration))) if t < duration/2 else (0, 0))
    
    # Add slight fade to simulate motion blur
    clip1_blurred = FadeOut(duration=duration * 0.7).apply(clip1_animated)
    clip2_blurred = FadeIn(duration=duration * 0.5).apply(clip2_animated)
    
    # Create composite
    transition_composite = CompositeVideoClip([
        clip1_blurred,
        clip2_blurred
    ], size=(w, h)).with_duration(duration)
    
    # Return shortened clips and the transition composite
    clip1_shortened = clip1.subclipped(0, max(0, clip1.duration - duration)) if clip1.duration > duration else clip1
    clip2_shortened = clip2.subclipped(min(duration, clip2.duration), clip2.duration) if clip2.duration > duration else clip2
    
    return clip1_shortened, transition_composite, clip2_shortened


def _apply_glitch_transition(clip1: VideoFileClip, clip2: VideoFileClip, duration: float = 0.15) -> tuple:
    """
    Apply glitch transition - modern, tech products.
    Digital distortion effect with RGB shift simulation.
    
    Returns:
        Tuple of (shortened_clip1, transition_composite, shortened_clip2)
    """
    w, h = clip1.size
    
    # Extract the overlapping sections
    clip1_end = clip1.subclipped(max(0, clip1.duration - duration), clip1.duration)
    clip2_start = clip2.subclipped(0, min(duration, clip2.duration))
    
    # Simulate glitch with rapid position changes and opacity
    # Create multiple "glitched" versions with slight offsets
    def glitch_position(t):
        # Random-looking but deterministic position offsets
        if t < duration * 0.3:
            return (int(w * 0.02 * np.sin(t * 50)), 0)
        elif t < duration * 0.6:
            return (-int(w * 0.03 * np.cos(t * 50)), 0)
        else:
            return (int(w * 0.01 * np.sin(t * 100)), 0)
    
    # Apply glitch effect simulation with position jitter and fades
    clip1_glitched = clip1_end.with_position(glitch_position)
    clip1_faded = FadeOut(duration=duration * 0.8).apply(clip1_glitched)
    
    clip2_glitched = clip2_start.with_position(glitch_position)
    clip2_faded = FadeIn(duration=duration * 0.8).apply(clip2_glitched)
    
    # Create composite with glitch effect
    transition_composite = CompositeVideoClip([
        clip1_faded.with_position((0, 0)),
        clip2_faded.with_position((0, 0))
    ], size=(w, h)).with_duration(duration)
    
    # Return shortened clips and the transition composite
    clip1_shortened = clip1.subclipped(0, max(0, clip1.duration - duration)) if clip1.duration > duration else clip1
    clip2_shortened = clip2.subclipped(min(duration, clip2.duration), clip2.duration) if clip2.duration > duration else clip2
    
    return clip1_shortened, transition_composite, clip2_shortened


def apply_transition(clip1: VideoFileClip, clip2: VideoFileClip, transition_type: str, duration: float = 0.5) -> tuple:
    """
    Apply a transition effect between two clips.
    
    Args:
        clip1: First video clip
        clip2: Second video clip
        transition_type: Type of transition (crossfade, cut, wipe_*, flash, zoom_blur, whip_pan_*, glitch)
        duration: Transition duration in seconds
    
    Returns:
        Tuple of either:
        - (processed_clip1, processed_clip2) for simple transitions (crossfade, cut)
        - (shortened_clip1, transition_composite, shortened_clip2) for complex transitions
    """
    transition_type = transition_type.lower() if transition_type else "crossfade"
    
    # Adjust duration for specific transitions
    if transition_type == "flash":
        duration = 0.1  # Flash is always very quick
    elif transition_type == "glitch":
        duration = 0.15  # Glitch is short and snappy
    elif transition_type.startswith("whip_pan"):
        duration = 0.2  # Whip pan is fast
    elif transition_type == "zoom_blur":
        duration = 0.3  # Zoom blur is moderate speed
    
    if transition_type == "cut":
        # Hard cut - no transition effects
        return clip1, clip2
    elif transition_type == "crossfade":
        return _apply_crossfade_transition(clip1, clip2, duration)
    elif transition_type == "flash":
        return _apply_flash_transition(clip1, clip2, duration)
    elif transition_type == "zoom_blur":
        return _apply_zoom_blur_transition(clip1, clip2, duration)
    elif transition_type == "glitch":
        return _apply_glitch_transition(clip1, clip2, duration)
    elif transition_type.startswith("wipe_"):
        direction = transition_type.split("_")[1]  # Extract direction (left, right, up, down)
        return _apply_wipe_transition(clip1, clip2, direction, duration)
    elif transition_type.startswith("whip_pan_"):
        direction = transition_type.split("_")[-1]  # Extract direction (left, right, up, down)
        return _apply_whip_pan_transition(clip1, clip2, direction, duration)
    else:
        # Default to crossfade for unknown transition types
        logger.warning(f"Unknown transition type '{transition_type}', defaulting to crossfade")
        return _apply_crossfade_transition(clip1, clip2, duration)


def stitch_video_clips(
    clip_paths: List[str],
    output_path: str,
    transitions: Optional[List[str]] = None,
    cancellation_check: Optional[callable] = None
) -> str:
    """
    Stitch multiple video clips together with intelligent transitions.
    
    Args:
        clip_paths: List of paths to video clips to stitch
        output_path: Path to save the stitched video
        transitions: List of transition types for each clip boundary (length should be len(clip_paths)-1).
                    If None or True, defaults to crossfade for all transitions.
                    If False, uses hard cuts.
                    Valid transition types: crossfade, cut, wipe_left, wipe_right, 
                    wipe_up, wipe_down, flash, zoom_blur, whip_pan_left, whip_pan_right, 
                    whip_pan_up, whip_pan_down, glitch
        cancellation_check: Optional function to check if processing should be cancelled
    
    Returns:
        str: Path to the stitched video file
    
    Raises:
        RuntimeError: If stitching fails
        ValueError: If clip_paths is empty or invalid
    """
    if not clip_paths:
        raise ValueError("clip_paths cannot be empty")
    
    if cancellation_check and cancellation_check():
        raise RuntimeError("Stitching cancelled by user")
    
    # Handle backward compatibility: transitions can be bool or list
    if isinstance(transitions, bool):
        if transitions:
            # True means use crossfade for all
            transition_list = ["crossfade"] * (len(clip_paths) - 1)
        else:
            # False means use hard cuts
            transition_list = ["cut"] * (len(clip_paths) - 1)
    elif transitions is None:
        # Default to crossfade
        transition_list = ["crossfade"] * (len(clip_paths) - 1)
    else:
        transition_list = transitions
        # Validate transition list length
        if len(transition_list) != len(clip_paths) - 1:
            logger.warning(f"Transition list length ({len(transition_list)}) doesn't match clip boundaries ({len(clip_paths) - 1}). Padding with crossfade.")
            # Pad or truncate as needed
            while len(transition_list) < len(clip_paths) - 1:
                transition_list.append("crossfade")
            transition_list = transition_list[:len(clip_paths) - 1]
    
    logger.info(f"Stitching {len(clip_paths)} video clips with transitions: {transition_list}")
    
    try:
        # Check cancellation before loading clips
        if cancellation_check and cancellation_check():
            raise RuntimeError("Stitching cancelled by user")
        
        # Load all video clips
        clips = []
        for i, clip_path in enumerate(clip_paths, start=1):
            if cancellation_check and cancellation_check():
                raise RuntimeError("Stitching cancelled by user")
            
            clip_path_obj = Path(clip_path)
            if not clip_path_obj.exists():
                raise RuntimeError(f"Clip file not found: {clip_path}")
            
            logger.debug(f"Loading clip {i}/{len(clip_paths)}: {clip_path}")
            clip = VideoFileClip(str(clip_path))

            # Validate clip integrity
            if not _validate_clip(clip, f"clip_{i}"):
                logger.error(f"Clip {i} ({clip_path}) is corrupted or invalid")
                raise RuntimeError(f"Clip {i} is corrupted or has invalid frames. Please regenerate this video clip.")

            # Normalize frame rate to 24 fps (default) for consistency
            # MoviePy will handle frame rate conversion
            if clip.fps and clip.fps != 24:
                logger.debug(f"Normalizing clip {i} frame rate from {clip.fps} to 24 fps")
                clip = clip.with_fps(24)

            clips.append(clip)
        
        if not clips:
            raise RuntimeError("No valid clips loaded")
        
        # Check cancellation before processing
        if cancellation_check and cancellation_check():
            # Clean up loaded clips
            for clip in clips:
                clip.close()
            raise RuntimeError("Stitching cancelled by user")
        
        # Apply fade in to first clip (0.3s) - only if not using a cut at the start
        logger.debug("Applying fade in to first clip (0.3s)")
        first_clip = clips[0]
        first_clip = FadeIn(duration=0.3).apply(first_clip)
        clips[0] = first_clip
        
        # Apply fade out to last clip (0.3s) - only if not using a cut at the end
        logger.debug("Applying fade out to last clip (0.3s)")
        last_clip = clips[-1]
        last_clip = FadeOut(duration=0.3).apply(last_clip)
        clips[-1] = last_clip
        
        # Apply transitions between clips
        if len(clips) > 1:
            logger.debug(f"Applying {len(transition_list)} transitions between {len(clips)} clips")
            processed_clips = [clips[0]]  # First clip already has fade in
            
            for i in range(1, len(clips)):
                if cancellation_check and cancellation_check():
                    # Clean up
                    for clip in clips:
                        clip.close()
                    raise RuntimeError("Stitching cancelled by user")
                
                transition_type = transition_list[i - 1]  # Transition from clip i-1 to clip i
                prev_clip = processed_clips[-1]
                current_clip = clips[i]
                
                logger.debug(f"Applying '{transition_type}' transition between clip {i} and {i + 1}")
                
                # Apply the transition
                try:
                    result = apply_transition(
                        prev_clip, current_clip, transition_type, duration=0.5
                    )

                    # Handle both 2-tuple and 3-tuple returns
                    if len(result) == 2:
                        # Simple transition (crossfade, cut)
                        processed_prev, processed_current = result

                        # Validate results
                        if not _validate_clip(processed_prev, f"processed_clip_{i-1}"):
                            raise ValueError(f"Processed clip {i-1} became invalid after transition")
                        if not _validate_clip(processed_current, f"processed_clip_{i}"):
                            raise ValueError(f"Processed clip {i} became invalid after transition")

                        processed_clips[-1] = processed_prev
                        processed_clips.append(processed_current)
                    elif len(result) == 3:
                        # Complex transition with composite (wipe, flash, zoom_blur, whip_pan, glitch)
                        shortened_prev, transition_composite, shortened_current = result

                        # Validate all three clips
                        if not _validate_clip(shortened_prev, f"shortened_clip_{i-1}"):
                            raise ValueError(f"Shortened clip {i-1} became invalid")
                        if not _validate_clip(transition_composite, f"transition_{i-1}_{i}"):
                            raise ValueError(f"Transition composite {i-1}->{i} is invalid")
                        if not _validate_clip(shortened_current, f"shortened_clip_{i}"):
                            raise ValueError(f"Shortened clip {i} became invalid")

                        processed_clips[-1] = shortened_prev
                        processed_clips.append(transition_composite)
                        processed_clips.append(shortened_current)
                    else:
                        raise ValueError(f"Invalid transition result length: {len(result)}")

                except Exception as e:
                    logger.warning(f"Failed to apply transition '{transition_type}': {e}. Using crossfade fallback.")
                    # Fallback to crossfade if transition fails
                    try:
                        processed_prev, processed_current = apply_transition(
                            prev_clip, current_clip, "crossfade", duration=0.5
                        )

                        # Validate crossfade results
                        if not _validate_clip(processed_prev, f"crossfade_clip_{i-1}"):
                            raise ValueError("Crossfade produced invalid previous clip")
                        if not _validate_clip(processed_current, f"crossfade_clip_{i}"):
                            raise ValueError("Crossfade produced invalid current clip")

                        processed_clips[-1] = processed_prev
                        processed_clips.append(processed_current)
                    except Exception as fallback_error:
                        logger.error(f"Fallback crossfade also failed: {fallback_error}. Using hard cut.")
                        # Last resort: hard cut (no processing, just use original clips)
                        # The prev_clip is already in processed_clips, just add current_clip
                        processed_clips.append(current_clip)
            
            clips = processed_clips
        
        # Check cancellation before concatenation
        if cancellation_check and cancellation_check():
            # Clean up
            for clip in clips:
                clip.close()
            raise RuntimeError("Stitching cancelled by user")
        
        # Concatenate clips
        logger.debug("Concatenating clips")
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Ensure consistent frame rate (24 fps default)
        if final_video.fps != 24:
            logger.debug(f"Setting final video frame rate to 24 fps (was {final_video.fps})")
            final_video = final_video.with_fps(24)
        
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
        
        logger.info(f"Writing stitched video to {output_path_abs}")
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
                pass  # Ignore errors when restoring directory
        
        # Clean up
        for clip in clips:
            clip.close()
        final_video.close()
        
        logger.info(f"Video stitching completed: {output_path_abs}")
        return output_path_abs
        
    except RuntimeError as e:
        if "cancelled" in str(e).lower():
            raise
        logger.error(f"Video stitching failed: {e}", exc_info=True)
        raise RuntimeError(f"Video stitching failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during video stitching: {e}", exc_info=True)
        raise RuntimeError(f"Video stitching failed: {e}")



