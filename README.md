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
- [Documentation](#documentation)
- [Team & Responsibilities](#team--responsibilities)
- [Evidence Packs](#evidence-packs)
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

See `docs/threat_test_coverage_matrix.md` for detailed mapping.

---

## Documentation

| Document | Description | Location |
|----------|-------------|----------|
| **M3 Team Assignment** | Role responsibilities | `docs/M3_TEAM_ASSIGNMENT.md` |
| **TODO List** | Outstanding tasks | `docs/TODO.md` |
| **Coverage Matrix** | Threat→Test mapping | `docs/threat_test_coverage_matrix.md` |
| **Spec-Driven Mapping** | threat→invariant→test→result | `docs/spec_driven_mapping.md` |
| **Final Report** | Complete project report | `docs/final_report.md` |
| **Presentation** | Slides for demo | `docs/presentation.md` |

---

## Team & Responsibilities

### M3 Role Assignments

| Role | Member | Responsibilities |
|------|--------|------------------|
| **A - PM/Threat Alignment** | TBD | Coverage matrix, gap list, review minutes |
| **B - AI Attack Designer** | TBD | Legitimate samples, paymaster vectors, Prompt v3 |
| **C - Test Execution** | TBD | Three-tier tests, metrics CSV, comparison charts |
| **D - Report & PPT** | TBD | Final report, AI appendix, Spec-Driven page |

See `docs/M3_TEAM_ASSIGNMENT.md` for detailed task breakdown.

---

## Evidence Packs

Each team member must submit an Individual Evidence Pack (1-2 pages PDF) containing:

### Required Sections

1. **Contributions** (2-5 bullets)
2. **Verifiable Evidence** (≥2 items)
3. **Validation Performed** (≥1 item)
4. **AI Usage Transparency** (1 adopted, 1 rejected)

### Evidence Templates

Located in `docs/evidence/evidence_role_{a,b,c,d}.md`

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

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**CS6290 Privacy-Enhancing Technologies** | Group Project | 2026

---

# 🚨 M3 里程碑交付指南 (中文)

> **重要**: 所有M3任务已完成！每位组员可直接领取PDF文件提交。

---

## 一、项目状态总览

### ✅ 所有任务已完成

| 类别 | 文件/功能 | 状态 |
|------|----------|------|
| **文档** | README.md | ✅ 完成 |
| **文档** | docs/M3_TEAM_ASSIGNMENT.md | ✅ 完成 |
| **文档** | docs/TODO.md | ✅ 完成 |
| **文档** | docs/threat_test_coverage_matrix.md | ✅ 完成 |
| **文档** | docs/spec_driven_mapping.md (+5%) | ✅ 完成 |
| **文档** | docs/prompt_v3_design.md | ✅ 完成 |
| **文档** | docs/final_report.md | ✅ 完成 |
| **文档** | docs/presentation.md | ✅ 完成 |
| **代码** | attack_generator.py (Prompt v3 + 合法样本 + Paymaster) | ✅ 完成 |
| **代码** | batch_runner.py (执行时间追踪) | ✅ **已修改 - Rotate** |
| **代码** | visualizer.py (指标计算 + 图表) | ✅ 完成 |
| **代码** | deploy_contracts.py (--verify/--addresses) | ✅ **已修改 - Rotate** |
| **脚本** | run_all_tiers.sh | ✅ 完成 |
| **证据** | evidence_role_a.md + .pdf | ✅ 完成 |
| **证据** | evidence_role_b.md + .pdf | ✅ 完成 |
| **证据** | evidence_role_c.md + .pdf | ✅ 完成 |
| **证据** | evidence_role_d.md + .pdf | ✅ 完成 |
| **证据** | review_minutes.md | ✅ 完成 |
| **证据** | ai_error_correction.md | ✅ 完成 |
| **PDF** | final_report.pdf | ✅ **已生成** |
| **PDF** | presentation.pdf | ✅ **已生成** |
| **测试** | 真实攻击数据集 | ✅ **已生成** |

---

## 二、每位成员领取文件

### 📌 Role A — PM / 威胁对齐负责人

**直接提交的PDF:**
```
docs/evidence/evidence_role_a.pdf  ← 直接提交到Canvas
```

**已完成文件 (可用于Git commit):**
```
docs/threat_test_coverage_matrix.md  ← 威胁覆盖矩阵
docs/evidence/review_minutes.md      ← Review纪要
docs/M3_TEAM_ASSIGNMENT.md           ← 团队分工
```

**Git提交命令:**
```bash
cd ERC-4337
git add docs/threat_test_coverage_matrix.md docs/evidence/review_minutes.md
git commit -m "docs: add coverage matrix and review minutes for M3"
git push
```

---

### 📌 Role B — AI 攻击设计师

**直接提交的PDF:**
```
docs/evidence/evidence_role_b.pdf  ← 直接提交到Canvas
```

**已完成文件:**
```
docs/prompt_v3_design.md               ← Prompt v3设计
docs/evidence/ai_error_correction.md   ← AI错误修正案例
ai-attack-generator/attack_generator.py ← 已添加Prompt v3 + 合法样本
```

**✅ Rotate Commit 已完成 (batch_runner.py已修改)**

**Git提交命令:**
```bash
cd "ERC-4337/erc4337-security-test V2"
git add batch_test/batch_runner.py ai-attack-generator/attack_generator.py
git commit -m "feat(M3): add execution time tracking and Prompt v3"
git push
```

---

### 📌 Role C — 测试执行 & 数据分析师

**直接提交的PDF:**
```
docs/evidence/evidence_role_c.pdf  ← 直接提交到Canvas
```

**已完成文件:**
```
run_all_tiers.sh                      ← 三档测试脚本
batch_test/visualizer.py              ← 指标计算 + 图表生成
logs/tier_100_sample.log              ← 测试日志示例
analysis_outputs/metrics_summary_sample.csv  ← 指标CSV
analysis_outputs/metrics_chart_sample.png    ← 指标图表
analysis_outputs/attacks_real_10.json        ← 真实攻击数据
```

**✅ Rotate Commit 已完成 (deploy_contracts.py已修改)**

**Git提交命令:**
```bash
cd "ERC-4337/erc4337-security-test V2"
git add scripts/deploy_contracts.py batch_test/visualizer.py run_all_tiers.sh
git commit -m "feat(M3): add metrics computation and three-tier testing"
git push
```

---

### 📌 Role D — 报告 & PPT 负责人

**直接提交的PDF:**
```
docs/final_report.pdf           ← 最终报告
docs/presentation.pdf           ← 7页PPT
docs/evidence/evidence_role_d.pdf  ← Evidence Pack
```

**已完成文件:**
```
docs/final_report.md              ← 最终报告 (11节)
docs/presentation.md              ← 7页PPT
docs/spec_driven_mapping.md       ← +5% 加分页
docs/FILE_OWNERSHIP.md            ← 文件归属汇总
docs/TODO.md                      ← 任务追踪
```

**Git提交命令:**
```bash
cd ERC-4337
git add docs/final_report.md docs/presentation.md docs/spec_driven_mapping.md
git commit -m "docs: add final report and presentation for M3"
git push
```

---

## 三、文件结构图

```
📁 ERC-4337/
│
├── 📄 README.md                    ← 所有成员必读
│
├── 📁 docs/
│   ├── 📄 final_report.pdf         ← 【D提交】最终报告PDF
│   ├── 📄 presentation.pdf         ← 【D提交】PPT PDF
│   ├── 📄 M3_TEAM_ASSIGNMENT.md    ← 【A负责】详细分工
│   ├── 📄 TODO.md                  ← 【D负责】任务追踪
│   ├── 📄 threat_test_coverage_matrix.md ← 【A负责】威胁矩阵
│   ├── 📄 spec_driven_mapping.md   ← 【D负责】+5%加分
│   ├── 📄 prompt_v3_design.md      ← 【B负责】Prompt设计
│   ├── 📄 FILE_OWNERSHIP.md        ← 文件归属汇总
│   │
│   └── 📁 evidence/
│       ├── 📄 evidence_role_a.pdf  ← 【A提交】
│       ├── 📄 evidence_role_b.pdf  ← 【B提交】
│       ├── 📄 evidence_role_c.pdf  ← 【C提交】
│       ├── 📄 evidence_role_d.pdf  ← 【D提交】
│       ├── 📄 review_minutes.md    ← 【A负责】Review纪要
│       └── 📄 ai_error_correction.md ← 【B负责】AI错误案例
│
├── 📁 erc4337-security-test V2/
│   ├── 📄 run_all_tiers.sh         ← 【C创建】三档测试
│   │
│   ├── 📁 ai-attack-generator/
│   │   └── 📄 attack_generator.py  ← 【B已修改】Prompt v3
│   │
│   ├── 📁 batch_test/
│   │   ├── 📄 batch_runner.py      ← 【B Rotate】已修改
│   │   └── 📄 visualizer.py        ← 【C已修改】指标计算
│   │
│   ├── 📁 scripts/
│   │   └── 📄 deploy_contracts.py  ← 【C Rotate】已修改
│   │
│   ├── 📁 logs/
│   │   └── tier_100_sample.log     ← 【C生成】测试日志
│   │
│   └── 📁 analysis_outputs/
│       ├── attacks_real_10.json    ← 【C生成】真实攻击数据
│       ├── metrics_chart_sample.png ← 【C生成】指标图表
│       └── metrics_summary_sample.csv ← 【C生成】指标CSV
│
├── 📄 Threat Model V1.pdf          ← 已存在
└── 📄 Threat Model V2.pdf          ← 已存在
```

---

## 四、Git 提交指南

### 所有成员统一的提交流程

```bash
# 1. 进入项目目录
cd /path/to/ERC-4337

# 2. 查看当前状态
git status

# 3. 添加你负责的文件 (参考上面每人的文件列表)
git add <your-files>

# 4. 提交
git commit -m "feat(M3): <描述你的修改>"

# 5. 推送
git push origin main
```

### Commit 消息格式

```
feat(M3): add execution time tracking to batch_runner
docs(M3): add coverage matrix and review minutes
fix(M3): correct metrics calculation in visualizer
```

---

## 五、Canvas 提交清单

| 角色 | 提交文件 | 状态 |
|------|----------|------|
| **A** | evidence_role_a.pdf | ✅ 已生成 |
| **B** | evidence_role_b.pdf | ✅ 已生成 |
| **C** | evidence_role_c.pdf | ✅ 已生成 |
| **D** | evidence_role_d.pdf + final_report.pdf + presentation.pdf | ✅ 已生成 |

---

## 六、验证检查清单

### 提交前确认

- [ ] Evidence Pack PDF 已生成
- [ ] Git commit 已推送
- [ ] GitHub commit 链接已记录
- [ ] 所有文件已在 README 中列出

### 代码验证

```bash
# Python 语法检查
cd "ERC-4337/erc4337-security-test V2"
python3 -m py_compile ai-attack-generator/attack_generator.py
python3 -m py_compile batch_test/batch_runner.py
python3 -m py_compile batch_test/visualizer.py

# 攻击生成器测试
export DEEPSEEK_API_KEY="your-key"
python3 ai-attack-generator/attack_generator.py --mode single
```

---

## 七、文件大小参考

| 文件 | 大小 |
|------|------|
| final_report.pdf | 54KB |
| presentation.pdf | 44KB |
| evidence_role_a.pdf | 28KB |
| evidence_role_b.pdf | 28KB |
| evidence_role_c.pdf | 35KB |
| evidence_role_d.pdf | 33KB |

---

**所有 M3 任务已完成！直接领取 PDF 提交即可！** 🎉
npm install

# 3. 检查Hardhat节点
npx hardhat node
```

---

**如有问题，请联系团队协调。祝顺利完成M3！** 🎉