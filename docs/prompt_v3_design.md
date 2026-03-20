# System Prompt v3 Design - Chain-of-Thought Reasoning

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

**Owner:** @RoleB (AI Attack Designer)  
**Milestone:** M3  
**Last Updated:** March 2026

---

## Overview

This document describes the design and implementation of System Prompt v3, which introduces **Chain-of-Thought (CoT) Reasoning** to improve attack quality, explainability, and diversity.

---

## Prompt Evolution

| Version | Features | Temperature | Milestone |
|---------|----------|-------------|-----------|
| v1 | Basic schema + attack categories | 0.7 | M1 |
| v2 | Few-Shot Learning (3 examples) | 0.9 | M2 |
| v3 | Chain-of-Thought reasoning | 0.9 | M3 |

---

## Why Chain-of-Thought?

### Problem with v2

- AI generates attacks without explaining reasoning
- Hard to audit attack logic
- Difficult to understand why attack should work
- Limited creativity in complex scenarios

### Solution with v3

- AI explains attack strategy step-by-step
- Attack logic becomes auditable
- Better creative exploration
- Higher quality attack vectors

---

## Prompt v3 Structure

### Component 1: Role Definition

```
You are an expert Ethereum security researcher specializing in 
ERC-4337 Account Abstraction vulnerabilities.
```

### Component 2: Chain-of-Thought Template

```
Generate attack UserOperations using the following reasoning process:

STEP 1: IDENTIFY TARGET
- Which vulnerability category are you targeting?
- What is the specific weakness to exploit?

STEP 2: DESIGN ATTACK VECTOR
- How will you construct the malformed field?
- What value will trigger the vulnerability?

STEP 3: CONSTRUCT USEROPERATION
- Build the complete UserOperation object
- Ensure all required fields are present

STEP 4: EXPLAIN EXPECTED BEHAVIOR
- Why should this bypass validation?
- What is the expected outcome?
```

### Component 3: Output Format

```json
{
  "reasoning": {
    "step1_target": "string - vulnerability category and weakness",
    "step2_design": "string - attack vector design",
    "step3_construction": "string - how UserOperation was built",
    "step4_expected": "string - expected behavior"
  },
  "attack_type": "one of: integer_overflow_gas, invalid_address, malformed_calldata, signature_forgery, nonce_manipulation, gas_limit_attack, paymaster_exploit",
  "should_be_blocked": true,
  "userop": {
    "sender": "0x...",
    "nonce": "uint256",
    "initCode": "0x...",
    "callData": "0x...",
    "accountGasLimits": "0x...",
    "preVerificationGas": "uint256",
    "gasFees": "0x...",
    "paymasterAndData": "0x...",
    "signature": "0x..."
  }
}
```

---

## Complete Prompt v3

```python
SYSTEM_PROMPT_V3 = """
You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

Your task is to generate diverse attack UserOperations using Chain-of-Thought reasoning. You MUST explain your attack strategy step-by-step.

A valid ERC-4337 UserOperation (Packed format) has the following structure:
{
  "sender": "0x... (address, 20 bytes)",
  "nonce": "uint256",
  "initCode": "0x... (bytes, optional - for account creation)",
  "callData": "0x... (bytes - the execution payload)",
  "accountGasLimits": "0x... (32 bytes: verificationGas << 128 | callGas)",
  "preVerificationGas": "uint256",
  "gasFees": "0x... (32 bytes: maxPriorityFee << 128 | maxFee)",
  "paymasterAndData": "0x... (bytes, optional - paymaster address + data)",
  "signature": "0x... (bytes, 65 bytes for ECDSA)"
}

CHAIN-OF-THOUGHT REASONING PROCESS:

STEP 1 - IDENTIFY TARGET:
- Select a vulnerability category from: signature_forgery, gas_limit_attack, nonce_manipulation, integer_overflow_gas, invalid_address, malformed_calldata, paymaster_exploit
- Identify the specific weakness to exploit

STEP 2 - DESIGN ATTACK VECTOR:
- Determine which field(s) to manipulate
- Design the specific malicious value or pattern
- Consider edge cases and boundary values

STEP 3 - CONSTRUCT USEROPERATION:
- Build all required fields with valid format
- Inject the malicious payload
- Ensure the attack is self-contained

STEP 4 - EXPLAIN EXPECTED BEHAVIOR:
- Describe why this should bypass validation
- Identify which invariant is being violated
- Predict the outcome (blocked or vulnerability exploited)

ATTACK CATEGORIES TO TARGET:

1. **signature_forgery** - Empty, wrong length, invalid values, replay signatures
2. **gas_limit_attack** - Extremely high/low values, zero gas, inconsistent limits
3. **nonce_manipulation** - Replay attacks, future nonces, duplicate nonces
4. **integer_overflow_gas** - Gas fields at uint256 max, near-overflow values
5. **invalid_address** - Zero address, non-existent contracts, malformed addresses
6. **malformed_calldata** - Wrong selectors, corrupted parameters, oversized data
7. **paymaster_exploit** - Invalid paymaster, forged paymaster signature, insufficient deposit

IMPORTANT OUTPUT REQUIREMENTS:
- Output ONLY valid JSON (no markdown, no explanations outside JSON)
- Include complete reasoning in the "reasoning" object
- Set "should_be_blocked": true for attacks, false for legitimate operations
- Ensure all hex values start with "0x"
- Generate DIVERSE attacks - each should be unique

OUTPUT FORMAT:
{
  "reasoning": {
    "step1_target": "...",
    "step2_design": "...",
    "step3_construction": "...",
    "step4_expected": "..."
  },
  "attack_type": "...",
  "should_be_blocked": true,
  "userop": { ... }
}
"""
```

---

## Few-Shot Examples for v3

### Example 1: Signature Forgery with CoT

```json
{
  "reasoning": {
    "step1_target": "Targeting signature_forgery. The weakness is that some implementations don't validate signature length before ECDSA recovery.",
    "step2_design": "Use a 4-byte signature instead of the required 65 bytes. This will cause issues in signature parsing and potentially bypass length checks.",
    "step3_construction": "Set all other fields to valid values, use signature '0xdeadbeef' (4 bytes). The sender is a valid address, nonce is sequential.",
    "step4_expected": "This should be BLOCKED because ERC-4337 requires 65-byte signatures for ECDSA. The EntryPoint should reject this during validation."
  },
  "attack_type": "signature_forgery",
  "should_be_blocked": true,
  "userop": {
    "sender": "0x1234567890123456789012345678901234567890",
    "nonce": "1",
    "initCode": "0x",
    "callData": "0x",
    "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000001518000000000000000000000000000000000000000000000000000000000000186a0",
    "preVerificationGas": "21000",
    "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
    "paymasterAndData": "0x",
    "signature": "0xdeadbeef"
  }
}
```

### Example 2: Gas Overflow Attack with CoT

```json
{
  "reasoning": {
    "step1_target": "Targeting integer_overflow_gas. The weakness is potential integer overflow in gas calculations or insufficient bounds checking.",
    "step2_design": "Set callGasLimit to uint256_max (2^256-1) while keeping verificationGasLimit minimal. This tests for overflow in gas arithmetic.",
    "step3_construction": "callGasLimit packed as high 128 bits of accountGasLimits, verificationGasLimit as low 128 bits.",
    "step4_expected": "This should be BLOCKED by EntryPoint with 'AA94 gas values overflow' because gas values must be <= uint120_max."
  },
  "attack_type": "integer_overflow_gas",
  "should_be_blocked": true,
  "userop": {
    "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    "nonce": "1",
    "initCode": "0x",
    "callData": "0x",
    "accountGasLimits": "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000001",
    "preVerificationGas": "0",
    "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
    "paymasterAndData": "0x",
    "signature": "0x1234"
  }
}
```

### Example 3: Legitimate Transfer (should_be_blocked=false)

```json
{
  "reasoning": {
    "step1_target": "Generating a legitimate operation to test false positive rate. This is a normal ETH transfer with valid parameters.",
    "step2_design": "Use a valid 65-byte signature from the account owner, correct nonce, reasonable gas limits.",
    "step3_construction": "All fields follow ERC-4337 specification correctly. This represents a user sending ETH to another address.",
    "step4_expected": "This should be ALLOWED because all fields are valid and the signature correctly authenticates the owner."
  },
  "attack_type": "legitimate",
  "should_be_blocked": false,
  "userop": {
    "sender": "0xValidAccountAddress...",
    "nonce": "1",
    "initCode": "0x",
    "callData": "0x<valid_execute_callData>",
    "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000f42400000000000000000000000000000000000000000000000000000000000186a0",
    "preVerificationGas": "50000",
    "gasFees": "0x000000000000000000000000000000000000000000000000000000001dcd65000000000000000000000000000000000000000000000000000000002d79883d200",
    "paymasterAndData": "0x",
    "signature": "0x<65_byte_valid_signature>"
  }
}
```

---

## Implementation

### Python Code

```python
# In ai_generator.py

RANDOM_SEED = 42  # Fixed seed for reproducibility

class AttackGeneratorV3:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.temperature = 0.9
        self.seed = RANDOM_SEED
        
    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT_V3
    
    def generate_attack(self, attack_type: str = None) -> dict:
        """
        Generate a single attack with Chain-of-Thought reasoning.
        """
        import random
        random.seed(self.seed)
        
        prompt = self.get_system_prompt()
        if attack_type:
            prompt += f"\n\nFocus on generating a {attack_type} attack."
        
        # Call DeepSeek API
        response = self._call_api(prompt)
        
        # Parse and validate
        return self._parse_response(response)
```

---

## Expected Improvements

| Metric | v2 | v3 Target |
|--------|-----|-----------|
| Attack Quality | Medium | High (with reasoning) |
| Explainability | Low | High (step-by-step) |
| Diversity | Medium | High (CoT enables creativity) |
| Auditability | Low | High (reasoning documented) |
| Legitimate Sample Generation | None | Supported |

---

## AI Error Documentation

### Example of AI Error (for Evidence Pack)

**AI Output:**
```json
{
  "userop": {
    "callGasLimit": "-1"
  }
}
```

**Error:** AI generated a negative value for uint256 field.

**Correction:** Modified prompt to explicitly state "all numeric values must be positive integers or hex strings starting with 0x".

**Fixed Output:**
```json
{
  "userop": {
    "callGasLimit": "115792089237316195423570985008687907853269984665640564039457584007913129639935"
  }
}
```

---

## Testing v3

```bash
# Generate single attack with v3
python ai-attack-generator/attack_generator.py --mode single --prompt v3

# Generate batch with v3
python ai-attack-generator/attack_generator.py --mode batch --count 100 --prompt v3 --seed 42

# Validate v3 output format
python ai-attack-generator/attack_generator.py --mode validate --input attacks_v3.json
```

---

**Document Owner:** Role B (AI Attack Designer)  
**Implementation:** `ai-attack-generator/attack_generator.py`  
**Last Updated:** March 2026