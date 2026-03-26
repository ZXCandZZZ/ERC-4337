# ERC-4337 V2 M4 Update Log

Date: 2026-03-26

## Summary

This update expands the ERC-4337 attack generation pipeline, integrates the new attack controls into the Streamlit frontend, adds test-page support for AI dataset validation and AI-dataset chain execution, verifies local runtime dependencies, and executes the main test methods end-to-end.

## Attack Generator Updates

Updated file:

- ai-attack-generator/attack_generator.py

### New Attack Coverage

Extended attack categories from the earlier baseline to 18 total categories, including:

- reentrancy_attack
- bundler_griefing
- initcode_exploit
- cross_chain_replay
- aggregator_bypass
- access_list_poisoning
- calldata_bomb
- time_range_abuse
- eip7702_auth_bypass
- paymaster_postop_griefing
- factory_stake_bypass
- transient_storage_collision
- combo_sig_nonce
- combo_gas_paymaster
- combo_initcode_invalid_addr
- combo_7702_time_range
- combo_factory_paymaster

### Combination Attacks

Added explicit combination attack support via:

- combo_sig_nonce
- combo_gas_paymaster
- combo_initcode_invalid_addr

Generation weighting now allocates roughly:

- 85% single-vector attacks
- 15% combination attacks

### Prompt System

Added SYSTEM_PROMPT_V4 with:

- packed ERC-4337 UserOperation format guidance
- 14 single-vector categories
- 3 combination categories
- structured reasoning output
- stronger instructions for unique and realistic attack generation

### Static Samples

Added M4 static samples covering:

- reentrancy attacks
- bundler griefing
- initcode exploits
- cross-chain replay
- calldata bomb cases
- combination attack samples

### CLI Enhancements

Added support for:

- --prompt-version
- --include-static
- --no-static

Batch generation now defaults to:

- prompt v4
- static sample prepending enabled

### Dataset Validation Compatibility Fix

During testing, the validator was updated to support:

- packed schema fields: accountGasLimits and gasFees
- legacy unpacked schema fields
- nested userop wrapper compatibility for older generated datasets

Generation output normalization was also added so future datasets store the actual UserOperation body under userop instead of the full wrapper object.

### Clean Dataset Build Pipeline

Added two new scripts:

- ai-attack-generator/clean_dataset.py
- ai-attack-generator/build_attack_dataset.py

These scripts support:

- normalization
- schema validation
- deduplication
- deterministic mutation-based corpus expansion
- balanced category selection for final delivery datasets

## Frontend Updates

Updated files:

- streamlit_app/core/ai_tools.py
- streamlit_app/core/tests.py
- streamlit_app/pages/ai_generator.py
- streamlit_app/pages/test_runner.py

### AI Generator Page

Changes:

- kept a single unified generation button
- added optional auto-clean dataset build after generation
- added prompt version selector: v4, v3, v2
- added static sample toggle
- added clean dataset output path and target size options
- expanded visible attack category list
- preserved environment-variable or manual API key entry flow

### Test Runner Page

Changes:

- added AI Dataset validation action
- added AI Dataset chain execution action
- allowed dataset path input for validation
- integrated validation and chain-test commands into the existing runner service

## Environment Setup

Verified environment:

- Python 3.12
- Node.js 24
- npm 11

Installed missing Python dependencies and project Node dependencies required for:

- Web3 and test execution
- lint and typing tools
- local Hardhat execution

## Execution Results

### Dataset Generation

- Historical raw dataset file: ai-attack-generator/attacks_dataset_500.json
- Final clean dataset file: ai-attack-generator/attacks_dataset_1200_clean.json
- Final clean sample count: 1200

### Test Results

- Final clean dataset validation: 1200/1200 valid
- Final clean dataset chain sample: 25/25 blocked
- BatchRunner: passed
- Signature suite: passed
- Vulnerability/front-running simulation: passed

## Notes

- A local Hardhat node had to be started before chain-based tests could run.
- Contracts were redeployed for the active local chain before running chain-based tests.
- Large raw AI generations are limited by external API quota and output instability, so final delivery now uses a clean build pipeline over validated seeds.

## Recommended Next Iteration

1. Extend seed sources with more audited real-world wallet and paymaster cases when available.
2. Add richer on-chain dataset executors if future tests need paymaster-specific deployed fixtures.
3. Keep the current clean dataset build path as the default deliverable path for large corpora.