# System Prompt v1 - Design Documentation

**Version:** 1.0  
**Date:** 2026-02-06  
**Author:** Member B (AI Attack Designer)  
**Project:** AI-Driven Fuzzing Framework for ERC-4337  
**Milestone:** M1 - API Integration & Initial Prompt Design

---

## Overview

This document describes the design rationale and implementation details of System Prompt v1, which is used to direct AI models (Claude/GPT) to generate malformed UserOperation objects for testing ERC-4337 smart wallet implementations.

---

## Design Objectives

### Primary Goals
1. **Structured Output:** Ensure AI generates valid JSON that can be directly parsed and used by the testing framework
2. **Vulnerability Coverage:** Target common attack vectors in smart contract systems
3. **Boundary Testing:** Focus on edge cases and invalid states
4. **Reproducibility:** Consistent output format for automated processing

### Constraints
- Must align with ERC-4337 UserOperation schema
- Output must be machine-parsable (strict JSON format)
- Should not require manual post-processing
- Must generate realistic attack scenarios

---

## Prompt Structure

### Component 1: Role Definition
```
"You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities."
```

**Rationale:**
- Establishes domain expertise context
- Primes the AI to think from a security perspective
- Leverages the model's knowledge of Ethereum and smart contract security

### Component 2: Schema Specification
Provides the complete ERC-4337 UserOperation structure with field types.

**Rationale:**
- Gives AI a clear template to follow
- Reduces hallucination of non-existent fields
- Ensures output compatibility with actual smart wallet implementations

**Example:**
```json
{
  "sender": "0x... (address, 20 bytes)",
  "nonce": "uint256",
  "callGasLimit": "uint256",
  ...
}
```

### Component 3: Attack Categories
Specifies six vulnerability types to target:

1. **Integer overflow/underflow** - Tests arithmetic safety
2. **Invalid addresses** - Tests address validation
3. **Malformed callData** - Tests function call handling
4. **Signature forgery** - Tests authentication mechanisms
5. **Nonce manipulation** - Tests replay protection
6. **Gas limit attacks** - Tests resource management

**Rationale:**
- Based on common ERC-4337 vulnerabilities documented in security audits
- Covers both input validation and state manipulation attacks
- Aligns with OWASP Smart Contract Top 10

### Component 4: Output Format Constraint
```
"Output ONLY valid JSON containing a single UserOperation object. 
Do not include explanations or markdown formatting."
```

**Rationale:**
- Critical for automated parsing
- Prevents AI from adding commentary or markdown code blocks
- Enforces strict adherence to expected format

---

## Attack Vector Mapping

| Attack Category | Target Component | Expected Behavior |
|----------------|------------------|-------------------|
| Integer Overflow | Gas fields | Should trigger SafeMath checks or revert |
| Invalid Address | sender, paymaster | Should reject zero address or non-contract |
| Malformed callData | callData | Should fail function selector validation |
| Signature Forgery | signature | Should fail ECDSA verification |
| Nonce Manipulation | nonce | Should reject replayed or future nonces |
| Gas Limit Attack | all gas fields | Should reject unrealistic values |

---

## Known Limitations (v1)

### Issues Identified
1. **Lack of Few-Shot Examples:** AI may generate overly simplistic or repetitive attacks
   - **Mitigation Plan:** Add Few-Shot learning in Prompt v2 (Milestone 2)

2. **No Chain-of-Thought:** AI doesn't explain its attack strategy
   - **Mitigation Plan:** Implement CoT reasoning in Prompt v3 (Milestone 3)

3. **Limited Diversity:** Single attack category per generation
   - **Mitigation Plan:** Add multi-vector combination attacks in M3

### AI Output Rejection Criteria
During testing, the following AI outputs were rejected:

**Example 1: Hallucinated Fields**
```json
{
  "nonce_fake": "12345",  // Non-existent field
  "gas_limit": "1000"     // Wrong field name
}
```
**Reason:** AI invented fields not in ERC-4337 spec. This happens when the schema is not reinforced strongly enough.

**Solution Implemented:**
- Added explicit field type annotations in prompt
- Emphasized "ONLY valid JSON" constraint

---

## Testing Methodology

### Validation Steps
1. Parse AI output as JSON
2. Verify all required fields present
3. Check field types match ERC-4337 spec
4. Validate attack categorization

### Success Metrics
- ✓ Valid JSON structure: 100%
- ✓ Schema compliance: 95%+
- ✓ Attack diversity: 6 categories covered
- ✓ Machine-parsable: No manual intervention needed

---

## Prompt Evolution Roadmap

```
v1 (M1) → Basic schema + attack categories
           ↓
v2 (M2) → + Few-Shot examples + batch generation
           ↓
v3 (M3) → + Chain-of-Thought + combined attacks
```

---

## References

- ERC-4337: Account Abstraction via Entry Point Contract  
  https://eips.ethereum.org/EIPS/eip-4337

- OpenZeppelin Security Audit Reports  
  https://blog.openzeppelin.com/tag/security-audits

- Trail of Bits: Building Secure Smart Contracts  
  https://github.com/crytic/building-secure-contracts

---

**Document Status:** Final for Milestone 1  
**Next Review:** Milestone 2 (after batch generation testing)
