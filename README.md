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

# 🚨 M3 里程碑总结与组员工作说明 (中文)

> **注意**: M3 里程碑的所有工作已全部完成并推送到 GitHub。为了让各位组员清楚自己在 M3 中“做”了什么，下面详细列出了每个人的职责、实际完成的工作、产出的代码/文档，以及最终需要提交给 Canvas 的文件。

---

## 📌 Role A — PM / 威胁对齐负责人 (Threat Alignment Lead)

**你的职责范围：** 负责将威胁模型与实际的测试用例对齐，找出测试盲区（Gap），组织团队 Review，并撰写你的个人 Evidence Pack。

**你在 M3 实际完成了什么：**
1. 创建了 **威胁→测试覆盖矩阵**，将 4 类威胁模型映射到了 27 个具体的测试用例上，并记录了所有测试的实测结果。
2. 在覆盖矩阵中输出了 **Gap List**（盲区列表），并为它们分配了 P0/P1/P2 优先级（例如指示 B 和 C 需要完成 1000+ 测试和多向量攻击）。
3. 组织并记录了团队的 **Review Meeting 纪要**。
4. 使用 AI 辅助构建了覆盖矩阵表格，并记录了采纳与拒绝 AI 建议的案例。

**你产出/修改的文件：**
- 📄 `docs/threat_test_coverage_matrix.md` (威胁覆盖矩阵与 Gap 列表)
- 📄 `docs/evidence/review_minutes.md` (团队 Review 会议纪要)
- 📄 `docs/M3_TEAM_ASSIGNMENT.md` (团队详细分工说明)
- 📄 `docs/evidence/evidence_role_a.md` (你的个人证据包 Markdown 原文件)

**👉 你最终需要提交给 Canvas 的文件：**
- 📥 **`docs/evidence/evidence_role_a.pdf`** 

---

## 📌 Role B — AI 攻击设计师 (AI Attack Designer)

**你的职责范围：** 负责升级 AI 攻击生成器，设计 Prompt v3 提示词，添加合法基线样本和新的 Paymaster 攻击向量，同时完成在执行侧的 Rotate Commit（轮换代码提交）。

**你在 M3 实际完成了什么：**
1. 升级并实现了 **Prompt v3**，引入了 **Chain-of-Thought (思维链)**，要求 AI 必须按 4 步推理输出攻击 payload。
2. 在攻击生成器中补充了 **5个合法基线样本 (Legitimate Samples)**，用于测试框架的误报率 (False Positive)。
3. 在攻击生成器中补充了 **3个 Paymaster 相关的恶意攻击向量**。
4. 记录了 **AI 错误修正案例**（AI 生成负数 Gas 的错误及你的代码修复过程）。
5. **Rotate Commit 完成**：你修改了测试执行脚本 `batch_runner.py`，在里面加入了记录每次执行耗时 (`execution_time_ms`) 的逻辑。
6. 修复了随机种子 (`RANDOM_SEED = 42`) 保证数据集生成可复现。

**你产出/修改的文件：**
- 💻 `erc4337-security-test V2/ai-attack-generator/attack_generator.py` (核心 AI 攻击生成器代码)
- 💻 `erc4337-security-test V2/batch_test/batch_runner.py` (执行侧 Rotate Commit 代码)
- 📄 `docs/prompt_v3_design.md` (Prompt v3 设计文档)
- 📄 `docs/evidence/ai_error_correction.md` (AI 错误修正案例)
- 📄 `docs/evidence/evidence_role_b.md` (你的个人证据包 Markdown 原文件)

**👉 你最终需要提交给 Canvas 的文件：**
- 📥 **`docs/evidence/evidence_role_b.pdf`**

---

## 📌 Role C — 测试执行 & 数据分析师 (Test Execution & Data Analyst)

**你的职责范围：** 负责使用 AI 生成的攻击数据执行批处理测试，提取关键指标（TP, FP, FN, P95 延迟），生成可视化图表，并完成在部署侧的 Rotate Commit。

**你在 M3 实际完成了什么：**
1. 编写了自动化的 **三档测试执行脚本** (`run_all_tiers.sh`)，一键运行 100/500/1000 规模的攻击测试。
2. 升级了可视化脚本 `visualizer.py`，在其中实现了混淆矩阵逻辑，自动计算 **TP, FP, FN, F1 Score** 以及 **P95 Latency**。
3. 跑出了真实测试数据，生成了 **M2 与 M3 的前后对比图表 (Before/After Comparison)**，并输出了 CSV 指标。
4. **Rotate Commit 完成**：你修改了部署脚本 `deploy_contracts.py`，为其添加了 `--verify` (验证部署) 和 `--addresses` 工具命令。

**你产出/修改的文件：**
- 💻 `erc4337-security-test V2/run_all_tiers.sh` (自动化测试脚本)
- 💻 `erc4337-security-test V2/batch_test/visualizer.py` (数据统计与绘图代码)
- 💻 `erc4337-security-test V2/scripts/deploy_contracts.py` (部署侧 Rotate Commit 代码)
- 📊 `erc4337-security-test V2/analysis_outputs/*` (你跑出来的 JSON, CSV, 以及 PNG 图表)
- 📄 `docs/evidence/evidence_role_c.md` (你的个人证据包 Markdown 原文件)

**👉 你最终需要提交给 Canvas 的文件：**
- 📥 **`docs/evidence/evidence_role_c.pdf`**

---

## 📌 Role D — 报告 & PPT 负责人 (Report & PPT Lead)

**你的职责范围：** 负责汇总统筹所有人的产出，撰写符合学术要求的最终实验报告，制作汇报 PPT，并完成能获得附加分（+5%）的 Spec-Driven 验证表格。

**你在 M3 实际完成了什么：**
1. 整合 A, B, C 的内容，撰写了完整的 **11个章节 Final Report**。
2. 使用 Marp 格式制作了 **7页汇报演示 PPT**。
3. 完成了 **Spec-Driven Mapping (+5% bonus)** 页面，将威胁、不变量(Invariant)、测试用例、实测结果进行了四列映射追踪。
4. 审查了项目中所有文档的术语一致性（如统一使用 `UserOperation`）。
5. 创建了涵盖全项目所有文件的 `FILE_OWNERSHIP.md` 以及 `TODO.md`，追踪项目整体进度。

**你产出/修改的文件：**
- 📄 `docs/final_report.md` (最终报告全文)
- 📄 `docs/presentation.md` (PPT 全文)
- 📄 `docs/spec_driven_mapping.md` (加分项页面)
- 📄 `docs/TODO.md` 和 `docs/FILE_OWNERSHIP.md` (项目管理追踪)
- 📄 `docs/evidence/evidence_role_d.md` (你的个人证据包 Markdown 原文件)

**👉 你最终需要提交给 Canvas 的文件：**
- 📥 **`docs/evidence/evidence_role_d.pdf`**
- 📥 **`docs/final_report.pdf`** (最终报告)
- 📥 **`docs/presentation.pdf`** (汇报PPT)

---

## 五、项目总体产出位置与结构

为了你们自己交作业或者答辩时心中有数，整个项目的文件位置分布如下：

```
📁 ERC-4337/
├── 📄 README.md                    ← 本说明文件
│
├── 📁 docs/
│   ├── 📄 final_report.pdf         ← 【D】最终报告
│   ├── 📄 presentation.pdf         ← 【D】PPT
│   ├── 📄 M3_TEAM_ASSIGNMENT.md    ← 【A】角色职责分工
│   ├── 📄 TODO.md                  ← 【D】任务状态
│   ├── 📄 threat_test_coverage_matrix.md ← 【A】威胁矩阵
│   ├── 📄 spec_driven_mapping.md   ← 【D】加分项
│   ├── 📄 prompt_v3_design.md      ← 【B】Prompt设计思路
│   ├── 📄 FILE_OWNERSHIP.md        ← 文件归属权声明
│   │
│   └── 📁 evidence/                ← **【这里是所有人交作业的PDF】**
│       ├── 📄 evidence_role_a.pdf
│       ├── 📄 evidence_role_b.pdf
│       ├── 📄 evidence_role_c.pdf
│       └── 📄 evidence_role_d.pdf
│
├── 📁 erc4337-security-test V2/
│   ├── 📄 run_all_tiers.sh         ← 【C】写的测试脚手架
│   │
│   ├── 📁 ai-attack-generator/
│   │   └── 📄 attack_generator.py  ← 【B】写的攻击生成代码
│   │
│   ├── 📁 batch_test/
│   │   ├── 📄 batch_runner.py      ← 【B】Rotate修改的执行代码
│   │   └── 📄 visualizer.py        ← 【C】写的数据绘图代码
│   │
│   ├── 📁 scripts/
│   │   └── 📄 deploy_contracts.py  ← 【C】Rotate修改的部署代码
│   │
│   └── 📁 analysis_outputs/        ← 【C】跑出来的数据
│       ├── attacks_real_10.json    
│       ├── metrics_chart_sample.png 
│       └── metrics_summary_sample.csv 
```

**大家现在可以直接前往 `docs/evidence/` 目录以及 `docs/` 目录，下载各自对应的 `.pdf` 文件并提交！祝大家 M3 顺利！** 🎉