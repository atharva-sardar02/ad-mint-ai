"""
Time estimation service for video generation.

Calculates estimated generation time based on:
- Number of variations/clips
- Duration per clip
- Model selection
- Coherence settings (LLM, quality control, etc.)
"""

import logging
from typing import List, Optional
from app.schemas.generation import GenerateRequest

logger = logging.getLogger(__name__)

# Base time estimates (in seconds)
BASE_LLM_TIME = 5  # LLM prompt enhancement
BASE_SCENE_PLANNING_TIME = 3  # Scene planning
BASE_CLIP_GENERATION_TIME = 30  # Per clip (model-dependent)
BASE_STITCHING_TIME = 10  # Stitching clips together
BASE_AUDIO_TIME = 5  # Adding audio
BASE_EXPORT_TIME = 15  # Final export
BASE_QUALITY_CONTROL_TIME = 5  # Per clip quality evaluation

# Model-specific generation time multipliers
MODEL_TIME_MULTIPLIERS = {
    "stable-video-diffusion": 1.0,  # Baseline
    "zeroscope-v2": 0.8,  # Faster
    "animatediff": 1.2,  # Slower
    "gen-2": 1.0,  # Baseline
    "kling-v1": 1.1,  # Slightly slower
    "runway-gen3": 1.0,  # Baseline
}

# Average clip duration (seconds) - used when not specified
DEFAULT_CLIP_DURATION = 5


def estimate_generation_time(
    variations: List[GenerateRequest],
    parallel: bool = True
) -> int:
    """
    Estimate total generation time in seconds for parallel generation.
    
    Args:
        variations: List of generation requests
        parallel: Whether generations run in parallel (default: True)
    
    Returns:
        Estimated time in seconds
    """
    if not variations:
        return 0
    
    total_time = 0
    
    # For parallel generation, estimate based on the longest variation
    # since they run concurrently
    if parallel:
        max_variation_time = 0
        
        for variation in variations:
            variation_time = _estimate_single_generation_time(variation)
            max_variation_time = max(max_variation_time, variation_time)
        
        total_time = max_variation_time
    else:
        # Sequential: sum all variation times
        for variation in variations:
            total_time += _estimate_single_generation_time(variation)
    
    # Add overhead for parallel coordination
    if parallel and len(variations) > 1:
        total_time += 5  # Small overhead for coordination
    
    return int(total_time)


def _estimate_single_generation_time(variation: GenerateRequest) -> float:
    """
    Estimate time for a single video generation.
    
    Args:
        variation: Single generation request
    
    Returns:
        Estimated time in seconds
    """
    time = 0
    
    # LLM enhancement time
    use_llm = variation.use_llm if variation.use_llm is not None else True
    # Check if single clip mode (via num_clips=1 and no LLM, or explicit flag if exists)
    use_single_clip = False
    if hasattr(variation, 'use_single_clip'):
        use_single_clip = variation.use_single_clip
    elif hasattr(variation, 'num_clips') and variation.num_clips == 1 and not use_llm:
        use_single_clip = True
    
    if use_llm and not use_single_clip:
        time += BASE_LLM_TIME
        time += BASE_SCENE_PLANNING_TIME
    
    # Determine number of clips
    if use_single_clip:
        num_clips = 1
    elif hasattr(variation, 'num_clips') and variation.num_clips:
        num_clips = variation.num_clips
    else:
        # Default: estimate based on typical scene plan (3-5 scenes)
        num_clips = 4
    
    # Model selection affects generation time
    model_multiplier = 1.0
    if variation.model:
        model_multiplier = MODEL_TIME_MULTIPLIERS.get(
            variation.model,
            1.0  # Default multiplier
        )
    
    # Clip generation time (per clip, model-dependent)
    clip_time = BASE_CLIP_GENERATION_TIME * model_multiplier
    time += clip_time * num_clips
    
    # Quality control time (per clip, if enabled)
    coherence_settings = variation.coherence_settings
    if coherence_settings:
        # Handle both Pydantic model and dict
        if hasattr(coherence_settings, 'vbench_quality_control'):
            vbench_enabled = coherence_settings.vbench_quality_control
        elif isinstance(coherence_settings, dict):
            vbench_enabled = coherence_settings.get("vbench_quality_control", False)
        else:
            vbench_enabled = False
        
        if vbench_enabled:
            time += BASE_QUALITY_CONTROL_TIME * num_clips
            # Potential regeneration time (estimate 20% chance per clip)
            time += (BASE_CLIP_GENERATION_TIME * model_multiplier * 0.2) * num_clips
    
    # Post-processing steps (only if not single clip)
    if not use_single_clip:
        time += BASE_STITCHING_TIME
        time += BASE_AUDIO_TIME
        time += BASE_EXPORT_TIME
    
    return time


def format_estimated_time(seconds: int) -> str:
    """
    Format estimated time in a human-readable format.
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted string (e.g., "2 minutes", "1.5 minutes", "30 seconds")
    """
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 120:
        return "1 minute"
    else:
        minutes = seconds / 60
        if minutes < 2:
            return f"{int(minutes)} minute"
        else:
            return f"{int(minutes)} minutes"

