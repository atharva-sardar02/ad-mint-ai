"""
Post-processing and export service for final video export, color grading, and thumbnail generation.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from moviepy import VideoFileClip

logger = logging.getLogger(__name__)

# Output directories
VIDEOS_OUTPUT_DIR = Path("output/videos")
THUMBNAILS_OUTPUT_DIR = Path("output/thumbnails")


def export_final_video(
    video_path: str,
    brand_style: str,
    output_dir: str,
    generation_id: str,
    cancellation_check: Optional[callable] = None
) -> Tuple[str, str]:
    """
    Apply color grading, export final video, and generate thumbnail.
    
    Args:
        video_path: Path to input video file (with audio)
        brand_style: Brand style keywords for color grading (e.g., "cinematic", "luxury", "vibrant")
        output_dir: Base output directory for videos and thumbnails
        generation_id: Generation ID for filename
        cancellation_check: Optional function to check if processing should be cancelled
    
    Returns:
        Tuple[str, str]: (video_url, thumbnail_url) paths relative to output directory
    
    Raises:
        RuntimeError: If export fails
    """
    if cancellation_check and cancellation_check():
        raise RuntimeError("Export processing cancelled by user")
    
    logger.info(f"Exporting final video: {video_path} (style: {brand_style})")
    
    try:
        # Check cancellation before loading video
        if cancellation_check and cancellation_check():
            raise RuntimeError("Export processing cancelled by user")
        
        # Load video
        video = VideoFileClip(video_path)
        
        # Apply color grading based on brand style
        logger.debug(f"Applying color grading (style: {brand_style})")
        graded_video = _apply_color_grading(video, brand_style)
        
        # Check cancellation before export
        if cancellation_check and cancellation_check():
            video.close()
            graded_video.close()
            raise RuntimeError("Export processing cancelled by user")
        
        # Ensure output directories exist
        videos_dir = Path(output_dir) / "videos"
        thumbnails_dir = Path(output_dir) / "thumbnails"
        videos_dir.mkdir(parents=True, exist_ok=True)
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filenames
        video_filename = f"{generation_id}.mp4"
        thumbnail_filename = f"{generation_id}.jpg"
        
        video_output_path = videos_dir / video_filename
        thumbnail_output_path = thumbnails_dir / thumbnail_filename
        
        # Ensure video is 1080p resolution (1920x1080)
        # Resize if needed to enforce minimum 1080p resolution
        current_size = graded_video.size
        target_resolution = (1920, 1080)
        
        if current_size[0] < 1920 or current_size[1] < 1080:
            logger.info(f"Resizing video from {current_size} to {target_resolution} for 1080p minimum")
            graded_video = graded_video.resized(target_resolution)
        elif current_size != target_resolution:
            # If larger than 1080p, resize to exactly 1080p for consistency
            logger.debug(f"Resizing video from {current_size} to {target_resolution} for consistency")
            graded_video = graded_video.resized(target_resolution)
        
        # Export video as 1080p MP4 with H.264 codec
        logger.info(f"Exporting video to {video_output_path} (1080p, H.264)")
        graded_video.write_videofile(
            str(video_output_path),
            codec='libx264',
            audio_codec='aac',
            fps=24,  # Consistent frame rate
            preset='medium',
            bitrate='8000k',  # High quality for 1080p
            logger=None  # Suppress MoviePy progress logs
        )
        
        # Check cancellation before thumbnail generation
        if cancellation_check and cancellation_check():
            video.close()
            graded_video.close()
            raise RuntimeError("Export processing cancelled by user")
        
        # Generate thumbnail from first frame
        logger.info(f"Generating thumbnail: {thumbnail_output_path}")
        _generate_thumbnail(graded_video, str(thumbnail_output_path))
        
        # Clean up
        video.close()
        graded_video.close()
        
        # Return relative paths (for database storage)
        video_url = f"videos/{video_filename}"
        thumbnail_url = f"thumbnails/{thumbnail_filename}"
        
        logger.info(f"Final video exported successfully: {video_url}, thumbnail: {thumbnail_url}")
        return (video_url, thumbnail_url)
        
    except RuntimeError as e:
        if "cancelled" in str(e).lower():
            raise
        logger.error(f"Video export failed: {e}", exc_info=True)
        raise RuntimeError(f"Video export failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during video export: {e}", exc_info=True)
        raise RuntimeError(f"Video export failed: {e}")


def _apply_color_grading(video: VideoFileClip, brand_style: str) -> VideoFileClip:
    """
    Apply color grading to video based on brand style keywords using OpenCV.
    
    Args:
        video: VideoFileClip to grade
        brand_style: Brand style keywords (e.g., "cinematic", "luxury", "vibrant")
    
    Returns:
        VideoFileClip: Color-graded video clip
    """
    style_lower = brand_style.lower() if brand_style else ""
    
    # Apply color grading using OpenCV frame-by-frame processing
    def apply_grading_to_frame(frame):
        """Apply color grading to a single frame."""
        # Convert RGB to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Convert to LAB color space for better color manipulation
        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        if "cinematic" in style_lower:
            # Cinematic: Desaturated, cooler tones (reduce saturation, shift to blue)
            logger.debug("Applying cinematic color grading")
            # Reduce saturation (L channel adjustment)
            l = cv2.add(l, -10)  # Slightly darker
            # Shift to cooler tones (reduce yellow, increase blue in B channel)
            b = cv2.add(b, -15)  # Shift towards blue
            # Reduce saturation by scaling A and B channels
            a = cv2.multiply(a, 0.85)  # Reduce color saturation
            b = cv2.multiply(b, 0.85)
        
        elif "luxury" in style_lower:
            # Luxury: Warm tones, enhanced contrast
            logger.debug("Applying luxury color grading")
            # Enhance contrast (L channel)
            l = cv2.add(l, 5)  # Slightly brighter
            # Apply contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            # Shift to warm tones (increase yellow in B channel)
            b = cv2.add(b, 10)  # Shift towards yellow/warm
        
        elif "vibrant" in style_lower:
            # Vibrant: Enhanced saturation, bright colors
            logger.debug("Applying vibrant color grading")
            # Increase brightness
            l = cv2.add(l, 10)
            # Enhance saturation by scaling A and B channels
            a = cv2.multiply(a, 1.2)  # Increase color saturation
            b = cv2.multiply(b, 1.2)
        
        else:
            # Default: Slight contrast enhancement
            logger.debug("Applying default color grading (slight contrast enhancement)")
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            l = clahe.apply(l)
        
        # Merge channels back
        lab_graded = cv2.merge([l, a, b])
        
        # Convert back to BGR then RGB
        frame_bgr_graded = cv2.cvtColor(lab_graded, cv2.COLOR_LAB2BGR)
        frame_rgb_graded = cv2.cvtColor(frame_bgr_graded, cv2.COLOR_BGR2RGB)
        
        return frame_rgb_graded
    
    # Apply grading to all frames using MoviePy's transform helper
    # MoviePy v2 removed `.fl`, so we use `image_transform` instead.
    graded_video = video.image_transform(apply_grading_to_frame)
    
    return graded_video


def _generate_thumbnail(video: VideoFileClip, output_path: str) -> None:
    """
    Generate thumbnail from first frame of video.
    
    Args:
        video: VideoFileClip to extract frame from
        output_path: Path to save thumbnail image
    """
    try:
        # Get first frame (at t=0.1s to avoid black frame)
        frame_time = min(0.1, video.duration / 2)  # Use first 0.1s or middle if video is very short
        
        # Extract frame using MoviePy
        frame = video.get_frame(frame_time)
        
        # Convert to RGB if needed (MoviePy returns RGB)
        # Save using OpenCV (more reliable than MoviePy's save_frame)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Ensure output directory exists
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Save thumbnail (JPEG format, high quality)
        cv2.imwrite(str(output_path), frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        logger.debug(f"Thumbnail saved: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}", exc_info=True)
        raise RuntimeError(f"Thumbnail generation failed: {e}")

