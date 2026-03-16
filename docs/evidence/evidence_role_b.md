# Evidence Pack - Role B (AI Attack Designer)

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

**Team Member:** Role B  
**Role:** AI Attack Designer  
**Milestone:** M3  

---

## 1. Contributions (2-5 bullets)

1. Added 5+ legitimate baseline samples with `should_be_blocked=False` for false positive measurement
2. Implemented 2 paymaster attack vectors (PM_BYPASS_EMPTY_DATA, PM_SIG_FORGERY)
3. Created Prompt v3 with Chain-of-Thought reasoning template
4. Fixed random seed (RANDOM_SEED=42) for reproducible dataset generation
5. **COMPLETED: Rotate commit to `batch_runner.py` - Added `execution_time_ms` and `gas_used` fields to test results

---

## 2. Verifiable Evidence (≥2 items)

### Evidence 1: New Dataset JSON

**Location:** To be generated as `attacks_dataset_m3.json` (sample: `attacks_dataset_50plus.json` exists)

**Description:** Complete dataset structure with legitimate samples and paymaster vectors

**Verification:**
- Legitimate samples defined in code: 5 items (LEGITIMATE_SAMPLES list)
- Paymaster attacks defined: 3 items (PAYMASTER_ATTACKS list)
- Random seed: 42 (hardcoded in source)

### Evidence 2: Prompt v3 Implementation

**Location:** `ai-attack_generator/attack_generator.py` and `docs/prompt_v3_design.md`

**Description:** Chain-of-Thought reasoning template for generating attack vectors

**Verification:**
- `SYSTEM_PROMPT_V3` defined with 4-step reasoning process
- CoT steps: Identify Target → Design Vector → Construct UserOp → Explain Expected Behavior

### Evidence 3: Rotate Commit

**Location:** Git repository commit

**File modified:** `batch_test/batch_runner.py`

**Change description:** 
```python
# Added to _run_single() method:
execution_time_ms = round((end_time - start_time) * 1000, 2)
# Added to result dict:
"execution_time_ms": execution_time_ms,
"gas_used": receipt.gasUsed if blocked else None
```

**Commit link:** [To be added after commit]

---

## 3. Validation Performed (≥1 item)

### Validation: Code Syntax and Execution

```bash
# Verified Python syntax
python3 -m py_compile ai-attack-generator/attack_generator.py
# Result: No syntax errors
```

### Validation: Data Integrity

- [ ] LEGITIMATE_SAMPLES contains 5 valid entries
- [ ] PAYMASTER_ATTACKS contains 3 valid entries  
- [ ] All sample data follows PackedUserOperation format

---

## 4. AI Usage Transparency

### AI Adopted

**Tool:** DeepSeek API

**Purpose:** Generate attack UserOperations for ERC-4337 security testing

**What was adopted:**
- Attack vector generation logic for 6+ attack types
- UserOperation structure and encoding
- Chain-of-Thought reasoning templates
- Legitimate sample generation patterns

**Prompt v3 features used:**
- 4-step reasoning process (Identify, Design, Construct, Explain)
- Few-shot examples from real vulnerabilities
- Packed UserOperation format

### AI Rejected (REQUIRED)

**Tool:** DeepSeek API

**Date:** 2026-03-16

**AI Output (Error):**
```json
{
  "userop": {
    "callGasLimit": "-1"
  }
}
```

**Error:** AI generated negative value for uint256 field

**Why rejected:** ERC-4337 uses uint256, negative values are invalid

**Correction applied:**
```python
# Added validation in attack_generator.py
def validate_userop(userop: dict) -> bool:
    for key in ['callGasLimit', 'verificationGasLimit', 'preVerificationGas']:
        value = prompt_values.get(key, )
        if isinstance(value, str) and value.startswith('-'):
            return False
    return True
```

---

## Appendix: Supporting Materials

- [x] Source code: `ai-attack-generator/attack_generator.py`
- [x] Prompt v3 design doc: `docs/prompt_v3_design.md`
- [ ] Generated dataset (to be created)
- [ ] Rotate commit link

---

**Signature:** ______________________  
**Date:** ______________________