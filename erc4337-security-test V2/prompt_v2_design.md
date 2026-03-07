# System Prompt v2 - Few-Shot Learning Design

**Version:** 2.0  
**Date:** 2026-03-04  
**Author:** Member B (AI Attack Designer)  
**Project:** AI-Driven Fuzzing Framework for ERC-4337  
**Milestone:** M2 - Batch Generation & Few-Shot Learning

---

## Overview

This document describes the design rationale and implementation of System Prompt v2, which introduces **Few-Shot Learning** to improve attack quality and diversity. Prompt v2 builds on v1's foundation by adding concrete attack examples from real-world vulnerabilities.

---

## What's New in v2

### Key Enhancements from v1

| Feature | v1 (M1) | v2 (M2) |
|---------|---------|---------|
| **Examples** | None | 3 Few-Shot examples from real vulnerabilities |
| **Guidance** | Basic schema | Detailed attack explanations |
| **Diversity** | Single category | Multi-category with examples |
| **Temperature** | 0.7 | 0.9 (higher for more variety) |

### Why Few-Shot Learning?

**Problem with v1:**
- AI generated simplistic, repetitive attacks
- Lack of real-world context led to unrealistic test cases
- Missing edge cases that actual attackers would exploit

**Solution with v2:**
- Provide 3 concrete examples of real attacks
- Show AI what "good" attack looks like
- Guide AI toward realistic vulnerability patterns
- Increase temperature for more creative variations

---

## Prompt Structure

### Component 1: Role Definition (Unchanged from v1)
```
"You are an expert Ethereum security researcher specializing in 
ERC-4337 Account Abstraction vulnerabilities."
```

### Component 2: Schema Specification (Unchanged from v1)
Provides complete ERC-4337 UserOperation structure with field types.

### Component 3: Few-Shot Examples (NEW in v2)

Three real-world inspired attack examples with explanations:

#### Example 1: Nonce Replay Attack
**Source:** Inspired by Gnosis Safe vulnerability  
**Attack Vector:** Reusing nonce=0 after deployment

```json
{
  "sender": "0x1234567890123456789012345678901234567890",
  "nonce": "0",
  "callData": "0x",
  "callGasLimit": "100000",
  "verificationGasLimit": "50000",
  "preVerificationGas": "21000",
  "maxFeePerGas": "20000000000",
  "maxPriorityFeePerGas": "1000000000",
  "signature": "0x0000000000000000000000000000000000000000000000000000000000000000"
}
```

**Attack Explanation:** Reusing nonce=0 after deployment allows replay attacks if implementation doesn't properly track executed nonces.

**Why This Example:**
- Real vulnerability pattern from audited contracts
- Tests nonce validation logic
- Simple but effective attack strategy

---

#### Example 2: Gas Limit Manipulation
**Source:** Inspired by Argent wallet audit findings  
**Attack Vector:** uint256 max value with minimal verification gas

```json
{
  "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdef",
  "nonce": "1",
  "callData": "0xa9059cbb0000000000000000000000000000000000000000000000000000000000000000",
  "callGasLimit": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
  "verificationGasLimit": "1",
  "preVerificationGas": "0",
  "maxFeePerGas": "1000000000",
  "maxPriorityFeePerGas": "1000000000",
  "signature": "0x1234"
}
```

**Attack Explanation:** callGasLimit set to uint256 max value (2^256-1) while verificationGasLimit is minimal - tests for gas estimation vulnerabilities and integer overflow in gas calculations.

**Why This Example:**
- Tests arithmetic overflow protection
- Realistic attack on gas estimation logic
- Shows importance of checking gas field relationships

---

#### Example 3: Signature Forgery with Wrong Length
**Source:** Inspired by OpenZeppelin audit findings  
**Attack Vector:** Zero address with malformed 4-byte signature

```json
{
  "sender": "0x0000000000000000000000000000000000000000",
  "nonce": "42",
  "callData": "0x",
  "callGasLimit": "100000",
  "verificationGasLimit": "100000",
  "preVerificationGas": "21000",
  "maxFeePerGas": "3000000000",
  "maxPriorityFeePerGas": "2000000000",
  "signature": "0xdeadbeef"
}
```

**Attack Explanation:** Zero address sender with malformed 4-byte signature (should be 65 bytes for ECDSA) tests for edge cases in signature validation logic.

**Why This Example:**
- Tests multiple validation layers (address + signature)
- Common vulnerability pattern: insufficient length checks
- Realistic attack vector seen in production audits

---

### Component 4: Attack Categories (Enhanced in v2)

Same 6 categories as v1, but with more specific guidance:

1. **Integer overflow/underflow** - Gas fields at extreme values (uint256 max, negative-like values)
2. **Invalid addresses** - Zero address, non-existent contracts, contract creation addresses
3. **Malformed callData** - Wrong selectors, corrupted params, empty data, oversized data
4. **Signature forgery** - Empty, wrong length, invalid values, replay signatures
5. **Nonce manipulation** - Replay (duplicate), future nonces, negative-looking values
6. **Gas limit attacks** - Extremely high/low, inconsistent limits, zero gas

### Component 5: Diversity Emphasis (NEW in v2)
```
IMPORTANT: Generate DIVERSE attacks. Each UserOperation should be 
unique and test different edge cases.
```

---

## Design Rationale

### Why These Specific Examples?

1. **Nonce Replay (Example 1)**
   - Classic attack pattern
   - Easy for AI to understand and vary
   - Tests fundamental replay protection

2. **Gas Manipulation (Example 2)**
   - Shows integer overflow pattern
   - Demonstrates field relationships
   - Tests gas estimation edge cases

3. **Signature Forgery (Example 3)**
   - Multi-vector attack (address + signature)
   - Tests validation chain
   - Real-world vulnerability pattern

### Why 3 Examples?

**Research shows:**
- 1 example: Too little guidance
- 2 examples: Better but limited diversity
- 3 examples: Optimal balance of guidance and variety
- 5+ examples: Diminishing returns, increases token cost

**Source:** "Language Models are Few-Shot Learners" (GPT-3 paper)

---

## Temperature Tuning

### v1 Temperature: 0.7
- Conservative, consistent outputs
- Lower diversity
- Fewer creative attacks

### v2 Temperature: 0.9
- Higher creativity
- More diverse attack patterns
- Better exploration of edge cases

**Why 0.9?**
- Balances consistency with variety
- Prevents excessive randomness
- Works well with Few-Shot examples to anchor outputs

---

## Expected Improvements

### Attack Quality Metrics

| Metric | v1 (M1) | v2 (M2 Target) |
|--------|---------|----------------|
| **Realism** | Low | High (real-vulnerability inspired) |
| **Diversity** | Low | High (temperature 0.9 + examples) |
| **Edge Case Coverage** | Basic | Comprehensive |
| **Multi-Vector Attacks** | None | Emerging |

### Success Criteria for v2

- ✓ Generate 50+ attacks with >90% schema compliance
- ✓ Cover all 6 attack categories
- ✓ Include realistic attack patterns
- ✓ Demonstrate variation in attack strategies
- ✓ Pass automated validation

---

## Attack Vector Mapping (Enhanced)

| Attack Category | Few-Shot Example | Target Component | Expected Improvement |
|----------------|-------------------|------------------|----------------------|
| Nonce Manipulation | Example 1 | nonce field | Better replay attack variants |
| Integer Overflow | Example 2 | Gas fields | More extreme value combinations |
| Signature Forgery | Example 3 | signature field | Varied length attacks |
| Invalid Address | Example 3 | sender field | Edge case addresses |
| Malformed callData | Implicit | callData field | Better selector attacks |
| Gas Limit Attack | Example 2 | All gas fields | Inconsistent limit patterns |

---

## Implementation Details

### Prompt Integration
The v2 prompt is implemented in `batch_generator.py`:

```python
def get_system_prompt_v2(self) -> str:
    return """..."""  # Contains Few-Shot examples
```

### Usage in Batch Generation
```python
generator = BatchAttackGenerator(api_key=api_key)
generator.temperature = 0.9  # Higher temperature for diversity
attacks = await generator.generate_batch(count=50)
```

---

## Known Limitations (v2)

### Issues to Address in v3

1. **No Chain-of-Thought Reasoning**
   - AI doesn't explain attack strategy
   - Hard to audit attack logic
   - **Solution:** Add CoT in Prompt v3 (Milestone 3)

2. **Single-Vector Attacks Only**
   - Each attack targets one vulnerability type
   - Real attackers combine multiple vectors
   - **Solution:** Multi-vector combination attacks in M3

3. **Manual Example Curation**
   - Few-Shot examples manually selected
   - May miss emerging attack patterns
   - **Solution:** Automated example mining from audit reports

---

## Testing Methodology

### Validation Pipeline
1. Generate 50+ attacks using Prompt v2
2. Run automated validation (schema checking)
3. Measure diversity metrics
4. Categorize attack patterns
5. Compare against v1 baseline

### Success Metrics
- Schema compliance: >90%
- Attack diversity: All 6 categories covered
- Uniqueness: <10% duplicate patterns
- Realism: Matches real vulnerability patterns

---

## Prompt Evolution Roadmap

```
v1 (M1) → Basic schema + attack categories
          ↓
v2 (M2) → + Few-Shot examples (3 real attacks)
          + Higher temperature (0.9)
          + Diversity emphasis
          ↓
v3 (M3) → + Chain-of-Thought reasoning
          + Multi-vector combination attacks
          + Production-ready attack strategies
```

---

## References

### Vulnerability Sources

1. **Gnosis Safe Replay Attack**
   - https://github.com/safe-global/safe-smart-account

2. **Argent Wallet Gas Estimation**
   - https://www.argent.xyz/

3. **OpenZeppelin Audit Findings**
   - https://blog.openzeppelin.com/tag/security-audits

### Few-Shot Learning Research

- "Language Models are Few-Shot Learners" (Brown et al., 2020)
- "Prompt Engineering Guide" - https://www.promptingguide.ai/techniques/fewshot

### ERC-4337 Resources

- ERC-4337 Specification: https://eips.ethereum.org/EIPS/eip-4337
- Account Abstraction Implementation: https://github.com/eth-infinitism/account-abstraction

---

## Appendix: Full Prompt v2

See `batch_generator.py` lines 67-138 for the complete System Prompt v2 implementation.

---

**Document Status:** ✅ Complete  
**Next Step:** Generate 50+ attacks using Prompt v2 and validate diversity