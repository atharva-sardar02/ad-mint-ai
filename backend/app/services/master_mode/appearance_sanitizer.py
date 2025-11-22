"""
Appearance Sanitizer for Video Generation.

Removes ALL physical appearance descriptions (face, hair, race, body) from prompts
before sending to Veo 3.1, allowing reference images to be the SOLE source of truth
for character appearance.
"""
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# Comprehensive list of physical appearance terms to remove
APPEARANCE_TERMS = [
    # Face features
    "face", "facial", "eyes", "eye color", "eyelashes", "eyebrows", "nose", 
    "lips", "mouth", "cheeks", "cheekbones", "jawline", "jaw", "chin", 
    "forehead", "temples", "dimples", "freckles", "moles", "beauty mark",
    "complexion", "skin tone", "pale", "fair", "olive", "tan", "dark skin",
    "light skin", "porcelain", "bronze", "ebony", "ivory", "peaches and cream",
    
    # Hair
    "hair", "hairstyle", "haircut", "bangs", "ponytail", "bun", "braids",
    "dreadlocks", "afro", "curly", "wavy", "straight", "long hair", "short hair",
    "blonde", "brunette", "redhead", "black hair", "brown hair", "gray hair",
    "white hair", "silver hair", "highlights", "hair color", "hairstyle",
    "bald", "balding", "receding hairline", "crew cut", "buzz cut",
    
    # Race and ethnicity descriptors
    "caucasian", "white", "black", "african", "asian", "hispanic", "latino",
    "latina", "middle eastern", "indian", "native american", "pacific islander",
    "mixed race", "biracial", "ethnic", "ethnicity", "race", "racial",
    
    # Body descriptions
    "muscular", "athletic build", "slim", "slender", "curvy", "voluptuous",
    "fit", "toned", "buff", "ripped", "lean", "stocky", "heavyset", "petite",
    "tall", "short", "height", "build", "physique", "body type", "frame",
    "broad shoulders", "narrow waist", "thick", "thin",
    
    # Age-related (if too specific)
    "wrinkles", "age lines", "crow's feet", "laugh lines", "aged",
    "youthful", "young-looking", "mature-looking",
    
    # Other physical traits
    "beard", "mustache", "goatee", "stubble", "clean-shaven", "facial hair",
    "glasses", "spectacles", "contacts", "tattoos", "piercings", "scars",
]

# Regex patterns for more complex descriptions
APPEARANCE_PATTERNS = [
    # Color descriptions before face/hair/skin
    r'\b(light|dark|pale|fair|olive|tan|deep|rich|warm|cool|golden|bronze|ebony|ivory)\s+(skin|complexion|tone)\b',
    r'\b(blue|brown|green|hazel|gray|grey|amber|dark|light)\s+(eyes?|eyed)\b',
    r'\b(blonde?|brunette?|red|black|brown|gray|grey|white|silver)\s+(hair|haired)\b',
    
    # Age descriptors with numbers
    r'\b\d{2}(-|\s)?year(-|\s)?old\b',
    r'\bin\s+(his|her|their)\s+(early|mid|late)\s+\d{2}s\b',
    
    # Height and weight
    r'\b\d+[\'\"]?\d*\s*(feet|ft|foot|inches|in|cm|centimeters)\b',
    r'\b\d+\s*(lbs?|pounds?|kg|kilograms?)\b',
    
    # Specific facial feature descriptions
    r'\b(sharp|soft|chiseled|defined|delicate|strong|prominent|small|large|full|thin)\s+(nose|lips|chin|jaw|jawline|cheekbones|features)\b',
    r'\b(wide|narrow|almond|round|hooded)\s+(eyes?|set eyes?)\b',
    
    # Skin descriptors
    r'\b(smooth|rough|clear|blemished|flawless|radiant|glowing)\s+(skin|complexion)\b',
    
    # Body part descriptions
    r'\b(muscular|toned|defined|broad|narrow|slim|thick)\s+(arms|legs|shoulders|chest|torso|physique)\b',
    
    # Comparative descriptions
    r'\bappears to be (in (his|her|their)|about|around|approximately)\s+\d+\b',
    
    # Full descriptive phrases that should be removed
    r'\b(the\s+)?(man|woman|person|individual|subject|character)\s+(has|with|wearing|sporting)\s+[^.;,]*?(hair|eyes|skin|complexion|build|physique|features?)[^.;,]*?(?=[.;,]|\s+and\s+|\s+with\s+)',
]

# Reference phrases to keep (but simplify)
REFERENCE_REPLACEMENTS = {
    # Complex reference phrases -> Simple reference
    r'the\s+exact\s+same\s+\d{2}(-|\s)?year(-|\s)?old\s+(man|woman|person)': r'the exact same \3',
    r'the\s+same\s+\d{2}(-|\s)?year(-|\s)?old\s+(man|woman|person)': r'the same \3',
    
    # Remove age from reference phrases
    r'(from\s+Reference\s+Image\s+\d+)[^,.\n]*?(,|\.|and|\n)': r'\1\2',
    
    # Simplify descriptions after "exact same"
    r'(the\s+exact\s+same\s+)(man|woman|person)[^,.\n]*?(from\s+Reference)': r'\1\2 \3',
    r'(the\s+exact\s+same\s+)(man|woman|person)[^,.\n]*?(,|\.)': r'\1\2\3',
}


def sanitize_appearance_from_prompt(prompt: str) -> str:
    """
    Remove ALL physical appearance descriptions from a video generation prompt.
    
    Args:
        prompt: Original video generation prompt
        
    Returns:
        Sanitized prompt with appearance descriptions removed
    """
    original_prompt = prompt
    sanitized = prompt
    
    # Step 1: Apply reference phrase simplifications first (to preserve structure)
    for pattern, replacement in REFERENCE_REPLACEMENTS.items():
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    # Step 2: Remove complex appearance patterns
    for pattern in APPEARANCE_PATTERNS:
        matches = re.findall(pattern, sanitized, flags=re.IGNORECASE)
        if matches:
            logger.debug(f"[Appearance Sanitizer] Removing pattern: {pattern[:50]}... (found {len(matches)} matches)")
        sanitized = re.sub(pattern, '[APPEARANCE REMOVED]', sanitized, flags=re.IGNORECASE)
    
    # Step 3: Remove individual appearance terms (whole words only)
    for term in APPEARANCE_TERMS:
        # Use word boundaries to avoid removing parts of other words
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, sanitized, flags=re.IGNORECASE):
            logger.debug(f"[Appearance Sanitizer] Removing term: {term}")
        sanitized = re.sub(pattern, '[APPEARANCE REMOVED]', sanitized, flags=re.IGNORECASE)
    
    # Step 4: Clean up the text
    # Remove placeholder markers and extra whitespace
    sanitized = re.sub(r'\[APPEARANCE REMOVED\]', '', sanitized)
    
    # Remove empty parentheses or brackets
    sanitized = re.sub(r'\(\s*\)', '', sanitized)
    sanitized = re.sub(r'\[\s*\]', '', sanitized)
    
    # Clean up punctuation issues (double spaces, double commas, etc.)
    sanitized = re.sub(r'\s+', ' ', sanitized)  # Multiple spaces -> single space
    sanitized = re.sub(r'\s*,\s*,\s*', ', ', sanitized)  # Double commas
    sanitized = re.sub(r'\s*\.\s*\.\s*', '. ', sanitized)  # Double periods
    sanitized = re.sub(r',\s*\.', '.', sanitized)  # Comma before period
    sanitized = re.sub(r',\s*,', ',', sanitized)  # Double commas (again)
    
    # Fix spacing around punctuation
    sanitized = re.sub(r'\s+([.,;:!?])', r'\1', sanitized)  # Remove space before punctuation
    sanitized = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', sanitized)  # Add space after punctuation
    
    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()
    
    # Log the changes
    if sanitized != original_prompt:
        removed_chars = len(original_prompt) - len(sanitized)
        logger.info(f"[Appearance Sanitizer] Removed {removed_chars} characters ({removed_chars/len(original_prompt)*100:.1f}%) of appearance descriptions")
        logger.debug(f"[Appearance Sanitizer] BEFORE ({len(original_prompt)} chars):\n{original_prompt[:200]}...")
        logger.debug(f"[Appearance Sanitizer] AFTER ({len(sanitized)} chars):\n{sanitized[:200]}...")
    else:
        logger.info("[Appearance Sanitizer] No appearance descriptions found to remove")
    
    return sanitized


def sanitize_all_video_params(video_params_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitize appearance descriptions from all video generation parameters.
    
    Args:
        video_params_list: List of video generation parameters
        
    Returns:
        Sanitized video parameters with appearance-free prompts
    """
    logger.info(f"[Appearance Sanitizer] Sanitizing {len(video_params_list)} video prompts")
    
    sanitized_params = []
    
    for idx, params in enumerate(video_params_list):
        scene_number = params.get("scene_number", idx + 1)
        original_prompt = params.get("prompt", "")
        
        # Sanitize the prompt
        sanitized_prompt = sanitize_appearance_from_prompt(original_prompt)
        
        # Create new params dict with sanitized prompt
        sanitized = params.copy()
        sanitized["prompt"] = sanitized_prompt
        
        # Add metadata about sanitization
        if "metadata" not in sanitized:
            sanitized["metadata"] = {}
        sanitized["metadata"]["appearance_sanitized"] = True
        sanitized["metadata"]["original_prompt_length"] = len(original_prompt)
        sanitized["metadata"]["sanitized_prompt_length"] = len(sanitized_prompt)
        
        sanitized_params.append(sanitized)
        
        logger.info(
            f"[Appearance Sanitizer] Scene {scene_number}: "
            f"{len(original_prompt)} -> {len(sanitized_prompt)} chars "
            f"({(len(original_prompt) - len(sanitized_prompt))/len(original_prompt)*100:.1f}% removed)"
        )
    
    logger.info("[Appearance Sanitizer] ✅ All prompts sanitized - reference images are now sole source of appearance")
    
    return sanitized_params

