# Threat → Test Coverage Matrix

**CS6290 Group Project | ERC-4337 Account Abstraction Security Testing**

**Owner:** @RoleA (PM / Threat Alignment Lead)  
**Status:** 🔄 In Progress  
**Last Updated:** March 2026

---

## Overview

This document maps the 4 threat categories from Threat Model V1/V2 to specific test cases and results, ensuring complete coverage of the ERC-4337 attack surface.

---

## Threat Categories Summary

| ID | Threat Category | Description | Risk Level |
|----|-----------------|-------------|------------|
| T1 | Signature Bypass | Forged, empty, or malformed signatures | 🔴 High |
| T2 | Gas Manipulation | Integer overflow/underflow in gas fields | 🔴 High |
| T3 | Replay Attacks | Nonce manipulation, transaction replay | 🟡 Medium |
| T4 | Paymaster Exploits | paymasterAndData forgery, gas sponsorship abuse | 🟡 Medium |

---

## Coverage Matrix

### T1: Signature Bypass

| Test Case ID | Test Description | Attack Vector | Expected Result | Actual Result | Status |
|--------------|------------------|---------------|-----------------|---------------|--------|
| T1-001 | Empty signature | `signature: "0x"` | Block | ✅ Blocked | ✅ Pass |
| T1-002 | Short signature (4 bytes) | `signature: "0xdeadbeef"` | Block | ✅ Blocked | ✅ Pass |
| T1-003 | All-zero signature | `signature: "0x00...00"` (65 bytes) | Block | ✅ Blocked | ✅ Pass |
| T1-004 | Wrong signer signature | Valid sig, wrong key | Block | ✅ Blocked | ✅ Pass |
| T1-005 | Replay signature | Reuse valid sig with new nonce | Block | ✅ Blocked | ✅ Pass |
| T1-006 | Truncated signature | 64 bytes instead of 65 | Block | ✅ Blocked | ✅ Pass |
| T1-007 | Extended signature | 66 bytes instead of 65 | Block | ✅ Blocked | ✅ Pass |

**Coverage:** 7/7 tests (100%)

---

### T2: Gas Manipulation

| Test Case ID | Test Description | Attack Vector | Expected Result | Actual Result | Status |
|--------------|------------------|---------------|-----------------|---------------|--------|
| T2-001 | callGasLimit overflow | `callGasLimit: uint256_max` | Block/Handle | ✅ Handled | ✅ Pass |
| T2-002 | verificationGasLimit = 0 | `verificationGasLimit: 0` | Block | ✅ Blocked | ✅ Pass |
| T2-003 | preVerificationGas = 0 | `preVerificationGas: 0` | Block | ✅ Blocked | ✅ Pass |
| T2-004 | maxFeePerGas = 0 | `maxFeePerGas: 0` | Block | ✅ Blocked | ✅ Pass |
| T2-005 | All gas fields max | All at uint256_max | Block/Handle | ✅ Handled | ✅ Pass |
| T2-006 | Negative-like gas value | Gas = 2^255 (appears negative) | Block | ✅ Blocked | ✅ Pass |
| T2-007 | Inconsistent gas limits | callGas >> verificationGas | Block | ✅ Blocked | ✅ Pass |

**Coverage:** 7/7 tests (100%)

---

### T3: Replay Attacks

| Test Case ID | Test Description | Attack Vector | Expected Result | Actual Result | Status |
|--------------|------------------|---------------|-----------------|---------------|--------|
| T3-001 | Nonce = 0 reuse | Replay with same nonce=0 | Block | ✅ Blocked | ✅ Pass |
| T3-002 | Future nonce | `nonce: 999999` | Block | ✅ Blocked | ✅ Pass |
| T3-003 | Negative-like nonce | `nonce: 2^255` | Block | ✅ Blocked | ✅ Pass |
| T3-004 | Duplicate UserOp in bundle | Same op twice | Block | ✅ Blocked | ✅ Pass |
| T3-005 | Cross-chain replay | Same op on different chain | Block | ✅ Blocked | ✅ Pass |
| T3-006 | Same sender, different nonce | Valid signature, wrong nonce | Block | ✅ Blocked | ✅ Pass |

**Coverage:** 6/6 tests (100%)

---

### T4: Paymaster Exploits

| Test Case ID | Test Description | Attack Vector | Expected Result | Actual Result | Status |
|--------------|------------------|---------------|-----------------|---------------|--------|
| T4-001 | Empty paymasterAndData | `paymasterAndData: "0x"` | Handle | ✅ Handled | ✅ Pass |
| T4-002 | Invalid paymaster address | Non-existent paymaster | Block | ✅ Blocked | ✅ Pass |
| T4-003 | Zero address paymaster | `paymaster: 0x0` | Block | ✅ Blocked | ✅ Pass |
| T4-004 | Forged paymaster signature | Invalid signature in data | Block | ✅ Blocked | ✅ Pass |
| T4-005 | Paymaster gas manipulation | Invalid gas limits in data | Block | ✅ Blocked | ✅ Pass |
| T4-006 | Malformed paymaster data | Wrong length/format | Block | ✅ Blocked | ✅ Pass |
| T4-007 | Paymaster with insufficient deposit | Empty balance | Block | ✅ Blocked | ✅ Pass |

**Coverage:** 7/7 tests (100%)

---

## Legitimate Sample Coverage (M3 New)

| Test Case ID | Test Description | Expected Result | Actual Result | Status |
|--------------|------------------|-----------------|---------------|--------|
| L-001 | Normal ETH transfer | Allow | ✅ Allowed | ✅ Pass |
| L-002 | Valid token transfer | Allow | ✅ Allowed | ✅ Pass |
| L-003 | Valid contract call | Allow | ✅ Allowed | ✅ Pass |
| L-004 | Valid paymaster-sponsored tx | Allow | ✅ Allowed | ✅ Pass |
| L-005 | Normal signature (65 bytes, valid) | Allow | ✅ Allowed | ✅ Pass |

**False Positive Rate:** 0/5 (0%)

---

## Gap List

### P0 (Critical - Must Fix)

| Gap ID | Description | Threat | Assigned To | Status |
|--------|-------------|--------|-------------|--------|
| G-P0-001 | Multi-vector combined attacks not tested | All | B | ❌ Pending |
| G-P0-002 | 1000+ operation stability test | All | C | ❌ Pending |

### P1 (Important - Should Fix)

| Gap ID | Description | Threat | Assigned To | Status |
|--------|-------------|--------|-------------|--------|
| G-P1-001 | More paymaster attack variants | T4 | B | ❌ Pending |
| G-P1-002 | Edge case signatures (v=27 vs v=28) | T1 | B | ❌ Pending |
| G-P1-003 | P95 latency measurement | All | C | ❌ Pending |

### P2 (Nice to Have)

| Gap ID | Description | Threat | Assigned To | Status |
|--------|-------------|--------|-------------|--------|
| G-P2-001 | Gas price manipulation | T2 | B | ❌ Pending |
| G-P2-002 | Cross-contract reentrancy | T1 | A | ❌ Pending |
| G-P2-003 | Formal verification | All | D | ❌ Pending |

---

## Summary Statistics

### Coverage by Threat Category

| Threat | Test Cases | Passed | Failed | Coverage |
|--------|------------|--------|--------|----------|
| T1: Signature | 7 | 7 | 0 | 100% |
| T2: Gas | 7 | 7 | 0 | 100% |
| T3: Replay | 6 | 6 | 0 | 100% |
| T4: Paymaster | 7 | 7 | 0 | 100% |
| Legitimate | 5 | 5 | 0 | 100% |
| **Total** | **32** | **32** | **0** | **100%** |

### Metrics Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | 32 |
| True Positive (TP) | 27 |
| True Negative (TN) | 5 |
| False Positive (FP) | 0 |
| False Negative (FN) | 0 |
| Precision | 100% |
| Recall | 100% |
| F1 Score | 100% |

---

## Test Execution Log

### M2 Baseline (Before Fixes)

| Run ID | Date | Tests | Passed | Failed | Notes |
|--------|------|-------|--------|--------|-------|
| M2-001 | 2026-02-XX | 50 | 45 | 5 | Signature validation gaps |
| M2-002 | 2026-02-XX | 50 | 47 | 3 | Gas overflow handling |

### M3 Results (After Fixes)

| Run ID | Date | Tests | Passed | Failed | Notes |
|--------|------|-------|--------|--------|-------|
| M3-100 | TBD | 100 | - | - | Smoke test |
| M3-500 | TBD | 500 | - | - | Medium test |
| M3-1000 | TBD | 1000 | - | - | Large test |

---

## Next Steps

1. **Role B**: Implement multi-vector attack tests (G-P0-001)
2. **Role C**: Run three-tier tests and record results
3. **Role C**: Measure P95 latency (G-P1-003)
4. **Role A**: Update matrix with M3 results
5. **Role D**: Integrate into Final Report

---

**Document Owner:** Role A (PM / Threat Alignment Lead)  
**Review Required:** All team members  
**Last Updated:** March 2026