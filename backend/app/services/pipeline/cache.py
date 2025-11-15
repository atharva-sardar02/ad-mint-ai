"""
Cache service for storing and retrieving generated video clips.
Caches clips for common prompts to speed up testing and development.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path("output/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Default prompt for caching (exact match required)
DEFAULT_PROMPT = "Create a 10 second ad for a Gauntlet water bottle"


def get_cache_key(prompt: str, scene_index: int) -> str:
    """
    Generate a cache key for a prompt and scene index.
    
    Args:
        prompt: User prompt text
        scene_index: Scene number (0-based index)
    
    Returns:
        str: Cache key (hash)
    """
    cache_str = f"{prompt}_{scene_index}"
    return hashlib.md5(cache_str.encode()).hexdigest()


def get_cached_clip(prompt: str, scene_index: int) -> Optional[str]:
    """
    Retrieve a cached video clip if available.
    
    Args:
        prompt: User prompt text
        scene_index: Scene number (0-based index)
    
    Returns:
        Optional[str]: Path to cached clip if exists, None otherwise
    """
    cache_key = get_cache_key(prompt, scene_index)
    cache_file = CACHE_DIR / f"{cache_key}.mp4"
    
    if cache_file.exists():
        logger.info(f"Cache hit for prompt '{prompt[:50]}...' scene {scene_index}")
        return str(cache_file)
    
    logger.debug(f"Cache miss for prompt '{prompt[:50]}...' scene {scene_index}")
    return None


def cache_clip(prompt: str, scene_index: int, clip_path: str) -> str:
    """
    Cache a generated video clip.
    
    Args:
        prompt: User prompt text
        scene_index: Scene number (0-based index)
        clip_path: Path to the generated clip
    
    Returns:
        str: Path to cached clip
    """
    cache_key = get_cache_key(prompt, scene_index)
    cache_file = CACHE_DIR / f"{cache_key}.mp4"
    
    try:
        import shutil
        shutil.copy2(clip_path, cache_file)
        logger.info(f"Cached clip for prompt '{prompt[:50]}...' scene {scene_index} -> {cache_file}")
        
        # Also save metadata
        metadata_file = CACHE_DIR / f"{cache_key}.json"
        metadata = {
            "prompt": prompt,
            "scene_index": scene_index,
            "original_path": clip_path,
            "cache_key": cache_key
        }
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return str(cache_file)
    except Exception as e:
        logger.error(f"Failed to cache clip: {e}")
        return clip_path


def should_cache_prompt(prompt: str) -> bool:
    """
    Check if a prompt should be cached.
    Currently only caches the default prompt.
    
    Args:
        prompt: User prompt text
    
    Returns:
        bool: True if prompt should be cached
    """
    return prompt.strip() == DEFAULT_PROMPT


def get_all_cached_clips(prompt: str) -> Dict[int, str]:
    """
    Get all cached clips for a prompt.
    
    Args:
        prompt: User prompt text
    
    Returns:
        Dict[int, str]: Dictionary mapping scene index to clip path
    """
    cached_clips = {}
    
    # Check metadata files to find all clips for this prompt
    for metadata_file in CACHE_DIR.glob("*.json"):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            if metadata.get("prompt") == prompt:
                scene_index = metadata.get("scene_index")
                cache_key = metadata.get("cache_key")
                clip_file = CACHE_DIR / f"{cache_key}.mp4"
                
                if clip_file.exists():
                    cached_clips[scene_index] = str(clip_file)
        except Exception as e:
            logger.warning(f"Failed to read cache metadata {metadata_file}: {e}")
    
    return cached_clips

