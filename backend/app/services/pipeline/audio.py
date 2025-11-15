"""
Audio layer service for adding background music and sound effects to videos.
"""
import logging
import os
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.generation import ScenePlan

from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

logger = logging.getLogger(__name__)

# Music library directory structure
MUSIC_LIBRARY_DIR = Path("backend/assets/music")
SFX_LIBRARY_DIR = Path("backend/assets/sfx")

# Music style mapping (maps style keywords to music file names)
# For MVP, we'll use simple keyword matching
MUSIC_STYLE_MAP = {
    "energetic": "energetic.mp3",
    "calm": "calm.mp3",
    "professional": "professional.mp3",
    "upbeat": "energetic.mp3",
    "relaxed": "calm.mp3",
    "corporate": "professional.mp3",
    # Default fallback
    "default": "professional.mp3"
}


def add_audio_layer(
    video_path: str,
    music_style: str,
    output_path: str,
    scene_plan: Optional["ScenePlan"] = None,
    cancellation_check: Optional[callable] = None
) -> str:
    """
    Add background music and sound effects to a video.
    
    Args:
        video_path: Path to input video file
        music_style: Music style keyword (e.g., "energetic", "calm", "professional")
        output_path: Path to save output video with audio
        cancellation_check: Optional function to check if processing should be cancelled
    
    Returns:
        str: Path to output video file with audio
    
    Raises:
        RuntimeError: If audio addition fails
        FileNotFoundError: If music file not found
    """
    if cancellation_check and cancellation_check():
        raise RuntimeError("Audio layer processing cancelled by user")
    
    logger.info(f"Adding audio layer to video: {video_path} (style: {music_style})")
    
    try:
        # Check cancellation before loading video
        if cancellation_check and cancellation_check():
            raise RuntimeError("Audio layer processing cancelled by user")
        
        # Load video
        video = VideoFileClip(video_path)
        video_duration = video.duration
        
        # Select music file based on style (graceful fallback if not found)
        music_file = _select_music_file(music_style)
        
        # Check cancellation before loading music
        if cancellation_check and cancellation_check():
            video.close()
            raise RuntimeError("Audio layer processing cancelled by user")
        
        # Load and process background music (if available)
        music_clip = None
        if music_file and music_file.exists():
            logger.debug(f"Selected music file: {music_file}")
            music_clip = AudioFileClip(str(music_file))
        
        # Process music if available
        if music_clip:
            # Trim music to video duration
            if music_clip.duration > video_duration:
                logger.debug(f"Trimming music from {music_clip.duration}s to {video_duration}s")
                music_clip = music_clip.subclip(0, video_duration)
            elif music_clip.duration < video_duration:
                # Loop music if shorter than video (for MVP, just repeat once)
                logger.debug(f"Music ({music_clip.duration}s) shorter than video ({video_duration}s), looping")
                loops_needed = int(video_duration / music_clip.duration) + 1
                music_clips = [music_clip] * loops_needed
                music_clip = CompositeAudioClip(music_clips).subclip(0, video_duration)
            
            # Adjust music volume to 30%
            logger.debug("Adjusting music volume to 30%")
            music_clip = music_clip.volumex(0.3)
        else:
            logger.info("No music file available - video will be exported without background music")
        
        # Check cancellation before adding sound effects
        if cancellation_check and cancellation_check():
            video.close()
            if music_clip:
                music_clip.close()
            raise RuntimeError("Audio layer processing cancelled by user")
        
        # Add sound effects at scene transitions
        sfx_clips = []
        if scene_plan and scene_plan.scenes:
            # Calculate transition points based on scene durations
            transition_times = []
            current_time = 0.0
            for i, scene in enumerate(scene_plan.scenes[:-1]):  # All but last scene
                current_time += scene.duration
                # Account for crossfade transition (0.5s) - place SFX at transition point
                transition_times.append(current_time - 0.25)  # Middle of transition
            
            # Add SFX at each transition point
            try:
                sfx_file = _select_sfx_file("transition")
                if sfx_file and sfx_file.exists():
                    logger.debug(f"Adding sound effects at {len(transition_times)} scene transitions")
                    base_sfx = AudioFileClip(str(sfx_file))
                    # Trim SFX to 0.5s (transition duration)
                    if base_sfx.duration > 0.5:
                        base_sfx = base_sfx.subclip(0, 0.5)
                    
                    # Create SFX clips at each transition point
                    for transition_time in transition_times:
                        if transition_time < video_duration:  # Only if within video duration
                            sfx_at_transition = base_sfx.set_start(transition_time)
                            sfx_clips.append(sfx_at_transition)
                            logger.debug(f"Added SFX at transition: {transition_time:.2f}s")
                else:
                    logger.debug("Sound effect file not found, skipping SFX")
            except Exception as e:
                # SFX is optional - log warning but continue
                logger.warning(f"Could not add sound effects: {e}")
        else:
            # Fallback: Add SFX at start if no scene plan available
            try:
                sfx_file = _select_sfx_file("transition")
                if sfx_file and sfx_file.exists():
                    logger.debug("Adding sound effect at start (no scene plan available)")
                    sfx_clip = AudioFileClip(str(sfx_file))
                    if sfx_clip.duration > 0.5:
                        sfx_clip = sfx_clip.subclip(0, 0.5)
                    sfx_clip = sfx_clip.set_start(0)
                    sfx_clips.append(sfx_clip)
            except Exception as e:
                logger.debug(f"Could not add sound effect at start: {e}")
        
        # Composite audio tracks (music + all SFX clips)
        audio_tracks = []
        if music_clip:
            audio_tracks.append(music_clip)
        if sfx_clips:
            audio_tracks.extend(sfx_clips)
        
        if len(audio_tracks) > 1:
            logger.debug(f"Compositing {len(audio_tracks)} audio track(s): music + {len(sfx_clips)} sound effect(s)")
            final_audio = CompositeAudioClip(audio_tracks)
        elif len(audio_tracks) == 1:
            logger.debug("Using single audio track")
            final_audio = audio_tracks[0]
        else:
            # No audio - video will be silent
            logger.warning("No audio tracks available - video will be exported without audio")
            final_audio = None
        
        # Check cancellation before attaching audio
        if cancellation_check and cancellation_check():
            video.close()
            if music_clip:
                music_clip.close()
            for sfx in sfx_clips:
                sfx.close()
            if final_audio:
                final_audio.close()
            raise RuntimeError("Audio layer processing cancelled by user")
        
        # Attach composite audio to video (if available)
        if final_audio:
            logger.debug("Attaching audio to video")
            final_video = video.set_audio(final_audio)
        else:
            logger.debug("No audio to attach - video will be silent")
            final_video = video
        
        # Write output video
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Writing video with audio to {output_path}")
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
        if music_clip:
            music_clip.close()
        for sfx in sfx_clips:
            sfx.close()
        if final_audio:
            final_audio.close()
        final_video.close()
        
        logger.info(f"Audio layer added successfully: {output_path}")
        return output_path
        
    except RuntimeError as e:
        if "cancelled" in str(e).lower():
            raise
        logger.error(f"Audio layer addition failed: {e}", exc_info=True)
        raise RuntimeError(f"Audio layer addition failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during audio layer addition: {e}", exc_info=True)
        raise RuntimeError(f"Audio layer addition failed: {e}")


def _select_music_file(style: str) -> Optional[Path]:
    """
    Select music file based on style keyword.
    
    Args:
        style: Music style keyword (e.g., "energetic", "calm", "professional")
    
    Returns:
        Optional[Path]: Path to music file, or None if not found (graceful fallback)
    """
    # Normalize style to lowercase
    style_lower = style.lower() if style else "default"
    
    # Map style to filename
    filename = MUSIC_STYLE_MAP.get(style_lower, MUSIC_STYLE_MAP["default"])
    
    # Try exact match first
    music_file = MUSIC_LIBRARY_DIR / filename
    
    # If not found, try default
    if not music_file.exists():
        logger.warning(f"Music file not found: {music_file}, trying default")
        music_file = MUSIC_LIBRARY_DIR / MUSIC_STYLE_MAP["default"]
    
    if not music_file.exists():
        logger.warning(
            f"Music library is empty. No music files found in {MUSIC_LIBRARY_DIR}. "
            f"Video will be exported without background music. "
            f"Please add music files to enable audio layer."
        )
        return None
    
    return music_file


def _select_sfx_file(sfx_type: str) -> Optional[Path]:
    """
    Select sound effect file based on type.
    
    Args:
        sfx_type: Sound effect type (e.g., "transition", "click", "whoosh")
    
    Returns:
        Optional[Path]: Path to sound effect file, or None if not found
    """
    # For MVP, use a simple mapping
    sfx_filename = f"{sfx_type}.mp3"
    sfx_file = SFX_LIBRARY_DIR / sfx_filename
    
    if not sfx_file.exists():
        # Try WAV format
        sfx_file = SFX_LIBRARY_DIR / f"{sfx_type}.wav"
    
    if not sfx_file.exists():
        logger.debug(f"Sound effect not found: {sfx_file}")
        return None
    
    return sfx_file

