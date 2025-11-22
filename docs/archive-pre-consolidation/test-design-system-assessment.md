# Test Design: System-Level Assessment - ad-mint-ai

**Date:** 2025-11-15
**Author:** BMad (TEA Agent)
**Status:** Assessment Complete
**Mode:** System-Level (Brownfield Review)

---

## Executive Summary

**Current State:**
- **Total Tests**: 255 (frontend: ~32 test files, backend: ~30 test files)
- **Failing Tests**: 49/255 (19% failure rate)
- **Test Frameworks**: Vitest (frontend), pytest (backend)
- **Product Status**: ✅ Working MVP - product functions correctly despite test failures

**Assessment Focus:**
- Evaluate current testing strategy for MVP context
- Assess risk of 49 failing tests
- Provide decision framework: **Fix vs Remove vs Defer**
- Recommend lightweight testing strategy for MVP

**Key Finding:** The failing tests are primarily **test infrastructure issues** (mock setup, network timeouts) rather than **product defects**. The product works, but test suite needs systematization.

---

## Current Test State Analysis

### Test Distribution

**Frontend (Vitest + React Testing Library):**
- Unit tests: Service layer, utilities
- Component tests: React components
- Integration tests: API client, auth flows
- E2E tests: User journeys (Dashboard, Editor, Gallery)

**Backend (pytest):**
- Unit tests: Service layer, business logic
- Integration tests: Complete pipeline, database operations
- API tests: Route handlers, authentication

### Failure Pattern Analysis

**Category 1: Mock Setup Issues (High Frequency)**
- **Issue**: Missing exports in mocks (e.g., `getGeneration` not exported in `VideoDetail.test.tsx`)
- **Impact**: Tests fail immediately, no product impact
- **Examples**:
  - `VideoDetail.test.tsx`: Mock missing `getGeneration` export
  - Various tests: Incomplete mock implementations
- **Risk Score**: TECH-2 (Probability: 2, Impact: 1) = **Score 2** (Low)

**Category 2: Network Timeout Issues**
- **Issue**: Tests making real API calls instead of using mocks
- **Impact**: Tests timeout (300s), slow test runs
- **Examples**:
  - `Dashboard.polling.test.tsx`: Real API calls to `getUserProfile`
  - Integration tests: Network requests not intercepted
- **Risk Score**: TECH-2 (Probability: 2, Impact: 1) = **Score 2** (Low)

**Category 3: Test Isolation Issues**
- **Issue**: Tests interfering with each other, state leakage
- **Impact**: Flaky tests, non-deterministic failures
- **Examples**: Shared state in auth store, localStorage not cleared
- **Risk Score**: TECH-3 (Probability: 2, Impact: 2) = **Score 4** (Medium)

**Category 4: Outdated Test Expectations**
- **Issue**: Tests written for old API contracts, component structure changed
- **Impact**: False negatives, maintenance burden
- **Examples**: Component props changed, API response format updated
- **Risk Score**: TECH-2 (Probability: 1, Impact: 2) = **Score 2** (Low)

### Test Quality Assessment

**Strengths:**
- ✅ Good test coverage structure (unit/integration/E2E)
- ✅ Tests follow Given-When-Then pattern
- ✅ Proper use of testing libraries (Vitest, RTL, pytest)
- ✅ Integration tests cover critical paths

**Weaknesses:**
- ❌ Inconsistent mock setup patterns
- ❌ Network calls not properly mocked in some tests
- ❌ Missing test data factories (hardcoded data)
- ❌ No test execution prioritization (P0/P1/P2/P3)
- ❌ No systematic test organization by risk

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
|---------|----------|-------------|-------------|-------|-------|------------|--------|----------|
| R-001 | TECH | Test suite debt blocks CI/CD automation | 2 | 3 | 6 | Systematize mock setup, fix critical tests | Dev | Sprint 1 |
| R-002 | OPS | No test prioritization = slow feedback loops | 2 | 3 | 6 | Implement P0/P1/P2/P3 tagging | Dev | Sprint 1 |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
|---------|----------|-------------|-------------|-------|-------|------------|--------|
| R-003 | TECH | Test isolation issues cause flaky failures | 2 | 2 | 4 | Fix state cleanup, improve fixtures | Dev |
| R-004 | TECH | Outdated tests give false confidence | 1 | 3 | 3 | Audit and update or remove outdated tests | Dev |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
|---------|----------|-------------|-------------|-------|-------|--------|
| R-005 | TECH | Mock setup inconsistencies | 2 | 1 | 2 | Monitor, fix incrementally |
| R-006 | TECH | Network timeout in tests | 2 | 1 | 2 | Monitor, improve mocking |

---

## Decision Framework: Fix vs Remove vs Defer

### **RECOMMENDATION: Selective Fix + Systematic Cleanup**

For an **MVP with working product**, the strategy should be **pragmatic, not comprehensive**.

### Decision Matrix

| Test Category | Count | Action | Rationale | Effort |
|---------------|-------|--------|-----------|--------|
| **P0 Tests (Critical Paths)** | ~30-40 | ✅ **FIX** | Core user journeys must work | 8-12 hours |
| **P1 Tests (Important Features)** | ~50-60 | ⚠️ **FIX OR DEFER** | Fix if <1hr, defer if >2hr | 10-20 hours |
| **P2 Tests (Secondary Features)** | ~80-100 | ⏸️ **DEFER** | Can wait until post-MVP | - |
| **P3 Tests (Edge Cases)** | ~60-70 | 🗑️ **REMOVE** | Remove flaky/low-value tests | 2-4 hours |
| **Infrastructure Tests** | ~20-30 | ✅ **FIX** | Mock setup, test utilities | 4-6 hours |

### Specific Recommendations

**1. Fix Immediately (P0 - Critical Paths):**
- ✅ Authentication flows (login, logout, protected routes)
- ✅ Video generation pipeline (start, status, completion)
- ✅ Video playback and download
- ✅ Core API endpoints (health, auth, generations)

**2. Fix or Defer (P1 - Important Features):**
- ⚠️ Dashboard polling logic (if used in production)
- ⚠️ Editor operations (trim, split, merge) - if actively used
- ⚠️ Gallery search and filtering - if actively used

**3. Remove (P3 - Low Value):**
- 🗑️ Tests with hardcoded data that's outdated
- 🗑️ Tests for features that changed significantly
- 🗑️ Flaky tests that fail randomly
- 🗑️ Tests that duplicate coverage (test same thing at multiple levels)

**4. Systematize (Infrastructure):**
- ✅ Create shared mock utilities
- ✅ Standardize test data factories
- ✅ Fix network mocking patterns
- ✅ Add test execution prioritization

---

## Lightweight MVP Testing Strategy

### Core Principles

1. **Risk-Based Testing**: Test what breaks the product, not everything
2. **Fast Feedback**: P0 tests run on every commit (<5 min)
3. **Pragmatic Coverage**: 80% of value from 20% of tests
4. **Maintainable**: Easy to fix, easy to extend

### Test Level Distribution (MVP)

**Recommended Split:**
- **Unit Tests**: 40% (fast, isolated, business logic)
- **API/Integration Tests**: 40% (service contracts, critical flows)
- **E2E Tests**: 20% (critical user journeys only)

**Current Split (Estimated):**
- Unit: ~35%
- Integration: ~40%
- E2E: ~25%

**Assessment**: ✅ Current distribution is reasonable for MVP.

### Priority-Based Execution

**P0 (Critical) - Run on Every Commit:**
- Authentication (login, logout, token refresh)
- Video generation start/status
- Video playback
- Core API health checks
- **Target**: <5 minutes execution time

**P1 (High) - Run on PR to Main:**
- Video gallery operations
- Editor operations (if used)
- User profile
- **Target**: <15 minutes execution time

**P2 (Medium) - Run Nightly:**
- Search and filtering
- Advanced editor features
- Quality metrics
- **Target**: <30 minutes execution time

**P3 (Low) - Run On-Demand:**
- Edge cases
- Performance benchmarks
- Exploratory tests

### Test Organization Structure

```
frontend/src/__tests__/
├── unit/              # Pure functions, utilities
│   ├── services/
│   └── utils/
├── integration/       # API client, auth flows
│   ├── api/
│   └── auth/
├── e2e/               # Critical user journeys
│   ├── auth.e2e.test.tsx
│   ├── generation.e2e.test.tsx
│   └── playback.e2e.test.tsx
└── support/           # Test utilities, factories
    ├── factories/
    ├── mocks/
    └── fixtures/
```

**Current State**: Tests are flat in `__tests__/` directory.
**Recommendation**: ⏸️ **Defer reorganization** - not critical for MVP, can refactor later.

---

## Systematization Recommendations

### 1. Mock Setup Standardization (HIGH PRIORITY)

**Problem**: Inconsistent mock patterns across tests.

**Solution**: Create shared mock utilities.

**Implementation:**
```typescript
// frontend/src/__tests__/support/mocks/generations.ts
import { vi } from 'vitest';

export const createGenerationsMock = () => ({
  getGenerations: vi.fn(),
  getGeneration: vi.fn(),
  deleteGeneration: vi.fn(),
  getQualityMetrics: vi.fn(),
  cancelGeneration: vi.fn(),
});

// Usage in tests
import { createGenerationsMock } from '../support/mocks/generations';

vi.mock('../lib/services/generations', () => ({
  ...createGenerationsMock(),
}));
```

**Effort**: 4-6 hours
**Impact**: Fixes ~20-30 failing tests
**Priority**: P0

### 2. Network Mocking Standardization (HIGH PRIORITY)

**Problem**: Tests making real API calls, causing timeouts.

**Solution**: Use MSW (Mock Service Worker) or Vitest's fetch mocking.

**Implementation:**
```typescript
// frontend/src/__tests__/support/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/user/profile', () => {
    return HttpResponse.json({
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
    });
  }),
];
```

**Effort**: 6-8 hours
**Impact**: Fixes timeout issues, speeds up tests
**Priority**: P0

### 3. Test Data Factories (MEDIUM PRIORITY)

**Problem**: Hardcoded test data, difficult to maintain.

**Solution**: Create factories using faker or similar.

**Implementation:**
```typescript
// frontend/src/__tests__/support/factories/generation.ts
import { faker } from '@faker-js/faker';

export const createGenerationFactory = (overrides = {}) => ({
  id: faker.string.uuid(),
  prompt: faker.lorem.sentence(),
  status: 'completed',
  video_url: faker.internet.url(),
  ...overrides,
});
```

**Effort**: 4-6 hours
**Impact**: Improves test maintainability
**Priority**: P1

### 4. Test Prioritization Tags (MEDIUM PRIORITY)

**Problem**: No way to run only critical tests.

**Solution**: Add priority tags to tests.

**Implementation:**
```typescript
// P0 test
it('should authenticate user [P0]', () => {
  // ...
});

// Run only P0 tests
npm test -- --grep="\[P0\]"
```

**Effort**: 2-4 hours
**Impact**: Enables fast feedback loops
**Priority**: P1

### 5. Test Isolation Improvements (LOW PRIORITY)

**Problem**: Tests interfering with each other.

**Solution**: Improve cleanup, use proper fixtures.

**Effort**: 4-6 hours
**Impact**: Reduces flakiness
**Priority**: P2

---

## Action Plan

### Phase 1: Quick Wins (Sprint 1 - 1-2 days)

**Goal**: Fix critical test infrastructure issues.

1. ✅ Create shared mock utilities (4-6 hours)
   - Fix `getGeneration` mock export issue
   - Standardize service mocks
   - **Impact**: Fixes ~20-30 tests

2. ✅ Fix network mocking (6-8 hours)
   - Set up MSW or Vitest fetch mocking
   - Fix timeout issues in polling tests
   - **Impact**: Fixes ~10-15 tests

3. ✅ Tag P0 tests (2 hours)
   - Identify and tag critical path tests
   - Enable fast feedback loops
   - **Impact**: Enables selective test execution

**Total Effort**: 12-16 hours (~2 days)
**Expected Result**: ~30-45 tests fixed, P0 tests running reliably

### Phase 2: Cleanup (Sprint 2 - 1 day)

**Goal**: Remove low-value tests, defer non-critical fixes.

1. ⏸️ Audit and remove outdated tests (2-4 hours)
   - Identify tests for removed/changed features
   - Remove duplicate coverage
   - **Impact**: Reduces maintenance burden

2. ⏸️ Defer P2/P3 test fixes (document only)
   - Document which tests are deferred
   - Add TODO comments
   - **Impact**: Clear backlog for post-MVP

**Total Effort**: 2-4 hours
**Expected Result**: Cleaner test suite, clear priorities

### Phase 3: Systematization (Post-MVP - Optional)

**Goal**: Build robust test infrastructure for scale.

1. Create test data factories
2. Improve test isolation
3. Reorganize test directory structure
4. Add test coverage reporting
5. Set up CI/CD test execution

---

## Quality Gate Criteria (MVP)

### Minimum Viable Testing

**Must Have:**
- ✅ All P0 tests pass (100%)
- ✅ P0 tests execute in <5 minutes
- ✅ No flaky P0 tests
- ✅ Critical user journeys covered

**Nice to Have:**
- ⚠️ P1 tests pass rate ≥80%
- ⚠️ Test coverage ≥60% for critical paths
- ⚠️ No network timeouts in tests

**Can Defer:**
- ⏸️ P2/P3 test fixes
- ⏸️ Comprehensive test coverage
- ⏸️ Test infrastructure perfection

### Release Readiness

**For MVP Launch:**
- ✅ Product works (verified manually)
- ✅ P0 tests pass (automated verification)
- ✅ Critical paths tested
- ⚠️ Known test debt documented

**Not Required for MVP:**
- ❌ 100% test pass rate
- ❌ Comprehensive test coverage
- ❌ Perfect test infrastructure
- ❌ All tests passing

---

## Cost-Benefit Analysis

### Option 1: Fix All Tests (Comprehensive)

**Effort**: 40-60 hours (~1-1.5 weeks)
**Benefit**: 100% test pass rate, comprehensive coverage
**Cost**: Delays MVP launch, high opportunity cost
**Recommendation**: ❌ **NOT RECOMMENDED** for MVP

### Option 2: Selective Fix (Recommended)

**Effort**: 12-16 hours (~2 days)
**Benefit**: P0 tests pass, fast feedback, clear priorities
**Cost**: Some tests still failing (P2/P3)
**Recommendation**: ✅ **RECOMMENDED** for MVP

### Option 3: Remove All Failing Tests

**Effort**: 4-6 hours (~1 day)
**Benefit**: Clean test suite, no failures
**Cost**: Loss of test coverage, technical debt
**Recommendation**: ⚠️ **NOT RECOMMENDED** - too aggressive

### Option 4: Defer All Fixes

**Effort**: 0 hours
**Benefit**: No time spent on tests
**Cost**: Test debt accumulates, no automated verification
**Recommendation**: ❌ **NOT RECOMMENDED** - too risky

---

## Recommendations Summary

### Immediate Actions (This Week)

1. ✅ **Fix mock setup issues** (4-6 hours)
   - Create shared mock utilities
   - Fix `getGeneration` export issue
   - Standardize service mocks

2. ✅ **Fix network mocking** (6-8 hours)
   - Set up MSW or Vitest fetch mocking
   - Fix timeout issues

3. ✅ **Tag P0 tests** (2 hours)
   - Identify critical path tests
   - Enable selective execution

**Total**: 12-16 hours (~2 days)

### Short-Term Actions (Next Sprint)

1. ⏸️ **Remove outdated tests** (2-4 hours)
   - Clean up tests for removed features
   - Remove duplicate coverage

2. ⏸️ **Document deferred tests** (1 hour)
   - Add TODO comments
   - Create backlog

### Long-Term Actions (Post-MVP)

1. Create test data factories
2. Improve test isolation
3. Reorganize test structure
4. Add coverage reporting

---

## Conclusion

**Current State**: Product works ✅, but test suite has infrastructure debt.

**Recommendation**: **Selective Fix Strategy**
- Fix P0 tests (critical paths) - 12-16 hours
- Remove/defer P2/P3 tests - 2-4 hours
- Systematize mock setup - ongoing

**Expected Outcome**:
- ✅ P0 tests passing (<5 min execution)
- ✅ Fast feedback loops enabled
- ✅ Clear test priorities
- ⚠️ Some P2/P3 tests still failing (acceptable for MVP)

**Risk Assessment**: Low risk for MVP launch. Test debt is manageable and can be addressed post-MVP without blocking product delivery.

---

## Appendix

### Test Failure Examples

**Example 1: Missing Mock Export**
```typescript
// VideoDetail.test.tsx
vi.mock("../lib/services/generations", () => ({
  getGenerations: vi.fn(),
  deleteGeneration: vi.fn(),
  // Missing: getGeneration
}));

// Fix:
vi.mock("../lib/services/generations", () => ({
  getGenerations: vi.fn(),
  getGeneration: vi.fn(), // Add this
  deleteGeneration: vi.fn(),
}));
```

**Example 2: Network Timeout**
```typescript
// Dashboard.polling.test.tsx
// Problem: Real API call, not mocked
const profile = await getUserProfile(); // Times out after 300s

// Fix: Mock the service
vi.mock("../lib/userService", () => ({
  getUserProfile: vi.fn().mockResolvedValue(mockProfile),
}));
```

### Related Documents

- PRD: `docs/PRD.md`
- Epics: `docs/epics.md`
- Architecture: `docs/architecture.md`
- Sprint Status: `docs/sprint-artifacts/sprint-status.yaml`

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `.bmad/bmm/testarch/test-design`
**Version**: 4.0 (BMad v6)
**Assessment Type**: System-Level Brownfield Review


