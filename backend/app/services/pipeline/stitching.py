"""
Video stitching service for concatenating video clips with transitions.
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from moviepy.video.fx.FadeIn import FadeIn
from moviepy.video.fx.FadeOut import FadeOut

logger = logging.getLogger(__name__)


def stitch_video_clips(
    clip_paths: List[str],
    output_path: str,
    transitions: bool = True,
    cancellation_check: Optional[callable] = None
) -> str:
    """
    Stitch multiple video clips together with crossfade transitions and fade effects.
    
    Args:
        clip_paths: List of paths to video clips to stitch
        output_path: Path to save the stitched video
        transitions: Whether to apply crossfade transitions between clips (default: True)
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
    
    logger.info(f"Stitching {len(clip_paths)} video clips")
    
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
        
        # Apply fade in to first clip (0.3s)
        logger.debug("Applying fade in to first clip (0.3s)")
        first_clip = clips[0]
        first_clip = FadeIn(duration=0.3).apply(first_clip)
        clips[0] = first_clip
        
        # Apply fade out to last clip (0.3s)
        logger.debug("Applying fade out to last clip (0.3s)")
        last_clip = clips[-1]
        last_clip = FadeOut(duration=0.3).apply(last_clip)
        clips[-1] = last_clip
        
        # Apply crossfade transitions between clips (0.5s)
        if transitions and len(clips) > 1:
            logger.debug(f"Applying crossfade transitions (0.5s) between {len(clips)} clips")
            processed_clips = []
            
            for i in range(len(clips)):
                if cancellation_check and cancellation_check():
                    # Clean up
                    for clip in clips:
                        clip.close()
                    raise RuntimeError("Stitching cancelled by user")
                
                clip = clips[i]
                
                # For middle clips, apply both fade out and fade in for crossfade effect
                if i > 0 and i < len(clips) - 1:
                    # Apply fade out at end (0.5s for crossfade)
                    clip = FadeOut(duration=0.5).apply(clip)
                    # Apply fade in at start (0.5s for crossfade)
                    clip = FadeIn(duration=0.5).apply(clip)
                
                processed_clips.append(clip)
            
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



