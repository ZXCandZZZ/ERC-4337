# System Prompt v2 - Few-Shot Learning Design

**Version:** 2.0  
**Date:** 2026-03-04  
**Author:** Member B (AI Attack Designer)  
**Project:** AI-Driven Fuzzing Framework for ERC-4337  
**Milestone:** M2 - Batch Generation & Few-Shot Learning

---

## Overview

This document describes the design rationale and implementation of System Prompt v2, which introduces **Few-Shot Learning** to improve attack quality and diversity. Prompt v2 builds on v1's foundation by adding concrete attack examples from real-world vulnerabilities.

---

## What's New in v2

### Key Enhancements from v1

| Feature | v1 (M1) | v2 (M2) |
|---------|---------|---------|
| **Examples** | None | 3 Few-Shot examples from real vulnerabilities |
| **Guidance** | Basic schema | Detailed attack explanations |
| **Diversity** | Single category | Multi-category with examples |
| **Temperature** | 0.7 | 0.9 (higher for more variety) |

### Why Few-Shot Learning?

**Problem with v1:**
- AI generated simplistic, repetitive attacks
- Lack of real-world context led to unrealistic test cases
- Missing edge cases that actual attackers would exploit

**Solution with v2:**
- Provide 3 concrete examples of real attacks
- Show AI what "good" attack looks like
- Guide AI toward realistic vulnerability patterns
- Increase temperature for more creative variations

---

## Few-Shot Examples

Three real-world inspired attack examples with explanations:

### Example 1: Nonce Replay Attack
**Source:** Inspired by Gnosis Safe vulnerability  
**Attack Vector:** Reusing nonce=0 after deployment

### Example 2: Gas Limit Manipulation
**Source:** Inspired by Argent wallet audit findings  
**Attack Vector:** uint256 max value with minimal verification gas

### Example 3: Signature Forgery with Wrong Length
**Source:** Inspired by OpenZeppelin audit findings  
**Attack Vector:** Zero address with malformed 4-byte signature

---

## Temperature Tuning

### v1 Temperature: 0.7
- Conservative, consistent outputs
- Lower diversity
- Fewer creative attacks

### v2 Temperature: 0.9
- Higher creativity
- More diverse attack patterns
- Better exploration of edge cases

**Why 0.9?**
- Balances consistency with variety
- Prevents excessive randomness
- Works well with Few-Shot examples to anchor outputs

---

## Expected Improvements

| Metric | v1 (M1) | v2 (M2 Target) |
|--------|---------|----------------|
| **Realism** | Low | High (real-vulnerability inspired) |
| **Diversity** | Low | High (temperature 0.9 + examples) |
| **Edge Case Coverage** | Basic | Comprehensive |
| **Multi-Vector Attacks** | None | Emerging |

---

## Known Limitations (v2)

1. **No Chain-of-Thought Reasoning** - AI doesn't explain attack strategy
2. **Single-Vector Attacks Only** - Each attack targets one vulnerability type
3. **Manual Example Curation** - Few-Shot examples manually selected

---

**Document Status:** ✅ Complete  
**Next Step:** Generate 50+ attacks using Prompt v2 and validate diversity