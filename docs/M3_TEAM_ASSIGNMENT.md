# M3 Team Assignment - Detailed Task Breakdown

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

**Document Version:** 1.0  
**Last Updated:** March 2026  
**Status:** 🔄 Active

---

## Overview

This document defines the detailed task assignments for Milestone 3 (M3), based on the official M3分工详细说明.pdf requirements. Each role has specific deliverables with clear success criteria.

---

## Role Assignments Summary

| Role | Primary Focus | Key Deliverables | Rotate Commit |
|------|---------------|------------------|---------------|
| **A** | PM / Threat Alignment | Coverage Matrix, Gap List, Review Minutes | N/A |
| **B** | AI Attack Designer | Legitimate Samples, Paymaster Vectors, Prompt v3 | Execution side (`batch_runner.py`) |
| **C** | Test Execution & Analysis | Three-tier Tests, Metrics CSV, Comparison Charts | Deployment side (`scripts/`, `hardhat.config.js`) |
| **D** | Report & PPT | Final Report, AI Appendix, Spec-Driven Page, Slides | N/A |

---

## Role A — PM / Threat Alignment Lead

### Core Responsibility
Map Threat Model V1 to current code implementation, drive B/C to fill gaps, ensure M3 transitions from "code demo" to "deliverable with threat alignment and empirical validation".

### Tasks & Deliverables

| Task ID | Task Description | Deliverable | Success Criteria | Estimated Time |
|---------|------------------|-------------|------------------|----------------|
| A1 | Create Threat→Test Coverage Matrix | `docs/threat_test_coverage_matrix.md` | All 4 threat types × test cases × results filled | 4h |
| A2 | Create Gap List | Section in coverage matrix | P0/P1/P2 priority with assigned owner | 2h |
| A3 | Team Review Minutes | `docs/evidence/review_minutes.md` | Decision + Owner + Deadline | 1h |
| A4 | Coordinate with B | Provide legitimate sample requirements | Requirements documented | 0.5h |
| A5 | Coordinate with C | Provide metrics requirements | Metrics list provided | 0.5h |
| A6 | Coordinate with D | Provide matrix and gap list | Materials delivered | 1h |

### Evidence Pack Requirements

| Required Item | Evidence Type | Location |
|---------------|---------------|----------|
| Coverage Matrix | PDF/Table | `docs/threat_test_coverage_matrix.md` |
| Review Minutes | Screenshot/Notes | `docs/evidence/review_minutes.md` |
| Requirements for B/C | Issue/Message | GitHub Issues or chat screenshot |
| AI Error Correction | Example | 1 case of AI-assisted matrix analysis |

### Collaboration Points

- **With B**: Output legitimate baseline sample requirements, paymaster vector requirements
- **With C**: Output metrics requirements (TP/FP/FN/P95, 1000+ stability)
- **With D**: Provide matrix and gap list for Final Report integration

---

## Role B — AI Attack Designer

### Core Responsibility
Fill Threat Model gaps with diverse attack vectors, provide high-quality dataset, complete Rotate commit (execution side).

### Tasks & Deliverables

| Task ID | Task Description | Deliverable | Success Criteria | Estimated Time |
|---------|------------------|-------------|------------------|----------------|
| B1 | Add Legitimate Baseline Samples | `LEGIT_*` vectors in `ai_generator.py` | ≥5 samples with `should_be_blocked=False` | 3h |
| B2 | Add Paymaster Attack Vectors | `PM_BYPASS_*`, `PM_SIG_*` in `ai_generator.py` | ≥2 paymaster attack types | 2h |
| B3 | Create Prompt v3 | `SYSTEM_PROMPT_V3` with CoT | Chain-of-Thought template | 2h |
| B4 | Document Prompt v3 Design | `docs/prompt_v3_design.md` | Design rationale documented | 1h |
| B5 | Fix Random Seed | `RANDOM_SEED = 42` in code | Dataset reproducible | 0.5h |
| B6 | **Rotate Commit** | Commit to `batch_runner.py` | At least 1 commit with meaningful change | 0.5h |
| B7 | AI Error Correction | Documentation | 1 case documented | 1h |

### Evidence Pack Requirements

| Required Item | Evidence Type | Location |
|---------------|---------------|----------|
| New Dataset JSON | JSON file | `attacks_dataset_m3.json` |
| Prompt v3 | Text file | `ai_generator.py`, `docs/prompt_v3_design.md` |
| AI Error Output | Screenshot + Fix | `docs/evidence/ai_error_correction.md` |
| Rotate Commit | Git commit link | GitHub commit URL |

### Rotate Commit Requirement

**Must commit to execution-side code:**
- File: `batch_test/batch_runner.py`
- Examples: Add result fields, exception handling, log format improvements

### Attack Vector Requirements

```python
# Legitimate Samples (should_be_blocked=False)
LEGIT_TRANSFER = {
    "sender": "0xValidAddress...",
    "nonce": "1",
    "callData": "0xa9059cbb...",  # valid transfer
    "should_be_blocked": False
}

# Paymaster Vectors
PM_BYPASS_EMPTY_DATA = {
    "paymasterAndData": "0x",  # Empty - should fail validation
    "attack_type": "paymaster_bypass"
}

PM_SIG_FORGERY = {
    "paymasterAndData": "0x<fake_paymaster><invalid_signature>",
    "attack_type": "paymaster_sig_forgery"
}
```

---

## Role C — Test Execution & Data Analyst

### Core Responsibility
Upgrade batch testing to 1000+ quantifiable results, produce before/after comparison charts, complete Rotate commit (deployment side).

### Tasks & Deliverables

| Task ID | Task Description | Deliverable | Success Criteria | Estimated Time |
|---------|------------------|-------------|------------------|----------------|
| C1 | Create Three-Tier Test Script | `run_all_tiers.sh` | Runs 100/500/1000 tests | 3h |
| C2 | Smoke Test (100 ops) | `logs/tier_100.log` | Test passes, log saved | 1h |
| C3 | Medium Test (500 ops) | `logs/tier_500.log` | Test passes, log saved | 2h |
| C4 | Large Test (1000+ ops) | `logs/tier_1000.log` | Test passes, log saved | 4h |
| C5 | Metrics Computation | `metrics_summary.csv` | TP/FP/FN/P95 computed | 3h |
| C6 | Before/After Comparison | PNG charts | ≥2 comparison charts | 2h |
| C7 | **Rotate Commit** | Commit to `scripts/` or `hardhat.config.js` | At least 1 commit | 0.5h |
| C8 | Statistical Report | PDF/Markdown | Summary of all results | 2h |

### Evidence Pack Requirements

| Required Item | Evidence Type | Location |
|---------------|---------------|----------|
| Three-Tier Logs | Terminal screenshots | `logs/tier_*.log` |
| Metrics CSV | CSV file | `metrics_summary.csv` |
| Comparison Charts | PNG images | `analysis_outputs/*.png` |
| Reproduction Commands | Text | Commands to reproduce |
| Rotate Commit | Git commit link | GitHub commit URL |

### Rotate Commit Requirement

**Must commit to deployment/environment-side code:**
- Files: `scripts/deploy_contracts.py`, `hardhat.config.js`, or `run.bat`
- Examples: Update deployment scripts, fix README, fix environment config

### Metrics to Compute

```csv
metric,value,description
true_positive,0.85,Blocked attacks / Total attacks
false_negative,0.15,Passed attacks / Total attacks
false_positive,0.05,Blocked legit / Total legit
precision,0.94,TP / (TP + FP)
recall,0.85,TP / (TP + FN)
f1_score,0.89,2 * (P * R) / (P + R)
p95_latency_ms,125,95th percentile execution time
total_tests,1000,Total operations tested
```

---

## Role D — Report & PPT Lead

### Core Responsibility
Integrate all A/B/C outputs, deliver defensible Final Report + Slides, perform consistency validation.

### Tasks & Deliverables

| Task ID | Task Description | Deliverable | Success Criteria | Estimated Time |
|---------|------------------|-------------|------------------|----------------|
| D1 | Write Final Report | `docs/final_report.md` | All 11 sections complete | 8h |
| D2 | Write AI Appendix | Section in report | Tools + Usage + Error example | 2h |
| D3 | Create Spec-Driven Page | `docs/spec_driven_mapping.md` | 4-column table complete | 2h |
| D4 | Create Presentation | `docs/presentation.md` | 7 slides complete | 4h |
| D5 | Consistency Validation | Checklist | All terminology unified | 1h |
| D6 | Integrate A's Materials | Threat Model section | Matrix integrated | 1h |
| D7 | Integrate C's Charts | Results section | All charts included | 1h |

### Evidence Pack Requirements

| Required Item | Evidence Type | Location |
|---------------|---------------|----------|
| Report Commits | Git history | Commit links |
| Spec-Driven Matrix | Screenshot | `docs/spec_driven_mapping.md` |
| PPT | PDF/PPTX | `docs/presentation.md` |
| AI Transparency | Section | AI Appendix |

### Final Report Structure

```
1. Abstract
2. Background & Motivation
3. Threat Model
   3.1 System Assumptions
   3.2 Attack Surface
   3.3 Threat Categories (from A's matrix)
4. Methodology
   4.1 AI Attack Generation
   4.2 Test Framework
5. Dataset
   5.1 Attack Vectors
   5.2 Legitimate Samples (from B)
6. Experiment Design
   6.1 Three-Tier Testing
   6.2 Metrics Definition
7. Results (from C)
   7.1 TP/FP/FN Analysis
   7.2 Before/After Comparison
8. Analysis & Discussion
   8.1 Key Findings
   8.2 Limitations
9. AI Collaboration Appendix
   9.1 Tools Used
   9.2 AI Error Example
10. Spec-Driven Evidence
11. Conclusion
```

### Presentation Structure (7 Slides)

| Slide | Title | Content |
|-------|-------|---------|
| 1 | Title | Project name, team |
| 2 | Architecture | System diagram |
| 3 | Architecture (cont.) | Component details |
| 4 | Threat Model | 4 threat categories |
| 5 | Experiment Design | Three-tier testing |
| 6 | Results | Charts + Metrics |
| 7 | Results (cont.) | Before/After comparison |
| 8 | Conclusion | Key findings |

---

## Timeline (3 Weeks)

### Week 1

| Role | Tasks |
|------|-------|
| A | Complete coverage matrix, output gap list to B/C |
| B | Legitimate samples + Prompt v3 draft |
| C | Setup three-tier framework, complete 100-op smoke test |
| D | Report outline + section placeholders |

### Week 2

| Role | Tasks |
|------|-------|
| A | Review minutes, confirm B/C gaps filled, sync with D |
| B | Paymaster vectors + Rotate commit (execution) |
| C | 500 tests + Metrics CSV + Rotate commit (deployment) |
| D | Threat Model section + AI Appendix draft |

### Week 3 (Final)

| Role | Tasks |
|------|-------|
| A | Final matrix confirmation, assist D with Q&A prep |
| B | 1000+ dataset finalized, seed saved, final JSON |
| C | 1000+ tests complete, comparison charts, statistics PDF |
| D | Full report + PPT + Spec-Driven bonus page |

---

## Evidence Pack Checklist

Each member must submit 1-2 page PDF covering:

### Role A Checklist
- [ ] Coverage Matrix PDF
- [ ] Gap List with P0/P1/P2
- [ ] Review minutes screenshot
- [ ] AI error correction example (1)
- [ ] Requirements issued to B/C

### Role B Checklist
- [ ] New dataset JSON (legit + paymaster)
- [ ] Prompt v3 file
- [ ] AI error screenshot + fix
- [ ] Rotate commit link
- [ ] Fixed seed documentation

### Role C Checklist
- [ ] Three-tier log screenshots
- [ ] Metrics CSV file
- [ ] Comparison charts (PNG)
- [ ] Reproduction commands
- [ ] Rotate commit link

### Role D Checklist
- [ ] Report commit history
- [ ] Spec-Driven matrix
- [ ] PPT file
- [ ] AI Appendix
- [ ] Consistency validation

---

## Anti-Failure Checklist

- [ ] **A**: A is not pure management - must have verifiable artifacts (matrix + gap list)
- [ ] **B/C**: Rotate commits must have GitHub links, not just verbal claims
- [ ] **D**: D does not just write - must validate consistency (terminology, charts, parameters)
- [ ] **All**: All Evidence Pack 4 required blocks must be filled
- [ ] **Bonus**: Spec-Driven (+5%) - D must create threat→invariant→test→result 4-column page
- [ ] **Repo**: Repository must be GitHub link (not ZIP), README explains reproduction

---

**Document Owner:** Role A (PM)  
**Last Updated:** March 2026