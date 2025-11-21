"""
Video stitching service specifically for Master Mode.
Simplified, clean implementation for concatenating scene videos with transitions.
"""
import logging
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from moviepy import VideoFileClip, concatenate_videoclips
from moviepy.video.fx.FadeIn import FadeIn
from moviepy.video.fx.FadeOut import FadeOut

logger = logging.getLogger(__name__)


class VideoStitcher:
    """Handles video stitching operations for Master Mode."""
    
    TRANSITION_DURATIONS = {
        "cut": 0.0,
        "crossfade": 0.5,
        "fade": 0.8,
    }
    
    def __init__(self, target_fps: int = 24):
        """
        Initialize video stitcher.
        
        Args:
            target_fps: Target frame rate for output video (default: 24)
        """
        self.target_fps = target_fps
        self.loaded_clips = []
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup all loaded clips."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up all loaded video clips."""
        for clip in self.loaded_clips:
            try:
                clip.close()
            except:
                pass
        self.loaded_clips = []
    
    def _load_clip(self, clip_path: str, clip_number: int, total_clips: int) -> VideoFileClip:
        """
        Load a video clip and normalize its properties.
        
        Args:
            clip_path: Path to the video file
            clip_number: Current clip number (for logging)
            total_clips: Total number of clips (for logging)
            
        Returns:
            Loaded VideoFileClip
            
        Raises:
            FileNotFoundError: If clip file doesn't exist
            RuntimeError: If clip loading fails
        """
        clip_path_obj = Path(clip_path)
        
        if not clip_path_obj.exists():
            raise FileNotFoundError(f"Clip file not found: {clip_path}")
        
        logger.info(f"[Stitcher] Loading clip {clip_number}/{total_clips}: {clip_path_obj.name}")
        
        try:
            clip = VideoFileClip(str(clip_path))
            
            # Normalize frame rate if needed
            if clip.fps and clip.fps != self.target_fps:
                logger.debug(f"[Stitcher] Normalizing clip {clip_number} FPS: {clip.fps} -> {self.target_fps}")
                clip = clip.with_fps(self.target_fps)
            
            self.loaded_clips.append(clip)
            return clip
            
        except Exception as e:
            logger.error(f"[Stitcher] Failed to load clip {clip_number}: {e}")
            raise RuntimeError(f"Failed to load clip: {e}")
    
    def _apply_crossfade(self, clip1: VideoFileClip, clip2: VideoFileClip, duration: float) -> tuple:
        """
        Apply crossfade transition between two clips.
        
        Args:
            clip1: First clip
            clip2: Second clip
            duration: Transition duration
            
        Returns:
            Tuple of (clip1_with_fadeout, clip2_with_fadein)
        """
        clip1_faded = FadeOut(duration=duration).apply(clip1)
        clip2_faded = FadeIn(duration=duration).apply(clip2)
        return clip1_faded, clip2_faded
    
    def _apply_fade(self, clip1: VideoFileClip, clip2: VideoFileClip, duration: float) -> tuple:
        """
        Apply fade transition (fade to black, then fade in) between two clips.
        
        Args:
            clip1: First clip
            clip2: Second clip
            duration: Transition duration
            
        Returns:
            Tuple of (clip1_with_fadeout, clip2_with_fadein)
        """
        # Fade durations are split: half for fade out, half for fade in
        fade_duration = duration / 2
        
        clip1_faded = FadeOut(duration=fade_duration).apply(clip1)
        clip2_faded = FadeIn(duration=fade_duration).apply(clip2)
        
        return clip1_faded, clip2_faded
    
    def _apply_transition(
        self, 
        clip1: VideoFileClip, 
        clip2: VideoFileClip, 
        transition_type: str
    ) -> tuple:
        """
        Apply transition between two clips.
        
        Args:
            clip1: First clip
            clip2: Second clip
            transition_type: Type of transition (cut, crossfade, fade)
            
        Returns:
            Tuple of (processed_clip1, processed_clip2)
        """
        transition_type = transition_type.lower().strip()
        duration = self.TRANSITION_DURATIONS.get(transition_type, 0.5)
        
        if transition_type == "cut":
            # No transition - return clips as-is
            return clip1, clip2
        elif transition_type == "crossfade":
            return self._apply_crossfade(clip1, clip2, duration)
        elif transition_type == "fade":
            return self._apply_fade(clip1, clip2, duration)
        else:
            # Unknown transition - default to crossfade
            logger.warning(f"[Stitcher] Unknown transition '{transition_type}', using crossfade")
            return self._apply_crossfade(clip1, clip2, 0.5)
    
    def stitch_videos(
        self,
        video_paths: List[str],
        output_path: str,
        transitions: Optional[List[str]] = None,
        add_intro_outro_fades: bool = True
    ) -> str:
        """
        Stitch multiple video clips together with transitions.
        
        Args:
            video_paths: List of paths to video files to stitch
            output_path: Path where the final video will be saved
            transitions: List of transition types between clips (length = len(video_paths) - 1)
                        Valid types: "cut", "crossfade", "fade"
                        If None, defaults to "crossfade" for all transitions
            add_intro_outro_fades: Whether to add fade in/out at start/end (default: True)
            
        Returns:
            Absolute path to the stitched video file
            
        Raises:
            ValueError: If video_paths is empty or invalid
            RuntimeError: If stitching fails
        """
        if not video_paths:
            raise ValueError("video_paths cannot be empty")
        
        if len(video_paths) == 1:
            logger.info("[Stitcher] Only one video provided, no stitching needed")
            # Just copy the file or return the path
            # For simplicity, we'll still process it to apply intro/outro fades if requested
        
        # Validate transitions
        if transitions is None:
            transitions = ["crossfade"] * (len(video_paths) - 1)
        elif len(transitions) != len(video_paths) - 1:
            logger.warning(
                f"[Stitcher] Transitions length mismatch: got {len(transitions)}, "
                f"expected {len(video_paths) - 1}. Padding with crossfade."
            )
            # Pad or truncate
            while len(transitions) < len(video_paths) - 1:
                transitions.append("crossfade")
            transitions = transitions[:len(video_paths) - 1]
        
        logger.info(f"[Stitcher] Starting stitch: {len(video_paths)} clips with transitions: {transitions}")
        start_time = datetime.now()
        
        try:
            # Step 1: Load all clips
            logger.info("[Stitcher] Step 1/4: Loading video clips")
            clips = []
            for i, video_path in enumerate(video_paths, start=1):
                clip = self._load_clip(video_path, i, len(video_paths))
                clips.append(clip)
            
            # Step 2: Apply intro fade to first clip
            if add_intro_outro_fades and clips:
                logger.info("[Stitcher] Step 2/4: Applying intro fade (0.3s)")
                clips[0] = FadeIn(duration=0.3).apply(clips[0])
            else:
                logger.info("[Stitcher] Step 2/4: Skipping intro fade")
            
            # Step 3: Apply transitions between clips
            if len(clips) > 1:
                logger.info(f"[Stitcher] Step 3/4: Applying {len(transitions)} transitions")
                processed_clips = [clips[0]]
                
                for i in range(1, len(clips)):
                    transition_type = transitions[i - 1]
                    prev_clip = processed_clips[-1]
                    current_clip = clips[i]
                    
                    logger.debug(f"[Stitcher] Applying '{transition_type}' between clip {i} and {i+1}")
                    
                    try:
                        processed_prev, processed_current = self._apply_transition(
                            prev_clip, current_clip, transition_type
                        )
                        processed_clips[-1] = processed_prev
                        processed_clips.append(processed_current)
                    except Exception as e:
                        logger.warning(f"[Stitcher] Transition failed: {e}. Using hard cut.")
                        # Fallback to hard cut
                        processed_clips.append(current_clip)
                
                clips = processed_clips
            else:
                logger.info("[Stitcher] Step 3/4: Single clip, no transitions")
            
            # Step 4: Apply outro fade to last clip
            if add_intro_outro_fades and clips:
                logger.info("[Stitcher] Step 4/4: Applying outro fade (0.3s)")
                clips[-1] = FadeOut(duration=0.3).apply(clips[-1])
            else:
                logger.info("[Stitcher] Step 4/4: Skipping outro fade")
            
            # Step 5: Concatenate all clips
            logger.info("[Stitcher] Concatenating clips")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Ensure consistent frame rate
            if final_video.fps != self.target_fps:
                logger.debug(f"[Stitcher] Setting final FPS: {final_video.fps} -> {self.target_fps}")
                final_video = final_video.with_fps(self.target_fps)
            
            # Step 6: Write output file
            output_path_obj = Path(output_path).resolve()
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"[Stitcher] Writing final video to: {output_path_obj}")
            
            final_video.write_videofile(
                str(output_path_obj),
                codec='libx264',
                audio_codec='aac',
                fps=self.target_fps,
                preset='medium',
                bitrate='5000k',  # High quality
                logger=None  # Suppress MoviePy progress
            )
            
            # Cleanup
            final_video.close()
            
            # Log completion
            duration = (datetime.now() - start_time).total_seconds()
            file_size_mb = output_path_obj.stat().st_size / (1024 * 1024)
            logger.info(
                f"[Stitcher] ✅ Stitching complete! "
                f"Duration: {duration:.1f}s, Size: {file_size_mb:.1f}MB"
            )
            
            return str(output_path_obj)
            
        except Exception as e:
            logger.error(f"[Stitcher] ❌ Stitching failed: {e}", exc_info=True)
            raise RuntimeError(f"Video stitching failed: {e}")


# Convenience function for backward compatibility
def stitch_master_mode_videos(
    video_paths: List[str],
    output_path: str,
    transitions: Optional[List[str]] = None
) -> str:
    """
    Stitch Master Mode scene videos together.
    
    Args:
        video_paths: List of scene video paths
        output_path: Output path for final video
        transitions: List of transitions between scenes
        
    Returns:
        Path to stitched video
    """
    with VideoStitcher() as stitcher:
        return stitcher.stitch_videos(video_paths, output_path, transitions)


