"""
Batch Attack Generator for ERC-4337 Smart Wallet Testing
Member B: AI Attack Designer
Milestone 2: Batch Generation & Few-Shot Learning

This script extends M1's single-generation approach to support:
- Batch generation of 50+ attack UserOperations
- Async parallel processing for efficiency
- Retry logic with exponential backoff
- Integration with automated validation
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


class BatchAttackGenerator:
    """
    Batch generator for malformed UserOperations using AI.
    Supports async parallel generation with retry logic.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key not found. Set DEEPSEEK_API_KEY environment variable "
                "or pass it directly."
            )

        self.base_url = base_url
        self.model = "deepseek-chat"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = 0.9

    def get_system_prompt_v2(self) -> str:
        return """You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

Your task is to generate diverse malformed or malicious UserOperation objects that test real-world vulnerabilities.

A valid ERC-4337 UserOperation has the following structure:
{
  "sender": "0x... (address, 20 bytes)",
  "nonce": "uint256",
  "initCode": "0x... (bytes, optional)",
  "callData": "0x... (bytes)",
  "callGasLimit": "uint256",
  "verificationGasLimit": "uint256",
  "preVerificationGas": "uint256",
  "maxFeePerGas": "uint256",
  "maxPriorityFeePerGas": "uint256",
  "paymasterAndData": "0x... (bytes, optional)",
  "signature": "0x... (bytes)"
}

FEW-SHOT EXAMPLES FROM REAL VULNERABILITIES:

Example 1 - Nonce Replay Attack (Inspired by Gnosis Safe vulnerability):
{
  "sender": "0x1234567890123456789012345678901234567890",
  "nonce": "0",
  "callData": "0x",
  "callGasLimit": "100000",
  "verificationGasLimit": "50000",
  "preVerificationGas": "21000",
  "maxFeePerGas": "20000000000",
  "maxPriorityFeePerGas": "1000000000",
  "signature": "0x0000000000000000000000000000000000000000000000000000000000000000"
}
ATTACK: Reusing nonce=0 after deployment allows replay attacks if implementation doesn't properly track executed nonces.

Example 2 - Gas Limit Manipulation (Inspired by Argent wallet audit findings):
{
  "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdef",
  "nonce": "1",
  "callData": "0xa9059cbb0000000000000000000000000000000000000000000000000000000000000000",
  "callGasLimit": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
  "verificationGasLimit": "1",
  "preVerificationGas": "0",
  "maxFeePerGas": "1000000000",
  "maxPriorityFeePerGas": "1000000000",
  "signature": "0x1234"
}
ATTACK: callGasLimit set to uint256 max value (2^256-1) while verificationGasLimit is minimal - tests for gas estimation vulnerabilities and integer overflow in gas calculations.

Example 3 - Signature Forgery with Wrong Length (Inspired by OpenZeppelin findings):
{
  "sender": "0x0000000000000000000000000000000000000000",
  "nonce": "42",
  "callData": "0x",
  "callGasLimit": "100000",
  "verificationGasLimit": "100000",
  "preVerificationGas": "21000",
  "maxFeePerGas": "3000000000",
  "maxPriorityFeePerGas": "2000000000",
  "signature": "0xdeadbeef"
}
ATTACK: Zero address sender with malformed 4-byte signature (should be 65 bytes) tests for edge cases in signature validation logic.

Generate UserOperations that target these categories:
1. **Integer overflow/underflow** - Gas fields at extreme values (uint256 max, negative-like values)
2. **Invalid addresses** - Zero address, non-existent contracts, contract creation addresses
3. **Malformed callData** - Wrong selectors, corrupted params, empty data, oversized data
4. **Signature forgery** - Empty, wrong length, invalid values, replay signatures
5. **Nonce manipulation** - Replay (duplicate), future nonces, negative-looking values
6. **Gas limit attacks** - Extremely high/low, inconsistent limits, zero gas

IMPORTANT: Generate DIVERSE attacks. Each UserOperation should be unique and test different edge cases. Output ONLY valid JSON containing a single UserOperation object. Do not include explanations or markdown formatting."""

    async def _call_deepseek_api_async(
        self,
        session: aiohttp.ClientSession,
        system_prompt: str,
        user_message: str,
        attempt: int = 0,
    ) -> Tuple[str, bool]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": self.temperature,
            "max_tokens": 1024,
        }

        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"], True
                elif response.status == 429 and attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2**attempt))
                    return await self._call_deepseek_api_async(
                        session, system_prompt, user_message, attempt + 1
                    )
                else:
                    error_text = await response.text()
                    return f"API Error {response.status}: {error_text}", False
        except asyncio.TimeoutError:
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2**attempt))
                return await self._call_deepseek_api_async(
                    session, system_prompt, user_message, attempt + 1
                )
            return "Timeout after retries", False
        except Exception as e:
            return f"Exception: {str(e)}", False

    def _parse_userop_json(self, response_text: str) -> Optional[Dict]:
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            lines = cleaned_text.split("\n")
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or (not line.strip().startswith("```")):
                    json_lines.append(line)
            cleaned_text = "\n".join(json_lines).strip()

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            return None

    async def generate_single_attack(
        self, session: aiohttp.ClientSession, attack_type: str, index: int
    ) -> Dict:
        system_prompt = self.get_system_prompt_v2()
        user_message = f"Generate a malformed UserOperation that targets: {attack_type}. Make it unique and different from standard cases."

        response_text, success = await self._call_deepseek_api_async(
            session, system_prompt, user_message
        )

        result = {
            "index": index,
            "attack_type": attack_type,
            "timestamp": datetime.now().isoformat(),
            "success": success,
        }

        if success:
            userop = self._parse_userop_json(response_text)
            if userop:
                result["userop"] = userop
                result["valid_json"] = True
            else:
                result["userop"] = None
                result["valid_json"] = False
                result["raw_response"] = response_text
        else:
            result["userop"] = None
            result["valid_json"] = False
            result["error"] = response_text

        return result

    async def generate_batch(
        self, count: int = 50, attack_types: Optional[List[str]] = None
    ) -> List[Dict]:
        if attack_types is None:
            attack_types = [
                "integer_overflow_gas",
                "invalid_address",
                "malformed_calldata",
                "signature_forgery",
                "nonce_manipulation",
                "gas_limit_attack",
            ]

        print(f"\n[Batch Generator] Starting generation of {count} attacks...")
        print(f"[Batch Generator] Attack types: {attack_types}")
        print(f"[Batch Generator] Temperature: {self.temperature}")

        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(count):
                attack_type = attack_types[i % len(attack_types)]
                tasks.append(self.generate_single_attack(session, attack_type, i + 1))

            results = await asyncio.gather(*tasks)

        return results

    def save_dataset(
        self, attacks: List[Dict], filename: str = "attacks_dataset_50plus.json"
    ) -> str:
        output = {
            "metadata": {
                "total_count": len(attacks),
                "valid_count": sum(1 for a in attacks if a.get("valid_json")),
                "generation_date": datetime.now().isoformat(),
                "prompt_version": "v2",
                "temperature": self.temperature,
            },
            "attacks": attacks,
        }

        filepath = Path(__file__).parent / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Dataset saved to {filepath}")
        return str(filepath)


def main():
    print("=" * 60)
    print("Batch Attack Generator - Milestone 2")
    print("Member B: AI Attack Designer")
    print("Provider: DeepSeek API")
    print("=" * 60)

    print("\n[1] Initializing batch generator...")
    try:
        api_key = "sk-85f96e1bfc48422fa3755f8b7721892d"
        generator = BatchAttackGenerator(api_key=api_key)
        print("✓ Batch generator initialized")
        print(f"✓ Model: {generator.model}")
        print(f"✓ Temperature: {generator.temperature}")
        print(f"✓ Max retries: {generator.max_retries}")
    except ValueError as e:
        print(f"✗ Error: {e}")
        return

    print("\n[2] Generating 50+ attacks in parallel...")
    attacks = asyncio.run(generator.generate_batch(count=50))

    valid_count = sum(1 for a in attacks if a.get("valid_json"))
    print(f"\n[3] Generation complete:")
    print(f"   Total generated: {len(attacks)}")
    print(f"   Valid JSON: {valid_count}")
    print(f"   Success rate: {valid_count / len(attacks) * 100:.1f}%")

    print("\n[4] Saving dataset...")
    filepath = generator.save_dataset(attacks)

    print("\n" + "=" * 60)
    print("Milestone 2 batch generation complete!")
    print(f"Dataset: {filepath}")
    print("=" * 60)


if __name__ == "__main__":
    main()