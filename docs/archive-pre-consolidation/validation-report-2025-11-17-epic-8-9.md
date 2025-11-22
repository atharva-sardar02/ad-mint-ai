# Validation Report

**Document:** docs/epics.md (Epics 8 & 9 focus)  
**Checklist:** .bmad/bmm/workflows/2-plan-workflows/prd/checklist.md  
**Date:** 2025-11-17

## Scope

- This validation is **scoped specifically to Epic 8 (Hero-Frame Generation)** and **Epic 9 (Hero-Frame Iteration & Image-to-Video Workflow)** and how they integrate with existing epics and FRs.
- Primary source: `docs/epics.md` (lines ~1895–2210) plus FR inventory and FR coverage matrix.
- Supporting artifacts: `docs/sprint-artifacts/sprint-status.yaml` for story status.
- Full PRD-wide checklist was leveraged, but items unrelated to Epics 8–9 are treated as **N/A** for this report.

## Section Results (Scoped to Epics 8 & 9)

### 3. Epics Document Completeness

- **[✓ PASS] epics.md exists & epics 8–9 have full breakdowns**
  - Evidence: `docs/epics.md` defines Epic 8 and Epic 9 with goals, status, and detailed stories (8.1–8.4, 9.1–9.6).
- **[✓ PASS] Clear goals and value propositions**
  - Epic 8 goal: hero-frame-first entry point for cinematic stills as anchors for ads.  
  - Epic 9 goal: hero-frame → motion workflow with multi-attempt evaluation and iteration workspace.
- **[✓ PASS] Stories follow user-story + BDD style with acceptance criteria and technical notes**
  - Each 8.x and 9.x story uses “As a … I want … so that …” with concrete acceptance criteria and tech notes.
- **[⚠ PARTIAL] Explicit per-story dependencies within epics**
  - Most stories include prerequisites referencing earlier epics (1–7) and preceding 8.x/9.x stories.  
  - Suggestion: add an explicit **epic-level dependency summary** tying Epics 8–9 back to specific FRs and epics at the top of each epic for faster comprehension.

### 4. FR Coverage Validation (for FR-036–FR-044)

- **[✓ PASS] Every FR 036–044 is covered by Epics 8–9 stories**
  - Evidence (FR inventory & coverage map in `docs/epics.md`):
    - FR-036, FR-037, FR-038 → Epic 8 (Stories 8.1–8.4).
    - FR-039, FR-040, FR-041, FR-042, FR-043, FR-044 → Epic 9 (Stories 9.1–9.6).
- **[✓ PASS] No orphan FRs or stories for hero-frame/iteration scope**
  - FR coverage matrix explicitly maps each FR-036–044 to at least one story; all 8.x/9.x stories are tied to at least one FR.
- **[⚠ PARTIAL] Cross-check against PRD.md**
  - The FR definitions for 036–044 are mirrored in `docs/epics.md`, but this report did not exhaustively re-validate them against `docs/PRD.md` due to size; spot checks suggest alignment.  
  - Recommendation: run a quick PRD-focused grep/scan to ensure FR 036–044 wording is exactly consistent between PRD and epics.

### 5. Story Sequencing & Dependencies (Epics 8 & 9)

- **[✓ PASS] No forward dependencies within Epics 8 & 9**
  - Prerequisites always reference earlier epics (1–7) or earlier stories in the same epic chain (e.g., 8.2 → 8.1; 9.2 → 9.1 & 7.6; 9.6 → 9.4, Epics 3/6/7).
- **[✓ PASS] Vertical slices that deliver value**
  - 8.1 delivers an LLM-based cinematographer prompt enhancement usable on its own.  
  - 8.2–8.4 incrementally add generation, selection, and iteration capabilities on top of existing pipeline.  
  - 9.x stories each deliver end-to-end, user-visible capabilities (image-to-video, auto 3-attempt mode, iteration workspace, quality dashboard, pipeline integration).
- **[⚠ PARTIAL] Explicit MVP vs Growth tagging**
  - For Epics 8–9, MVP vs Growth delineation is implicit via FRs and story descriptions, but not explicitly marked per story like in Epic 7.  
  - Recommendation: add MVP/Growth tags to each 8.x/9.x story to make scope management clearer.

### 8. Cross-Document Consistency (Epics vs FRs & Existing Epics)

- **[✓ PASS] Terminology and epic titles**
  - Epic 8 and 9 titles and concepts match their FR names and are consistent with the FR coverage matrix.
- **[✓ PASS] Alignment with existing pipeline epics (3, 6, 7)**
  - Stories 8.2, 8.3, 9.1, 9.2, and 9.6 explicitly reference reusing generation infrastructure, VBench, and the editor instead of introducing parallel pipelines.
- **[⚠ PARTIAL] PRD linkage**
  - While epics.md references the PRD and includes FR inventory, this validation did not fully re-walk the PRD’s epic list to confirm 1:1 naming and ordering for Epics 8–9.  
  - Recommendation: confirm PRD epic list explicitly includes Epics 8 and 9 with identical titles and FR mappings.

### 9. Readiness for Implementation (Focused on Epics 8 & 9)

- **[✓ PASS] Architecture readiness**
  - Stories specify integration points with:  
    - Existing generation pipeline (Epic 3).  
    - Editor (Epic 6).  
    - Coherence/quality stack including VBench and quality metrics (Epic 7).  
  - Technical notes point to concrete infra (Replicate, SDXL, image-to-video models, VBench, LoRA infra) suitable for architecture workflows.
- **[⚠ PARTIAL] Operational & cost considerations**
  - Epics correctly state that quality is priority over cost, but there is limited explicit handling of operational constraints (GPU capacity, rate limits, parallelism limits) in the epic text itself.  
  - Suggestion: add a short “Operational Constraints & Safeguards” sub-section under Epic 9 (for parallel attempts and VBench evaluation) to anticipate production concerns.
- **[⚠ PARTIAL] Track-appropriate detail**
  - For BMad Method level, detail is strong at story level, but some system-wide concerns (SLAs for hero-frame throughput, UX fallbacks when VBench is unavailable) are implied rather than spelled out.

## Integration Assessment for Epics 8 & 9

1. **Pipeline Integration (Epic 9.6) – Overall: ✓ PASS with minor risks**
   - Integration strategy is clearly **additive**: hero-frame workflow layers on top of existing prompt → video path, reusing Epics 3, 6, and 7 instead of forking the pipeline.
   - FR-044 and Story 9.6 explicitly require reuse of stitching, audio, coherence settings, and editor entry, reducing architectural duplication.
   - Risks: need explicit plan for how hero-frame flows share cost tracking, progress reporting, and cancellation semantics with the existing generation pipeline.

2. **Data & Model Reuse – ✓ PASS**
   - Epics 8–9 reuse FR-036–044 definitions and extend the FR matrix cleanly without breaking earlier mappings.
   - Story tech notes emphasize reusing generation_groups, quality_metrics, and parallel generation patterns introduced in Epic 7.

3. **Delivery Path & Value**
   - Hero-frame and iteration flows form a coherent “pro mode” on top of the existing product: advanced users can opt in without degrading the simple workflow.
   - Value is incremental but meaningful at each step: better stills → better motion → informed selection → improved quality insights.

## Critical Failures (Scoped)

- No scoped **auto-fail** conditions detected for Epics 8 & 9:
  - epics.md exists and is complete.
  - FR 036–044 all have story coverage and traceability into Epics 8–9.
  - Stories are vertically sliced and avoid forward dependencies.

## Recommendations (Next Actions)

1. **Tighten PRD alignment for Epics 8–9**
   - Confirm PRD epic list and FR wording for 036–044 exactly match epics.md; update either doc if drift exists.
2. **Add explicit MVP/Growth flags to 8.x and 9.x stories**
   - This will clarify which parts of the hero-frame workflow are essential for the first release vs later enhancements.
3. **Add an “Operational & Constraints” subsection under Epic 9**
   - Call out concurrency limits, GPU capacity assumptions, and VBench availability/fallbacks to de-risk production rollout.


