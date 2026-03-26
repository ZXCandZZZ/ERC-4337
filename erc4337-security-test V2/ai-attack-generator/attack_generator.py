"""
AI-Driven Attack Generator for ERC-4337 Smart Wallet Fuzzing

Generates malformed UserOperation objects using DeepSeek API to test
vulnerabilities in ERC-4337 smart wallet implementations.

Usage:
    # Single attack (quick test)
    python attack_generator.py --mode single
    python attack_generator.py --mode single --attack-type nonce_manipulation

    # Batch generation
    python attack_generator.py --mode batch --count 50 --output attacks.json

    # Validate an existing dataset
    python attack_generator.py --mode validate --input attacks.json

Environment:
    DEEPSEEK_API_KEY  DeepSeek API key (or pass --api-key)
"""

import argparse
import asyncio
import json
import os
import random
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

# M3: Fixed random seed for reproducibility
RANDOM_SEED = 42

ATTACK_TYPES: List[str] = [
    "integer_overflow_gas",
    "invalid_address",
    "malformed_calldata",
    "signature_forgery",
    "nonce_manipulation",
    "gas_limit_attack",
    "paymaster_exploit",           # M3: Paymaster abuse
    "legitimate",                  # M3: For baseline samples
    # --- M4: Extended attack categories ---
    "reentrancy_attack",           # M4: Cross-function reentrancy during validateUserOp / execute
    "bundler_griefing",            # M4: Gas-wasting ops that fail on-chain after simulation passes
    "initcode_exploit",            # M4: Malicious factory via initCode (CREATE2 salt collision / address squatting)
    "cross_chain_replay",          # M4: Signature reuse across different chain IDs
    "aggregator_bypass",           # M4: Exploit ERC-4337 signature aggregator callback (IAggregator)
    "access_list_poisoning",       # M4: Storage slot inconsistency between simulation and execution
    "calldata_bomb",               # M4: Oversized / gas-bomb callData to DoS mempool / bundler
    "time_range_abuse",            # M5: Invalid validAfter/validUntil semantics encoded through signature context assumptions
    "eip7702_auth_bypass",         # M5: EIP-7702 authorization/initCode confusion
    "paymaster_postop_griefing",   # M5: postOp griefing or oversized paymaster context patterns
    "factory_stake_bypass",        # M5: unstaked or malformed factory/initCode patterns
    "transient_storage_collision", # M5: transient storage or bundle cross-op leakage assumptions
    "combo_sig_nonce",             # M4: Combination: signature forgery + nonce replay
    "combo_gas_paymaster",         # M4: Combination: gas exhaustion + paymaster exploit
    "combo_initcode_invalid_addr", # M4: Combination: malicious initCode + zero/invalid sender address
    "combo_7702_time_range",       # M5: 7702 authorization confusion + invalid timing assumptions
    "combo_factory_paymaster",     # M5: malicious factory + paymaster griefing
]

# M4: Combination (multi-vector) attack type identifiers for clear categorization
COMBO_ATTACK_TYPES: List[str] = [
    "combo_sig_nonce",
    "combo_gas_paymaster",
    "combo_initcode_invalid_addr",
    "combo_7702_time_range",
    "combo_factory_paymaster",
]

NUMERIC_STRING_FIELDS = {
    "nonce",
    "preVerificationGas",
    "callGasLimit",
    "verificationGasLimit",
    "maxFeePerGas",
    "maxPriorityFeePerGas",
}


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_V1 = """You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

Your task is to generate malformed or malicious UserOperation objects that could potentially exploit vulnerabilities in smart wallet implementations.

A valid ERC-4337 UserOperation has the following structure:
{
  "sender": "0x... (address, 20 bytes)",
  "nonce": "uint256",
  "initCode": "0x... (bytes, optional)",
  "callData": "0x... (bytes)",
  "callGasLimit": "uint256",
  "verificationGasLimit": "uint256",
  "preVerificationGas": "uint256",
  "maxFeePerGas": "uint256",
  "maxPriorityFeePerGas": "uint256",
  "paymasterAndData": "0x... (bytes, optional)",
  "signature": "0x... (bytes)"
}

Generate UserOperations that test the following vulnerability categories:
1. **Integer overflow/underflow** in gas fields
2. **Invalid addresses** (zero address, non-existent contracts, EOAs)
3. **Malformed callData** (wrong function selectors, corrupted parameters)
4. **Signature forgery attempts** (empty, wrong length, invalid values)
5. **Nonce manipulation** (replay attacks, future nonces)
6. **Gas limit attacks** (extremely high/low values, inconsistent limits)

Output ONLY valid JSON containing a single UserOperation object. Do not include explanations or markdown formatting."""

SYSTEM_PROMPT_V2 = """You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

Your task is to generate diverse malformed or malicious UserOperation objects that test real-world vulnerabilities.

A valid ERC-4337 UserOperation has the following structure:
{
  "sender": "0x... (address, 20 bytes)",
  "nonce": "uint256",
  "initCode": "0x... (bytes, optional)",
  "callData": "0x... (bytes)",
  "callGasLimit": "uint256",
  "verificationGasLimit": "uint256",
  "preVerificationGas": "uint256",
  "maxFeePerGas": "uint256",
  "maxPriorityFeePerGas": "uint256",
  "paymasterAndData": "0x... (bytes, optional)",
  "signature": "0x... (bytes)"
}

FEW-SHOT EXAMPLES FROM REAL VULNERABILITIES:

Example 1 - Nonce Replay Attack (Gnosis Safe):
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
ATTACK: Reusing nonce=0 after deployment allows replay if the implementation doesn't track executed nonces.

Example 2 - Gas Limit Manipulation (Argent wallet):
{
  "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
  "nonce": "1",
  "callData": "0xa9059cbb0000000000000000000000000000000000000000000000000000000000000000",
  "callGasLimit": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
  "verificationGasLimit": "1",
  "preVerificationGas": "0",
  "maxFeePerGas": "1000000000",
  "maxPriorityFeePerGas": "1000000000",
  "signature": "0x1234"
}
ATTACK: callGasLimit = uint256 max while verificationGasLimit is minimal - tests gas estimation and integer overflow.

Example 3 - Signature Forgery (OpenZeppelin):
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
ATTACK: Zero address sender with 4-byte signature (should be 65 bytes) tests signature validation edge cases.

Generate UserOperations that target these categories:
1. **Integer overflow/underflow** - Gas fields at extreme values (uint256 max, near-zero)
2. **Invalid addresses** - Zero address, non-existent contracts, creation addresses
3. **Malformed callData** - Wrong selectors, corrupted params, empty or oversized data
4. **Signature forgery** - Empty, wrong length, invalid values, replay signatures
5. **Nonce manipulation** - Replay (duplicate), future nonces, negative-looking values
6. **Gas limit attacks** - Extremely high/low, inconsistent limits, zero gas

Generate DIVERSE attacks. Each UserOperation must be unique. Output ONLY valid JSON. No explanations, no markdown."""

# M3: Prompt v3 with Chain-of-Thought reasoning
SYSTEM_PROMPT_V3 = """You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

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
1. signature_forgery - Empty, wrong length, invalid values, replay signatures
2. gas_limit_attack - Extremely high/low values, zero gas, inconsistent limits
3. nonce_manipulation - Replay attacks, future nonces, duplicate nonces
4. integer_overflow_gas - Gas fields at uint256 max, near-overflow values
5. invalid_address - Zero address, non-existent contracts, malformed addresses
6. malformed_calldata - Wrong selectors, corrupted parameters, oversized data
7. paymaster_exploit - Invalid paymaster, forged paymaster signature, insufficient deposit
8. legitimate - Valid operations for false positive testing (should_be_blocked: false)

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
}"""


# M4: Extended System Prompt v4 - covers new attack categories and combination attacks
SYSTEM_PROMPT_V4 = """You are an elite Ethereum security researcher with deep expertise in ERC-4337 Account Abstraction (AA) vulnerabilities.

Your mission: generate highly realistic, diverse malformed UserOperation objects that expose real vulnerabilities in ERC-4337 smart wallet implementations. Draw from published CVEs, audit reports (ChainSecurity, ConsenSys Diligence, OpenZeppelin) and the official ERC-4337 specification.

A valid ERC-4337 PackedUserOperation has the following structure:
{
  "sender": "0x... (address, 20 bytes)",
  "nonce": "uint256",
  "initCode": "0x... (bytes, optional - factory address + calldata)",
  "callData": "0x... (bytes - execution payload)",
  "accountGasLimits": "0x... (bytes32: upper 128 = verificationGasLimit, lower 128 = callGasLimit)",
  "preVerificationGas": "uint256",
  "gasFees": "0x... (bytes32: upper 128 = maxPriorityFeePerGas, lower 128 = maxFeePerGas)",
  "paymasterAndData": "0x... (bytes, optional: first 20 bytes = paymaster address)",
  "signature": "0x... (bytes, 65 bytes for ECDSA)"
}

ATTACK TAXONOMY (generate exactly one per call):

**TIER 1 - Single-Vector Attacks:**
1. signature_forgery - Invalid ECDSA signatures (empty, wrong length, bad v value, zero sig)
2. gas_limit_attack - Extreme gas values (uint256 max, zero, sub-gwei inconsistencies)
3. nonce_manipulation - Replay nonce=0 reuse, future nonces, 2^128 key-space overflow
4. integer_overflow_gas - Gas field arithmetic overflow near uint256 max boundary
5. invalid_address - Zero sender, non-contract sender, create2 addr before deployment
6. malformed_calldata - Wrong function selectors, ABI-corrupted params, reentrancy triggers
7. paymaster_exploit - Forged paymaster sig, zero-addr paymaster, underfunded paymaster
8. reentrancy_attack - callData that re-enters EntryPoint.handleOps during execute phase
9. bundler_griefing - Op passes simulation but intentionally reverts on-chain (simulation-execution divergence)
10. initcode_exploit - initCode with malicious factory, CREATE2 address squatting, initCode on existing account
11. cross_chain_replay - Valid signature from chainId=1 reused on chainId=31337 (missing chainId binding)
12. aggregator_bypass - Manipulate paymasterAndData to point to untrusted IAggregator contract
13. access_list_poisoning - Storage read/write pattern that differs between simulation (eth_call) and execution (on-chain)
14. calldata_bomb - Massive callData (>10KB) to exhaust mempool gas / bundler bandwidth
15. time_range_abuse - Encode impossible or inconsistent validity windows, expired timing, or abuse of validationData assumptions
16. eip7702_auth_bypass - Abuse 0x7702-style initCode/authorization confusion, repeated initialization, or missing delegate binding
17. paymaster_postop_griefing - Craft paymasterAndData/context patterns that pressure postOp gas or refund assumptions
18. factory_stake_bypass - Use malformed initCode or unstaked-factory-like patterns to violate sender creation expectations
19. transient_storage_collision - Assume transient storage or bundle-shared scratch state leaks across UserOperations

**TIER 2 - Combination Attacks (multi-vector, harder to detect):**
20. combo_sig_nonce - Simultaneously: invalid signature AND replay nonce (forces bundler to evaluate both paths)
21. combo_gas_paymaster - Simultaneously: uint256-max gas limits AND underfunded/fake paymaster address
22. combo_initcode_invalid_addr - Simultaneously: malicious initCode bytes AND zero/mismatched sender address
23. combo_7702_time_range - Simultaneously: 7702 authorization confusion AND invalid/expired timing assumptions
24. combo_factory_paymaster - Simultaneously: malicious factory/initCode pattern AND paymaster griefing payload

CHAIN-OF-THOUGHT PROCESS:
STEP 1: Select an attack type from the taxonomy above
STEP 2: Identify which invariant/check is being violated
STEP 3: Craft the minimal field values to trigger the vulnerability while keeping JSON valid
STEP 4: Explain the expected bundler/EntryPoint response

IMPORTANT RULES:
- Output ONLY valid JSON, no markdown, no prose outside the JSON structure
- For combination attacks, explicitly label each vector in step2_design
- "should_be_blocked": true for all attacks; false ONLY for "legitimate" type
- All hex strings must start with "0x"
- Vary field values between calls - no two UserOperations should be identical
- accountGasLimits and gasFees MUST be bytes32 hex strings (exactly 64 hex chars after 0x)
- nonce and preVerificationGas MUST be decimal strings, never hex strings
- Do not wrap the final UserOperation inside another nested userop object unless you also include the actual userop field exactly once

OUTPUT FORMAT:
{
  "reasoning": {
    "step1_target": "attack type and specific invariant",
    "step2_design": "field manipulation strategy",
    "step3_construction": "how each field is crafted",
    "step4_expected": "expected EntryPoint/bundler behavior"
  },
  "attack_type": "one of the taxonomy types above",
  "should_be_blocked": true,
  "vectors": ["primary_vector", "secondary_vector (if combo)"],
  "userop": { ... }
}"""


# M3: Legitimate baseline samples for False Positive measurement
LEGITIMATE_SAMPLES = [
    {
        "description": "Normal ETH transfer",
        "should_be_blocked": False,
        "userop": {
            "sender": "0x1234567890123456789012345678901234567890",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000f42400000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "50000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000001dcd650000000000000000000000000000000000000000000000000000000002d79883d200",
            "paymasterAndData": "0x",
            "signature": "0x1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345",
        },
    },
    {
        "description": "Valid token transfer",
        "should_be_blocked": False,
        "userop": {
            "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "nonce": "2",
            "initCode": "0x",
            "callData": "0xa9059cbb000000000000000000000000123456789012345678901234567890123456789000000000000000000000000000000000000000000000000000000000000003e8",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000001518000000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "60000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000002540be4000000000000000000000000000000000000000000000000000000002540be400",
            "paymasterAndData": "0x",
            "signature": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefab",
        },
    },
    {
        "description": "Valid contract call",
        "should_be_blocked": False,
        "userop": {
            "sender": "0xfedcbafedcbafedcbafedcbafedcbafedcba0987",
            "nonce": "3",
            "initCode": "0x",
            "callData": "0x70a08231000000000000000000000000fedcbafedcbafedcbafedcbafedcbafedcba0987",
            "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000f424000000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "45000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0x1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111",
        },
    },
    {
        "description": "Valid paymaster-sponsored transaction",
        "should_be_blocked": False,
        "userop": {
            "sender": "0x0987654321098765432109876543210987654321",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000001518000000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "30000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000001dcd650000000000000000000000000000000000000000000000000000000001dcd6500",
            "paymasterAndData": "0xaabbccddaabbccddaabbccddaabbccddaabbccdd00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002",
            "signature": "0x2222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222",
        },
    },
    {
        "description": "Normal account deployment",
        "should_be_blocked": False,
        "userop": {
            "sender": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            "nonce": "0",
            "initCode": "0xaabbccddaabbccddaabbccddaabbccddaabbccddffffffff",
            "callData": "0x",
            "accountGasLimits": "0x0000000000000000000000000000000000000000000000000000000002dc6c00000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "100000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000004a817c80000000000000000000000000000000000000000000000000000000004a817c80",
            "paymasterAndData": "0x",
            "signature": "0x3333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333",
        },
    },
]

# M3: Paymaster attack vectors
PAYMASTER_ATTACKS = [
    {
        "description": "Empty paymasterAndData bypass attempt",
        "attack_type": "paymaster_exploit",
        "should_be_blocked": True,
        "userop": {
            "sender": "0x1234567890123456789012345678901234567890",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000f42400000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "21000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        },
    },
    {
        "description": "Forged paymaster signature",
        "attack_type": "paymaster_exploit",
        "should_be_blocked": True,
        "userop": {
            "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000f42400000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "21000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            "signature": "0x1234",
        },
    },
    {
        "description": "Zero address paymaster",
        "attack_type": "paymaster_exploit",
        "should_be_blocked": True,
        "userop": {
            "sender": "0xfedcbafedcbafedcbafedcbafedcbafedcba0987",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000f42400000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "21000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            "signature": "0x1234",
        },
    },
    {
        "description": "Zero address paymaster",
        "attack_type": "paymaster_exploit",
        "should_be_blocked": True,
        "userop": {
            "sender": "0xfedcbafedcbafedcbafedcbafedcbafedcba0987",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000f42400000000000000000000000000000000000000000000000000000000000186a0",
            "preVerificationGas": "21000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            "signature": "0xabcd",
        },
    },
]


# M4: Extended static attack samples for new categories
M4_STATIC_ATTACKS = [
    # --- reentrancy_attack ---
    {
        "description": "Re-entrant callData targeting EntryPoint.handleOps selector",
        "attack_type": "reentrancy_attack",
        "should_be_blocked": True,
        "vectors": ["reentrancy_attack"],
        "userop": {
            "sender": "0x1111111111111111111111111111111111111111",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x1fad948c0000000000000000000000000000000000000000000000000000000000000020",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000002dc6c0000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "50000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        },
    },
    {
        "description": "Re-entrant callData targeting depositTo after partial execution",
        "attack_type": "reentrancy_attack",
        "should_be_blocked": True,
        "vectors": ["reentrancy_attack"],
        "userop": {
            "sender": "0x2222222222222222222222222222222222222222",
            "nonce": "2",
            "initCode": "0x",
            "callData": "0xb760faf90000000000000000000000002222222222222222222222222222222222222222",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000001d4c00000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "50000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        },
    },
    # --- bundler_griefing ---
    {
        "description": "Gas-wasting op: passes simulation (balance sufficient) but reverts on-chain via storage slot flip",
        "attack_type": "bundler_griefing",
        "should_be_blocked": True,
        "vectors": ["bundler_griefing"],
        "userop": {
            "sender": "0x3333333333333333333333333333333333333333",
            "nonce": "0",
            "initCode": "0x",
            "callData": "0xdeadbeef00000000000000000000000000000000000000000000000000000000",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000007a1200000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "21000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000001",
            "paymasterAndData": "0x",
            "signature": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        },
    },
    # --- initcode_exploit ---
    {
        "description": "initCode with non-existent factory (address squatting attack)",
        "attack_type": "initcode_exploit",
        "should_be_blocked": True,
        "vectors": ["initcode_exploit"],
        "userop": {
            "sender": "0x4444444444444444444444444444444444444444",
            "nonce": "0",
            "initCode": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef5fbfb9cf0000000000000000000000000000000000000000000000000000000000000000",
            "callData": "0x",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000004c4b40000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "100000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        },
    },
    {
        "description": "initCode on already-deployed account (should fail: account exists)",
        "attack_type": "initcode_exploit",
        "should_be_blocked": True,
        "vectors": ["initcode_exploit"],
        "userop": {
            "sender": "0x1234567890123456789012345678901234567890",
            "nonce": "5",
            "initCode": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa5fbfb9cf0000000000000000000000000000000000000000000000000000000000000042",
            "callData": "0x",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000002dc6c0000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "100000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0xdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        },
    },
    # --- cross_chain_replay ---
    {
        "description": "Signature from mainnet (chainId=1) replayed on local testnet (chainId=31337) - no chainId in sig hash binding",
        "attack_type": "cross_chain_replay",
        "should_be_blocked": True,
        "vectors": ["cross_chain_replay"],
        "userop": {
            "sender": "0x5555555555555555555555555555555555555555",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0xa9059cbb000000000000000000000000deadbeefdeadbeefdeadbeefdeadbeefdeadbeef00000000000000000000000000000000000000000000000000000000000003e8",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000001d4c00000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "50000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0x4d5c6b7a8f9e0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b1b",
        },
    },
    # --- calldata_bomb ---
    {
        "description": "Oversized callData (8KB) to exhaust bundler bandwidth and mempool",
        "attack_type": "calldata_bomb",
        "should_be_blocked": True,
        "vectors": ["calldata_bomb"],
        "userop": {
            "sender": "0x6666666666666666666666666666666666666666",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x" + "aa" * 8192,
            "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000002dc6c000000000000000000000000000000000000000000000000000000000001e8480",
            "preVerificationGas": "9999999",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        },
    },
    # --- combo_sig_nonce ---
    {
        "description": "Combination: empty signature + replay nonce-0 (double-vector, hard to triage)",
        "attack_type": "combo_sig_nonce",
        "should_be_blocked": True,
        "vectors": ["signature_forgery", "nonce_manipulation"],
        "userop": {
            "sender": "0x7777777777777777777777777777777777777777",
            "nonce": "0",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000001d4c00000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "50000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0x",
        },
    },
    {
        "description": "Combination: all-zero 65-byte signature + future nonce (nonce=99999999)",
        "attack_type": "combo_sig_nonce",
        "should_be_blocked": True,
        "vectors": ["signature_forgery", "nonce_manipulation"],
        "userop": {
            "sender": "0x8888888888888888888888888888888888888888",
            "nonce": "99999999",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000001d4c00000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "50000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        },
    },
    # --- combo_gas_paymaster ---
    {
        "description": "Combination: uint256-max callGasLimit AND forged paymaster address with fake signature",
        "attack_type": "combo_gas_paymaster",
        "should_be_blocked": True,
        "vectors": ["gas_limit_attack", "paymaster_exploit"],
        "userop": {
            "sender": "0x9999999999999999999999999999999999999999",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "preVerificationGas": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
            "gasFees": "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "paymasterAndData": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef0000000000000000000000000000000000000000000000000000000000000001deadbeef",
            "signature": "0x1234",
        },
    },
    {
        "description": "Combination: zero callGasLimit AND underfunded zero-deposit paymaster",
        "attack_type": "combo_gas_paymaster",
        "should_be_blocked": True,
        "vectors": ["gas_limit_attack", "paymaster_exploit"],
        "userop": {
            "sender": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "nonce": "1",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            "preVerificationGas": "0",
            "gasFees": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            "paymasterAndData": "0x0000000000000000000000000000000000000000",
            "signature": "0x1b",
        },
    },
    # --- combo_initcode_invalid_addr ---
    {
        "description": "Combination: malicious initCode + sender is zero address (factory-to-zero exploit)",
        "attack_type": "combo_initcode_invalid_addr",
        "should_be_blocked": True,
        "vectors": ["initcode_exploit", "invalid_address"],
        "userop": {
            "sender": "0x0000000000000000000000000000000000000000",
            "nonce": "0",
            "initCode": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef5fbfb9cf00000000000000000000000000000000000000000000000000000000000000ff",
            "callData": "0x",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000004c4b40000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "100000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff1b",
        },
    },
    {
        "description": "Combination: initCode pointing to known EOA + mismatched sender address",
        "attack_type": "combo_initcode_invalid_addr",
        "should_be_blocked": True,
        "vectors": ["initcode_exploit", "invalid_address"],
        "userop": {
            "sender": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "nonce": "0",
            "initCode": "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266000000000000000000000000000000000000000000000000000000000000beef",
            "callData": "0xa9059cbb",
            "accountGasLimits": "0x000000000000000000000000000000000000000000000000000000000002dc6c0000000000000000000000000000000000000000000000000000000000030d40",
            "preVerificationGas": "100000",
            "gasFees": "0x000000000000000000000000000000000000000000000000000000003b9aca0000000000000000000000000000000000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc1b",
        },
    },
    # --- time_range_abuse ---
    {
        "description": "Expired timing semantics encoded via malformed signature context assumptions",
        "attack_type": "time_range_abuse",
        "should_be_blocked": True,
        "vectors": ["time_range_abuse"],
        "userop": {
            "sender": "0x1212121212121212121212121212121212121212",
            "nonce": "7",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x00000000000000000000000000030d400000000000000000000000000001d4c0",
            "preVerificationGas": "50000",
            "gasFees": "0x0000000000000000000000003b9aca000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1b",
        },
    },
    # --- eip7702_auth_bypass ---
    {
        "description": "0x7702-style initCode prefix with extra trailing initialization payload",
        "attack_type": "eip7702_auth_bypass",
        "should_be_blocked": True,
        "vectors": ["eip7702_auth_bypass"],
        "userop": {
            "sender": "0x1313131313131313131313131313131313131313",
            "nonce": "0",
            "initCode": "0x7702000000000000000000000000000000000000deadbeefcafebabe0000000000000000000000000000000000000000000000000000000000000001",
            "callData": "0x12345678",
            "accountGasLimits": "0x0000000000000000000000000004c4b40000000000000000000000000001d4c0",
            "preVerificationGas": "75000",
            "gasFees": "0x00000000000000000000000059682f0000000000000000000000000059682f00",
            "paymasterAndData": "0x",
            "signature": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb1b",
        },
    },
    # --- paymaster_postop_griefing ---
    {
        "description": "paymasterAndData with oversized context and fake signature trailer to stress postOp assumptions",
        "attack_type": "paymaster_postop_griefing",
        "should_be_blocked": True,
        "vectors": ["paymaster_postop_griefing"],
        "userop": {
            "sender": "0x1414141414141414141414141414141414141414",
            "nonce": "3",
            "initCode": "0x",
            "callData": "0x",
            "accountGasLimits": "0x0000000000000000000000000002dc6c0000000000000000000000000001d4c0",
            "preVerificationGas": "88000",
            "gasFees": "0x0000000000000000000000004a817c800000000000000000000000004a817c80",
            "paymasterAndData": "0x2222222222222222222222222222222222222222000000000000000000000000000186a0000000000000000000000000000186a0" + "ab" * 96,
            "signature": "0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc1b",
        },
    },
    # --- factory_stake_bypass ---
    {
        "description": "Factory-like initCode referencing an EOA and malformed deterministic deployment salt",
        "attack_type": "factory_stake_bypass",
        "should_be_blocked": True,
        "vectors": ["factory_stake_bypass"],
        "userop": {
            "sender": "0x1515151515151515151515151515151515151515",
            "nonce": "0",
            "initCode": "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "callData": "0x",
            "accountGasLimits": "0x0000000000000000000000000004c4b400000000000000000000000000030d40",
            "preVerificationGas": "95000",
            "gasFees": "0x0000000000000000000000003b9aca0000000000000000000000000077359400",
            "paymasterAndData": "0x",
            "signature": "0xdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd1b",
        },
    },
    # --- transient_storage_collision ---
    {
        "description": "callData crafted as if previous bundle state leaked through transient storage",
        "attack_type": "transient_storage_collision",
        "should_be_blocked": True,
        "vectors": ["transient_storage_collision"],
        "userop": {
            "sender": "0x1616161616161616161616161616161616161616",
            "nonce": "11",
            "initCode": "0x",
            "callData": "0x9f3f89dc" + "00" * 28 + "deadbeef" * 8,
            "accountGasLimits": "0x0000000000000000000000000002dc6c0000000000000000000000000002dc6c",
            "preVerificationGas": "64000",
            "gasFees": "0x0000000000000000000000003b9aca000000000000000000000000003b9aca00",
            "paymasterAndData": "0x",
            "signature": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee1b",
        },
    },
    # --- combo_7702_time_range ---
    {
        "description": "Combination: 7702-style initCode confusion with expired timing assumptions",
        "attack_type": "combo_7702_time_range",
        "should_be_blocked": True,
        "vectors": ["eip7702_auth_bypass", "time_range_abuse"],
        "userop": {
            "sender": "0x1717171717171717171717171717171717171717",
            "nonce": "0",
            "initCode": "0x7702000000000000000000000000000000000000ffffffffffffffffffffffffffffffffffffffff",
            "callData": "0xabcdef01",
            "accountGasLimits": "0x0000000000000000000000000004c4b40000000000000000000000000001d4c0",
            "preVerificationGas": "120000",
            "gasFees": "0x00000000000000000000000059682f000000000000000000000000009502f900",
            "paymasterAndData": "0x",
            "signature": "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff1b",
        },
    },
    # --- combo_factory_paymaster ---
    {
        "description": "Combination: malformed factory initCode with oversized paymaster payload",
        "attack_type": "combo_factory_paymaster",
        "should_be_blocked": True,
        "vectors": ["factory_stake_bypass", "paymaster_postop_griefing"],
        "userop": {
            "sender": "0x1818181818181818181818181818181818181818",
            "nonce": "0",
            "initCode": "0x8ba1f109551bd432803012645ac136ddd64dba72" + "ff" * 32,
            "callData": "0x",
            "accountGasLimits": "0x0000000000000000000000000007a1200000000000000000000000000002dc6c",
            "preVerificationGas": "140000",
            "gasFees": "0x0000000000000000000000007735940000000000000000000000000077359400",
            "paymasterAndData": "0x3333333333333333333333333333333333333333" + "cd" * 120,
            "signature": "0xabababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab1b",
        },
    },
]


# ---------------------------------------------------------------------------
# JSON parsing utility
# ---------------------------------------------------------------------------


def _parse_userop_json(response_text: str) -> Optional[Dict]:
    """Extract a UserOperation dict from raw AI response text.

    Handles markdown code blocks (```json ... ```) and extra whitespace.
    Returns None if JSON cannot be parsed.
    """
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        json_lines: List[str] = []
        inside = False
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                json_lines.append(line)
        text = "\n".join(json_lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _normalize_numeric_string(value: object) -> object:
    if isinstance(value, int):
        return str(value)
    if not isinstance(value, str):
        return value

    text = value.strip()
    if re.fullmatch(r"^\d+$", text):
        return text
    if re.fullmatch(r"^0x[a-fA-F0-9]+$", text):
        try:
            return str(int(text, 16))
        except ValueError:
            return value
    return value


def _normalize_packed_bytes32(value: object) -> object:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not re.fullmatch(r"^0x[a-fA-F0-9]+$", text):
        return value

    payload = text[2:]
    if not payload:
        return "0x" + ("0" * 64)
    if len(payload) == 64:
        return f"0x{payload.lower()}"
    if len(payload) == 128:
        lower_128 = int(payload[:64], 16) & ((1 << 128) - 1)
        upper_128 = int(payload[64:], 16) & ((1 << 128) - 1)
        packed = (upper_128 << 128) | lower_128
        return f"0x{packed:064x}"

    packed = int(payload, 16) & ((1 << 256) - 1)
    return f"0x{packed:064x}"


def normalize_attack_record(attack: Dict, fallback_attack_type: Optional[str] = None) -> Dict:
    """Normalize one AI-generated attack record into the project dataset shape.

    Handles wrapper-style responses, nested userop payloads, and hex-encoded numeric
    fields that should be emitted as decimal strings for downstream validation.
    """
    normalized = dict(attack)
    candidate = normalized.get("userop", normalized)

    if isinstance(candidate, dict) and "sender" not in candidate and isinstance(candidate.get("userop"), dict):
        wrapper = candidate
        candidate = wrapper["userop"]
        normalized["attack_type"] = wrapper.get(
            "attack_type", normalized.get("attack_type", fallback_attack_type)
        )
        for key in ["should_be_blocked", "vectors", "reasoning", "description"]:
            if key in wrapper and key not in normalized:
                normalized[key] = wrapper[key]

    if isinstance(candidate, dict):
        userop = dict(candidate)
        for field in NUMERIC_STRING_FIELDS:
            if field in userop:
                userop[field] = _normalize_numeric_string(userop[field])
        for field in ["accountGasLimits", "gasFees"]:
            if field in userop:
                userop[field] = _normalize_packed_bytes32(userop[field])
        normalized["userop"] = userop
        normalized.setdefault("attack_type", fallback_attack_type)
        normalized["valid_json"] = True
    else:
        normalized["userop"] = None
        normalized["valid_json"] = False

    return normalized


# ---------------------------------------------------------------------------
# Single-shot generator (sync)
# ---------------------------------------------------------------------------


class AttackGenerator:
    """Single-shot attack generator using DeepSeek API (synchronous).

    Good for quick tests and interactive use.
    Uses System Prompt v1 (schema-only, no few-shot examples).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        temperature: float = 0.7,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Set DEEPSEEK_API_KEY or pass --api-key."
            )
        self.base_url = base_url
        self.model = "deepseek-chat"
        self.temperature = temperature

    def generate(self, attack_type: Optional[str] = None) -> Dict:
        """Generate a single malformed UserOperation.

        Args:
            attack_type: One of ATTACK_TYPES, or None for default (integer_overflow_gas).

        Returns:
            Parsed UserOperation dict, or an error dict on failure.
        """
        prompt = (
            f"Generate a malformed UserOperation that targets: {attack_type}."
            if attack_type
            else "Generate a malformed UserOperation that attempts an integer overflow in gas fields."
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_V1},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 1024,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            parsed = _parse_userop_json(raw)
            if parsed is not None:
                return parsed
            return {
                "error": "JSON parse failed",
                "raw_response": raw,
                "attack_type": attack_type,
            }
        except Exception as exc:
            return {"error": str(exc), "attack_type": attack_type}


# ---------------------------------------------------------------------------
# Batch generator (async)
# ---------------------------------------------------------------------------


class BatchAttackGenerator:
    """Batch attack generator using async parallel DeepSeek API calls.

    Uses System Prompt v2 with few-shot examples from real vulnerabilities.
    Includes exponential-backoff retry on rate limits and timeouts.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        temperature: float = 0.9,
        prompt_version: str = "v4",
        seed: int = RANDOM_SEED,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Set DEEPSEEK_API_KEY or pass --api-key."
            )
        self.base_url = base_url
        self.model = "deepseek-chat"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = temperature
        self.prompt_version = prompt_version
        self.seed = seed
        random.seed(seed)

    async def _call_api(
        self,
        session: aiohttp.ClientSession,
        user_message: str,
        attempt: int = 0,
    ) -> Tuple[str, bool]:
        """Single async API call with retry logic."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        SYSTEM_PROMPT_V4 if self.prompt_version == "v4"
                        else SYSTEM_PROMPT_V3 if self.prompt_version == "v3"
                        else SYSTEM_PROMPT_V2
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            "temperature": self.temperature,
            "max_tokens": 1024,
        }
        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"], True
                if resp.status == 429 and attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2**attempt))
                    return await self._call_api(session, user_message, attempt + 1)
                error_body = await resp.text()
                return f"API error {resp.status}: {error_body}", False
        except asyncio.TimeoutError:
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2**attempt))
                return await self._call_api(session, user_message, attempt + 1)
            return "Timeout after retries", False
        except Exception as exc:
            return f"Exception: {exc}", False

    async def _generate_one(
        self, session: aiohttp.ClientSession, attack_type: str, index: int
    ) -> Dict:
        """Generate one attack and return result dict with metadata."""
        is_combo = attack_type in COMBO_ATTACK_TYPES
        if is_combo:
            msg = (
                f"Generate a COMBINATION attack UserOperation for type: {attack_type}. "
                "This must simultaneously exploit TWO distinct vulnerability vectors as described in your taxonomy. "
                "Make it realistic and unique."
            )
        else:
            msg = (
                f"Generate a malformed UserOperation that targets: {attack_type}. "
                "Make it unique and different from standard cases."
            )
        raw, ok = await self._call_api(session, msg)
        result: Dict = {
            "index": index,
            "attack_type": attack_type,
            "timestamp": datetime.now().isoformat(),
            "success": ok,
        }
        if ok:
            parsed = _parse_userop_json(raw)
            if isinstance(parsed, dict):
                result = normalize_attack_record({**result, "userop": parsed}, result["attack_type"])
            else:
                result["userop"] = None
                result["valid_json"] = False
            if parsed is None:
                result["raw_response"] = raw
        else:
            result["userop"] = None
            result["valid_json"] = False
            result["error"] = raw
        return result

    async def generate_batch(
        self,
        count: int = 50,
        attack_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Generate `count` attacks in parallel, cycling through attack_types.

        M4: Default uses full ATTACK_TYPES including new categories and combo attacks.
        Combo attacks receive ~15% share of slots to reflect real-world complexity.
        """
        base_types = [t for t in ATTACK_TYPES if t != "legitimate"]
        combo_types = COMBO_ATTACK_TYPES
        # Build weighted type sequence: ~15% combo attacks
        if attack_types is None:
            n_combo = max(1, int(count * 0.15))
            n_single = count - n_combo
            weighted: List[str] = []
            for i in range(n_single):
                weighted.append(base_types[i % len(base_types)])
            for i in range(n_combo):
                weighted.append(combo_types[i % len(combo_types)])
            random.shuffle(weighted)
            types_seq = weighted
        else:
            types_seq = [attack_types[i % len(attack_types)] for i in range(count)]

        print(
            f"Generating {count} attacks (prompt={self.prompt_version}, categories={len(set(types_seq))}, temperature={self.temperature})..."
        )
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._generate_one(session, types_seq[i], i + 1)
                for i in range(count)
            ]
            return await asyncio.gather(*tasks)

    def save_dataset(self, attacks: List[Dict], output_path: str) -> str:
        normalized_attacks = [
            normalize_attack_record(attack, attack.get("attack_type")) for attack in attacks
        ]
        valid_count = sum(1 for a in normalized_attacks if a.get("valid_json"))
        type_counts: Dict[str, int] = {}
        for a in normalized_attacks:
            t = a.get("attack_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        validator = AttackValidator(strict_mode=False)
        valid_schema, invalid_schema, schema_stats = validator.validate_batch(normalized_attacks)
        data = {
            "metadata": {
                "total_count": len(normalized_attacks),
                "valid_count": valid_count,
                "schema_valid_count": len(valid_schema),
                "schema_invalid_count": len(invalid_schema),
                "generation_date": datetime.now().isoformat(),
                "prompt_version": self.prompt_version,
                "temperature": self.temperature,
                "random_seed": self.seed,
                "attack_type_distribution": type_counts,
                "quality_summary": schema_stats,
            },
            "attacks": normalized_attacks,
        }
        Path(output_path).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(
            f"Dataset saved → {output_path}  ({valid_count}/{len(normalized_attacks)} JSON-valid, {len(valid_schema)}/{len(normalized_attacks)} schema-valid)"
        )
        return output_path

    def get_legitimate_samples(self) -> List[Dict]:
        return [
            {
                "index": i,
                "attack_type": "legitimate",
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "valid_json": True,
                **sample,
            }
            for i, sample in enumerate(LEGITIMATE_SAMPLES, 1)
        ]

    def get_paymaster_attacks(self) -> List[Dict]:
        return [
            {
                "index": i,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "valid_json": True,
                **attack,
            }
            for i, attack in enumerate(PAYMASTER_ATTACKS, 1)
        ]

    def get_m4_static_attacks(self) -> List[Dict]:
        """M4: Return static attack samples for extended categories (reentrancy, bundler griefing, initcode, cross-chain replay, calldata bomb, combination attacks)."""
        return [
            {
                "index": i,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "valid_json": True,
                **attack,
            }
            for i, attack in enumerate(M4_STATIC_ATTACKS, 1)
        ]


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_issues: Dict[str, List[str]]


class AttackValidator:
    """Validate AI-generated UserOperations against the ERC-4337 schema.

    Checks required fields, value types, hex/numeric formats, and (in strict
    mode) rejects unknown fields.
    """

    COMMON_REQUIRED_FIELDS = {
        "sender": {"pattern": r"^0x[a-fA-F0-9]{40}$"},
        "nonce": {"pattern": r"^\d+$"},
        "callData": {"pattern": r"^0x[a-fA-F0-9]*$"},
        "preVerificationGas": {"pattern": r"^\d+$"},
        "signature": {"pattern": r"^0x[a-fA-F0-9]*$"},
    }
    UNPACKED_REQUIRED_FIELDS = {
        "callGasLimit": {"pattern": r"^\d+$"},
        "verificationGasLimit": {"pattern": r"^\d+$"},
        "maxFeePerGas": {"pattern": r"^\d+$"},
        "maxPriorityFeePerGas": {"pattern": r"^\d+$"},
    }
    PACKED_REQUIRED_FIELDS = {
        "accountGasLimits": {"pattern": r"^0x[a-fA-F0-9]+$"},
        "gasFees": {"pattern": r"^0x[a-fA-F0-9]+$"},
    }
    OPTIONAL_FIELDS = {
        "initCode": {"pattern": r"^0x[a-fA-F0-9]*$"},
        "paymasterAndData": {"pattern": r"^0x[a-fA-F0-9]*$"},
    }

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def validate(self, userop: Dict) -> ValidationResult:
        """Validate a single UserOperation dict."""
        errors: List[str] = []
        warnings: List[str] = []
        field_issues: Dict[str, List[str]] = {}

        if not isinstance(userop, dict):
            return ValidationResult(False, ["Not a dict"], [], {})

        # Common required fields present + string type
        for name, spec in self.COMMON_REQUIRED_FIELDS.items():
            if name not in userop:
                errors.append(f"Missing required field: {name}")
                field_issues[name] = ["Missing"]
                continue
            val = userop[name]
            if not isinstance(val, str):
                errors.append(f"{name}: expected str, got {type(val).__name__}")
                field_issues[name] = [f"Wrong type: {type(val).__name__}"]
                continue
            if not re.match(spec["pattern"], val):
                errors.append(f"{name}: invalid format '{val}'")
                field_issues.setdefault(name, []).append("Invalid format")

        has_packed = any(name in userop for name in self.PACKED_REQUIRED_FIELDS)
        has_unpacked = any(name in userop for name in self.UNPACKED_REQUIRED_FIELDS)

        if has_packed:
            for name, spec in self.PACKED_REQUIRED_FIELDS.items():
                if name not in userop:
                    errors.append(f"Missing required field: {name}")
                    field_issues[name] = ["Missing"]
                    continue
                val = userop[name]
                if not isinstance(val, str):
                    errors.append(f"{name}: expected str, got {type(val).__name__}")
                    field_issues[name] = [f"Wrong type: {type(val).__name__}"]
                    continue
                if not re.match(spec["pattern"], val):
                    errors.append(f"{name}: invalid format '{val}'")
                    field_issues.setdefault(name, []).append("Invalid format")
        elif has_unpacked:
            for name, spec in self.UNPACKED_REQUIRED_FIELDS.items():
                if name not in userop:
                    errors.append(f"Missing required field: {name}")
                    field_issues[name] = ["Missing"]
                    continue
                val = userop[name]
                if not isinstance(val, str):
                    errors.append(f"{name}: expected str, got {type(val).__name__}")
                    field_issues[name] = [f"Wrong type: {type(val).__name__}"]
                    continue
                if not re.match(spec["pattern"], val):
                    errors.append(f"{name}: invalid format '{val}'")
                    field_issues.setdefault(name, []).append("Invalid format")
        else:
            for name in self.PACKED_REQUIRED_FIELDS:
                errors.append(f"Missing required field: {name}")
                field_issues.setdefault(name, []).append("Missing")

        # Optional fields format check
        for name, spec in self.OPTIONAL_FIELDS.items():
            val = userop.get(name)
            if val is None:
                continue
            if isinstance(val, str) and not re.match(spec["pattern"], val):
                errors.append(f"{name}: invalid format '{val}'")
                field_issues.setdefault(name, []).append("Invalid format")

        # Unknown fields (strict mode)
        if self.strict_mode:
            known = (
                set(self.COMMON_REQUIRED_FIELDS)
                | set(self.UNPACKED_REQUIRED_FIELDS)
                | set(self.PACKED_REQUIRED_FIELDS)
                | set(self.OPTIONAL_FIELDS)
            )
            unknown = set(userop.keys()) - known
            if unknown:
                warnings.append(f"Unknown fields: {unknown}")
                for f in unknown:
                    field_issues[f] = ["Unknown field"]

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_issues=field_issues,
        )

    def validate_batch(
        self, attacks: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """Validate a list of attack dicts (each with a 'userop' key).

        Returns:
            (valid_attacks, invalid_attacks, statistics)
        """
        valid, invalid = [], []
        for attack in attacks:
            normalized_attack = normalize_attack_record(
                attack,
                attack.get("attack_type"),
            )
            userop = normalized_attack.get("userop")
            if not userop:
                invalid.append(
                    {
                        **normalized_attack,
                        "validation": {"is_valid": False, "errors": ["No userop"]},
                    }
                )
                continue
            r = self.validate(userop)
            annotated = {
                **normalized_attack,
                "validation": {
                    "is_valid": r.is_valid,
                    "errors": r.errors,
                    "warnings": r.warnings,
                    "field_issues": r.field_issues,
                },
            }
            (valid if r.is_valid else invalid).append(annotated)

        stats = {
            "total": len(attacks),
            "valid": len(valid),
            "invalid": len(invalid),
            "success_rate_pct": round(len(valid) / len(attacks) * 100, 1)
            if attacks
            else 0,
        }
        return valid, invalid, stats

    def save_report(
        self,
        valid: List[Dict],
        invalid: List[Dict],
        stats: Dict,
        output_path: str = "validation_report.json",
    ) -> str:
        """Write a validation report JSON. Returns saved path."""
        error_counts: Dict[str, int] = {}
        for atk in invalid:
            for err in atk.get("validation", {}).get("errors", []):
                key = err.split(":")[0]
                error_counts[key] = error_counts.get(key, 0) + 1

        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "error_breakdown": error_counts,
            "invalid_sample": [
                {
                    "index": a.get("index"),
                    "attack_type": a.get("attack_type"),
                    "errors": a.get("validation", {}).get("errors", []),
                }
                for a in invalid[:10]
            ],
        }
        Path(output_path).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Validation report saved \u2192 {output_path}")
        return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="ERC-4337 AI fuzzing attack generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python attack_generator.py --mode single
  python attack_generator.py --mode single --attack-type nonce_manipulation
  python attack_generator.py --mode batch --count 50 --output attacks.json
  python attack_generator.py --mode validate --input attacks.json
""",
    )
    p.add_argument(
        "--mode",
        choices=["single", "batch", "validate"],
        default="single",
        help="Operation mode (default: single)",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="DeepSeek API key (overrides DEEPSEEK_API_KEY env var)",
    )
    p.add_argument(
        "--attack-type",
        choices=ATTACK_TYPES,
        default=None,
        help="Attack category for single mode",
    )
    p.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of attacks to generate in batch mode (default: 50)",
    )
    p.add_argument(
        "--output",
        default="attacks_dataset.json",
        help="Output JSON file for batch/validate modes",
    )
    p.add_argument(
        "--input",
        default=None,
        help="Input dataset JSON file for validate mode",
    )
    p.add_argument(
        "--no-strict",
        action="store_true",
        help="Disable strict validation (allow unknown fields)",
    )
    p.add_argument(
        "--prompt-version",
        choices=["v2", "v3", "v4"],
        default="v4",
        help="System prompt version for batch generation (default: v4)",
    )
    p.add_argument(
        "--include-static",
        action="store_true",
        default=True,
        help="Prepend M3/M4 static attack samples to the dataset (default: True)",
    )
    p.add_argument(
        "--no-static",
        action="store_true",
        help="Disable static sample prepending (overrides --include-static)",
    )
    return p


def main() -> None:
    args = _build_parser().parse_args()
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")

    # ------------------------------------------------------------------ single
    if args.mode == "single":
        if not api_key:
            print("Error: API key required. Set DEEPSEEK_API_KEY or pass --api-key.")
            return
        gen = AttackGenerator(api_key=api_key)
        print(f"Generating single attack (type={args.attack_type or 'default'})...")
        result = gen.generate(args.attack_type)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # ------------------------------------------------------------------ batch
    elif args.mode == "batch":
        if not api_key:
            print("Error: API key required. Set DEEPSEEK_API_KEY or pass --api-key.")
            return
        prompt_ver = getattr(args, "prompt_version", "v4")
        gen = BatchAttackGenerator(api_key=api_key, prompt_version=prompt_ver)
        attacks = asyncio.run(gen.generate_batch(count=args.count))

        # Prepend static samples (M3 paymaster + M4 extended) unless --no-static
        include_static = not getattr(args, "no_static", False)
        if include_static:
            static_samples = gen.get_legitimate_samples() + gen.get_paymaster_attacks() + gen.get_m4_static_attacks()
            all_attacks = static_samples + attacks
            print(f"Prepended {len(static_samples)} static samples (legitimate + paymaster + M4)")
        else:
            all_attacks = attacks

        valid_n = sum(1 for a in all_attacks if a.get("valid_json"))
        print(
            f"Done: {valid_n}/{len(all_attacks)} valid JSON ({valid_n / len(all_attacks) * 100:.1f}%)"
        )
        gen.save_dataset(all_attacks, args.output)

    # --------------------------------------------------------------- validate
    elif args.mode == "validate":
        input_path = args.input or args.output
        if not Path(input_path).exists():
            print(f"Error: input file not found: {input_path}")
            return
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
        attacks = data.get("attacks", data) if isinstance(data, dict) else data
        validator = AttackValidator(strict_mode=not args.no_strict)
        valid, invalid, stats = validator.validate_batch(attacks)
        print(
            f"Validation: {stats['valid']}/{stats['total']} valid ({stats['success_rate_pct']}%)"
        )
        report_path = args.output.replace(".json", "_report.json")
        validator.save_report(valid, invalid, stats, report_path)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
