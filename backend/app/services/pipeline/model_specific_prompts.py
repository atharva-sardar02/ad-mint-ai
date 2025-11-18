"""
Model-specific prompt enhancement configurations and strategies.

Different image generation models have different prompt requirements and optimizations.
This module provides model-specific guidance for prompt enhancement.
"""
from typing import Dict, Optional

# Model-specific prompt enhancement strategies
MODEL_ENHANCEMENT_STRATEGIES = {
    "black-forest-labs/flux": {
        "name": "Flux",
        "description": "Black Forest Labs Flux - High quality, prefers detailed natural language",
        "preferences": {
            "style": "natural_language",
            "length": "medium_to_long",  # Flux handles longer prompts well
            "technical_details": "include",  # Can handle camera specs
            "negative_prompts": "supported",
            "keywords": "avoid",  # Prefers natural language over keywords
            "structure": "flowing_sentence",
        },
        "tips": [
            "Flux responds well to detailed, cinematic descriptions",
            "Can handle technical camera specifications naturally",
            "Prefers natural language flow over keyword lists",
            "Supports negative prompts for quality control",
            "Longer prompts (100-200 words) often work better than short ones",
        ],
        "negative_prompt_defaults": [
            "blurry", "low quality", "distorted", "deformed", "ugly", "bad anatomy",
            "watermark", "text", "signature", "extra limbs", "mutated hands",
            "poorly drawn", "bad proportions", "cloned face", "disfigured"
        ],
    },
    "black-forest-labs/flux-schnell": {
        "name": "Flux Schnell",
        "description": "Flux fast variant - Similar to Flux but optimized for speed",
        "preferences": {
            "style": "natural_language",
            "length": "medium",  # Slightly shorter than full Flux
            "technical_details": "include",
            "negative_prompts": "supported",
            "keywords": "avoid",
            "structure": "flowing_sentence",
        },
        "tips": [
            "Similar to Flux but optimized for faster generation",
            "Slightly less detail tolerance than full Flux",
            "Still prefers natural language over keywords",
        ],
        "negative_prompt_defaults": [
            "blurry", "low quality", "distorted", "deformed", "ugly", "bad anatomy",
            "watermark", "text", "signature", "extra limbs", "mutated hands",
            "poorly drawn", "bad proportions", "cloned face", "disfigured"
        ],
    },
    "black-forest-labs/flux-dev": {
        "name": "Flux Dev",
        "description": "Flux development version - Experimental features",
        "preferences": {
            "style": "natural_language",
            "length": "medium_to_long",
            "technical_details": "include",
            "negative_prompts": "supported",
            "keywords": "avoid",
            "structure": "flowing_sentence",
        },
        "tips": [
            "Development version of Flux with experimental features",
            "Follows same prompt guidelines as Flux",
        ],
        "negative_prompt_defaults": [
            "blurry", "low quality", "distorted", "deformed", "ugly", "bad anatomy",
            "watermark", "text", "signature", "extra limbs", "mutated hands",
            "poorly drawn", "bad proportions", "cloned face", "disfigured"
        ],
    },
    "google/nano-banana": {
        "name": "Nano Banana",
        "description": "Google Nano Banana - Fast, efficient, prefers concise prompts",
        "preferences": {
            "style": "concise_natural",
            "length": "short_to_medium",  # Prefers shorter, more focused prompts
            "technical_details": "simplify",  # Simplify technical jargon
            "negative_prompts": "supported",
            "keywords": "minimal",  # Some keywords OK but keep natural
            "structure": "clear_and_direct",
        },
        "tips": [
            "Nano Banana works best with concise, clear prompts",
            "Avoid overly complex multi-concept prompts",
            "Focus on one main subject and scene",
            "Simplify technical camera specifications",
            "Shorter prompts (50-100 words) often work better",
        ],
        "negative_prompt_defaults": [
            "blurry", "low quality", "distorted", "deformed", "ugly", "bad anatomy",
            "watermark", "text", "signature", "extra limbs", "mutated hands",
            "poorly drawn", "bad proportions", "cloned face", "disfigured"
        ],
    },
    "stability-ai/sdxl-turbo": {
        "name": "SDXL Turbo",
        "description": "Stable Diffusion XL Turbo - Fast SDXL variant",
        "preferences": {
            "style": "natural_with_keywords",
            "length": "medium",
            "technical_details": "simplify",
            "negative_prompts": "strongly_supported",  # SDXL models excel with negative prompts
            "keywords": "acceptable",  # Can handle some keyword lists
            "structure": "flexible",
        },
        "tips": [
            "SDXL Turbo benefits significantly from negative prompts",
            "Can handle a mix of natural language and keywords",
            "Negative prompts are very effective for quality control",
        ],
        "negative_prompt_defaults": [
            "blurry", "low quality", "distorted", "deformed", "ugly", "bad anatomy",
            "watermark", "text", "signature", "extra limbs", "mutated hands",
            "poorly drawn", "bad proportions", "cloned face", "disfigured",
            "lowres", "jpeg artifacts", "worst quality", "normal quality"
        ],
    },
    "stability-ai/stable-diffusion": {
        "name": "Stable Diffusion",
        "description": "Original Stable Diffusion - Classic model",
        "preferences": {
            "style": "natural_with_keywords",
            "length": "medium",
            "technical_details": "simplify",
            "negative_prompts": "strongly_supported",
            "keywords": "acceptable",
            "structure": "flexible",
        },
        "tips": [
            "Classic Stable Diffusion model",
            "Negative prompts are essential for quality",
            "Can handle keyword-style prompts",
        ],
        "negative_prompt_defaults": [
            "blurry", "low quality", "distorted", "deformed", "ugly", "bad anatomy",
            "watermark", "text", "signature", "extra limbs", "mutated hands",
            "poorly drawn", "bad proportions", "cloned face", "disfigured",
            "lowres", "jpeg artifacts", "worst quality", "normal quality"
        ],
    },
}

# Default strategy for unknown models
DEFAULT_STRATEGY = {
    "name": "Generic",
    "description": "Generic model - Using default enhancement strategy",
    "preferences": {
        "style": "natural_language",
        "length": "medium",
        "technical_details": "include",
        "negative_prompts": "supported",
        "keywords": "avoid",
        "structure": "flowing_sentence",
    },
    "tips": [
        "Using generic prompt enhancement strategy",
        "Natural language prompts generally work best",
    ],
    "negative_prompt_defaults": [
        "blurry", "low quality", "distorted", "deformed", "ugly", "bad anatomy",
        "watermark", "text", "signature", "extra limbs", "mutated hands",
        "poorly drawn", "bad proportions", "cloned face", "disfigured"
    ],
}


def get_model_strategy(model_name: str) -> Dict:
    """
    Get model-specific enhancement strategy.
    
    Args:
        model_name: Replicate model identifier (e.g., "black-forest-labs/flux-schnell")
    
    Returns:
        Dict with model-specific strategy configuration
    """
    # Try exact match first
    if model_name in MODEL_ENHANCEMENT_STRATEGIES:
        return MODEL_ENHANCEMENT_STRATEGIES[model_name]
    
    # Try partial match (e.g., "flux" matches "black-forest-labs/flux")
    for key, strategy in MODEL_ENHANCEMENT_STRATEGIES.items():
        if model_name.lower() in key.lower() or key.lower() in model_name.lower():
            return strategy
    
    # Return default strategy
    return DEFAULT_STRATEGY


def should_simplify_for_model(model_name: str) -> bool:
    """Check if prompt should be simplified for this model."""
    strategy = get_model_strategy(model_name)
    return strategy["preferences"]["length"] in ["short", "short_to_medium"]


def should_include_technical_details(model_name: str) -> bool:
    """Check if technical camera details should be included."""
    strategy = get_model_strategy(model_name)
    return strategy["preferences"]["technical_details"] == "include"


def supports_negative_prompts(model_name: str) -> bool:
    """Check if model supports negative prompts."""
    strategy = get_model_strategy(model_name)
    return strategy["preferences"]["negative_prompts"] in ["supported", "strongly_supported"]


def get_default_negative_prompt(model_name: str) -> str:
    """Get default negative prompt for model."""
    strategy = get_model_strategy(model_name)
    defaults = strategy.get("negative_prompt_defaults", [])
    return ", ".join(defaults)

