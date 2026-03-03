# Milestone 2: Batch Generation & Few-Shot Learning

**Status:** ✅ Complete
**Date:** March 4, 2026
**Dependencies:** M1 complete ✅

---

## What Was Built

### 1. Batch Generation System (`batch_generator.py`)
- Async parallel processing using `asyncio` + `aiohttp`
- Generate 50+ attacks in single run
- Automatic retry with exponential backoff for rate limits
- System Prompt v2 with Few-Shot learning

### 2. Automated Validator (`attack_validator.py`)
- ERC-4337 schema compliance checking
- Field type and format validation
- Batch filtering of invalid outputs
- Detailed validation reports

### 3. Core Deliverables
- `batch_generator.py` - Main implementation (390 lines)
- `attack_validator.py` - Validation module (270 lines)
- `prompt_v2_design.md` - Few-Shot learning design
- `EVIDENCE_PACK_M2.md` - Individual evidence pack

---

## How to Use

### Setup
```bash
cd m2_batch_generation
pip install -r requirements.txt
```

### Run Batch Generation
```bash
python batch_generator.py
```

This will:
1. Generate 50+ attack UserOperations in parallel
2. Save to `attacks_dataset_50plus.json`
3. Display generation statistics

---

## M1 vs M2 Comparison

| Feature | M1 | M2 |
|---------|----|----|
| **Generation** | Single | Batch (50+) |
| **Prompt** | Basic schema | Few-Shot examples |
| **Temperature** | 0.7 | 0.9 |
| **Validation** | Manual | Automated |
| **Diversity** | Low | High (measured) |
| **Parallelization** | None | Async |

---

## Key Design Decisions

### Few-Shot Learning (Prompt v2)
Added 3 real-world attack examples from Gnosis Safe, Argent Wallet, and OpenZeppelin audits.

### Temperature Tuning
- M1 (v1): 0.7 - Conservative, low diversity
- M2 (v2): 0.9 - Higher creativity, better coverage

### Async Architecture
50 parallel requests vs 50 sequential → 10-20x speedup

---

## Known Limitations (to fix in M3)

1. **No Chain-of-Thought** - AI doesn't explain attack reasoning
2. **Single-Vector Attacks** - Each attack targets one vulnerability
3. **Static Few-Shot** - Examples manually curated

---

**Last Updated:** March 4, 2026
**Status:** M2 complete, ready for M3