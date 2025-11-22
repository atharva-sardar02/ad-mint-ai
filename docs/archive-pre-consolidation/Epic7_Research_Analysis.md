# Epic 7 vs. Research Report: Strategic Analysis & Recommendations

**Date:** 2025-11-14  
**Analyst:** Business Analyst (BMad)  
**Purpose:** Evaluate current Epic 7 definitions against bleeding-edge research and determine optimal integration strategy

---

## Executive Summary

After analyzing the Multi-Scene Video Ad Generation Research Report against our current Epic 7 (Video Quality Optimization), I recommend **restructuring Epic 7** to align with the research roadmap rather than skipping it. The current Epic 7 stories are **partially aligned** but miss critical state-of-the-art techniques that would significantly improve multi-scene coherence—the core challenge for professional ad generation.

**Key Finding:** Our current Epic 7 focuses on post-generation analysis and enhancement, while the research emphasizes **pre-generation planning** (LLM-guided scene planning with consistency markers) and **generation-time consistency** (IP-Adapter, LoRA, seed control) as more effective approaches.

---

## Current Epic 7 Analysis

### Story 7.1: Video Coherence Analysis
**Current Approach:**
- Post-generation analysis using OpenCV
- Color, lighting, style consistency detection
- Generates coherence score (0-100)
- Identifies inconsistencies

**Research Alignment:** ⚠️ **Partial**
- Research emphasizes **prevention over correction**
- VBench metrics are recommended, but should be integrated earlier
- Post-analysis is valuable but secondary to generation-time consistency

### Story 7.2: Coherence Enhancement
**Current Approach:**
- Post-processing color grading adjustments
- Transition optimization
- Lighting/contrast normalization
- Applied during stitching phase

**Research Alignment:** ⚠️ **Partial**
- Missing: **Seed control** and **latent reuse** (fundamental techniques)
- Missing: **IP-Adapter** for character/product consistency
- Missing: **ControlNet** for compositional consistency
- Post-processing is good, but generation-time consistency is better

### Story 7.3: LLM-Powered Prompt Optimization
**Current Approach:**
- User-facing prompt optimization
- Enhances prompts before generation
- Adds visual style keywords, composition details

**Research Alignment:** ✅ **Strong**
- Aligns with research recommendation for LLM-guided planning
- However, research emphasizes **VideoDirectorGPT-style planning** with:
  - Explicit consistency groupings
  - Entity descriptions
  - Scene dependencies
  - Shot list with camera movements

### Story 7.4: Quality Feedback Loop
**Current Approach:**
- Tracks coherence scores
- Learns from user preferences
- Improves optimization algorithms

**Research Alignment:** ✅ **Good**
- Research recommends MSG Score, CSFD Score, VBench metrics
- Feedback loop is valuable for continuous improvement

---

## Research Report Roadmap Comparison

### Phase 1: Foundation ✅ **COMPLETED**
**Research Recommendation:**
- LLM Planner (GPT-4/Claude) → structured video plans
- Commercial APIs (Runway Gen-3, Veo 3)
- Asset Manager for reference images
- Compositor for assembly

**Our Status:**
- ✅ LLM enhancement implemented (Epic 3)
- ✅ Replicate API integration (Epic 3)
- ⚠️ Using basic models (Minimax, not Veo 3/Sora)
- ❌ No asset manager for character/product references

### Phase 2: Quality Enhancement ⚠️ **PARTIALLY MISSING**
**Research Recommendation:**
- IP-Adapter for identity preservation
- LoRA training for recurring characters/products
- Seed control for visual coherence
- Automated quality control (VBench metrics)

**Our Status:**
- ❌ No IP-Adapter implementation
- ❌ No LoRA training capability
- ❌ No seed control
- ❌ No VBench integration
- ✅ Post-processing color grading (partial)

### Phase 3: Custom Infrastructure ❌ **NOT PLANNED**
**Research Recommendation:**
- Hybrid generation (open-source + commercial)
- SkyReels V1 or HunyuanVideo for character-driven scenes
- Custom LoRA training pipeline
- Latent reuse for seamless transitions

**Our Status:**
- ❌ Not in current roadmap
- ❌ No self-hosted models
- ❌ No hybrid strategy

### Phase 4: Advanced Features ⚠️ **PARTIALLY PLANNED**
**Research Recommendation:**
- VideoDirectorGPT-style LLM planning
- Storyboard generation as intermediate step
- Multi-modal integration
- A/B testing and optimization
- MSG Score evaluation

**Our Status:**
- ⚠️ Basic LLM planning (Epic 3) but not VideoDirectorGPT-style
- ❌ No storyboard generation
- ❌ No A/B testing
- ❌ No MSG Score

---

## Gap Analysis: Critical Missing Components

### 🔴 **Critical Gaps (High Impact)**

1. **LLM-Guided Multi-Scene Planning (VideoDirectorGPT-style)**
   - **Current:** Basic scene planning with framework templates
   - **Research:** Explicit consistency groupings, entity descriptions, shot lists with camera movements
   - **Impact:** HIGH - Directly addresses multi-scene coherence challenge

2. **IP-Adapter for Character/Product Consistency**
   - **Current:** No character consistency mechanism
   - **Research:** Single-image identity preservation without training
   - **Impact:** HIGH - Essential for brand spokespersons, products

3. **Seed Control and Latent Reuse**
   - **Current:** No seed management
   - **Research:** Fundamental technique for visual coherence
   - **Impact:** HIGH - Maintains visual "DNA" across scenes

4. **VBench Integration for Automated Quality Control**
   - **Current:** Manual coherence analysis
   - **Research:** Comprehensive benchmark suite with automated metrics
   - **Impact:** MEDIUM - Reduces manual review, enables auto-regeneration

### 🟡 **Important Gaps (Medium Impact)**

5. **LoRA Training Pipeline**
   - **Current:** No custom model training
   - **Research:** Reusable character/product assets
   - **Impact:** MEDIUM - Long-term value for recurring brands

6. **Storyboard Generation as Intermediate Step**
   - **Current:** No visual preview before generation
   - **Research:** Client review checkpoint, reduces wasted generation
   - **Impact:** MEDIUM - Improves user experience, reduces costs

7. **ControlNet for Compositional Consistency**
   - **Current:** No structural control
   - **Research:** Enforces scene layout, character position
   - **Impact:** MEDIUM - Better control over complex scenes

### 🟢 **Nice-to-Have (Lower Priority)**

8. **Hybrid Generation Strategy (Open-Source + Commercial)**
   - **Current:** Commercial APIs only
   - **Research:** Cost efficiency for standard scenes
   - **Impact:** LOW (for MVP) - Cost optimization

9. **MSG Score for Multi-Scene Evaluation**
   - **Current:** Basic coherence scoring
   - **Research:** Specialized multi-scene metrics
   - **Impact:** LOW (for MVP) - Better evaluation

---

## Recommended Approach: Restructured Epic 7

### **Option A: Align with Research Roadmap (Recommended)**

Restructure Epic 7 into **two phases** aligned with research recommendations:

#### **Epic 7A: Generation-Time Consistency**
**Goal:** Implement state-of-the-art techniques for maintaining coherence during generation, not after.

**Stories:**
1. **7A.1: LLM-Guided Multi-Scene Planning (VideoDirectorGPT-style)**
   - Expand LLM planning to include explicit consistency groupings
   - Entity descriptions with consistency markers
   - Shot list with camera movements and framing
   - Scene dependencies and narrative flow

2. **7A.2: IP-Adapter Integration for Identity Preservation**
   - Implement IP-Adapter for character/product consistency
   - Reference image management system
   - Integration with video generation pipeline
   - Support for single-image identity transfer

3. **7A.3: Seed Control and Latent Reuse**
   - Implement seed control across all scenes
   - Latent reuse for seamless transitions
   - Visual "DNA" consistency mechanism
   - Integration with scene generation

4. **7A.4: ControlNet for Compositional Consistency**
   - Depth maps for perspective consistency
   - Layout control for scene structure
   - Character pose consistency
   - Integration with generation pipeline

**Deliverable:** Significantly improved multi-scene coherence through generation-time techniques.

#### **Epic 7B: Post-Generation Quality Control**
**Goal:** Automated quality assessment and enhancement.

**Stories:**
1. **7B.1: VBench Integration for Automated Quality Control**
   - Integrate VBench metrics (temporal quality, aesthetic quality, prompt alignment)
   - Automated scene evaluation
   - Quality threshold triggers for regeneration
   - CSFD Score for character-driven ads

2. **7B.2: Enhanced Coherence Analysis**
   - Cross-scene entity consistency detection
   - MSG Score evaluation for multi-scene sequences
   - Narrative flow assessment
   - Automated inconsistency reporting

3. **7B.3: Post-Processing Enhancement (Refined)**
   - Color grading with brand palette preservation
   - Transition optimization based on analysis
   - Lighting adjustments
   - Style normalization

4. **7B.4: Quality Feedback Loop**
   - Track VBench, MSG, CSFD scores
   - Learn from successful outcomes
   - Improve prompt optimization algorithms
   - Refine enhancement parameters

**Deliverable:** Automated quality control reducing manual review by 60-80%.

---

### **Option B: Incremental Enhancement (Conservative)**

Keep current Epic 7 structure but enhance stories with research insights:

**Story 7.1 Enhancement:**
- Add VBench metrics integration
- Add MSG Score evaluation
- Add CSFD Score for character consistency

**Story 7.2 Enhancement:**
- Add seed control and latent reuse
- Add IP-Adapter integration
- Add ControlNet support

**Story 7.3 Enhancement:**
- Expand to VideoDirectorGPT-style planning
- Add consistency groupings
- Add shot list generation

**Story 7.4 Enhancement:**
- Add research-recommended metrics
- Improve learning algorithms

**Risk:** May miss critical generation-time techniques that are more effective than post-processing.

---

## Integration Strategy: Step-by-Step Roadmap

### **Quick Wins Priority (Recommended Implementation Order)**

1. **Seed Control (High Impact, Low Complexity)**
   - Implement seed management in video generation service
   - Use same seed across all scenes in an ad
   - Quick win for immediate coherence improvement

2. **Enhanced LLM Planning (High Impact, Medium Complexity)**
   - Expand scene planning to include consistency markers
   - Add entity descriptions with consistency requirements
   - Foundation for all other consistency techniques

3. **IP-Adapter Integration (High Impact, Medium Complexity)**
   - Character/product identity preservation
   - Reference image management system
   - Integration with generation pipeline

4. **VBench Metrics Integration (Medium Impact, Medium Complexity)**
   - Automated quality assessment
   - Threshold-based regeneration triggers
   - Quality dashboard

5. **Latent Reuse (High Impact, Medium Complexity)**
   - Seamless transition generation
   - Scene linking mechanism

6. **VideoDirectorGPT-Style Planning (High Impact, High Complexity)**
   - Full LLM-guided planning with consistency groupings
   - Shot list generation
   - Camera movement specifications

7. **ControlNet Integration (Medium Impact, Medium Complexity)**
   - Depth maps for perspective
   - Layout control
   - Pose consistency

8. **Post-Processing Enhancement (Medium Impact, Low Complexity)**
   - Brand-aware color grading
   - Transition optimization
   - Style normalization

### **Future Enhancements (Post-MVP)**

9. **Storyboard Generation**
   - Intermediate visual preview
   - Client review checkpoint
   - Reduces wasted generation

10. **LoRA Training Pipeline**
    - Custom character/product training
    - Reusable brand assets

11. **Hybrid Generation Strategy**
    - Self-hosted models for cost efficiency
    - Commercial APIs for complex scenes

12. **Advanced Evaluation**
    - MSG Score implementation
    - Human-in-the-loop review
    - A/B testing framework

---

## PRD Comparison: How We Stack Up

### **Current PRD Strengths:**
✅ Framework-based storytelling (PAS, BAB, AIDA)  
✅ LLM enhancement for prompt processing  
✅ Multi-scene video generation  
✅ Post-processing and color grading  
✅ Progress tracking and cost management  

### **PRD Gaps vs. Research:**
❌ No mention of IP-Adapter or LoRA  
❌ No seed control or latent reuse  
❌ No VideoDirectorGPT-style planning  
❌ No VBench or MSG Score metrics  
❌ No storyboard generation  
❌ No ControlNet integration  
❌ Limited character/product consistency mechanisms  

### **PRD Enhancement Recommendations:**

1. **Add to Section 11 (AI Video Generation Pipeline):**
   - Seed control mechanism
   - IP-Adapter for identity preservation
   - Latent reuse for transitions

2. **Add to Section 8.5 (Video Quality Optimization):**
   - VBench metrics integration
   - MSG Score evaluation
   - CSFD Score for character consistency

3. **Enhance Section 11.3 (Scene Planning):**
   - VideoDirectorGPT-style planning with consistency groupings
   - Entity descriptions with consistency markers
   - Shot list with camera movements

4. **Add New Section: Character/Product Consistency:**
   - IP-Adapter implementation
   - Reference image management
   - LoRA training (post-MVP)

---

## Decision Framework: Should We Skip or Rework?

### **Recommendation: RESTRUCTURE, DON'T SKIP**

**Rationale:**
1. **Epic 7 addresses core product differentiator:** Multi-scene coherence is the #1 challenge for professional ad generation
2. **Research provides clear roadmap:** The 4-phase plan is actionable and proven
3. **Current Epic 7 is partially correct:** Post-processing is valuable, but generation-time consistency is more effective
4. **Incremental value:** Each research-recommended technique provides measurable improvement

### **Risk of Skipping:**
- ❌ Videos will lack professional coherence
- ❌ High regeneration rates (users reject inconsistent videos)
- ❌ Competitive disadvantage (competitors using these techniques)
- ❌ User satisfaction below target (80%+ acceptance rate)

### **Risk of Current Approach (Post-Processing Only):**
- ⚠️ Limited effectiveness (can't fix fundamental generation issues)
- ⚠️ Higher costs (regenerations due to poor initial quality)
- ⚠️ Slower iteration (post-processing adds time)

### **Risk of Full Research Roadmap:**
- ⚠️ Longer development timeline (8-12 weeks vs. 4 weeks)
- ⚠️ Higher complexity (more moving parts)
- ✅ But: Significantly better quality and user satisfaction

---

## Brainstorming: Hybrid Approaches

### **Approach: "Quick Wins First" (Recommended)**

**Priority Order:**
1. **Seed Control** - Immediate visual coherence improvement
2. **Enhanced LLM Planning** - Foundation for consistency techniques
3. **IP-Adapter** - Character/product identity preservation
4. **VBench Integration** - Automated quality control
5. **Post-Processing Enhancement** - Brand-aware refinement
6. **ControlNet** - Compositional consistency
7. **CSFD Scoring** - Character consistency measurement
8. **Quality Feedback Loop** - Continuous improvement

**Result:** 70% of research benefits with focused implementation, iterating based on results.

---

## Final Recommendations

### **Immediate Action Plan:**

1. **✅ RESTRUCTURE Epic 7** with bleeding-edge research techniques
2. **✅ PRIORITIZE** seed control and enhanced LLM planning (quick wins)
3. **✅ PLAN** IP-Adapter integration
4. **✅ UPDATE PRD** with research-recommended techniques
5. **✅ ITERATE** based on results, adding techniques incrementally

### **Success Criteria:**

- **Multi-scene coherence score:** >85% (vs. current ~60-70% estimated)
- **User acceptance rate:** >85% (vs. target 80%)
- **Regeneration rate:** <15% (vs. target <20%)
- **Character consistency:** CSFD Score <0.3 (excellent)

### **Key Insight:**

The research report reveals that **prevention (generation-time consistency) is more effective than correction (post-processing)**. Our current Epic 7 focuses too heavily on post-processing. Restructuring to emphasize generation-time techniques will yield significantly better results.

---

## Implementation Notes

**Multi-Scene Coherence is Core:** This epic addresses the #1 challenge for professional ad generation. All techniques should be prioritized accordingly.

**Quick Wins Approach:** Start with seed control and enhanced LLM planning, then iterate based on results. Each technique builds on the previous ones.

**Research-Based:** All techniques are based on state-of-the-art research from the Multi-Scene Video Ad Generation Research Report.

---

**Next Steps:**
1. Review this analysis with product owner
2. Decide on timeline and approach
3. Restructure Epic 7 stories accordingly
4. Update PRD with research insights
5. Begin implementation with seed control (quick win)

---

_End of Analysis_

