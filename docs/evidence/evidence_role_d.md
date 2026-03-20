# Evidence Pack - Role D (Report & PPT Lead)

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

**Team Member:** Role D  
**Role:** Report & PPT Lead  
**Milestone:** M3  

---

## 1. Contributions (2-5 bullets)

1. Wrote complete Final Report (11 sections, ~350 lines) integrating all team contributions
2. Created AI Collaboration Appendix documenting tool usage and error corrections
3. Produced Spec-Driven evidence page (threat→invariant→test→result 4-column mapping) for +5% bonus
4. Created 7-slide presentation (docs/presentation.md) for final demo
5. Performed consistency validation across all documents (terminology, charts, parameters)

---

## 2. Verifiable Evidence (≥2 items)

### Evidence 1: Final Report

**Location:** `docs/final_report.md`

**Description:** Complete project report with all 11 sections

**Sections verified:**
1. ✅ Abstract
2. ✅ Background & Motivation
3. ✅ Threat Model (from A's matrix)
4. ✅ Methodology
5. ✅ Dataset (from B's work)
6. ✅ Experiment Design
7. ✅ Results (from C's charts)
8. ✅ Analysis & Discussion
9. ✅ AI Collaboration Appendix
10. ✅ Spec-Driven Evidence
11. ✅ Conclusion

**File stats:** 341 lines, ~11KB

### Evidence 2: Spec-Driven Mapping

**Location:** `docs/spec_driven_mapping.md`

**Description:** 4-column mapping for +5% bonus

**Verification:**
- ✅ All 4 threat categories covered (T1-T4)
- ✅ 16 invariants defined
- ✅ 27 test cases mapped
- ✅ Results recorded
- ✅ Code references included

### Evidence 3: Presentation

**Location:** `docs/presentation.md`

**Description:** 7-slide presentation for final demo

**Slides verified:**
1. ✅ Title slide
2. ✅ Architecture (1/2)
3. ✅ Architecture (2/2)
4. ✅ Threat Model
5. ✅ Experiment Design
6. ✅ Results (1/2)
7. ✅ Results (2/2) / Conclusion

**Format:** Marp-compatible markdown

### Evidence 4: AI Error Correction Document

**Location:** `docs/evidence/ai_error_correction.md`

**Description:** Detailed AI error correction case studies

**Content:**
- ✅ 3 AI error cases documented
- ✅ Error descriptions
- ✅ Corrections applied
- ✅ Code fixes included

---

## 3. Validation Performed (≥1 item)

### Validation: Consistency Check

| Item | Check | Status |
|------|-------|--------|
| Terminology | "UserOperation" used consistently | ✅ |
| Attack count | Same total across report, slides, matrix | ✅ |
| Metrics values | TP/FP/FN values match in all documents | ✅ |
| Chart data | Charts match CSV data | ✅ |
| Parameter description | Test parameters consistent | ✅ |

### Validation: File Existence

```bash
ls -la docs/final_report.md docs/presentation.md docs/spec_driven_mapping.md
# All files exist with correct sizes
```

---

## 4. AI Usage Transparency

### AI Adopted

**Tool:** Claude

**Purpose:** Assisted in report structure and writing

**What was adopted:**
- Report section organization (11-section structure)
- Academic writing style suggestions
- Slide outline structure (7 slides)
- Spec-Driven mapping table format

### AI Rejected

**Tool:** Claude

**Proposed output:** AI suggested including extensive background literature review section

**Why rejected:** Project focuses on empirical analysis and implementation, not literature review

**Correction:** Focused on methodology and results sections instead; kept background concise

---

## Appendix: AI Collaboration Appendix Content

### Tools Used

| Tool | Purpose | Extent |
|------|---------|--------|
| DeepSeek API | Attack generation | Core component (Role B) |
| Claude | Report writing | Structure suggestions |
| Claude | Code assistance | Debugging help |

### AI Error Example (REQUIRED)

**Context:** Generating comparison charts

**AI Output:**
```python
df.plot(kind='bar', x='category', y='value')
```

**Error:** Missing figure setup, no axis labels, no title

**Correction:**
```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 6))
df.plot(kind='bar', x='category', y='value', ax=ax)
ax.set_xlabel('Attack Category')
ax.set_ylabel('Success Rate')
ax.set_title('M3 Security Test Results')
plt.savefig('chart.png')
```

---

## Appendix: Supporting Materials

- [x] Final report: `docs/final_report.md`
- [x] Spec-Driven matrix: `docs/spec_driven_mapping.md`
- [x] Presentation: `docs/presentation.md`
- [x] AI error correction: `docs/evidence/ai_error_correction.md`
- [ ] PDF versions (to be generated)

---

**Signature:** ______________________  
**Date:** 2026-03-16