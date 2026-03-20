# Document Ownership Summary

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

This document lists all project files and their assigned owners based on M3 team roles.

---

## Role Assignment Summary

| Role | Title | Focus Area |
|------|-------|------------|
| **A** | PM / Threat Alignment Lead | Coverage matrix, gap list, review coordination |
| **B** | AI Attack Designer | Attack vectors, Prompt v3, legitimate samples |
| **C** | Test Execution & Data Analyst | Three-tier tests, metrics, comparison charts |
| **D** | Report & PPT Lead | Final report, AI appendix, presentation |

---

## File Ownership Matrix

### Documentation Files (docs/)

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `README.md` | **ALL** | Project overview and M3 中文指南 | ✅ Complete |
| `docs/M3_TEAM_ASSIGNMENT.md` | **A** | Detailed role responsibilities | ✅ Complete |
| `docs/TODO.md` | **D** | Project task tracking | ✅ Complete |
| `docs/threat_test_coverage_matrix.md` | **A** | Threat→Test mapping | ✅ Complete |
| `docs/spec_driven_mapping.md` | **D** | Spec-Driven 4-column mapping (+5% bonus) | ✅ Complete |
| `docs/prompt_v3_design.md` | **B** | Prompt v3 design document | ✅ Complete |
| `docs/final_report.md` | **D** | Complete project report | ✅ Complete |
| `docs/presentation.md` | **D** | 7-slide presentation | ✅ Complete |
| `docs/FILE_OWNERSHIP.md` | **ALL** | File ownership summary | ✅ Complete |

### Evidence Pack Templates (docs/evidence/)

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `docs/evidence/evidence_role_a.md` | **A** | Evidence pack template for Role A | ✅ Complete |
| `docs/evidence/evidence_role_b.md` | **B** | Evidence pack template for Role B | ✅ Complete |
| `docs/evidence/evidence_role_c.md` | **C** | Evidence pack template for Role C | ✅ Complete |
| `docs/evidence/evidence_role_d.md` | **D** | Evidence pack template for Role D | ✅ Complete |
| `docs/evidence/review_minutes.md` | **A** | Team review meeting template | ✅ Complete |
| `docs/evidence/ai_error_correction.md` | **B** | AI error correction case study | ✅ Complete |

### Smart Contracts (erc4337-security-test V2/contracts/)

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `contracts/core/EntryPoint.sol` | **A** | Core ERC-4337 entry point | ✅ Existing |
| `contracts/accounts/SimpleAccount.sol` | **A** | Standard wallet implementation | ✅ Existing |
| `contracts/accounts/Attack.sol` | **B** | Malicious test contract | ✅ Existing |
| `contracts/core/BasePaymaster.sol` | **B** | Paymaster base contract | ✅ Existing |

### AI Attack Generator

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `ai-attack-generator/attack_generator.py` | **B** | Main attack generator with Prompt v3, legitimate samples, paymaster vectors | ✅ Updated |
| `ai-attack-generator/analyze_results.py` | **C** | Result analysis | ✅ Existing |

### Test Execution

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `batch_test/batch_runner.py` | **B** (Rotate) | Batch test execution with timing | ✅ Updated |
| `batch_test/visualizer.py` | **C** | Chart generation + metrics computation | ✅ Updated |
| `run_all_tiers.sh` | **C** | Three-tier test script | ✅ Created |
| `logs/sample_output.log` | **C** | Sample test output | ✅ Created |

### Analysis Outputs

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `analysis_outputs/metrics_summary_sample.csv` | **C** | Sample metrics CSV | ✅ Created |

### Deployment Scripts

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `scripts/deploy_contracts.py` | **C** (Rotate) | Contract deployment with verify utility | ✅ Updated |
| `hardhat.config.js` | **C** (Rotate) | Hardhat configuration | ✅ Existing |

### Dataset Files

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `attacks_dataset_50plus.json` | **B** | M2 attack dataset | ✅ Existing |
| `attacks_dataset_m3.json` | **B** | M3 dataset (with legit + paymaster) | ❌ To Generate |

### Threat Model Documents

| File | Owner | Description | Status |
|------|-------|-------------|--------|
| `Threat Model V1.pdf` | **D** | Initial threat model | ✅ Existing |
| `Threat Model V2.pdf` | **D** | Updated threat model | ✅ Existing |

---

## Pending Implementation Tasks

### Role A (PM / Threat Alignment)

| Task | File | Priority |
|------|------|----------|
| Review and update coverage matrix | `docs/threat_test_coverage_matrix.md` | P0 |
| Document team review minutes | `docs/evidence/review_minutes.md` | P1 |
| Coordinate with B/C on gaps | Issues/Messages | P0 |

### Role B (AI Attack Designer)

| Task | File | Priority | Rotate |
|------|------|----------|--------|
| Add legitimate baseline samples | `ai-attack-generator/attack_generator.py` | P0 | - |
| Add paymaster attack vectors | `ai-attack-generator/attack_generator.py` | P0 | - |
| Implement Prompt v3 | `ai-attack-generator/attack_generator.py` | P0 | - |
| Fix random seed (42) | `ai-attack-generator/attack_generator.py` | P1 | - |
| **Rotate commit** | `batch_test/batch_runner.py` | **Required** | ✅ |

### Role C (Test Execution & Data Analyst)

| Task | File | Priority | Rotate |
|------|------|----------|--------|
| Create run_all_tiers.sh | `run_all_tiers.sh` | P0 | - |
| Execute smoke test (100) | `logs/tier_100.log` | P0 | - |
| Execute medium test (500) | `logs/tier_500.log` | P1 | - |
| Execute large test (1000) | `logs/tier_1000.log` | P1 | - |
| Compute metrics | `metrics_summary.csv` | P0 | - |
| Generate comparison charts | `analysis_outputs/*.png` | P0 | - |
| Add metrics computation | `batch_test/visualizer.py` | P0 | - |
| **Rotate commit** | `scripts/` or `hardhat.config.js` | **Required** | ✅ |

### Role D (Report & PPT Lead)

| Task | File | Priority |
|------|------|----------|
| Finalize report | `docs/final_report.md` | P0 |
| Validate consistency | All documents | P0 |
| Generate PDF | `docs/final_report.pdf` | P1 |
| Generate PPT | `docs/presentation.pdf` | P1 |

---

## Rotate Commit Requirements

### Role B (Execution Side)

**Must commit to:** `batch_test/batch_runner.py`

**Examples of valid changes:**
- Add result field for execution duration
- Add exception handling for failed operations
- Improve log output format
- Add parallel execution support

### Role C (Deployment Side)

**Must commit to:** `scripts/deploy_contracts.py` OR `hardhat.config.js`

**Examples of valid changes:**
- Update deployment script for new contracts
- Fix environment configuration
- Add README instructions
- Update network configuration

---

## Evidence Pack Checklist by Role

### Role A
- [ ] Coverage Matrix PDF
- [ ] Gap List with P0/P1/P2
- [ ] Review minutes screenshot
- [ ] Requirements issued to B/C
- [ ] AI error correction example

### Role B
- [ ] New dataset JSON (legit + paymaster)
- [ ] Prompt v3 file
- [ ] AI error screenshot + fix
- [ ] Rotate commit link
- [ ] Fixed seed documentation

### Role C
- [ ] Three-tier log screenshots
- [ ] Metrics CSV file
- [ ] Comparison charts (PNG)
- [ ] Reproduction commands
- [ ] Rotate commit link

### Role D
- [ ] Report commit history
- [ ] Spec-Driven matrix
- [ ] PPT file
- [ ] AI Appendix
- [ ] Consistency validation

---

## Directory Structure

```
ERC-4337/
├── README.md                          # ALL - Project overview
├── Threat Model V1.pdf                # D - Threat model
├── Threat Model V2.pdf                # D - Threat model
├── docs/
│   ├── M3_TEAM_ASSIGNMENT.md          # A - Team responsibilities
│   ├── TODO.md                        # D - Task tracking
│   ├── threat_test_coverage_matrix.md # A - Threat mapping
│   ├── spec_driven_mapping.md         # D - Spec-Driven bonus
│   ├── prompt_v3_design.md            # B - Prompt design
│   ├── final_report.md                # D - Final report
│   ├── presentation.md                # D - Slides
│   └── evidence/
│       ├── evidence_role_a.md         # A - Evidence template
│       ├── evidence_role_b.md         # B - Evidence template
│       ├── evidence_role_c.md         # C - Evidence template
│       └── evidence_role_d.md         # D - Evidence template
├── erc4337-security-test V2/
│   ├── contracts/                     # A - Smart contracts
│   ├── ai-attack-generator/           # B - AI generator
│   ├── batch_test/                    # B/C - Testing
│   ├── scripts/                       # C - Deployment
│   └── tests/                         # C - Test scripts
└── logs/                              # C - Test logs (to create)
```

---

**Document Owner:** All Team Members  
**Last Updated:** March 2026