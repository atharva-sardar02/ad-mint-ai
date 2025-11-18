# Enhanced Test Prompt: Perfume + Woman (With Police Description)

**Purpose**: Test character consistency fix with forensically detailed character description

**Date**: November 18, 2025

## Test Prompt

```
Luxury perfume commercial for "Serenity Rose" - an elegant feminine fragrance for the modern woman.

PERFUME BOTTLE (Primary Subject):
The perfume bottle is distinctive and recognizable: 6.5 inches tall with a teardrop-shaped crystal-clear glass body, rose-gold metallic spherical cap (like a dewdrop, 1 inch diameter), and a delicate cream-colored satin ribbon tied around the neck. The liquid inside is pale blush pink with subtle pearl shimmer. A minimalist white label with "Serenity Rose" in gold cursive script adorns the front.

CHARACTER (Secondary Subject):
Woman, approximately 32 years old, 5 feet 6 inches tall, medium build (approximately 130 pounds). Long chestnut brown hair with subtle waves, naturally side-parted on left, reaching mid-back length, fine silky texture. Oval face with high cheekbones, emerald green eyes (almond-shaped), warm beige skin tone (Fitzpatrick Type III). Small beauty mark near left eye, positioned just above cheekbone. Wearing elegant ivory silk blouse with pearl buttons and pointed collar. Warm, confident expression with subtle smile.

SCENE GUIDE (AIDA Framework):
Scene 1 (Attention): The Serenity Rose perfume bottle sits elegantly on a white marble vanity in a bright, airy bedroom with soft morning light streaming through sheer curtains. The teardrop-shaped crystal glass catches and refracts the natural light, emphasizing the bottle's elegant curves and the pale pink liquid inside. The rose-gold cap gleams softly. Close-up product shot establishing the bottle's distinctive design.

Scene 2 (Interest): The woman enters the frame and reaches for the Serenity Rose bottle. She picks up the exact same teardrop-shaped crystal bottle (clearly showing the rose-gold spherical cap, cream ribbon, and pale pink liquid) and brings it closer to examine it with a gentle smile. The morning light illuminates her face (chestnut hair, emerald eyes, beauty mark) and the bottle's distinctive features - the crystal glass, rose-gold cap, and delicate ribbon are all clearly visible in her hand.

Scene 3 (Desire): Close-up of the same woman (chestnut hair, emerald eyes, beauty mark near left eye, ivory blouse) spraying the Serenity Rose perfume on her wrist. The same distinctive bottle is prominent in frame - teardrop crystal glass, rose-gold cap, cream ribbon, and pale pink liquid all clearly visible. A delicate mist of fragrance appears as she presses the atomizer. Her emerald eyes close momentarily as she appreciates the first notes of the scent. The soft morning light creates an ethereal, romantic atmosphere.

Scene 4 (Action): The same woman (maintaining all physical characteristics: chestnut hair, oval face, emerald eyes, beauty mark, ivory blouse) brings her wrist to her neck in a graceful gesture, fully experiencing the fragrance with a serene, satisfied expression. The Serenity Rose bottle sits on the vanity beside her, still clearly visible with its distinctive teardrop crystal shape, rose-gold spherical cap, and cream ribbon catching the morning light. She opens her eyes with renewed confidence, ready to start her day. The final shot shows both the woman's radiant expression and the beautiful bottle, creating desire and aspiration.

VISUAL CONSISTENCY:
- Maintain consistent soft morning lighting throughout - natural, warm, ethereal light that makes everything glow
- Color palette: whites, creams, blush pinks, rose-gold, and soft ivory tones
- Mood: serene, confident, and elegantly romantic - perfect for a modern feminine fragrance
- CRITICAL: The same teardrop perfume bottle (with all distinctive features) and the same woman (with all physical characteristics) must appear across all relevant scenes
```

## Expected Results

### ✅ Success Criteria:

**Bottle Consistency:**
- ✅ Teardrop-shaped crystal-clear glass maintained across all scenes
- ✅ Rose-gold spherical cap (1-inch diameter) identical in all appearances
- ✅ Cream-colored satin ribbon consistent
- ✅ Pale blush pink liquid with pearl shimmer maintained
- ✅ Same proportions and design throughout

**Character Consistency (THE FIX):**
- ✅ **Same woman in all scenes** (Scenes 2, 3, 4)
- ✅ Long chestnut brown hair with subtle waves, side-parted left
- ✅ Emerald green almond-shaped eyes
- ✅ Small beauty mark near left eye (above cheekbone)
- ✅ Oval face with high cheekbones
- ✅ Warm beige skin tone
- ✅ Ivory silk blouse with pearl buttons
- ✅ Warm, confident expression

**Scene Variation:**
- ✅ Scene 1: Bottle only (product beauty shot)
- ✅ Scene 2: Woman + bottle (discovery moment)
- ✅ Scene 3: Woman + bottle (usage moment, spray action)
- ✅ Scene 4: Woman + bottle (experience moment)
- ✅ Different camera angles, lighting, and moments
- ✅ Same subjects, different contexts

### 📊 Validation Checklist:

**Check Storyboard JSON:**
1. ✅ `consistency_markers.subject_description` contains BOTH:
   - Detailed bottle description (6+ unique features)
   - Detailed character description (10+ unique features including age, height, hair, eyes, skin, beauty mark)

2. ✅ Scene 1 `image_generation_prompt`:
   - Starts with detailed bottle description
   - No character (product shot only)

3. ✅ Scenes 2-4 `image_generation_prompt`:
   - Each starts with "The EXACT SAME" bottle description (copied from Scene 1)
   - Each includes "The EXACT SAME" woman description (copied from consistency_markers)
   - Only context varies (camera angle, action, lighting)

**Check Generated Images:**
4. ✅ All reference images: Same bottle design across all 4 scenes
5. ✅ All reference images: Same woman across Scenes 2, 3, 4
6. ✅ All start images: Maintain subject identity (when present)
7. ✅ All end images: Maintain subject identity (when present)

**Check Final Video:**
8. ✅ Bottle identity consistent throughout
9. ✅ Woman identity consistent throughout
10. ✅ Each scene shows unique moment/action
11. ✅ Visual cohesion maintained (lighting, color palette, mood)

## Test Comparison

### Before Fix (Original Test):
| Aspect | Result |
|--------|--------|
| Bottle identity | ✅ Maintained (6 unique identifiers) |
| Bottle size | ❌ Variations (10-15%) |
| Woman identity | ❌ DIFFERENT women in each scene |
| Woman description | ❌ Too generic ("woman in her 30s") |

### After Fix (This Test):
| Aspect | Expected Result |
|--------|-----------------|
| Bottle identity | ✅ Should maintain (same 6 identifiers) |
| Bottle size | ⚠️ May have variations (separate fix needed) |
| Woman identity | ✅ SHOULD BE SAME woman in all scenes |
| Woman description | ✅ Police description (10+ identifiers) |

## Key Differences from Previous Test

**Previous Prompt (Failed):**
```
"sophisticated woman in her 30s wearing elegant ivory silk blouse"
```
→ Only 2 vague descriptors, matched thousands of different people

**Current Prompt (Should Succeed):**
```
"Woman, approximately 32 years old, 5 feet 6 inches tall, medium build (130 pounds). 
Long chestnut brown hair with subtle waves, naturally side-parted on left, reaching 
mid-back length, fine silky texture. Oval face with high cheekbones, emerald green 
eyes (almond-shaped), warm beige skin tone (Fitzpatrick Type III). Small beauty mark 
near left eye, positioned just above cheekbone. Wearing elegant ivory silk blouse with 
pearl buttons and pointed collar. Warm, confident expression with subtle smile."
```
→ 10+ specific identifiers, matches ONE specific person

## Implementation Verification

**Changes Made to Fix:**
1. ✅ Added Rule #2 to `storyboard_planner.py` (lines 55-107)
2. ✅ Updated CRITICAL: SUBJECT IDENTITY section (line 137)
3. ✅ Enhanced `subject_description` field with character example (line 281)
4. ✅ Added CHARACTER CONSISTENCY CRITICAL examples (lines 327-333)
5. ✅ Updated CRITICAL REMINDER with character instructions (lines 265-272)

**Expected LLM Behavior:**
1. LLM reads Rule #2 (very first rules section)
2. LLM sees "police description" requirement for characters
3. LLM writes detailed character description in `consistency_markers.subject_description`
4. LLM copies this description verbatim into each scene's `image_generation_prompt` where character appears
5. Result: Same character across all scenes

## Testing Instructions

1. **Start Backend**: `cd backend && python -m uvicorn app.main:app --reload`
2. **Start Frontend**: `cd frontend && npm run dev`
3. **Navigate to Dashboard**
4. **Paste the test prompt above**
5. **Set target duration**: 15 seconds
6. **Generate video**
7. **Check storyboard JSON** (in Generation Details view)
8. **Verify**:
   - Character description in `consistency_markers` is detailed (age, height, hair, eyes, skin, beauty mark)
   - Each scene copies the character description
   - Generated images show same woman

## Success Indicators

**✅ Test PASSES if:**
- Same woman appears in Scenes 2, 3, 4
- Chestnut hair, emerald eyes, and beauty mark are consistent
- Bottle identity also maintained
- Visual cohesion across all scenes

**❌ Test FAILS if:**
- Different women appear in different scenes
- Hair color/eye color/facial features change
- Character description in JSON is too generic

## Rollback Plan

If test fails:
1. Check storyboard JSON for character description quality
2. If still generic, strengthen Rule #2 language further
3. If detailed but not copied, check image generation batch code
4. Can revert `storyboard_planner.py` to previous version if needed

## Notes

- This test focuses on CHARACTER consistency fix
- Size consistency is a separate issue (requires size reference objects)
- Bottle identity should continue working (already validated)
- The fix is LOW RISK (prompt engineering only, no code logic changes)

