"""
Video quality scoring service wrapper for VBench evaluation.

This service wraps the VBench evaluation from quality_control.py and provides:
- Overall quality score calculation (weighted combination)
- Video ranking by quality
- Batch scoring support
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.services.pipeline.quality_control import evaluate_vbench

logger = logging.getLogger(__name__)

# Quality score weights (from Story 9.2 AC #2)
TEMPORAL_QUALITY_WEIGHT = 0.40  # 40%
FRAME_WISE_QUALITY_WEIGHT = 0.35  # 35%
TEXT_VIDEO_ALIGNMENT_WEIGHT = 0.25  # 25%

# Temporal Quality dimensions (40% total)
TEMPORAL_DIMENSIONS = [
    "subject_consistency",
    "background_consistency",
    "motion_smoothness",
    "dynamic_degree",
]
TEMPORAL_DIMENSION_WEIGHT = TEMPORAL_QUALITY_WEIGHT / len(TEMPORAL_DIMENSIONS)  # 10% each

# Frame-wise Quality dimensions (35% total)
FRAME_WISE_DIMENSIONS = [
    "aesthetic_quality",
    "imaging_quality",
    "object_class_alignment",
]
FRAME_WISE_DIMENSION_WEIGHT = FRAME_WISE_QUALITY_WEIGHT / len(FRAME_WISE_DIMENSIONS)  # ~11.67% each

# Text-Video Alignment dimension (25% total)
TEXT_VIDEO_ALIGNMENT_DIMENSION = "text_video_alignment"


def calculate_overall_quality_score(vbench_scores: Dict[str, float]) -> float:
    """
    Calculate overall quality score from VBench scores using weighted combination.
    
    Weighting (from Story 9.2 AC #2):
    - Temporal Quality: 40% (subject_consistency, background_consistency, motion_smoothness, dynamic_degree)
    - Frame-wise Quality: 35% (aesthetic_quality, imaging_quality, object_class_alignment)
    - Text-Video Alignment: 25% (text_video_alignment)
    
    Args:
        vbench_scores: Dictionary of VBench scores (all 16 dimensions)
    
    Returns:
        float: Overall quality score (0-100)
    """
    overall = 0.0
    
    # Temporal Quality (40%)
    temporal_sum = 0.0
    temporal_count = 0
    for dim in TEMPORAL_DIMENSIONS:
        if dim in vbench_scores:
            temporal_sum += vbench_scores[dim]
            temporal_count += 1
    
    if temporal_count > 0:
        temporal_avg = temporal_sum / temporal_count
        overall += temporal_avg * TEMPORAL_QUALITY_WEIGHT
    
    # Frame-wise Quality (35%)
    frame_wise_sum = 0.0
    frame_wise_count = 0
    for dim in FRAME_WISE_DIMENSIONS:
        if dim in vbench_scores:
            frame_wise_sum += vbench_scores[dim]
            frame_wise_count += 1
    
    if frame_wise_count > 0:
        frame_wise_avg = frame_wise_sum / frame_wise_count
        overall += frame_wise_avg * FRAME_WISE_QUALITY_WEIGHT
    
    # Text-Video Alignment (25%)
    if TEXT_VIDEO_ALIGNMENT_DIMENSION in vbench_scores:
        overall += vbench_scores[TEXT_VIDEO_ALIGNMENT_DIMENSION] * TEXT_VIDEO_ALIGNMENT_WEIGHT
    
    # Normalize if some dimensions are missing
    # If all dimensions are present, total weight should be 1.0
    # If some are missing, we normalize by actual weight used
    actual_weight = (
        (TEMPORAL_QUALITY_WEIGHT if temporal_count > 0 else 0.0) +
        (FRAME_WISE_QUALITY_WEIGHT if frame_wise_count > 0 else 0.0) +
        (TEXT_VIDEO_ALIGNMENT_WEIGHT if TEXT_VIDEO_ALIGNMENT_DIMENSION in vbench_scores else 0.0)
    )
    
    if actual_weight > 0:
        overall = overall / actual_weight
    
    return round(overall, 2)


def score_video(
    video_path: str,
    prompt_text: str,
    vbench_available: Optional[bool] = None,
) -> Dict[str, float]:
    """
    Score a single video using VBench evaluation.
    
    Args:
        video_path: Path to the video file
        prompt_text: Text prompt used for generation
        vbench_available: Whether VBench library is available (default: from quality_control.py)
    
    Returns:
        Dict[str, float]: VBench scores dictionary with all dimensions + overall_quality
    
    Raises:
        FileNotFoundError: If video file doesn't exist
    """
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    logger.info(f"Scoring video: {video_path}")
    
    try:
        # Call VBench evaluation from quality_control.py
        vbench_scores = evaluate_vbench(
            video_clip_path=video_path,
            prompt_text=prompt_text,
            vbench_available=vbench_available,
        )
        
        # Calculate overall quality score
        overall_quality = calculate_overall_quality_score(vbench_scores)
        
        # Add overall quality to scores
        vbench_scores["overall_quality"] = overall_quality
        
        logger.info(f"Video scored: overall_quality={overall_quality:.2f}")
        
        return vbench_scores
        
    except Exception as e:
        logger.error(f"Failed to score video {video_path}: {e}", exc_info=True)
        # Return default scores if evaluation fails
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


def score_videos_batch(
    video_paths: List[str],
    prompt_texts: List[str],
    vbench_available: Optional[bool] = None,
) -> List[Dict[str, float]]:
    """
    Score multiple videos in batch.
    
    Args:
        video_paths: List of video file paths
        prompt_texts: List of prompts (one per video)
        vbench_available: Whether VBench library is available
    
    Returns:
        List[Dict[str, float]]: List of VBench scores dictionaries (one per video)
    
    Raises:
        ValueError: If video_paths and prompt_texts have different lengths
    """
    if len(video_paths) != len(prompt_texts):
        raise ValueError(
            f"video_paths ({len(video_paths)}) and prompt_texts ({len(prompt_texts)}) "
            "must have the same length"
        )
    
    logger.info(f"Scoring {len(video_paths)} videos in batch")
    
    scores_list = []
    failed_videos = []
    
    for i, (video_path, prompt_text) in enumerate(zip(video_paths, prompt_texts)):
        try:
            scores = score_video(video_path, prompt_text, vbench_available)
            scores_list.append(scores)
        except Exception as e:
            logger.error(f"Failed to score video {i+1}/{len(video_paths)} ({video_path}): {e}")
            failed_videos.append((video_path, str(e)))
            # Add default scores for failed videos
            scores_list.append({
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
            })
    
    if failed_videos:
        logger.warning(f"Failed to score {len(failed_videos)} videos:")
        for video_path, error in failed_videos:
            logger.warning(f"  - {video_path}: {error}")
    
    return scores_list


def rank_videos_by_quality(
    video_paths: List[str],
    scores_list: List[Dict[str, float]],
) -> List[Tuple[str, Dict[str, float], int]]:
    """
    Rank videos by overall quality score (best first).
    
    Args:
        video_paths: List of video file paths
        scores_list: List of VBench scores dictionaries (one per video)
    
    Returns:
        List of (video_path, scores_dict, rank) tuples, sorted by overall_quality (descending)
        Rank 1 = best, Rank 2 = second-best, etc.
    """
    if len(video_paths) != len(scores_list):
        raise ValueError(
            f"video_paths ({len(video_paths)}) and scores_list ({len(scores_list)}) "
            "must have the same length"
        )
    
    # Combine paths and scores
    video_results = list(zip(video_paths, scores_list))
    
    # Sort by overall_quality (descending)
    ranked = sorted(
        video_results,
        key=lambda x: x[1].get("overall_quality", 0.0),
        reverse=True,
    )
    
    # Add rank (1 = best, 2 = second-best, etc.)
    ranked_with_rank = [
        (video_path, scores, rank + 1)
        for rank, (video_path, scores) in enumerate(ranked)
    ]
    
    return ranked_with_rank


