import argparse
import csv
import importlib.util
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from eth_account import Account
from web3 import Web3, exceptions


ROOT = Path(__file__).resolve().parent
DATASET_DEFAULT = ROOT / "ai-attack-generator" / "attacks_dataset_500.json"
DEPLOYMENTS_PATH = ROOT / "data" / "deployments.json"
REPORTS_DIR = ROOT / "data" / "reports"
RPC_URL = "http://127.0.0.1:8545"
SUBMIT_TX_GAS = 3_000_000


def _load_attack_generator_module():
    module_path = ROOT / "ai-attack-generator" / "attack_generator.py"
    spec = importlib.util.spec_from_file_location("attack_generator", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_dataset(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hex_to_bytes(value: str) -> bytes:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"Invalid hex string: {value!r}")
    payload = value[2:]
    if len(payload) % 2 == 1:
        payload = f"0{payload}"
    return bytes.fromhex(payload)


def _pack_uint128_pair(lower_128: int, upper_128: int) -> bytes:
    lower_128 = lower_128 & ((1 << 128) - 1)
    upper_128 = upper_128 & ((1 << 128) - 1)
    packed = (upper_128 << 128) | lower_128
    return packed.to_bytes(32, "big")


def _userop_to_tuple(userop: Dict[str, str]) -> Tuple[Any, ...]:
    sender = Web3.to_checksum_address(userop["sender"])
    nonce = int(userop["nonce"])
    init_code = _hex_to_bytes(userop.get("initCode", "0x"))
    call_data = _hex_to_bytes(userop.get("callData", "0x"))
    pre_verification_gas = int(userop["preVerificationGas"])
    signature = _hex_to_bytes(userop.get("signature", "0x"))
    paymaster_and_data = _hex_to_bytes(userop.get("paymasterAndData", "0x"))

    if "accountGasLimits" in userop and "gasFees" in userop:
        account_gas_limits = _hex_to_bytes(userop["accountGasLimits"])
        gas_fees = _hex_to_bytes(userop["gasFees"])
    else:
        account_gas_limits = _pack_uint128_pair(
            int(userop["verificationGasLimit"]),
            int(userop["callGasLimit"]),
        )
        gas_fees = _pack_uint128_pair(
            int(userop["maxPriorityFeePerGas"]),
            int(userop["maxFeePerGas"]),
        )

    return (
        sender,
        nonce,
        init_code,
        call_data,
        account_gas_limits,
        pre_verification_gas,
        gas_fees,
        paymaster_and_data,
        signature,
    )


def _extract_exception_info(exc: Exception) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "exception_type": type(exc).__name__,
        "message": str(exc),
        "args": list(exc.args) if hasattr(exc, "args") else [],
        "code": None,
        "data": None,
        "raw": None,
    }
    first_arg = exc.args[0] if getattr(exc, "args", None) else None
    if isinstance(first_arg, dict):
        payload["raw"] = first_arg
        payload["code"] = first_arg.get("code")
        payload["data"] = first_arg.get("data")
        if isinstance(first_arg.get("message"), str):
            payload["message"] = first_arg["message"]
    elif isinstance(first_arg, str):
        payload["raw"] = first_arg
    return payload


def _is_revert_like_exception(exc: Exception) -> bool:
    info = _extract_exception_info(exc)
    blob = " | ".join(
        [
            str(info.get("message") or "").lower(),
            str(info.get("data") or "").lower(),
            str(info.get("raw") or "").lower(),
        ]
    )
    return any(
        key in blob
        for key in ["revert", "reverted", "vm exception", "execution reverted", "failedop", "aa23", "custom error"]
    )


def _is_client_side_rejection(exc: Exception) -> bool:
    blob = str(exc).lower()
    return any(
        key in blob
        for key in [
            "abi not found",
            "not compatible with type",
            "provided arguments are not valid",
            "could not identify the intended function",
        ]
    )


class AIDatasetChainRunner:
    def __init__(self) -> None:
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to Hardhat node at {RPC_URL}")

        deployments = json.loads(DEPLOYMENTS_PATH.read_text(encoding="utf-8"))
        self.entrypoint = self.w3.eth.contract(
            address=deployments["contracts"]["entryPoint"]["address"],
            abi=deployments["contracts"]["entryPoint"]["abi"],
        )
        self.deployer = Account.from_key(
            "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        )
        self.attacker = Account.from_key(
            "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
        )

    def run_single(self, attack: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        userop = attack.get("userop")
        expected_block = bool(attack.get("should_be_blocked", True))
        result = {
            "index": attack.get("index"),
            "attack_type": attack.get("attack_type", "unknown"),
            "expected": "BLOCKED" if expected_block else "ALLOWED",
            "status": "ERROR",
            "verdict": "FAIL",
            "error": None,
            "tx_hash": None,
        }

        try:
            op = _userop_to_tuple(userop)
            tx_hash = self.entrypoint.functions.handleOps([op], self.attacker.address).transact(
                {
                    "from": self.deployer.address,
                    "gas": SUBMIT_TX_GAS,
                }
            )
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            blocked = receipt.status == 0
            result["tx_hash"] = tx_hash.hex()
            result["status"] = "BLOCKED" if blocked else "VULNERABLE"
            result["verdict"] = "PASS" if blocked == expected_block else "FAIL"
            result["gas_used"] = receipt.gasUsed
        except exceptions.ContractLogicError as exc:
            result["status"] = "BLOCKED"
            result["verdict"] = "PASS" if expected_block else "FAIL"
            result["error"] = str(exc)
        except Exception as exc:
            if _is_revert_like_exception(exc) or _is_client_side_rejection(exc):
                result["status"] = "BLOCKED"
                result["verdict"] = "PASS" if expected_block else "FAIL"
            else:
                result["status"] = "ERROR"
                result["verdict"] = "FAIL"
            result["error"] = str(exc)

        result["execution_time_ms"] = round((time.time() - start) * 1000, 2)
        return result


def _save_results(results: List[Dict[str, Any]]) -> Tuple[Path, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORTS_DIR / f"ai_dataset_chain_{timestamp}.json"
    csv_path = REPORTS_DIR / f"ai_dataset_chain_{timestamp}.csv"

    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    fieldnames = [
        "index",
        "attack_type",
        "expected",
        "status",
        "verdict",
        "tx_hash",
        "gas_used",
        "execution_time_ms",
        "error",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({name: row.get(name) for name in fieldnames})

    return json_path, csv_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AI-generated ERC-4337 dataset on-chain")
    parser.add_argument("--input", default=str(DATASET_DEFAULT), help="Path to dataset JSON")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of attacks to execute")
    parser.add_argument(
        "--include-legitimate",
        action="store_true",
        help="Also execute attacks marked should_be_blocked=false",
    )
    args = parser.parse_args()

    attack_generator = _load_attack_generator_module()
    validator = attack_generator.AttackValidator(strict_mode=False)
    dataset = _load_dataset(Path(args.input))
    source_attacks = dataset.get("attacks", dataset)

    normalized_attacks: List[Dict[str, Any]] = []
    skipped_invalid = 0
    skipped_legitimate = 0

    for attack in source_attacks:
        normalized = attack_generator.normalize_attack_record(
            attack,
            attack.get("attack_type"),
        )
        userop = normalized.get("userop")
        if not userop:
            skipped_invalid += 1
            continue

        validation = validator.validate(userop)
        if not validation.is_valid:
            skipped_invalid += 1
            continue

        if not args.include_legitimate and normalized.get("should_be_blocked") is False:
            skipped_legitimate += 1
            continue

        normalized_attacks.append(normalized)
        if len(normalized_attacks) >= max(0, args.limit):
            break

    runner = AIDatasetChainRunner()
    print(f"Loaded dataset: {args.input}")
    print(f"Selected attacks for chain execution: {len(normalized_attacks)}")
    print(f"Skipped invalid attacks: {skipped_invalid}")
    print(f"Skipped legitimate attacks: {skipped_legitimate}")

    results = [runner.run_single(attack) for attack in normalized_attacks]
    blocked = sum(1 for item in results if item["status"] == "BLOCKED")
    vulnerable = sum(1 for item in results if item["status"] == "VULNERABLE")
    failed = sum(1 for item in results if item["verdict"] == "FAIL")
    errors = sum(1 for item in results if item["status"] == "ERROR")

    json_path, csv_path = _save_results(results)
    print(f"Results saved to: {json_path}")
    print(f"Results saved to: {csv_path}")
    print(f"Summary: BLOCKED={blocked}, VULNERABLE={vulnerable}, ERROR={errors}, VERDICT_FAIL={failed}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())