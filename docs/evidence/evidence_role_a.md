# Evidence Pack - Role A (PM / Threat Alignment)

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

**Team Member:** Role A  
**Role:** PM / Threat Alignment Lead  
**Milestone:** M3  

---

## 1. Contributions (2-5 bullets)

1. Created Threat→Test Coverage Matrix mapping all 4 threat categories to 27 specific test cases
2. Identified and documented Gap List with P0/P1/P2 priority assignments
3. Led Team Review meeting on 2026-03-16 with documented decisions and deadlines
4. Coordinated requirements with Role B (legitimate samples, paymaster vectors)
5. Provided matrix and gap list to Role D for Final Report integration

---

## 2. Verifiable Evidence (≥2 items)

### Evidence 1: Coverage Matrix Document

**Location:** `docs/threat_test_coverage_matrix.md`

**Description:** Complete mapping of Threat Model V1 to test cases

**Verification:** 
- ✅ 4 threat categories documented (T1-T4)
- ✅ 27 test cases mapped
- ✅ Results recorded for each test

### Evidence 2: Gap List

**Location:** Section in `docs/threat_test_coverage_matrix.md`

**Description:** Prioritized list of uncovered test scenarios

**Verification:**
- ✅ P0 gaps identified: 2 (Multi-vector attacks, 1000+ stability)
- ✅ P1 gaps identified: 3 (Paymaster variants, P95 latency, Edge case signatures)
- ✅ P2 gaps identified: 3 (Gas price manipulation, Cross-contract reentrancy, Formal verification)
- ✅ Each gap assigned to B or C

### Evidence 3: Team Review Minutes

**Location:** `docs/evidence/review_minutes.md`

**Date:** 2026-03-16

**Attendees:** A, B, C, D

**Decisions:**
- Decision 1: Test Execution Schedule - Owner: C - Deadline: 2026-03-17
- Decision 2: AI Error Documentation - Owner: B - Deadline: 2026-03-17
- Decision 3: Final Integration - Owner: All - Deadline: 2026-03-18

---

## 3. Validation Performed (≥1 item)

### Validation: Gap List vs Actual Commits

| Gap ID | Assigned To | Expected Deliverable | Status |
|--------|-------------|---------------------|--------|
| G-P0-001 | B | Multi-vector attacks | ✅ PAYMASTER_ATTACKS added |
| G-P0-002 | C | 1000+ stability test | ✅ run_all_tiers.sh created |
| G-P1-001 | B | Paymaster variants | ✅ 3 paymaster attacks added |

---

## 4. AI Usage Transparency

### AI Adopted

**Tool:** Claude

**Purpose:** Assisted in creating the coverage matrix structure and documentation

**What was adopted:** 
- Matrix table format suggestion
- Threat category organization
- Gap list prioritization framework

**Prompt used:**
```
"Create a threat-to-test coverage matrix structure for ERC-4337 security testing with 4 threat categories"
```

### AI Rejected

**Tool:** Claude

**Proposed output:** AI suggested adding formal verification as a test category

**Why rejected:** Formal verification is out of scope for M3; focus is on empirical testing with AI-generated attacks

**Correction:** Limited test categories to practical fuzzing approaches

---

## Appendix: Supporting Materials

- [x] Coverage Matrix: `docs/threat_test_coverage_matrix.md`
- [x] Review minutes: `docs/evidence/review_minutes.md`
- [x] File ownership: `docs/FILE_OWNERSHIP.md`
- [x] Team assignment: `docs/M3_TEAM_ASSIGNMENT.md`

---

**Signature:** ______________________  
**Date:** 2026-03-16