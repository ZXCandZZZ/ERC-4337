# AI-Driven Fuzzing Framework for ERC-4337

[![Solidity](https://img.shields.io/badge/Solidity-0.8.28-blue)](https://soliditylang.org/)
[![Hardhat](https://img.shields.io/badge/Hardhat-2.19.0-yellow)](https://hardhat.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-green)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)

**CS6290 Privacy-Enhancing Technologies - Group Project**

An AI-powered security testing framework for ERC-4337 Account Abstraction smart wallets, designed to discover vulnerabilities through automated fuzzing with malformed UserOperation objects.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [1. Deploy Contracts](#1-deploy-contracts)
  - [2. Generate Attacks](#2-generate-attacks)
  - [3. Run Tests](#3-run-tests)
  - [4. Analyze Results](#4-analyze-results)
- [AI Attack Generator](#ai-attack-generator)
- [Attack Categories](#attack-categories)
- [Key Metrics](#key-metrics)
- [Threat Model](#threat-model)
- [Reproduction Guide](#reproduction-guide)
- [References](#references)

---

## Overview

This project implements a comprehensive security testing framework for ERC-4337 Account Abstraction protocol. It uses AI (DeepSeek API) to generate malicious UserOperation objects that test smart wallet implementations for vulnerabilities.

### Key Features

- ✅ **Complete ERC-4337 Implementation**: EntryPoint, SimpleAccount, Paymaster, SignatureAggregator
- ✅ **AI-Driven Attack Generation**: DeepSeek API with Few-Shot Learning (Prompt v1/v2/v3)
- ✅ **Automated Fuzzing**: Batch generation of 50-1000+ malformed UserOperations
- ✅ **Comprehensive Metrics**: True Positive, False Negative, False Positive, P95 Latency
- ✅ **Before/After Analysis**: Vulnerability fix verification with comparison charts
- ✅ **Threat Model Alignment**: Mapped tests to 4 threat categories from Threat Model V1/V2

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI-Driven Fuzzing Framework                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ AI Generator │───▶│  Test Runner │───▶│  Visualizer  │      │
│  │  (DeepSeek)  │    │  (Hardhat)   │    │  (Charts)    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Attack JSON  │    │ EntryPoint   │    │ Metrics CSV  │      │
│  │ (UserOps)    │    │ Contracts    │    │ Charts PNG   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Description | Location |
|-----------|-------------|----------|
| **EntryPoint** | Core ERC-4337 singleton contract | `contracts/core/EntryPoint.sol` |
| **SimpleAccount** | Standard smart wallet implementation | `contracts/accounts/SimpleAccount.sol` |
| **Paymaster** | Gas sponsorship contract | `contracts/core/BasePaymaster.sol` |
| **Attack.sol** | Malicious account for testing | `contracts/accounts/Attack.sol` |
| **AI Generator** | DeepSeek-powered attack generator | `ai-attack-generator/attack_generator.py` |
| **Test Runner** | Batch execution framework | `batch_test/batch_runner.py` |

---

## Project Structure

```
ERC-4337/
├── erc4337-security-test V2/          # Main implementation (V2)
│   ├── contracts/
│   │   ├── core/                      # Core ERC-4337 components
│   │   │   ├── EntryPoint.sol         # Singleton entry point
│   │   │   ├── BaseAccount.sol        # Account abstraction base
│   │   │   ├── StakeManager.sol       # Staking mechanism
│   │   │   ├── NonceManager.sol       # Nonce tracking
│   │   │   └── ...
│   │   ├── accounts/                  # Wallet implementations
│   │   │   ├── SimpleAccount.sol      # Standard wallet
│   │   │   ├── Attack.sol             # Malicious test contract
│   │   │   └── Simple7702Account.sol  # EIP-7702 support
│   │   ├── interfaces/                # ERC-4337 interfaces
│   │   └── test/                      # Test helper contracts
│   ├── tests/                         # Python test scripts
│   ├── ai-attack-generator/           # AI attack generation
│   │   ├── attack_generator.py        # Main generator
│   │   └── analyze_results.py         # Result analysis
│   ├── batch_test/                    # Batch testing
│   ├── scripts/                       # Deployment scripts
│   └── hardhat.config.js              # Hardhat configuration
│
├── docs/                              # Documentation
│   ├── M3_TEAM_ASSIGNMENT.md          # Team responsibilities
│   ├── TODO.md                        # Project TODO list
│   ├── threat_test_coverage_matrix.md # Threat mapping
│   ├── spec_driven_mapping.md         # Spec-Driven evidence
│   ├── final_report.md                # Final report
│   └── evidence/                      # Evidence packs
│
├── Threat Model V1.pdf                # Threat model document
├── Threat Model V2.pdf                # Updated threat model
└── README.md                          # This file
```

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/ZXCandZZZ/ERC-4337.git
cd ERC-4337/erc4337-security-test\ V2

# 2. Install dependencies
npm install
pip install -r requirements.txt

# 3. Set API key
export DEEPSEEK_API_KEY=your_api_key_here

# 4. Run full test suite
./run_all_tiers.sh

# 5. View results
open analysis_outputs/
```

---

## Installation

### Prerequisites

- Node.js v18+ and npm
- Python 3.9+
- Hardhat
- DeepSeek API Key

### Step 1: Install Node.js Dependencies

```bash
cd "erc4337-security-test V2"
npm install
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Create .env file
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env

# Or export directly
export DEEPSEEK_API_KEY=your_api_key_here
```

### Step 4: Verify Installation

```bash
# Compile contracts
npx hardhat compile

# Run local node
npx hardhat node
```

---

## Usage

### 1. Deploy Contracts

```bash
# Terminal 1: Start local Hardhat node
npx hardhat node

# Terminal 2: Deploy contracts
cd scripts
python deploy_contracts.py
```

### 2. Generate Attacks

```bash
# Generate single attack
python ai-attack-generator/attack_generator.py --mode single

# Generate batch (50 attacks)
python ai-attack-generator/attack_generator.py --mode batch --count 50 --output attacks.json

# Generate with specific attack type
python ai-attack-generator/attack_generator.py --mode single --attack-type nonce_manipulation
```

### 3. Run Tests

```bash
# Run smoke test (100 operations)
python batch_test/batch_runner.py --scale smoke

# Run medium test (500 operations)
python batch_test/batch_runner.py --scale medium

# Run large test (1000+ operations)
python batch_test/batch_runner.py --scale large

# Run all tiers
./run_all_tiers.sh
```

### 4. Analyze Results

```bash
# Generate analysis report
python ai-attack-generator/analyze_results.py --input attacks.json --output-dir ./analysis_outputs
```

---

## AI Attack Generator

### Prompt Versions

| Version | Features | Temperature |
|---------|----------|-------------|
| **v1** | Basic schema + attack categories | 0.7 |
| **v2** | Few-Shot Learning (3 examples) | 0.9 |
| **v3** | Chain-of-Thought reasoning | 0.9 |

### Prompt v3 Example

```python
SYSTEM_PROMPT_V3 = """
You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

Generate attack UserOperations using Chain-of-Thought reasoning:

STEP 1: Identify the vulnerability type to exploit
STEP 2: Design the attack vector
STEP 3: Construct the malformed UserOperation
STEP 4: Explain why this should bypass validation

Output format:
{
  "reasoning": "...",
  "attack_type": "...",
  "userop": {...}
}
"""
```

### Attack Types

| Category | Description | Example |
|----------|-------------|---------|
| `integer_overflow_gas` | Gas field overflow | callGasLimit = uint256_max |
| `invalid_address` | Zero address, non-existent contracts | sender = 0x0 |
| `malformed_calldata` | Wrong selectors, corrupted params | callData = 0xdeadbeef |
| `signature_forgery` | Empty, wrong length signatures | signature = 0x |
| `nonce_manipulation` | Replay attacks, future nonces | nonce = 0 |
| `gas_limit_attack` | Extreme gas values | verificationGasLimit = 1 |

---

## Attack Categories

### 1. Integer Overflow/Underflow
```json
{
  "callGasLimit": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
  "verificationGasLimit": "1"
}
```

### 2. Invalid Address
```json
{
  "sender": "0x0000000000000000000000000000000000000000"
}
```

### 3. Signature Forgery
```json
{
  "signature": "0xdeadbeef"
}
```

### 4. Nonce Manipulation
```json
{
  "nonce": "0"
}
```

### 5. Paymaster Attacks (New in M3)
```json
{
  "paymasterAndData": "0x<malformed_bytes>"
}
```

---

## Key Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| **True Positive (TP)** | Correctly blocked attacks | Blocked / Total Attacks |
| **False Negative (FN)** | Attacks that passed | Passed / Total Attacks |
| **False Positive (FP)** | Legitimate ops blocked | Blocked Legit / Total Legit |
| **Precision** | TP / (TP + FP) | - |
| **Recall** | TP / (TP + FN) | - |
| **F1 Score** | 2 × (P × R) / (P + R) | - |
| **P95 Latency** | 95th percentile execution time | Measured in ms |

---

## Threat Model

Based on Threat Model V1/V2, we test 4 threat categories:

| Threat Category | Description | Test Coverage |
|-----------------|-------------|---------------|
| **T1: Signature Bypass** | Forged/empty signatures | `signature_forgery` tests |
| **T2: Gas Manipulation** | Overflow/underflow attacks | `integer_overflow_gas` tests |
| **T3: Replay Attacks** | Nonce manipulation | `nonce_manipulation` tests |
| **T4: Paymaster Exploits** | paymasterAndData forgery | `paymaster_*` tests (M3) |



---



## Reproduction Guide

### Full Experiment Reproduction

```bash
# Step 1: Environment setup
npm install
pip install -r requirements.txt
export DEEPSEEK_API_KEY=your_key

# Step 2: Start local blockchain
npx hardhat node &

# Step 3: Deploy contracts
python scripts/deploy_contracts.py

# Step 4: Generate attacks (seed=42 for reproducibility)
python ai-attack-generator/attack_generator.py --mode batch --count 1000 --seed 42

# Step 5: Run all test tiers
./run_all_tiers.sh

# Step 6: Generate analysis
python ai-attack-generator/analyze_results.py --input attacks_dataset_1000.json

# Expected output:
# - logs/tier_100.log
# - logs/tier_500.log
# - logs/tier_1000.log
# - metrics_summary.csv
# - analysis_outputs/*.png
```

---

## References

- [ERC-4337 Specification](https://eips.ethereum.org/EIPS/eip-4337)
- [Account Abstraction Implementation](https://github.com/eth-infinitism/account-abstraction)
- [DeepSeek API Documentation](https://platform.deepseek.com/docs)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/)

---
