"""
Test/Demo for Appearance Sanitizer

Shows before/after examples of prompt sanitization.
"""
from app.services.master_mode.appearance_sanitizer import sanitize_appearance_from_prompt

# Test prompts with various appearance descriptions
test_prompts = [
    # Example 1: Detailed person description
    """
    A 32-year-old man with short brown hair, blue eyes, and a strong jawline stands in a modern living room.
    He has an athletic build, standing approximately 6 feet tall, wearing a charcoal gray sweater.
    His face shows determination as he looks toward the window.
    """,
    
    # Example 2: With reference image phrase
    """
    The exact same 28-year-old woman from Reference Image 1, with long blonde hair and green eyes,
    picks up the perfume bottle. She has fair skin, delicate features, and stands in elegant posture.
    The lighting highlights her radiant complexion.
    """,
    
    # Example 3: Multiple people
    """
    A tall, muscular African American man in his early 30s with a fade haircut and facial hair
    interacts with a petite Asian woman with long black hair and brown eyes. Both have athletic builds
    and youthful appearances.
    """,
    
    # Example 4: Product-focused (should keep most of it)
    """
    A luxurious perfume bottle sits on a marble countertop, surrounded by soft ambient lighting.
    The crystal-clear glass reflects the warm 5400K key light, creating gentle highlights on its surface.
    Brand name 'Essence' is visible in elegant gold lettering.
    """,
]

if __name__ == "__main__":
    print("=" * 80)
    print("APPEARANCE SANITIZER TEST")
    print("=" * 80)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}")
        print(f"{'='*80}")
        
        original = prompt.strip()
        sanitized = sanitize_appearance_from_prompt(original)
        
        print(f"\n📝 BEFORE ({len(original)} chars):")
        print("-" * 80)
        print(original)
        
        print(f"\n✨ AFTER ({len(sanitized)} chars):")
        print("-" * 80)
        print(sanitized)
        
        removed = len(original) - len(sanitized)
        percent = (removed / len(original)) * 100 if len(original) > 0 else 0
        
        print(f"\n📊 STATS:")
        print(f"  - Removed: {removed} characters ({percent:.1f}%)")
        print(f"  - Kept: {len(sanitized)} characters ({100-percent:.1f}%)")
        
    print(f"\n{'='*80}")
    print("✅ TEST COMPLETE")
    print("=" * 80)

