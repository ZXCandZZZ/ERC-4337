"""
AI-Driven Attack Generator for ERC-4337 Smart Wallet Fuzzing

Generates malformed UserOperation objects using DeepSeek API to test
vulnerabilities in ERC-4337 smart wallet implementations.

Usage:
    # Single attack (quick test)
    python attack_generator.py --mode single
    python attack_generator.py --mode single --attack-type nonce_manipulation

    # Batch generation
    python attack_generator.py --mode batch --count 50 --output attacks.json

    # Validate an existing dataset
    python attack_generator.py --mode validate --input attacks.json

Environment:
    DEEPSEEK_API_KEY  DeepSeek API key (or pass --api-key)
"""

import argparse
import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

ATTACK_TYPES: List[str] = [
    "integer_overflow_gas",
    "invalid_address",
    "malformed_calldata",
    "signature_forgery",
    "nonce_manipulation",
    "gas_limit_attack",
]


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_V1 = """You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

Your task is to generate malformed or malicious UserOperation objects that could potentially exploit vulnerabilities in smart wallet implementations.

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

Generate UserOperations that test the following vulnerability categories:
1. **Integer overflow/underflow** in gas fields
2. **Invalid addresses** (zero address, non-existent contracts, EOAs)
3. **Malformed callData** (wrong function selectors, corrupted parameters)
4. **Signature forgery attempts** (empty, wrong length, invalid values)
5. **Nonce manipulation** (replay attacks, future nonces)
6. **Gas limit attacks** (extremely high/low values, inconsistent limits)

Output ONLY valid JSON containing a single UserOperation object. Do not include explanations or markdown formatting."""

SYSTEM_PROMPT_V2 = """You are an expert Ethereum security researcher specializing in ERC-4337 Account Abstraction vulnerabilities.

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

Example 1 - Nonce Replay Attack (Gnosis Safe):
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
ATTACK: Reusing nonce=0 after deployment allows replay if the implementation doesn't track executed nonces.

Example 2 - Gas Limit Manipulation (Argent wallet):
{
  "sender": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
  "nonce": "1",
  "callData": "0xa9059cbb0000000000000000000000000000000000000000000000000000000000000000",
  "callGasLimit": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
  "verificationGasLimit": "1",
  "preVerificationGas": "0",
  "maxFeePerGas": "1000000000",
  "maxPriorityFeePerGas": "1000000000",
  "signature": "0x1234"
}
ATTACK: callGasLimit = uint256 max while verificationGasLimit is minimal - tests gas estimation and integer overflow.

Example 3 - Signature Forgery (OpenZeppelin):
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
ATTACK: Zero address sender with 4-byte signature (should be 65 bytes) tests signature validation edge cases.

Generate UserOperations that target these categories:
1. **Integer overflow/underflow** - Gas fields at extreme values (uint256 max, near-zero)
2. **Invalid addresses** - Zero address, non-existent contracts, creation addresses
3. **Malformed callData** - Wrong selectors, corrupted params, empty or oversized data
4. **Signature forgery** - Empty, wrong length, invalid values, replay signatures
5. **Nonce manipulation** - Replay (duplicate), future nonces, negative-looking values
6. **Gas limit attacks** - Extremely high/low, inconsistent limits, zero gas

Generate DIVERSE attacks. Each UserOperation must be unique. Output ONLY valid JSON. No explanations, no markdown."""


# ---------------------------------------------------------------------------
# JSON parsing utility
# ---------------------------------------------------------------------------

def _parse_userop_json(response_text: str) -> Optional[Dict]:
    """Extract a UserOperation dict from raw AI response text.

    Handles markdown code blocks (```json ... ```) and extra whitespace.
    Returns None if JSON cannot be parsed.
    """
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        json_lines: List[str] = []
        inside = False
        for line in lines:
            if line.strip().startswith("```"):
                inside = not inside
                continue
            if inside:
                json_lines.append(line)
        text = "\n".join(json_lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Single-shot generator (sync)
# ---------------------------------------------------------------------------

class AttackGenerator:
    """Single-shot attack generator using DeepSeek API (synchronous).

    Good for quick tests and interactive use.
    Uses System Prompt v1 (schema-only, no few-shot examples).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        temperature: float = 0.7,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Set DEEPSEEK_API_KEY or pass --api-key."
            )
        self.base_url = base_url
        self.model = "deepseek-chat"
        self.temperature = temperature

    def generate(self, attack_type: Optional[str] = None) -> Dict:
        """Generate a single malformed UserOperation.

        Args:
            attack_type: One of ATTACK_TYPES, or None for default (integer_overflow_gas).

        Returns:
            Parsed UserOperation dict, or an error dict on failure.
        """
        prompt = (
            f"Generate a malformed UserOperation that targets: {attack_type}."
            if attack_type
            else "Generate a malformed UserOperation that attempts an integer overflow in gas fields."
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_V1},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 1024,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            parsed = _parse_userop_json(raw)
            if parsed is not None:
                return parsed
            return {"error": "JSON parse failed", "raw_response": raw, "attack_type": attack_type}
        except Exception as exc:
            return {"error": str(exc), "attack_type": attack_type}


# ---------------------------------------------------------------------------
# Batch generator (async)
# ---------------------------------------------------------------------------

class BatchAttackGenerator:
    """Batch attack generator using async parallel DeepSeek API calls.

    Uses System Prompt v2 with few-shot examples from real vulnerabilities.
    Includes exponential-backoff retry on rate limits and timeouts.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        temperature: float = 0.9,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Set DEEPSEEK_API_KEY or pass --api-key."
            )
        self.base_url = base_url
        self.model = "deepseek-chat"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = temperature

    async def _call_api(
        self,
        session: aiohttp.ClientSession,
        user_message: str,
        attempt: int = 0,
    ) -> Tuple[str, bool]:
        """Single async API call with retry logic."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_V2},
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
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"], True
                if resp.status == 429 and attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    return await self._call_api(session, user_message, attempt + 1)
                error_body = await resp.text()
                return f"API error {resp.status}: {error_body}", False
        except asyncio.TimeoutError:
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                return await self._call_api(session, user_message, attempt + 1)
            return "Timeout after retries", False
        except Exception as exc:
            return f"Exception: {exc}", False

    async def _generate_one(
        self, session: aiohttp.ClientSession, attack_type: str, index: int
    ) -> Dict:
        """Generate one attack and return result dict with metadata."""
        msg = (
            f"Generate a malformed UserOperation that targets: {attack_type}. "
            "Make it unique and different from standard cases."
        )
        raw, ok = await self._call_api(session, msg)
        result: Dict = {
            "index": index,
            "attack_type": attack_type,
            "timestamp": datetime.now().isoformat(),
            "success": ok,
        }
        if ok:
            parsed = _parse_userop_json(raw)
            result["userop"] = parsed
            result["valid_json"] = parsed is not None
            if parsed is None:
                result["raw_response"] = raw
        else:
            result["userop"] = None
            result["valid_json"] = False
            result["error"] = raw
        return result

    async def generate_batch(
        self,
        count: int = 50,
        attack_types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Generate `count` attacks in parallel, cycling through attack_types."""
        types = attack_types or ATTACK_TYPES
        print(f"Generating {count} attacks ({len(types)} categories, temperature={self.temperature})...")
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._generate_one(session, types[i % len(types)], i + 1)
                for i in range(count)
            ]
            return await asyncio.gather(*tasks)

    def save_dataset(self, attacks: List[Dict], output_path: str) -> str:
        """Save attack dataset to JSON file. Returns the saved path."""
        valid_count = sum(1 for a in attacks if a.get("valid_json"))
        data = {
            "metadata": {
                "total_count": len(attacks),
                "valid_count": valid_count,
                "generation_date": datetime.now().isoformat(),
                "prompt_version": "v2",
                "temperature": self.temperature,
            },
            "attacks": attacks,
        }
        Path(output_path).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Dataset saved \u2192 {output_path}  ({valid_count}/{len(attacks)} valid)")
        return output_path


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_issues: Dict[str, List[str]]


class AttackValidator:
    """Validate AI-generated UserOperations against the ERC-4337 schema.

    Checks required fields, value types, hex/numeric formats, and (in strict
    mode) rejects unknown fields.
    """

    REQUIRED_FIELDS = {
        "sender":                {"pattern": r"^0x[a-fA-F0-9]{40}$"},
        "nonce":                 {"pattern": r"^\d+$"},
        "callData":              {"pattern": r"^0x[a-fA-F0-9]*$"},
        "callGasLimit":          {"pattern": r"^\d+$"},
        "verificationGasLimit": {"pattern": r"^\d+$"},
        "preVerificationGas":    {"pattern": r"^\d+$"},
        "maxFeePerGas":          {"pattern": r"^\d+$"},
        "maxPriorityFeePerGas": {"pattern": r"^\d+$"},
        "signature":             {"pattern": r"^0x[a-fA-F0-9]*$"},
    }
    OPTIONAL_FIELDS = {
        "initCode":         {"pattern": r"^0x[a-fA-F0-9]*$"},
        "paymasterAndData": {"pattern": r"^0x[a-fA-F0-9]*$"},
    }

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def validate(self, userop: Dict) -> ValidationResult:
        """Validate a single UserOperation dict."""
        errors: List[str] = []
        warnings: List[str] = []
        field_issues: Dict[str, List[str]] = {}

        if not isinstance(userop, dict):
            return ValidationResult(False, ["Not a dict"], [], {})

        # Required fields present + string type
        for name, spec in self.REQUIRED_FIELDS.items():
            if name not in userop:
                errors.append(f"Missing required field: {name}")
                field_issues[name] = ["Missing"]
                continue
            val = userop[name]
            if not isinstance(val, str):
                errors.append(f"{name}: expected str, got {type(val).__name__}")
                field_issues[name] = [f"Wrong type: {type(val).__name__}"]
                continue
            if not re.match(spec["pattern"], val):
                errors.append(f"{name}: invalid format '{val}'")
                field_issues.setdefault(name, []).append("Invalid format")

        # Optional fields format check
        for name, spec in self.OPTIONAL_FIELDS.items():
            val = userop.get(name)
            if val is None:
                continue
            if isinstance(val, str) and not re.match(spec["pattern"], val):
                errors.append(f"{name}: invalid format '{val}'")
                field_issues.setdefault(name, []).append("Invalid format")

        # Unknown fields (strict mode)
        if self.strict_mode:
            known = set(self.REQUIRED_FIELDS) | set(self.OPTIONAL_FIELDS)
            unknown = set(userop.keys()) - known
            if unknown:
                warnings.append(f"Unknown fields: {unknown}")
                for f in unknown:
                    field_issues[f] = ["Unknown field"]

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_issues=field_issues,
        )

    def validate_batch(
        self, attacks: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """Validate a list of attack dicts (each with a 'userop' key).

        Returns:
            (valid_attacks, invalid_attacks, statistics)
        """
        valid, invalid = [], []
        for attack in attacks:
            userop = attack.get("userop")
            if not userop:
                invalid.append({**attack, "validation": {"is_valid": False, "errors": ["No userop"]}})
                continue
            r = self.validate(userop)
            annotated = {
                **attack,
                "validation": {
                    "is_valid": r.is_valid,
                    "errors": r.errors,
                    "warnings": r.warnings,
                    "field_issues": r.field_issues,
                },
            }
            (valid if r.is_valid else invalid).append(annotated)

        stats = {
            "total": len(attacks),
            "valid": len(valid),
            "invalid": len(invalid),
            "success_rate_pct": round(len(valid) / len(attacks) * 100, 1) if attacks else 0,
        }
        return valid, invalid, stats

    def save_report(
        self,
        valid: List[Dict],
        invalid: List[Dict],
        stats: Dict,
        output_path: str = "validation_report.json",
    ) -> str:
        """Write a validation report JSON. Returns saved path."""
        error_counts: Dict[str, int] = {}
        for atk in invalid:
            for err in atk.get("validation", {}).get("errors", []):
                key = err.split(":")[0]
                error_counts[key] = error_counts.get(key, 0) + 1

        report = {
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "error_breakdown": error_counts,
            "invalid_sample": [
                {
                    "index": a.get("index"),
                    "attack_type": a.get("attack_type"),
                    "errors": a.get("validation", {}).get("errors", []),
                }
                for a in invalid[:10]
            ],
        }
        Path(output_path).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Validation report saved \u2192 {output_path}")
        return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="ERC-4337 AI fuzzing attack generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python attack_generator.py --mode single
  python attack_generator.py --mode single --attack-type nonce_manipulation
  python attack_generator.py --mode batch --count 50 --output attacks.json
  python attack_generator.py --mode validate --input attacks.json
""",
    )
    p.add_argument(
        "--mode",
        choices=["single", "batch", "validate"],
        default="single",
        help="Operation mode (default: single)",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="DeepSeek API key (overrides DEEPSEEK_API_KEY env var)",
    )
    p.add_argument(
        "--attack-type",
        choices=ATTACK_TYPES,
        default=None,
        help="Attack category for single mode",
    )
    p.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of attacks to generate in batch mode (default: 50)",
    )
    p.add_argument(
        "--output",
        default="attacks_dataset.json",
        help="Output JSON file for batch/validate modes",
    )
    p.add_argument(
        "--input",
        default=None,
        help="Input dataset JSON file for validate mode",
    )
    p.add_argument(
        "--no-strict",
        action="store_true",
        help="Disable strict validation (allow unknown fields)",
    )
    return p


def main() -> None:
    args = _build_parser().parse_args()
    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")

    # ------------------------------------------------------------------ single
    if args.mode == "single":
        if not api_key:
            print("Error: API key required. Set DEEPSEEK_API_KEY or pass --api-key.")
            return
        gen = AttackGenerator(api_key=api_key)
        print(f"Generating single attack (type={args.attack_type or 'default'})...")
        result = gen.generate(args.attack_type)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # ------------------------------------------------------------------ batch
    elif args.mode == "batch":
        if not api_key:
            print("Error: API key required. Set DEEPSEEK_API_KEY or pass --api-key.")
            return
        gen = BatchAttackGenerator(api_key=api_key)
        attacks = asyncio.run(gen.generate_batch(count=args.count))
        valid_n = sum(1 for a in attacks if a.get("valid_json"))
        print(f"Done: {valid_n}/{len(attacks)} valid JSON ({valid_n / len(attacks) * 100:.1f}%)")
        gen.save_dataset(attacks, args.output)

    # --------------------------------------------------------------- validate
    elif args.mode == "validate":
        input_path = args.input or args.output
        if not Path(input_path).exists():
            print(f"Error: input file not found: {input_path}")
            return
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
        attacks = data.get("attacks", data) if isinstance(data, dict) else data
        validator = AttackValidator(strict_mode=not args.no_strict)
        valid, invalid, stats = validator.validate_batch(attacks)
        print(f"Validation: {stats['valid']}/{stats['total']} valid ({stats['success_rate_pct']}%)")
        report_path = args.output.replace(".json", "_report.json")
        validator.save_report(valid, invalid, stats, report_path)


if __name__ == "__main__":
    main()
