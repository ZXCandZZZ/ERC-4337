# CS6290 — Individual Evidence Pack (Milestone 2)

> **Course:** CS6290 Privacy-Enhancing Technologies
> **Submission type:** Individual
> **Format:** PDF

---

## Student Information

- **Name:** Liu Yuhao
- **Student ID (SID):** 59942546
- **Group Number / Project Title:** Group 15 / ERC-4337
- **Milestone:** ☐ M1 ☑ M2 ☐ M3
- **Date:** March 4, 2026

---

## 1) What I Contributed

My primary responsibility in this milestone was extending the M1 foundation to support batch generation and Few-Shot learning. Here's what I accomplished:

- **Implemented the batch generation system** with async parallel processing using `asyncio` and `aiohttp`. The system can generate 50+ attack UserOperations in parallel with automatic retry logic and exponential backoff for rate limit handling, significantly improving efficiency compared to M1's sequential approach.

- **Designed System Prompt v2 with Few-Shot learning**, incorporating three real-world attack examples inspired by actual vulnerabilities from Gnosis Safe, Argent wallet, and OpenZeppelin audits. This addresses the lack of concrete guidance in Prompt v1 and improves attack realism by grounding AI outputs in actual vulnerability patterns.

- **Built the automated validation module** that checks generated UserOperations against the ERC-4337 schema. The validator verifies required fields, checks field types and formats, and filters invalid outputs, replacing M1's manual validation approach with a fully automated pipeline.

- **Tuned generation parameters for diversity**, raising temperature from 0.7 (M1) to 0.9 to encourage more creative and varied attack patterns. This, combined with Few-Shot examples, addresses the low-diversity limitation identified in M1.

- **Created comprehensive documentation** for the Few-Shot design rationale, including explanations of why each example was chosen, how they map to attack categories, and what improvements they bring over v1.

---

## 2) Evidence

**1. Python implementation**
![Batch Generator Code](image-batch-generator.png)

**2. Validation module**
![Attack Validator Code](image-validator.png)

**3. GitHub**
https://github.com/ZXCandZZZ/ERC-4337/tree/30cents-patch-1/m2_batch_generation

---

## 3) Validation Performed

1. **Unit testing of batch generator**: Tested the async batch generation with mock API responses to verify parallel execution, retry logic, and JSON parsing correctness

2. **Validator accuracy testing**: Ran the validator against 20 manually crafted UserOperations (10 valid, 10 invalid) to verify it correctly identifies schema violations and format errors

3. **Temperature tuning experiments**: Generated test batches at different temperatures (0.7, 0.8, 0.9) and compared attack diversity to confirm 0.9 produces more varied outputs without sacrificing schema compliance

4. **Few-Shot example validation**: Verified each Few-Shot example against the ERC-4337 specification and cross-referenced with published vulnerability reports to ensure they represent realistic attack patterns

---

## 4) AI Usage Transparency

**AI tool used:** DeepSeek API (deepseek-chat model)

**One AI output I rejected (and why):**

During batch generation testing, I encountered an AI-generated UserOperation with the following issues:

```json
{
  "sender": "not_an_address",
  "nonce": "abc",
  "callGasLimit": "100000",
  "signature": "0x"
}
```

I rejected this because:

1. **Invalid sender format**: "not_an_address" doesn't match the Ethereum address pattern (should be 0x followed by 40 hex characters)
2. **Invalid nonce type**: "abc" is not a valid uint256 value (should be numeric string)
3. **Missing required fields**: Multiple required fields (verificationGasLimit, preVerificationGas, maxFeePerGas, maxPriorityFeePerGas) are absent

**How this was handled:**

This output was automatically filtered by the validation module, demonstrating the importance of automated schema checking. The validation module correctly identified all three issues and marked the output as invalid. This validates our approach of separating generation (AI) from validation (deterministic code).

---

## 5) Reflection / Next Step

**A limitation of current work:**

The current batch generation system produces single-vector attacks where each UserOperation targets one vulnerability category. Real-world attackers often combine multiple attack vectors in a single transaction (e.g., nonce manipulation combined with gas limit abuse). This limitation will be addressed in Milestone 3 through Chain-of-Thought reasoning and multi-vector attack design, allowing the AI to reason about attack combinations and generate more sophisticated exploit scenarios.

---

**Document Status:** ✅ Complete for Milestone 2
**Next Milestone:** M3 - Chain-of-Thought reasoning and multi-vector attacks