# Milestone 1 Foundation - Quick Reference

**Status:** ✅ Complete  
**Date:** 2026-02-06  
**Role:** Member B - AI Attack Designer

---

## What Was Built

### 1. API Integration (`ai_attack_generator.py`)
- DeepSeek API integration using OpenAI-compatible interface
- System Prompt v1 for generating malformed UserOperations
- JSON parsing and validation
- Evidence collection mechanism

### 2. Core Deliverables
- `ai_attack_generator.py` - Main implementation (185 lines)
- `evidence_ai_response_v0.1.json` - First AI-generated attack
- `prompt_v1_design.md` - System Prompt documentation
- `EVIDENCE_PACK_M1.md` - Individual evidence pack for submission

---

## How to Use

### Setup
```bash
cd m1_foundation
pip install -r requirements.txt
```

### Run Generator
```bash
python ai_attack_generator.py
```

### API Configuration
DeepSeek API key is hardcoded in the script for demo purposes:
```python
api_key = "sk-85f96e1bfc48422fa3755f8b7721892d"
```

---

## Key Design Decisions

1. **DeepSeek over Claude**: Cost-effective, good JSON adherence
2. **Explicit schema in prompt**: Reduces AI hallucination
3. **Attack category enumeration**: 6 specific vulnerability types
4. **Evidence-first approach**: Every component has proof

---

## Known Limitations (to fix in M2)

1. **Single generation only** - Need batch processing
2. **No Few-Shot examples** - AI outputs are simplistic
3. **No diversity metrics** - Can't measure attack coverage
4. **Manual validation** - Need automated schema checking

---

## Next: Milestone 2

See `PROJECT_STATUS.md` in root directory for M2 roadmap.
