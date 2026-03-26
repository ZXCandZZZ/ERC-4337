# ERC-4337 V2 Test Failure Report

Date: 2026-03-26

## Scope

- Generated AI attack dataset with prompt v4
- Ran AI dataset validation
- Ran BatchRunner security test
- Ran signature security suite
- Ran vulnerability/front-running simulation

## Final Status

### Passed

- BatchRunner: passed
- Signature security suite: passed
- Vulnerability/front-running simulation: passed

### Partially Passed

- Historical raw AI dataset validation was partially successful before cleaning

### Final Clean Dataset Status

- Clean dataset validation: 1200/1200 valid
- Clean dataset chain sample: 25/25 blocked, 0 vulnerable, 0 error

## Executed Results

### 1. AI Dataset Generation

- Output file: ai-attack-generator/attacks_dataset_500.json
- Actual total samples: 522
- Prompt version: v4
- Attack categories covered: 18
- Metadata valid_json count during generation: 374

### 2. AI Dataset Validation

- Historical raw dataset after compatibility fixes: improved from 0/522 to 349/522 valid
- Final clean dataset: 1200/1200 valid
- Report file: attacks_dataset_report.json

#### Root Cause Fixed During This Run

The validator was still enforcing the older unpacked schema:

- callGasLimit
- verificationGasLimit
- maxFeePerGas
- maxPriorityFeePerGas

But the generator had already switched to packed ERC-4337 fields:

- accountGasLimits
- gasFees

In addition, a large portion of AI responses returned a wrapper object with nested userop, while the generator stored the whole wrapper directly under the userop field. This caused the validator to treat the wrapper as if it were the final UserOperation.

This mismatch was fixed by:

- allowing the validator to accept both packed and unpacked schemas
- unwrapping nested userop payloads during validation
- normalizing new generation results so the saved userop is the actual UserOperation body

#### Remaining Invalid Cases In Raw AI Output

Remaining invalid cases after compatibility fixes in the raw AI dataset were still present and came mostly from model output quality.

Breakdown observed from live validation run:

- 148 cases: No userop
- 24 cases: preVerificationGas provided as hex string like 0x186a0
- 23 cases: preVerificationGas provided as hex string like 0x0f4240
- 13 cases: nonce provided as hex string like 0x42
- 8 cases: nonce provided as oversized hex string
- other smaller groups: additional hex-form numeric fields

#### Assessment

- The validation pipeline is now functional for packed-format datasets
- The remaining raw-AI failures were handled by a clean-data build pipeline instead of leaving the project dependent on unstable model output
- The final delivered dataset is the cleaned 1200-sample corpus, not the noisy raw 522-sample corpus

### 2.1 Final Clean Dataset

- File: ai-attack-generator/attacks_dataset_1200_clean.json
- Validation: 1200/1200 valid
- Category coverage: 25 attack categories
- Chain sample test: 25/25 blocked

### 3. BatchRunner Test

- Result: passed
- Summary: BLOCKED=18, VULNERABLE=0, VERDICT_FAIL=0
- Report files:
  - data/reports/batch_test_v2_20260326_023111.csv
  - data/reports/metrics_summary_20260326_023111.csv
  - data/reports/metrics_summary_20260326_023111.png

### 4. Signature Security Test

- Result: 4/4 passed
- Tested cases:
  - zero signature
  - short signature
  - invalid v signature
  - replay attack with same nonce
- Output files:
  - data/results/signature_tests_20260326_023107.json
  - data/results/signature_tests_20260326_023107.csv

### 5. Vulnerability / Front-Running Test

- Result: passed
- Observed behavior:
  - attacker transaction succeeded
  - user transaction also succeeded
  - user nonce advanced from 0 to 1
  - attack contract emitted AttackTriggered
  - user transaction remained unaffected

## Runtime Issues Encountered And Resolved

### Hardhat Node Not Running

Initial chain-based tests failed because the local Hardhat node was not active on 127.0.0.1:8545.

Resolution:

- started Hardhat node
- redeployed EntryPoint and SimpleAccount contracts
- redeployed Attack contract

This was an environment readiness issue, not a contract security failure.

## Recommendations

1. Keep the cleaned dataset build pipeline as the main deliverable path for large datasets.
2. Preserve validator support for both packed and unpacked schemas for backward compatibility.
3. Treat resisted attacks as expected blocked outcomes, not product failures.
