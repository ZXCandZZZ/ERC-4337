# Project TODO List

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

**Status Legend:** ✅ Complete | 🔄 In Progress | ❌ Not Started | ⏳ Blocked

---

## M3 Deliverables Overview

| Category | Total | Complete | Remaining |
|----------|-------|----------|-----------|
| **Role A** | 6 | 0 | 6 |
| **Role B** | 7 | 2 | 5 |
| **Role C** | 8 | 0 | 8 |
| **Role D** | 7 | 0 | 7 |
| **Shared** | 3 | 1 | 2 |
| **TOTAL** | 31 | 3 | 28 |

---

## Role A — PM / Threat Alignment

**Owner:** @RoleA

### High Priority (P0)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| A1 | Create Threat→Test Coverage Matrix | `docs/threat_test_coverage_matrix.md` | ❌ | Week 1 | Matrix with 4 threats × tests × results |
| A2 | Create Gap List | Section in matrix | ❌ | Week 1 | P0/P1/P2 with owners |

### Medium Priority (P1)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| A3 | Team Review Minutes | `docs/evidence/review_minutes.md` | ❌ | Week 2 | Screenshot/notes |
| A4 | Requirements for B (legitimate samples) | Documented requirements | ❌ | Week 1 | Issue/message |
| A5 | Requirements for C (metrics) | Documented requirements | ❌ | Week 1 | Issue/message |

### Low Priority (P2)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| A6 | Materials to D | Matrix + Gap list | ❌ | Week 2 | Delivery confirmation |

---

## Role B — AI Attack Designer

**Owner:** @RoleB

### High Priority (P0)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| B1 | Add Legitimate Baseline Samples | `LEGIT_*` vectors in `ai_generator.py` | ❌ | Week 1 | ≥5 samples with `should_be_blocked=False` |
| B2 | Add Paymaster Attack Vectors | `PM_*` vectors in `ai_generator.py` | ❌ | Week 2 | ≥2 paymaster attack types |
| B3 | Create Prompt v3 | `SYSTEM_PROMPT_V3` with CoT | ❌ | Week 1 | Chain-of-Thought template |

### Medium Priority (P1)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| B4 | Document Prompt v3 Design | `docs/prompt_v3_design.md` | ❌ | Week 1 | Design rationale |
| B5 | Fix Random Seed | `RANDOM_SEED = 42` | ❌ | Week 2 | Reproducible dataset |

### Rotate Commit (Required)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| B6 | **Rotate Commit** | Commit to `batch_runner.py` | ❌ | Week 2 | GitHub commit link |

### Documentation

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| B7 | AI Error Correction Case | `docs/evidence/ai_error_correction.md` | ❌ | Week 3 | Screenshot + fix explanation |

---

## Role C — Test Execution & Data Analyst

**Owner:** @RoleC

### High Priority (P0)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| C1 | Create Three-Tier Test Script | `run_all_tiers.sh` | ❌ | Week 1 | Script runs 100/500/1000 |
| C2 | Smoke Test (100 ops) | `logs/tier_100.log` | ❌ | Week 1 | Log saved |
| C3 | Medium Test (500 ops) | `logs/tier_500.log` | ❌ | Week 2 | Log saved |
| C4 | Large Test (1000+ ops) | `logs/tier_1000.log` | ❌ | Week 3 | Log saved |

### Medium Priority (P1)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| C5 | Compute Metrics | `metrics_summary.csv` | ❌ | Week 2 | TP/FP/FN/P95 |
| C6 | Before/After Comparison Charts | PNG files | ❌ | Week 3 | ≥2 charts |

### Rotate Commit (Required)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| C7 | **Rotate Commit** | Commit to `scripts/` or `hardhat.config.js` | ❌ | Week 2 | GitHub commit link |

### Documentation

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| C8 | Statistical Report | PDF/Markdown | ❌ | Week 3 | Summary |

---

## Role D — Report & PPT Lead

**Owner:** @RoleD

### High Priority (P0)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| D1 | Write Final Report | `docs/final_report.md` | ❌ | Week 3 | 11 sections complete |
| D2 | Write AI Appendix | Section in report | ❌ | Week 2 | Tools + Usage + Error |
| D3 | Create Spec-Driven Page | `docs/spec_driven_mapping.md` | ❌ | Week 3 | 4-column table |

### Medium Priority (P1)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| D4 | Create Presentation | `docs/presentation.md` | ❌ | Week 3 | 7 slides |
| D5 | Consistency Validation | Checklist | ❌ | Week 3 | Terminology unified |

### Low Priority (P2)

| ID | Task | Deliverable | Status | Due | Evidence |
|----|------|-------------|--------|-----|----------|
| D6 | Integrate A's Materials | Threat Model section | ❌ | Week 2 | Matrix in report |
| D7 | Integrate C's Charts | Results section | ❌ | Week 3 | Charts in report |

---

## Shared Tasks

| ID | Task | Owner | Deliverable | Status | Due |
|----|------|-------|-------------|--------|-----|
| S1 | Update README.md | All | `README.md` | ✅ | Week 1 |
| S2 | Create Evidence Pack Templates | D | `docs/evidence/` | ❌ | Week 2 |
| S3 | Final Repository Cleanup | A | Repo structure | ❌ | Week 3 |

---

## Completed Tasks (M1 & M2)

### M1 Completed

- ✅ Environment setup (Hardhat node)
- ✅ Deploy basic ERC-4337 contracts
- ✅ AI API integration (DeepSeek)
- ✅ Prompt v1 design
- ✅ Threat Model V1 document
- ✅ Test framework skeleton

### M2 Completed

- ✅ EntryPoint contract (1013 lines)
- ✅ SimpleAccount implementation
- ✅ Paymaster base contract
- ✅ Prompt v2 with Few-Shot Learning
- ✅ 50+ attack dataset
- ✅ Basic batch testing
- ✅ Threat Model V2 document

---

## Dependencies

```
A1 (Matrix) ──┬──▶ D6 (Integrate)
              │
A2 (Gap List) ──▶ B1, B2, C5
              │
B1, B2, B3 ──────▶ C1 (Test Script)
              │
C1, C2, C3, C4 ──▶ C5 (Metrics)
              │
C5, C6 ──────────▶ D7 (Charts in Report)
              │
All ─────────────▶ D1 (Final Report)
```

---

## Risk Register

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| API rate limiting | High | Batch with delays, local fallback | B |
| Test environment issues | High | Document setup clearly, Docker | C |
| Incomplete documentation | Medium | D validates consistency | D |
| Missing evidence | Medium | Use templates, checklist | All |

---

**Document Owner:** Role D (Report Lead)  
**Last Updated:** March 2026