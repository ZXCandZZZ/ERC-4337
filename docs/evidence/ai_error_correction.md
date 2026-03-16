# AI Error Correction Case Study

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

**Document Owner:** Role B (AI Attack Designer)  
**Purpose:** Document AI output errors and corrections for Evidence Pack

---

## Case 1: Negative Gas Value

### AI Output (Error)

**Prompt:** "Generate an integer overflow attack on gas fields"

**AI Response:**
```json
{
  "userop": {
    "sender": "0x1234567890123456789012345678901234567890",
    "nonce": "1",
    "callData": "0x",
    "callGasLimit": "-1",
    "verificationGasLimit": "100000",
    "preVerificationGas": "21000",
    "maxFeePerGas": "1000000000",
    "maxPriorityFeePerGas": "1000000000",
    "signature": "0x"
  }
}
```

### Error Identified

**Problem:** AI generated `-1` for `callGasLimit` field, but ERC-4337 uses `uint256` for all gas fields, which cannot be negative.

**Root Cause:** The AI model interpreted "overflow attack" as needing a negative value, not understanding Solidity's unsigned integer constraints.

### Correction Applied

```python
# Added validation in attack_generator.py
def validate_userop(userop: dict) -> bool:
    for key in ['callGasLimit', 'verificationGasLimit', 'preVerificationGas', 
                'maxFeePerGas', 'maxPriorityFeePerGas']:
        value = userop.get(key, 0)
        if isinstance(value, str):
            if value.startswith('-'):
                raise ValueError(f"{key} cannot be negative (uint256)")
            if not value.isdigit():
                raise ValueError(f"{key} must be a valid integer string")
    return True
```

**Corrected Output:**
```json
{
  "userop": {
    "sender": "0x1234567890123456789012345678901234567890",
    "nonce": "1",
    "callData": "0x",
    "callGasLimit": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
    "verificationGasLimit": "1",
    "preVerificationGas": "0",
    "maxFeePerGas": "1000000000",
    "maxPriorityFeePerGas": "1000000000",
    "signature": "0x1234"
  }
}
```

**Why This Works:** Using `uint256_max` (2^256 - 1) achieves the same overflow test intent without invalid negative values.

---

## Case 2: Invalid Signature Length

### AI Output (Error)

**Prompt:** "Generate a signature forgery attack"

**AI Response:**
```json
{
  "userop": {
    "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    "nonce": "1",
    "callData": "0x",
    "callGasLimit": "100000",
    "verificationGasLimit": "100000",
    "signature": "invalid_signature_data"
  }
}
```

### Error Identified

**Problem:** 
1. `signature` field contains non-hex string instead of hex bytes
2. Missing `0x` prefix
3. Not a valid hex string

**Root Cause:** AI generated a descriptive string instead of proper hex-encoded bytes.

### Correction Applied

**Added Prompt Enhancement:**
```
IMPORTANT: All hex values must start with "0x" and contain only 
valid hexadecimal characters (0-9, a-f, A-F). Signature must be 
hex-encoded bytes, typically 65 bytes for ECDSA.
```

**Corrected Output:**
```json
{
  "userop": {
    "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    "nonce": "1",
    "callData": "0x",
    "callGasLimit": "100000",
    "verificationGasLimit": "100000",
    "preVerificationGas": "21000",
    "maxFeePerGas": "1000000000",
    "maxPriorityFeePerGas": "1000000000",
    "signature": "0xdeadbeef"
  }
}
```

**Why This Works:** A 4-byte signature (instead of required 65 bytes) is a valid forgery test case that checks if implementation validates signature length.

---

## Case 3: Missing Required Fields

### AI Output (Error)

**Prompt:** "Generate a malformed calldata attack"

**AI Response:**
```json
{
  "sender": "0xfedcbafedcbafedcbafedcbafedcbafedcba0987",
  "nonce": "100",
  "callData": "0xdeadbeefcafebabe"
}
```

### Error Identified

**Problem:** Missing required fields:
- `callGasLimit`
- `verificationGasLimit`
- `preVerificationGas`
- `maxFeePerGas`
- `maxPriorityFeePerGas`
- `signature`

**Root Cause:** AI focused on the attack vector but forgot to include all required UserOperation fields.

### Correction Applied

**Added Schema Validation:**
```python
REQUIRED_FIELDS = [
    'sender', 'nonce', 'callData', 
    'callGasLimit', 'verificationGasLimit', 'preVerificationGas',
    'maxFeePerGas', 'maxPriorityFeePerGas', 'signature'
]

def validate_schema(userop: dict) -> bool:
    missing = [f for f in REQUIRED_FIELDS if f not in userop]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    return True
```

**Corrected Output:**
```json
{
  "sender": "0xfedcbafedcbafedcbafedcbafedcbafedcba0987",
  "nonce": "100",
  "initCode": "0x",
  "callData": "0xdeadbeefcafebabe",
  "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000f42400000000000000000000000000000000000000000000000000000000000186a0",
  "preVerificationGas": "21000",
  "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
  "paymasterAndData": "0x",
  "signature": "0xabcd"
}
```

---

## Summary Statistics

| Error Type | Count | Auto-Fixed | Required Manual Review |
|------------|-------|------------|------------------------|
| Negative values | 3 | 3 | 0 |
| Invalid hex format | 5 | 5 | 0 |
| Missing fields | 8 | 8 | 0 |
| Wrong field type | 2 | 2 | 0 |

---

## Lessons Learned

1. **Always validate AI output** before using in tests
2. **Add explicit constraints** to prompts (hex format, uint256 only, required fields)
3. **Implement schema validation** to catch structural errors early
4. **Use Few-Shot examples** with correct format to guide AI

---

**Document Owner:** Role B (AI Attack Designer)  
**Last Updated:** March 2026