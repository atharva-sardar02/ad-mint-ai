"""
Quality control service for VBench-based video quality assessment.

This service implements VBench metrics evaluation for automated quality control.
VBench (Video Benchmark) is a comprehensive evaluation framework that assesses:
- Temporal quality (subject consistency, background consistency, motion smoothness, dynamic degree)
- Frame-wise quality (aesthetic quality, imaging quality, object class alignment)
- Text-video alignment (prompt adherence)
- Multiple objects assessment (if applicable)

Note: VBench library integration is in progress. This implementation provides:
1. Structure for VBench integration when library becomes available
2. Fallback quality metrics using OpenCV and other available libraries
3. Graceful degradation if VBench evaluation is unavailable

Performance Monitoring:
- Tracks evaluation time per clip (target: <30 seconds)
- Logs performance metrics for monitoring
- Supports async evaluation to avoid blocking pipeline
"""
import logging
import os
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Performance monitoring
PERFORMANCE_TARGET_SECONDS = 30.0  # Target evaluation time per clip

# Try to import VBench if available
try:
    # VBench library import (when available)
    # from vbench import VBench
    # VBENCH_AVAILABLE = True
    VBENCH_AVAILABLE = False  # Set to True when VBench library is installed
except ImportError:
    VBENCH_AVAILABLE = False
    logger.warning("VBench library not available. Using fallback quality metrics.")


def evaluate_vbench(
    video_clip_path: str,
    prompt_text: str,
    vbench_available: bool = VBENCH_AVAILABLE
) -> Dict[str, float]:
    """
    Evaluate video clip using VBench metrics.
    
    This function implements VBench evaluation methodology:
    - Temporal quality: subject consistency, background consistency, motion smoothness, dynamic degree
    - Frame-wise quality: aesthetic quality, imaging quality, object class alignment
    - Text-video alignment: prompt adherence
    - Multiple objects assessment: if applicable
    
    Performance: Tracks evaluation time and logs if exceeds target (<30 seconds per clip).
    
    Args:
        video_clip_path: Path to the video clip file
        prompt_text: Text prompt used for generation (for text-video alignment)
        vbench_available: Whether VBench library is available (default: from import check)
    
    Returns:
        Dict[str, float]: Quality scores for each dimension (0-100 scale):
            - temporal_quality: Overall temporal consistency score
            - subject_consistency: Subject consistency across frames
            - background_consistency: Background consistency across frames
            - motion_smoothness: Motion smoothness score
            - dynamic_degree: Dynamic motion score
            - aesthetic_quality: Aesthetic quality score
            - imaging_quality: Image quality score
            - object_class_alignment: Object class alignment score
            - text_video_alignment: Prompt adherence score
            - overall_quality: Weighted average of all dimensions
    
    Raises:
        FileNotFoundError: If video clip path doesn't exist
        ValueError: If video cannot be processed
    """
    if not os.path.exists(video_clip_path):
        raise FileNotFoundError(f"Video clip not found: {video_clip_path}")
    
    logger.info(f"Evaluating video quality: {video_clip_path}")
    
    # Performance monitoring: track evaluation time
    start_time = time.time()
    
    try:
        if vbench_available:
            # TODO: Implement VBench library integration when available
            # Example structure:
            # vbench = VBench()
            # results = vbench.evaluate(video_clip_path, prompt_text)
            # return _normalize_vbench_results(results)
            logger.warning("VBench library integration pending. Using fallback metrics.")
        
        # Fallback: Use basic quality metrics
        scores = _evaluate_fallback_metrics(video_clip_path, prompt_text)
        
        # Convert NumPy float types to native Python floats for JSON serialization
        scores = _convert_numpy_to_python(scores)
        
        # Log performance
        elapsed_time = time.time() - start_time
        logger.info(f"Quality evaluation completed in {elapsed_time:.2f}s for {video_clip_path}")
        
        if elapsed_time > PERFORMANCE_TARGET_SECONDS:
            logger.warning(
                f"Quality evaluation exceeded target time: {elapsed_time:.2f}s > {PERFORMANCE_TARGET_SECONDS}s "
                f"for {video_clip_path}"
            )
        
        return scores
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"Quality evaluation failed after {elapsed_time:.2f}s for {video_clip_path}: {e}",
            exc_info=True
        )
        raise


def _convert_numpy_to_python(scores: Dict[str, float]) -> Dict[str, float]:
    """
    Convert NumPy float types to native Python floats for JSON serialization.
    
    Args:
        scores: Dictionary with potentially NumPy float values
    
    Returns:
        Dict with all float values converted to native Python floats
    """
    converted = {}
    for key, value in scores.items():
        if isinstance(value, (np.floating, np.integer)):
            converted[key] = float(value)
        elif isinstance(value, float):
            converted[key] = value
        else:
            converted[key] = value
    return converted


def _evaluate_fallback_metrics(video_path: str, prompt: str) -> Dict[str, float]:
    """
    Fallback quality evaluation using OpenCV and basic image processing.
    
    This provides basic quality metrics when VBench is unavailable.
    For production, VBench library integration should be prioritized.
    
    Args:
        video_path: Path to video file
        prompt: Generation prompt
    
    Returns:
        Dict[str, float]: Quality scores (0-100 scale)
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Optimize: Sample frames instead of processing all
        # Sample up to 20 frames evenly distributed across the video for faster evaluation
        max_samples = min(20, total_frames)
        sample_indices = []
        if total_frames > 1:
            step = max(1, total_frames // max_samples)
            sample_indices = list(range(0, total_frames, step))[:max_samples]
        else:
            sample_indices = [0]
        
        frames = []
        frame_count = 0
        
        # Extract sampled frames only
        for frame_idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                frame_count += 1
        
        cap.release()
        
        if frame_count == 0:
            raise ValueError(f"No frames extracted from video: {video_path}")
        
        logger.debug(f"Sampled {frame_count} frames from {total_frames} total frames for quality evaluation")
        
        # Basic quality metrics
        scores = {
            "temporal_quality": _compute_temporal_consistency(frames),
            "subject_consistency": _compute_subject_consistency(frames),
            "background_consistency": _compute_background_consistency(frames),
            "motion_smoothness": _compute_motion_smoothness(frames),
            "dynamic_degree": _compute_dynamic_degree(frames),
            "aesthetic_quality": _compute_aesthetic_quality(frames),
            "imaging_quality": _compute_imaging_quality(frames),
            "object_class_alignment": 70.0,  # Placeholder - requires object detection
            "text_video_alignment": 70.0,  # Placeholder - requires semantic analysis
        }
        
        # Compute overall quality (weighted average)
        scores["overall_quality"] = _compute_overall_quality(scores)
        
        logger.info(f"Quality evaluation complete. Overall score: {scores['overall_quality']:.2f}")
        return scores
        
    except Exception as e:
        logger.error(f"Error evaluating video quality: {e}", exc_info=True)
        # Return default scores on error (graceful degradation)
        return _get_default_scores()


def _compute_temporal_consistency(frames: list) -> float:
    """Compute temporal consistency score (0-100)."""
    if len(frames) < 2:
        return 50.0
    
    # Compute frame-to-frame similarity
    similarities = []
    for i in range(len(frames) - 1):
        # Convert to grayscale for comparison
        gray1 = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frames[i + 1], cv2.COLOR_BGR2GRAY)
        
        # Compute structural similarity
        # Using histogram correlation as simple metric
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        similarities.append(correlation * 100)
    
    result = np.mean(similarities) if similarities else 50.0
    return float(result)  # Convert to native Python float


def _compute_subject_consistency(frames: list) -> float:
    """Compute subject consistency score (0-100)."""
    # Placeholder: Would require object detection/tracking
    # For now, use temporal consistency as proxy
    return _compute_temporal_consistency(frames)


def _compute_background_consistency(frames: list) -> float:
    """Compute background consistency score (0-100)."""
    # Placeholder: Would require background segmentation
    # For now, use temporal consistency as proxy
    return _compute_temporal_consistency(frames)


def _compute_motion_smoothness(frames: list) -> float:
    """Compute motion smoothness score (0-100)."""
    if len(frames) < 2:
        return 50.0
    
    # Optimize: Use frame difference instead of expensive optical flow for speed
    # This is much faster while still providing reasonable motion smoothness estimate
    gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    frame_diffs = []
    
    for i in range(len(gray_frames) - 1):
        # Simple frame difference (much faster than optical flow)
        diff = cv2.absdiff(gray_frames[i], gray_frames[i + 1])
        mean_diff = float(np.mean(diff))
        frame_diffs.append(mean_diff)
    
    if not frame_diffs:
        return 50.0
    
    # Smooth motion = lower variance in frame differences
    mean_diff = float(np.mean(frame_diffs))
    std_diff = float(np.std(frame_diffs))
    
    # Score: higher for smoother motion (lower variance)
    # Normalize: assume max reasonable diff is ~50 (out of 255)
    smoothness = max(0, 100 - (std_diff / max(mean_diff, 1)) * 30)
    return float(min(100, smoothness))  # Convert to native Python float


def _compute_dynamic_degree(frames: list) -> float:
    """Compute dynamic degree score (0-100)."""
    if len(frames) < 2:
        return 50.0
    
    # Optimize: Use frame difference instead of expensive optical flow
    gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    motion_scores = []
    
    for i in range(len(gray_frames) - 1):
        # Simple frame difference (much faster than optical flow)
        diff = cv2.absdiff(gray_frames[i], gray_frames[i + 1])
        mean_diff = float(np.mean(diff))
        motion_scores.append(mean_diff)
    
    if not motion_scores:
        return 50.0
    
    # Dynamic degree: higher for more motion
    mean_motion = float(np.mean(motion_scores))
    # Normalize to 0-100 scale (assuming max reasonable diff is ~50 out of 255)
    dynamic = min(100, (mean_motion / 50) * 100)
    return float(dynamic)  # Convert to native Python float


def _compute_aesthetic_quality(frames: list) -> float:
    """Compute aesthetic quality score (0-100)."""
    if not frames:
        return 50.0
    
    # Basic aesthetic metrics: sharpness, contrast, brightness balance
    scores = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness = min(100, (laplacian_var / 500) * 100)  # Normalize
        
        # Contrast (standard deviation)
        contrast = min(100, np.std(gray) / 2.55)  # Normalize to 0-100
        
        # Brightness balance (avoid over/under exposure)
        mean_brightness = np.mean(gray)
        brightness_score = 100 - abs(mean_brightness - 128) / 1.28  # Optimal around 128
        
        # Combined aesthetic score
        aesthetic = (sharpness * 0.4 + contrast * 0.3 + brightness_score * 0.3)
        scores.append(aesthetic)
    
    result = np.mean(scores) if scores else 50.0
    return float(result)  # Convert to native Python float


def _compute_imaging_quality(frames: list) -> float:
    """Compute imaging quality score (0-100)."""
    if not frames:
        return 50.0
    
    # Imaging quality: resolution, noise, artifacts
    scores = []
    for frame in frames:
        # Resolution quality (assume HD+ is good)
        height, width = frame.shape[:2]
        resolution_score = min(100, (height * width / (1920 * 1080)) * 100)
        
        # Noise estimation (variance in smooth regions)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Use median filter to estimate noise
        filtered = cv2.medianBlur(gray, 5)
        noise = np.std(gray - filtered)
        noise_score = max(0, 100 - noise * 10)  # Lower noise = higher score
        
        # Combined imaging quality
        imaging = (resolution_score * 0.5 + noise_score * 0.5)
        scores.append(imaging)
    
    result = np.mean(scores) if scores else 50.0
    return float(result)  # Convert to native Python float


def _compute_overall_quality(scores: Dict[str, float]) -> float:
    """
    Compute overall quality score from individual dimension scores.
    
    Returns native Python float (not NumPy float).
    
    Weights:
    - Temporal quality: 30%
    - Frame-wise quality: 30%
    - Text-video alignment: 25%
    - Other factors: 15%
    """
    weights = {
        "temporal_quality": 0.15,
        "subject_consistency": 0.10,
        "background_consistency": 0.05,
        "motion_smoothness": 0.10,
        "dynamic_degree": 0.05,
        "aesthetic_quality": 0.20,
        "imaging_quality": 0.15,
        "object_class_alignment": 0.05,
        "text_video_alignment": 0.15,
    }
    
    overall = sum(scores.get(key, 0) * weight for key, weight in weights.items())
    return round(overall, 2)


def _get_default_scores() -> Dict[str, float]:
    """Return default quality scores when evaluation fails."""
    return {
        "temporal_quality": 50.0,
        "subject_consistency": 50.0,
        "background_consistency": 50.0,
        "motion_smoothness": 50.0,
        "dynamic_degree": 50.0,
        "aesthetic_quality": 50.0,
        "imaging_quality": 50.0,
        "object_class_alignment": 50.0,
        "text_video_alignment": 50.0,
        "overall_quality": 50.0,
    }


def check_quality_thresholds(
    vbench_scores: Dict[str, float],
    thresholds: Optional[Dict[str, float]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if quality scores meet thresholds.
    
    Args:
        vbench_scores: Quality scores from evaluate_vbench()
        thresholds: Optional custom thresholds (defaults to config values)
    
    Returns:
        Tuple[bool, Dict[str, Any]]: (passed, details)
            - passed: True if all thresholds met, False otherwise
            - details: Dict with threshold results, failed dimensions, etc.
    """
    from app.core.config import settings
    
    # Use provided thresholds or defaults from config
    if thresholds is None:
        thresholds = {
            "temporal_quality": settings.QUALITY_THRESHOLD_TEMPORAL,
            "frame_wise_quality": settings.QUALITY_THRESHOLD_FRAME_WISE,
            "text_video_alignment": settings.QUALITY_THRESHOLD_TEXT_VIDEO_ALIGNMENT,
            "overall_quality": settings.QUALITY_THRESHOLD_OVERALL,
        }
    
    # Check each threshold
    results = {
        "temporal_passed": vbench_scores.get("temporal_quality", 0) >= thresholds.get("temporal_quality", 70),
        "frame_wise_passed": (
            vbench_scores.get("aesthetic_quality", 0) >= thresholds.get("frame_wise_quality", 70) and
            vbench_scores.get("imaging_quality", 0) >= thresholds.get("frame_wise_quality", 70)
        ),
        "text_video_alignment_passed": vbench_scores.get("text_video_alignment", 0) >= thresholds.get("text_video_alignment", 70),
        "overall_passed": vbench_scores.get("overall_quality", 0) >= thresholds.get("overall_quality", 70),
    }
    
    # Collect failed dimensions
    failed_dimensions = []
    if not results["temporal_passed"]:
        failed_dimensions.append({
            "dimension": "temporal_quality",
            "score": vbench_scores.get("temporal_quality", 0),
            "threshold": thresholds.get("temporal_quality", 70),
        })
    if not results["frame_wise_passed"]:
        failed_dimensions.append({
            "dimension": "frame_wise_quality",
            "aesthetic_score": vbench_scores.get("aesthetic_quality", 0),
            "imaging_score": vbench_scores.get("imaging_quality", 0),
            "threshold": thresholds.get("frame_wise_quality", 70),
        })
    if not results["text_video_alignment_passed"]:
        failed_dimensions.append({
            "dimension": "text_video_alignment",
            "score": vbench_scores.get("text_video_alignment", 0),
            "threshold": thresholds.get("text_video_alignment", 70),
        })
    if not results["overall_passed"]:
        failed_dimensions.append({
            "dimension": "overall_quality",
            "score": vbench_scores.get("overall_quality", 0),
            "threshold": thresholds.get("overall_quality", 70),
        })
    
    # Overall result: all thresholds must pass
    passed = all(results.values())
    
    details = {
        "passed": passed,
        "threshold_results": results,
        "failed_dimensions": failed_dimensions,
        "overall_score": vbench_scores.get("overall_quality", 0),
        "overall_threshold": thresholds.get("overall_quality", 70),
    }
    
    logger.info(f"Quality threshold check: {'PASSED' if passed else 'FAILED'} (overall: {vbench_scores.get('overall_quality', 0):.2f}/{thresholds.get('overall_quality', 70)})")
    
    return passed, details


def store_quality_metric(
    db,
    generation_id: str,
    scene_number: int,
    clip_path: str,
    vbench_scores: Dict[str, float],
    passed_threshold: bool,
    regeneration_attempts: int = 0
) -> str:
    """
    Store quality metric in database.
    
    Args:
        db: Database session
        generation_id: Generation ID
        scene_number: Scene/clip number
        clip_path: Path to the evaluated clip
        vbench_scores: VBench quality scores
        passed_threshold: Whether thresholds were met
        regeneration_attempts: Number of regeneration attempts (default: 0)
    
    Returns:
        str: Quality metric ID
    """
    from app.db.models.quality_metric import QualityMetric
    
    # Ensure all scores are native Python types for JSON serialization
    vbench_scores = _convert_numpy_to_python(vbench_scores)
    overall_quality = float(vbench_scores.get("overall_quality", 0))
    
    quality_metric = QualityMetric(
        generation_id=generation_id,
        scene_number=scene_number,
        clip_path=clip_path,
        vbench_scores=vbench_scores,
        overall_quality=overall_quality,
        passed_threshold=passed_threshold,
        regeneration_attempts=regeneration_attempts,
    )
    
    db.add(quality_metric)
    db.commit()
    db.refresh(quality_metric)
    
    logger.info(
        f"Stored quality metric for generation {generation_id}, scene {scene_number}: "
        f"overall={vbench_scores.get('overall_quality', 0):.2f}, passed={passed_threshold}"
    )
    
    return quality_metric.id


async def evaluate_and_store_quality(
    db,
    generation_id: str,
    scene_number: int,
    clip_path: str,
    prompt_text: str,
    coherence_settings: Optional[Dict] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Evaluate video quality and store metrics if VBench quality control is enabled.
    
    This function is async to support non-blocking quality assessment in the pipeline.
    Performance is monitored and logged.
    
    Args:
        db: Database session
        generation_id: Generation ID
        scene_number: Scene/clip number
        clip_path: Path to the video clip
        prompt_text: Prompt text used for generation
        coherence_settings: Optional coherence settings dict (checks vbench_quality_control flag)
    
    Returns:
        Tuple[bool, Dict[str, Any]]: (passed_threshold, quality_details)
            - passed_threshold: True if quality meets thresholds, False otherwise
            - quality_details: Dict with evaluation results, scores, performance metrics, etc.
    """
    from app.services.coherence_settings import apply_defaults
    
    # Performance monitoring
    start_time = time.time()
    
    # Check if VBench quality control is enabled
    if coherence_settings:
        settings = apply_defaults(coherence_settings)
        if not settings.vbench_quality_control:
            logger.debug(f"VBench quality control disabled for generation {generation_id}, skipping evaluation")
            return True, {"skipped": True, "reason": "vbench_quality_control disabled"}
    else:
        # Default: enabled (from get_default_settings)
        settings = apply_defaults(None)
        if not settings.vbench_quality_control:
            logger.debug(f"VBench quality control disabled (default), skipping evaluation")
            return True, {"skipped": True, "reason": "vbench_quality_control disabled"}
    
    try:
        # Evaluate quality (async where possible - currently synchronous but structured for future async)
        vbench_scores = evaluate_vbench(clip_path, prompt_text)
        
        # Check thresholds
        passed, details = check_quality_thresholds(vbench_scores)
        
        # Store quality metric
        metric_id = store_quality_metric(
            db=db,
            generation_id=generation_id,
            scene_number=scene_number,
            clip_path=clip_path,
            vbench_scores=vbench_scores,
            passed_threshold=passed,
            regeneration_attempts=0,  # Initial attempt
        )
        
        # Calculate performance metrics
        elapsed_time = time.time() - start_time
        
        quality_details = {
            "metric_id": metric_id,
            "scores": vbench_scores,
            "passed": passed,
            "details": details,
            "skipped": False,
            "performance": {
                "evaluation_time_seconds": round(elapsed_time, 2),
                "within_target": elapsed_time <= PERFORMANCE_TARGET_SECONDS,
            },
        }
        
        # Log performance
        if elapsed_time > PERFORMANCE_TARGET_SECONDS:
            logger.warning(
                f"Quality assessment exceeded target time for generation {generation_id}, scene {scene_number}: "
                f"{elapsed_time:.2f}s > {PERFORMANCE_TARGET_SECONDS}s"
            )
        else:
            logger.debug(
                f"Quality assessment completed in {elapsed_time:.2f}s for generation {generation_id}, scene {scene_number}"
            )
        
        return passed, quality_details
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"Error evaluating quality for clip {clip_path} (took {elapsed_time:.2f}s): {e}",
            exc_info=True
        )
        # Graceful degradation: continue generation even if quality assessment fails
        return True, {
            "skipped": True,
            "reason": f"quality evaluation failed: {str(e)}",
            "error": str(e),
            "performance": {
                "evaluation_time_seconds": round(elapsed_time, 2),
                "within_target": False,
            },
        }


async def regenerate_clip(
    db,
    generation_id: str,
    scene_number: int,
    scene: "Scene",
    output_dir: str,
    original_clip_path: str,
    prompt_text: str,
    coherence_settings: Optional[Dict] = None,
    cancellation_check: Optional[callable] = None,
    seed: Optional[int] = None,
    preferred_model: Optional[str] = None,
    max_attempts: int = 3,
    all_attempts: Optional[List[Dict[str, Any]]] = None
) -> Tuple[Optional[str], bool, Dict[str, Any]]:
    """
    Regenerate a clip that failed quality thresholds.
    
    Tracks all regeneration attempts (including the original) and selects the best quality clip
    when max attempts are reached. Stops early if any attempt passes quality thresholds.
    
    Args:
        db: Database session
        generation_id: Generation ID
        scene_number: Scene/clip number
        scene: Scene object with visual_prompt and duration
        output_dir: Directory to save regenerated clip
        original_clip_path: Path to the original low-quality clip
        prompt_text: Prompt text used for generation
        coherence_settings: Optional coherence settings
        cancellation_check: Optional cancellation check function
        seed: Original seed value (will be modified for retry)
        preferred_model: Preferred model to use
        max_attempts: Maximum regeneration attempts (default: 3, including original = 4 total)
        all_attempts: Internal list tracking all attempts and their quality scores
    
    Returns:
        Tuple[Optional[str], bool, Dict[str, Any]]: (best_clip_path, success, details)
            - best_clip_path: Path to the best quality clip (may be original or regenerated)
            - success: True if any attempt passed quality thresholds, False otherwise
            - details: Dict with regeneration attempt info, quality scores, best attempt number, etc.
    """
    from app.services.video_generation import generate_video_clip
    from app.db.models.quality_metric import QualityMetric
    import random
    
    # Initialize attempts list if not provided (first call)
    if all_attempts is None:
        all_attempts = []
        # Get original clip quality from existing metric
        existing_metric = db.query(QualityMetric).filter(
            QualityMetric.generation_id == generation_id,
            QualityMetric.scene_number == scene_number
        ).first()
        if existing_metric:
            # Store original attempt
            all_attempts.append({
                "clip_path": original_clip_path,
                "overall_quality": existing_metric.overall_quality,
                "vbench_scores": existing_metric.vbench_scores,
                "attempt": 0,
                "is_original": True
            })
    
    # Get existing quality metric to track attempts
    existing_metric = db.query(QualityMetric).filter(
        QualityMetric.generation_id == generation_id,
        QualityMetric.scene_number == scene_number
    ).first()
    
    if not existing_metric:
        logger.warning(f"No quality metric found for generation {generation_id}, scene {scene_number}")
        return None, False, {"error": "No quality metric found"}
    
    current_attempts = existing_metric.regeneration_attempts
    
    if current_attempts >= max_attempts:
        logger.warning(
            f"Max regeneration attempts ({max_attempts}) reached for generation {generation_id}, scene {scene_number}"
        )
        return None, False, {
            "error": f"Max regeneration attempts ({max_attempts}) reached",
            "attempts": current_attempts
        }
    
    # Increment regeneration attempts
    new_attempt = current_attempts + 1
    
    # Performance monitoring for regeneration
    regen_start_time = time.time()
    
    logger.info(
        f"Regenerating clip for generation {generation_id}, scene {scene_number} "
        f"(attempt {new_attempt}/{max_attempts})"
    )
    
    # Modify seed for retry (add variation to get different result)
    retry_seed = None
    if seed is not None:
        # Add variation to seed: add attempt number and random offset
        retry_seed = (seed + new_attempt * 1000 + random.randint(1, 999)) % (2**31)
        logger.debug(f"Using modified seed for regeneration: {seed} -> {retry_seed}")
    else:
        # If no seed was used, generate a new one
        retry_seed = random.randint(0, 2**31 - 1)
        logger.debug(f"Generating new seed for regeneration: {retry_seed}")
    
    try:
        # Regenerate clip with modified seed
        new_clip_path, model_used = await generate_video_clip(
            scene=scene,
            output_dir=output_dir,
            generation_id=generation_id,
            scene_number=scene_number,
            cancellation_check=cancellation_check,
            seed=retry_seed,  # Use modified seed
            preferred_model=preferred_model
        )
        
        logger.info(f"Regenerated clip: {new_clip_path} (attempt {new_attempt})")
        
        # Re-evaluate quality (but don't store new metric - update existing one)
        from app.services.coherence_settings import apply_defaults
        
        # Check if VBench quality control is enabled
        if coherence_settings:
            settings = apply_defaults(coherence_settings)
            vbench_enabled = settings.vbench_quality_control
        else:
            settings = apply_defaults(None)
            vbench_enabled = settings.vbench_quality_control
        
        if vbench_enabled:
            try:
                vbench_scores = evaluate_vbench(new_clip_path, prompt_text)
                quality_passed, threshold_details = check_quality_thresholds(vbench_scores)
                quality_details = {
                    "scores": vbench_scores,
                    "passed": quality_passed,
                    "details": threshold_details,
                    "skipped": False,
                }
            except Exception as e:
                logger.error(f"Error re-evaluating quality for regenerated clip: {e}", exc_info=True)
                # If evaluation fails, assume it passed to continue
                quality_passed = True
                quality_details = {"skipped": True, "reason": f"evaluation failed: {str(e)}"}
        else:
            quality_passed = True
            quality_details = {"skipped": True, "reason": "vbench_quality_control disabled"}
        
        # Store this attempt in the list
        scores = _convert_numpy_to_python(quality_details.get("scores", {}))
        overall_quality = float(scores.get("overall_quality", 0))
        
        all_attempts.append({
            "clip_path": new_clip_path,
            "overall_quality": overall_quality,
            "vbench_scores": scores,
            "attempt": new_attempt,
            "is_original": False,
            "quality_passed": quality_passed
        })
        
        regen_elapsed = time.time() - regen_start_time
        
        if quality_passed:
            # Quality passed threshold - use this clip and stop
            existing_metric.regeneration_attempts = new_attempt
            existing_metric.clip_path = new_clip_path
            existing_metric.passed_threshold = True
            existing_metric.vbench_scores = scores
            existing_metric.overall_quality = overall_quality
            db.commit()
            
            logger.info(
                f"Regeneration successful! Quality improved for generation {generation_id}, scene {scene_number}. "
                f"New overall quality: {overall_quality:.2f} (took {regen_elapsed:.2f}s)"
            )
            
            return new_clip_path, True, {
                "attempt": new_attempt,
                "new_clip_path": new_clip_path,
                "quality_passed": True,
                "overall_quality": overall_quality,
                "scores": scores,
                "regeneration_time_seconds": round(regen_elapsed, 2),
            }
        else:
            # Quality still below threshold
            logger.warning(
                f"Regeneration attempt {new_attempt} completed but quality still below threshold "
                f"(overall: {overall_quality:.2f})"
            )
            
            # If we've reached max attempts, choose the best clip from all attempts
            if new_attempt >= max_attempts:
                # Find the best quality clip from all attempts
                best_attempt = max(all_attempts, key=lambda x: x["overall_quality"])
                best_clip_path = best_attempt["clip_path"]
                best_quality = best_attempt["overall_quality"]
                
                logger.info(
                    f"Max regeneration attempts ({max_attempts}) reached. "
                    f"Best quality from {len(all_attempts)} attempts: {best_quality:.2f} "
                    f"(attempt {best_attempt['attempt']}). Using: {best_clip_path}"
                )
                
                # Update metric with best attempt
                existing_metric.regeneration_attempts = new_attempt
                existing_metric.clip_path = best_clip_path
                existing_metric.passed_threshold = best_attempt.get("quality_passed", False)
                existing_metric.vbench_scores = best_attempt["vbench_scores"]
                existing_metric.overall_quality = best_quality
                db.commit()
                
                return best_clip_path, False, {
                    "attempt": new_attempt,
                    "new_clip_path": best_clip_path,
                    "quality_passed": best_attempt.get("quality_passed", False),
                    "overall_quality": best_quality,
                    "scores": best_attempt["vbench_scores"],
                    "max_attempts_reached": True,
                    "total_attempts": len(all_attempts),
                    "best_attempt_number": best_attempt["attempt"],
                }
            
            # Try again if we have attempts left
            return await regenerate_clip(
                db=db,
                generation_id=generation_id,
                scene_number=scene_number,
                scene=scene,
                output_dir=output_dir,
                original_clip_path=new_clip_path,
                prompt_text=prompt_text,
                coherence_settings=coherence_settings,
                cancellation_check=cancellation_check,
                seed=retry_seed,  # Use the modified seed as base for next attempt
                preferred_model=preferred_model,
                max_attempts=max_attempts,
                all_attempts=all_attempts  # Pass attempts list to next call
            )
        
    except Exception as e:
        logger.error(
            f"Error during regeneration attempt {new_attempt} for generation {generation_id}, "
            f"scene {scene_number}: {e}",
            exc_info=True
        )
        
        # Update attempt count even on failure
        existing_metric.regeneration_attempts = new_attempt
        db.commit()
        
        regen_elapsed = time.time() - regen_start_time
        logger.error(
            f"Regeneration failed after {regen_elapsed:.2f}s for generation {generation_id}, "
            f"scene {scene_number}, attempt {new_attempt}: {e}"
        )
        
        return None, False, {
            "attempt": new_attempt,
            "error": str(e),
            "regeneration_failed": True,
            "regeneration_time_seconds": round(regen_elapsed, 2),
        }

