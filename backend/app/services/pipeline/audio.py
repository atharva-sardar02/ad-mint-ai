"""
Audio layer service for adding background music and sound effects to videos.
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.generation import ScenePlan

from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, afx
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume

logger = logging.getLogger(__name__)

# Music library directory structure
# Resolve path relative to this file's location (backend/app/services/pipeline/)
# Go up 4 levels: pipeline -> services -> app -> backend, then into assets/music
_BASE_DIR = Path(__file__).parent.parent.parent.parent
MUSIC_LIBRARY_DIR = _BASE_DIR / "assets" / "music"
SFX_LIBRARY_DIR = _BASE_DIR / "assets" / "sfx"

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
    cancellation_check: Optional[callable] = None,
    llm_specification: Optional[dict] = None,
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
    
    # Get original working directory BEFORE changing directories
    original_cwd = os.getcwd()
    
    # Convert paths to absolute BEFORE changing directory
    # This ensures paths are resolved relative to the original working directory
    if not Path(video_path).is_absolute():
        # If relative, resolve from original working directory
        video_path_abs = str(Path(original_cwd) / video_path)
    else:
        video_path_abs = video_path
    
    if not Path(output_path).is_absolute():
        # If relative, resolve from original working directory
        output_path_abs = str(Path(original_cwd) / output_path)
    else:
        output_path_abs = output_path
    
    # Normalize paths (resolve any .. or .)
    video_path_abs = str(Path(video_path_abs).resolve())
    output_path_abs = str(Path(output_path_abs).resolve())
    
    # Set temp directory for MoviePy to use (ensures temp files are created in writable location)
    temp_dir = os.environ.get('TMPDIR', '/tmp')
    temp_dir_path = Path(temp_dir)
    if not temp_dir_path.exists():
        temp_dir_path.mkdir(parents=True, exist_ok=True)
    # Set tempfile's tempdir to ensure MoviePy uses it
    tempfile.tempdir = str(temp_dir_path.absolute())
    # Also set TMPDIR in environment for FFmpeg and other subprocesses
    os.environ['TMPDIR'] = str(temp_dir_path.absolute())
    
    # Change to temp directory so MoviePy creates temp files there (not in working directory)
    try:
        os.chdir(str(temp_dir_path.absolute()))
    except OSError as e:
        logger.warning(f"Could not change to temp directory {temp_dir_path}: {e}. Continuing with current directory.")
    
    logger.info(f"Adding audio layer to video: {video_path_abs} (style: {music_style})")
    
    try:
        # Check cancellation before loading video
        if cancellation_check and cancellation_check():
            raise RuntimeError("Audio layer processing cancelled by user")
        
        # Load video (preserve original audio from Sora-2 if present)
        video = VideoFileClip(video_path_abs)
        video_duration = video.duration
        
        # Check if video already has audio (from Sora-2 generation)
        original_audio = None
        if video.audio is not None:
            original_audio = video.audio
            logger.info(
                f"Video contains original audio from Sora-2 (duration: {original_audio.duration:.2f}s). "
                f"This will be preserved and mixed with background music."
            )
        else:
            logger.debug("Video has no original audio - will add background music only")
        
        # Select music file based on style (graceful fallback if not found)
        logger.info(f"Selecting music file for style: '{music_style}'")
        music_file = _select_music_file(music_style)
        if music_file:
            logger.info(f"Music file selected: {music_file.name} (path: {music_file.absolute()})")
        else:
            logger.warning(f"No music file found for style '{music_style}' - video will be exported without background music")
        
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
                music_clip = music_clip.subclipped(0, video_duration)
            elif music_clip.duration < video_duration and music_clip.duration > 0:
                # Loop music if shorter than video (for MVP, just repeat once)
                logger.debug(f"Music ({music_clip.duration}s) shorter than video ({video_duration}s), looping")
                loops_needed = int(video_duration / music_clip.duration) + 1
                music_clips = [music_clip] * loops_needed
                music_clip = CompositeAudioClip(music_clips).subclipped(0, video_duration)
            
            # Adjust music volume to 30%
            logger.debug("Adjusting music volume to 30%")
            music_clip = music_clip.with_effects([MultiplyVolume(0.3)])
        else:
            logger.info("No music file available - video will be exported without background music")
        
        # Check cancellation before adding sound effects
        if cancellation_check and cancellation_check():
            video.close()
            if music_clip:
                music_clip.close()
            raise RuntimeError("Audio layer processing cancelled by user")
        
        # Add sound effects: ambient SFX from LLM sound_design + transition SFX
        sfx_clips = []
        
        # First, add ambient sound effects based on LLM sound_design for each scene
        if llm_specification and scene_plan and scene_plan.scenes:
            scenes_data = llm_specification.get("scenes", [])
            current_time = 0.0
            
            for i, scene in enumerate(scene_plan.scenes):
                # Find matching scene in LLM specification by scene_number
                scene_spec = None
                for spec_scene in scenes_data:
                    if spec_scene.get("scene_number") == scene.scene_number:
                        scene_spec = spec_scene
                        break
                
                if scene_spec:
                    sound_design = scene_spec.get("sound_design")
                    if sound_design:
                        # Map sound_design description to appropriate ambient SFX
                        ambient_sfx_file = _select_ambient_sfx(sound_design)
                        if ambient_sfx_file and ambient_sfx_file.exists():
                            try:
                                ambient_clip = AudioFileClip(str(ambient_sfx_file))
                                # Trim to scene duration
                                scene_duration = scene.duration
                                if ambient_clip.duration > scene_duration:
                                    ambient_clip = ambient_clip.subclipped(0, scene_duration)
                                elif ambient_clip.duration < scene_duration:
                                    # Loop ambient SFX to match scene duration
                                    loops_needed = int(scene_duration / ambient_clip.duration) + 1
                                    ambient_clips = [ambient_clip] * loops_needed
                                    ambient_clip = CompositeAudioClip(ambient_clips).subclipped(0, scene_duration)
                                
                                # Position at scene start time
                                ambient_clip = ambient_clip.with_start(current_time)
                                # Lower volume for ambient (20% - subtle background)
                                ambient_clip = ambient_clip.with_effects([MultiplyVolume(0.2)])
                                sfx_clips.append(ambient_clip)
                                logger.info(
                                    f"Added ambient SFX for scene {scene.scene_number} "
                                    f"({sound_design[:50]}...) at {current_time:.2f}s"
                                )
                            except Exception as e:
                                logger.warning(f"Could not add ambient SFX for scene {scene.scene_number}: {e}")
                        else:
                            logger.debug(
                                f"No ambient SFX file found for sound_design '{sound_design[:50]}...' "
                                f"in scene {scene.scene_number}. Check {SFX_LIBRARY_DIR} for available SFX files."
                            )
                
                current_time += scene.duration
        
        # Add transition sound effects at scene boundaries
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
                    logger.info(f"Adding sound effects at {len(transition_times)} scene transitions")
                    base_sfx = AudioFileClip(str(sfx_file))
                    # Trim SFX to 0.5s (transition duration)
                    if base_sfx.duration > 0.5:
                        base_sfx = base_sfx.subclipped(0, 0.5)
                    
                    # Create SFX clips at each transition point
                    for transition_time in transition_times:
                        if transition_time < video_duration:  # Only if within video duration
                            sfx_at_transition = base_sfx.with_start(transition_time)
                            sfx_clips.append(sfx_at_transition)
                            logger.debug(f"Added SFX at transition: {transition_time:.2f}s")
                else:
                    logger.warning(
                        f"Sound effect file not found in {SFX_LIBRARY_DIR}. "
                        f"Expected: transition.mp3 or transition.wav. "
                        f"Skipping transition sound effects. "
                        f"To enable SFX, add sound effect files to {SFX_LIBRARY_DIR}"
                    )
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
                        sfx_clip = sfx_clip.subclipped(0, 0.5)
                    sfx_clip = sfx_clip.with_start(0)
                    sfx_clips.append(sfx_clip)
            except Exception as e:
                logger.debug(f"Could not add sound effect at start: {e}")
        
        # Composite audio tracks: original Sora-2 audio + music + SFX clips
        audio_tracks = []
        
        # Preserve original audio from Sora-2 (ambient sounds, sound effects generated by AI)
        if original_audio:
            # Lower volume of original audio to 60% so it doesn't overpower background music
            # This allows Sora-2's ambient sounds to be heard but not dominate
            original_audio_adjusted = original_audio.with_effects([MultiplyVolume(0.6)])
            audio_tracks.append(original_audio_adjusted)
            logger.info("Preserving Sora-2 generated audio (ambient sounds, SFX) at 60% volume")
        
        # Add background music
        if music_clip:
            audio_tracks.append(music_clip)
        
        # Add manual SFX clips (if files exist - optional)
        if sfx_clips:
            audio_tracks.extend(sfx_clips)
        
        # Composite all audio tracks
        if len(audio_tracks) > 1:
            track_names = []
            if original_audio:
                track_names.append("Sora-2 audio")
            if music_clip:
                track_names.append("background music")
            if sfx_clips:
                track_names.append(f"{len(sfx_clips)} SFX clip(s)")
            logger.info(f"Compositing {len(audio_tracks)} audio track(s): {', '.join(track_names)}")
            final_audio = CompositeAudioClip(audio_tracks)
        elif len(audio_tracks) == 1:
            track_name = "Sora-2 audio" if original_audio else ("background music" if music_clip else "SFX")
            logger.info(f"Using single audio track: {track_name}")
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
            final_video = video.with_audio(final_audio)
        else:
            logger.debug("No audio to attach - video will be silent")
            final_video = video
        
        # Write output video
        output_path_obj = Path(output_path_abs)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Writing video with audio to {output_path_abs}")
        final_video.write_videofile(
            output_path_abs,
            codec='libx264',
            audio_codec='aac',
            fps=video.fps,
            preset='medium',
            logger=None  # Suppress MoviePy progress logs
        )
        
        # Clean up
        video.close()
        if original_audio:
            original_audio.close()
        if music_clip:
            music_clip.close()
        for sfx in sfx_clips:
            sfx.close()
        if final_audio:
            final_audio.close()
        final_video.close()
        
        logger.info(f"Audio layer added successfully: {output_path_abs}")
        return output_path_abs
        
    except RuntimeError as e:
        if "cancelled" in str(e).lower():
            raise
        logger.error(f"Audio layer addition failed: {e}", exc_info=True)
        raise RuntimeError(f"Audio layer addition failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during audio layer addition: {e}", exc_info=True)
        raise RuntimeError(f"Audio layer addition failed: {e}")
    finally:
        # Restore original working directory
        try:
            os.chdir(original_cwd)
        except OSError:
            pass  # Ignore errors when restoring directory


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
    
    # Ensure music directory exists
    if not MUSIC_LIBRARY_DIR.exists():
        logger.warning(f"Music library directory does not exist: {MUSIC_LIBRARY_DIR}")
        return None
    
    # Try exact match first
    music_file = MUSIC_LIBRARY_DIR / filename
    
    # If not found, try case-insensitive match and different extensions
    if not music_file.exists():
        logger.debug(f"Music file not found: {music_file}, trying case-insensitive and alternative extensions")
        
        # Extract base name (without extension) - handle double extensions like .mp3.mp3
        expected_base = filename.replace(".mp3", "").lower()
        
        # Try case-insensitive match - check if filename starts with expected base
        for file in MUSIC_LIBRARY_DIR.iterdir():
            if file.is_file():
                # Get base name by removing all extensions (handle .mp3.mp3 case)
                file_base = file.name
                while '.' in file_base:
                    file_base = file_base.rsplit('.', 1)[0]
                
                if file_base.lower() == expected_base:
                    # Found a match (might have different extension or case)
                    logger.info(f"Found music file with different case/extension: {file.name} (looking for {filename})")
                    music_file = file
                    break
        else:
            # If still not found, try default
            logger.warning(f"Music file not found: {music_file}, trying default")
            default_filename = MUSIC_STYLE_MAP["default"]
            music_file = MUSIC_LIBRARY_DIR / default_filename
            expected_base_default = default_filename.replace(".mp3", "").lower()
            
            # Try case-insensitive for default too
            if not music_file.exists():
                for file in MUSIC_LIBRARY_DIR.iterdir():
                    if file.is_file():
                        # Get base name by removing all extensions
                        file_base = file.name
                        while '.' in file_base:
                            file_base = file_base.rsplit('.', 1)[0]
                        
                        if file_base.lower() == expected_base_default:
                            logger.info(f"Found default music file with different case/extension: {file.name}")
                            music_file = file
                            break
                
                # If default not found either, try to use ANY available MP3 file as fallback
                if not music_file.exists():
                    logger.warning(f"Default music file also not found, trying to use any available MP3 file")
                    for file in MUSIC_LIBRARY_DIR.iterdir():
                        if file.is_file() and file.suffix.lower() in ['.mp3', '.wav', '.m4a']:
                            logger.info(f"Using any available music file as fallback: {file.name}")
                            music_file = file
                            break
    
    if not music_file.exists():
        # List available files for debugging
        available_files = [f.name for f in MUSIC_LIBRARY_DIR.iterdir() if f.is_file()]
        logger.warning(
            f"Music library is empty or file not found. "
            f"Looking for: {filename} in {MUSIC_LIBRARY_DIR} (resolved: {music_file.absolute()}). "
            f"Available files: {available_files}. "
            f"Video will be exported without background music."
        )
        return None
    
    logger.info(f"Selected music file: {music_file} (absolute: {music_file.absolute()})")
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


def _select_ambient_sfx(sound_design: str) -> Optional[Path]:
    """
    Select ambient sound effect file based on sound_design description from LLM.
    
    Maps natural language descriptions like "gentle room tone" or "soft fabric movement"
    to appropriate ambient SFX files.
    
    Args:
        sound_design: Sound design description from LLM (e.g., "gentle room tone, faint fabric movement")
    
    Returns:
        Optional[Path]: Path to ambient sound effect file, or None if not found
    """
    if not sound_design:
        return None
    
    sound_design_lower = sound_design.lower()
    
    # Map keywords to SFX files
    # Priority order: more specific matches first
    ambient_mappings = [
        ("room tone", "room_tone"),
        ("ambient", "room_tone"),
        ("fabric", "fabric_movement"),
        ("cloth", "fabric_movement"),
        ("movement", "fabric_movement"),
        ("footsteps", "footsteps"),
        ("footstep", "footsteps"),
        ("paper", "paper_rustle"),
        ("rustle", "paper_rustle"),
        ("breeze", "breeze"),
        ("wind", "breeze"),
        ("nature", "nature_ambient"),
        ("outdoor", "nature_ambient"),
    ]
    
    # Find first matching keyword
    for keyword, sfx_name in ambient_mappings:
        if keyword in sound_design_lower:
            sfx_file = SFX_LIBRARY_DIR / f"{sfx_name}.mp3"
            if not sfx_file.exists():
                sfx_file = SFX_LIBRARY_DIR / f"{sfx_name}.wav"
            if sfx_file.exists():
                logger.debug(f"Mapped sound_design '{sound_design[:50]}...' to {sfx_name}")
                return sfx_file
    
    # Fallback: try generic "ambient" or "room_tone"
    fallback_files = ["room_tone", "ambient", "background"]
    for fallback_name in fallback_files:
        fallback_file = SFX_LIBRARY_DIR / f"{fallback_name}.mp3"
        if not fallback_file.exists():
            fallback_file = SFX_LIBRARY_DIR / f"{fallback_name}.wav"
        if fallback_file.exists():
            logger.debug(f"Using fallback ambient SFX: {fallback_name} for '{sound_design[:50]}...'")
            return fallback_file
    
    logger.debug(f"No ambient SFX found for sound_design: '{sound_design[:50]}...'")
    return None

