# ERC-4337 Attack Dataset 1200 Clean

Date: 2026-03-26

## Overview

This dataset is the final cleaned and usable ERC-4337 attack corpus produced for the V2 project.

Output file:

- ai-attack-generator/attacks_dataset_1200_clean.json

Key properties:

- Total samples: 1200
- Validation status: 1200/1200 schema-valid
- Chain execution sample: 25/25 blocked, 0 vulnerable, 0 error
- Coverage: 25 attack categories including combination attacks

## How It Was Built

The final dataset is not a raw dump of model output.

It was produced through a professional pipeline:

1. Collect seed attacks from existing AI-generated dataset and curated static templates.
2. Normalize records into a consistent ERC-4337 PackedUserOperation schema.
3. Canonicalize numeric fields and bytes32 packed gas fields.
4. Remove malformed, nested, or schema-invalid records.
5. Deduplicate attacks using a fingerprint over attack type, expectation, and normalized userop.
6. Expand clean seeds into a larger corpus through deterministic mutation.
7. Select the final 1200 records with balanced round-robin distribution across attack categories.

This gives a reproducible, testable, and better-controlled dataset than relying on raw AI output alone.

## Category Coverage

The final clean dataset covers 25 categories:

- access_list_poisoning
- aggregator_bypass
- bundler_griefing
- calldata_bomb
- combo_7702_time_range
- combo_factory_paymaster
- combo_gas_paymaster
- combo_initcode_invalid_addr
- combo_sig_nonce
- cross_chain_replay
- eip7702_auth_bypass
- factory_stake_bypass
- gas_limit_attack
- initcode_exploit
- integer_overflow_gas
- invalid_address
- legitimate
- malformed_calldata
- nonce_manipulation
- paymaster_exploit
- paymaster_postop_griefing
- reentrancy_attack
- signature_forgery
- time_range_abuse
- transient_storage_collision

## Source Rationale

The attack taxonomy was aligned with:

- ERC-4337 specification requirements for packed userops, nonce semantics, simulation, paymaster validation, and bundler behavior
- ERC-4337 documentation on paymaster griefing and simulation requirements
- account creation, factory, aggregator, EIP-7702, and transient storage risks described in the spec and supporting documentation

## Quality Notes

The project originally had a gap between generation format and validation format:

- generator emitted packed fields
- validator expected unpacked gas fields
- some AI responses nested the actual userop inside a wrapper object

These issues were fixed before producing the final clean dataset.

The final file is intended to be directly usable by:

- AI dataset validation
- AI dataset on-chain execution sampling
- frontend dataset validation flow
- frontend dataset chain-test flow

## Frontend Integration Status

The frontend now supports:

- AI generation with one primary generation button
- optional clean dataset build after generation
- dataset validation
- dataset chain-test execution

This means generation, cleaning, validation, and AI-dataset chain execution are linked end-to-end from the UI.

## Recommended Usage

For validation only:

python ai-attack-generator/attack_generator.py --mode validate --input ai-attack-generator/attacks_dataset_1200_clean.json --no-strict

For on-chain sampling:

python run_ai_dataset.py --input ai-attack-generator/attacks_dataset_1200_clean.json --limit 50

## Verification Snapshot

Final verification completed during this task:

- schema validation: 1200/1200 valid
- chain sample: 25/25 blocked, 0 vulnerable, 0 error
- batch runner: passed
- signature security suite: passed
- vulnerability scenario: passed
