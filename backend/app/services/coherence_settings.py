"""
Coherence settings service for managing video generation coherence technique settings.
"""
import logging
from typing import Dict, Optional

from app.schemas.generation import CoherenceSettings

logger = logging.getLogger(__name__)


def get_default_settings() -> CoherenceSettings:
    """
    Get default coherence settings with recommended values.
    
    Returns:
        CoherenceSettings: Default settings with recommended techniques enabled
    """
    return CoherenceSettings(
        seed_control=True,
        ip_adapter_reference=False,  # Enabled by default if entities detected (handled by backend logic)
        ip_adapter_sequential=False,
        lora=False,
        enhanced_planning=True,
        vbench_quality_control=True,
        automatic_regeneration=False,  # Disabled by default - user must explicitly enable
        post_processing_enhancement=True,
        color_grading=False,  # Disabled by default - user must explicitly enable
        controlnet=False,
        csfd_detection=False,
    )


def apply_defaults(settings: Optional[Dict]) -> CoherenceSettings:
    """
    Apply default values to coherence settings, filling in missing fields.
    
    Args:
        settings: Optional dictionary with partial coherence settings
    
    Returns:
        CoherenceSettings: Complete settings with defaults applied
    """
    defaults = get_default_settings()
    
    if not settings:
        return defaults
    
    # Convert dict to CoherenceSettings, using defaults for missing fields
    # Handle backward compatibility: if old ip_adapter field exists, map to ip_adapter_reference
    ip_adapter_reference = settings.get("ip_adapter_reference")
    ip_adapter_sequential = settings.get("ip_adapter_sequential")
    
    # Backward compatibility: if old ip_adapter field exists, use it for ip_adapter_reference
    if "ip_adapter" in settings and ip_adapter_reference is None:
        ip_adapter_reference = settings.get("ip_adapter", defaults.ip_adapter_reference)
    
    return CoherenceSettings(
        seed_control=settings.get("seed_control", defaults.seed_control),
        ip_adapter_reference=ip_adapter_reference if ip_adapter_reference is not None else defaults.ip_adapter_reference,
        ip_adapter_sequential=ip_adapter_sequential if ip_adapter_sequential is not None else defaults.ip_adapter_sequential,
        lora=settings.get("lora", defaults.lora),
        enhanced_planning=settings.get("enhanced_planning", defaults.enhanced_planning),
        vbench_quality_control=settings.get("vbench_quality_control", defaults.vbench_quality_control),
        automatic_regeneration=settings.get("automatic_regeneration", defaults.automatic_regeneration),
        post_processing_enhancement=settings.get("post_processing_enhancement", defaults.post_processing_enhancement),
        color_grading=settings.get("color_grading", defaults.color_grading),
        controlnet=settings.get("controlnet", defaults.controlnet),
        csfd_detection=settings.get("csfd_detection", defaults.csfd_detection),
    )


def validate_settings(settings: CoherenceSettings) -> tuple[bool, Optional[str]]:
    """
    Validate coherence settings for dependency violations and incompatible combinations.
    
    Args:
        settings: CoherenceSettings to validate
    
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Check dependencies
    # IP-Adapter (both modes) requires Enhanced Planning
    if (settings.ip_adapter_reference or settings.ip_adapter_sequential) and not settings.enhanced_planning:
        return False, "IP-Adapter requires Enhanced LLM Planning to be enabled"
    
    # Check incompatibilities: IP-Adapter modes are mutually exclusive
    if settings.ip_adapter_reference and settings.ip_adapter_sequential:
        return False, "IP-Adapter Reference Images and Sequential Images modes are incompatible - choose one approach"
    
    # LoRA requires Enhanced Planning for proper integration
    if settings.lora and not settings.enhanced_planning:
        return False, "LoRA Training requires Enhanced LLM Planning to be enabled"
    
    # ControlNet works best with Enhanced Planning
    if settings.controlnet and not settings.enhanced_planning:
        return False, "ControlNet requires Enhanced LLM Planning to be enabled"
    
    # CSFD Detection requires Enhanced Planning for entity detection
    if settings.csfd_detection and not settings.enhanced_planning:
        return False, "CSFD Character Consistency Detection requires Enhanced LLM Planning to be enabled"
    
    # Automatic regeneration requires VBench quality control
    if settings.automatic_regeneration and not settings.vbench_quality_control:
        return False, "Automatic Regeneration requires VBench Quality Control to be enabled"
    
    # Check incompatibilities
    # ControlNet and CSFD both do compositional consistency - using both is redundant
    if settings.controlnet and settings.csfd_detection:
        return False, "ControlNet and CSFD Detection are incompatible - both handle compositional consistency"
    
    # VBench Quality Control should be used with at least one coherence technique
    # (This is a recommendation, not a hard requirement, so we'll just log it)
    if settings.vbench_quality_control:
        coherence_techniques_enabled = sum([
            settings.seed_control,
            settings.ip_adapter_reference,
            settings.ip_adapter_sequential,
            settings.lora,
            settings.controlnet,
            settings.csfd_detection,
        ])
        if coherence_techniques_enabled == 0:
            logger.warning("VBench Quality Control enabled but no coherence techniques active - may not provide meaningful feedback")
    
    return True, None


def get_settings_metadata() -> Dict:
    """
    Get metadata about coherence settings including descriptions, recommendations, and impact estimates.
    
    Returns:
        Dict: Metadata for all coherence techniques
    """
    return {
        "seed_control": {
            "enabled": True,
            "recommended": True,
            "cost_impact": "None",
            "time_impact": "Low",
            "description": "Ensures consistent visual style across scenes using seed values",
            "tooltip": "Seed control maintains visual consistency by reusing seed values across video scenes. This is a lightweight technique with no additional cost.",
        },
        "ip_adapter_reference": {
            "enabled": False,
            "recommended": True,
            "cost_impact": "Low",
            "time_impact": "Medium",
            "description": "Uses the same real reference image(s) for all video clip generations to maintain character/product identity",
            "tooltip": "IP-Adapter with reference images: Provides the same real image(s) to all video clip generations. This maintains consistent appearance of characters or products across different scenes using static reference images. Requires Enhanced LLM Planning to be enabled.",
            "requires": ["enhanced_planning"],
        },
        "ip_adapter_sequential": {
            "enabled": False,
            "recommended": False,
            "cost_impact": "Low",
            "time_impact": "Medium-High",
            "description": "Uses reference images + images from previous generated clips for progressive consistency",
            "tooltip": "IP-Adapter with sequential images: Provides reference images plus images extracted from previously generated clips. This creates progressive visual consistency where each clip builds upon the previous one. Useful for comparing sequential vs static reference approaches. Requires Enhanced LLM Planning to be enabled. Incompatible with Reference Images mode.",
            "requires": ["enhanced_planning"],
        },
        "lora": {
            "enabled": False,
            "recommended": False,
            "cost_impact": "Medium",
            "time_impact": "High",
            "description": "Uses trained LoRA models for character/product consistency",
            "tooltip": "LoRA (Low-Rank Adaptation) training provides fine-tuned models for specific characters or products. Requires a pre-trained LoRA model to be available.",
        },
        "enhanced_planning": {
            "enabled": True,
            "recommended": True,
            "cost_impact": "Low",
            "time_impact": "Low",
            "description": "Uses advanced LLM techniques for better scene planning and coherence",
            "tooltip": "Enhanced LLM planning improves scene breakdown and visual prompt generation for better coherence. Recommended for all video generations.",
        },
        "vbench_quality_control": {
            "enabled": True,
            "recommended": True,
            "cost_impact": "Low",
            "time_impact": "Medium",
            "description": "Automated quality assessment using VBench metrics",
            "tooltip": "VBench quality control automatically evaluates generated video clips using research-backed quality metrics to ensure high standards.",
        },
        "post_processing_enhancement": {
            "enabled": True,
            "recommended": True,
            "cost_impact": "None",
            "time_impact": "Low",
            "description": "Applies color grading and visual enhancements to final video",
            "tooltip": "Post-processing enhancement applies color grading, contrast adjustments, and other visual improvements to the final video output.",
        },
        "controlnet": {
            "enabled": False,
            "recommended": False,
            "cost_impact": "Medium",
            "time_impact": "High",
            "description": "Advanced technique for maintaining compositional consistency (experimental)",
            "tooltip": "ControlNet provides advanced control over composition and structure across scenes. This is an experimental feature and may increase generation time significantly.",
        },
        "csfd_detection": {
            "enabled": False,
            "recommended": False,
            "cost_impact": "Low",
            "time_impact": "Medium",
            "description": "Cross-scene feature detection for character consistency (character-driven ads only)",
            "tooltip": "CSFD (Cross-Scene Feature Detection) analyzes and maintains character consistency across scenes. Best suited for character-driven advertisements.",
        },
    }

