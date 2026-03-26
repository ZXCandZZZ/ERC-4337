import argparse
import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


attack_generator = _load_module("attack_generator", ROOT / "attack_generator.py")
clean_dataset_mod = _load_module("clean_dataset", ROOT / "clean_dataset.py")


def _load_attacks(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("attacks", [])
    return data


def _hash_bytes(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _make_address(label: str) -> str:
    return "0x" + _hash_bytes(label)[:40]


def _mutate_decimal(text: str, seed: int, minimum: int = 0) -> str:
    base = int(text)
    bump = (seed % 997) + 1
    return str(max(minimum, base + bump))


def _mutate_bytes_field(text: str, seed_label: str, min_bytes: int = 0) -> str:
    if not isinstance(text, str) or not text.startswith("0x"):
        return text
    suffix = _hash_bytes(seed_label)
    payload = text[2:]
    if len(payload) < min_bytes * 2:
        payload = payload.ljust(min_bytes * 2, "0")
    if len(payload) >= 8:
        payload = payload[:-8] + suffix[:8]
    else:
        payload = (payload + suffix)[: max(min_bytes * 2, 8)]
    return "0x" + payload


def _mutate_call_data(text: str, attack_type: str, seed_label: str) -> str:
    if not isinstance(text, str) or not text.startswith("0x"):
        return text
    payload = text[2:]
    suffix = _hash_bytes(seed_label)
    if attack_type == "calldata_bomb":
        target = 4096
        expanded = (payload + suffix * 200)[: target * 2]
        return "0x" + expanded
    if attack_type in {"malformed_calldata", "reentrancy_attack", "transient_storage_collision"}:
        expanded = (payload + suffix[:64])[: max(len(payload), 72)]
        return "0x" + expanded
    return "0x" + ((payload + suffix[:16]) if payload else suffix[:16])


def _mutate_userop(userop: Dict[str, str], attack_type: str, variant: int, seed_index: int) -> Dict[str, str]:
    mutated = dict(userop)
    label = f"{attack_type}:{seed_index}:{variant}"

    if attack_type not in {"invalid_address", "combo_initcode_invalid_addr"}:
        mutated["sender"] = _make_address(label)

    if attack_type == "invalid_address":
        if variant % 2 == 0:
            mutated["sender"] = "0x0000000000000000000000000000000000000000"
        else:
            mutated["sender"] = _make_address(label)
    elif attack_type == "combo_initcode_invalid_addr":
        mutated["sender"] = "0x0000000000000000000000000000000000000000" if variant % 3 == 0 else _make_address(label)

    if "nonce" in mutated:
        mutated["nonce"] = _mutate_decimal(str(mutated["nonce"]), seed_index * 17 + variant, 0)
    if "preVerificationGas" in mutated:
        mutated["preVerificationGas"] = _mutate_decimal(str(mutated["preVerificationGas"]), seed_index * 29 + variant, 0)

    if "accountGasLimits" in mutated:
        mutated["accountGasLimits"] = attack_generator._normalize_packed_bytes32(
            _mutate_bytes_field(mutated["accountGasLimits"], f"agl:{label}", min_bytes=32)
        )
    if "gasFees" in mutated:
        mutated["gasFees"] = attack_generator._normalize_packed_bytes32(
            _mutate_bytes_field(mutated["gasFees"], f"fees:{label}", min_bytes=32)
        )

    if "initCode" in mutated:
        mutated["initCode"] = _mutate_bytes_field(mutated["initCode"], f"init:{label}", min_bytes=20)
    if "callData" in mutated:
        mutated["callData"] = _mutate_call_data(mutated["callData"], attack_type, f"call:{label}")
    if "paymasterAndData" in mutated:
        min_bytes = 20 if attack_type in {"paymaster_exploit", "paymaster_postop_griefing", "combo_gas_paymaster", "combo_factory_paymaster"} else 0
        mutated["paymasterAndData"] = _mutate_bytes_field(mutated["paymasterAndData"], f"pm:{label}", min_bytes=min_bytes)
    if "signature" in mutated:
        sig = mutated["signature"]
        if attack_type in {"signature_forgery", "combo_sig_nonce"}:
            mutated["signature"] = _mutate_bytes_field(sig, f"sig:{label}", min_bytes=1)
        else:
            mutated["signature"] = _mutate_bytes_field(sig, f"sig:{label}", min_bytes=65)

    return mutated


def _seed_pool(source_paths: List[Path]) -> List[Dict[str, Any]]:
    seeds: List[Dict[str, Any]] = []
    for path in source_paths:
        if path.exists():
            seeds.extend(_load_attacks(path))

    # Always include curated static seeds for new categories.
    gen = attack_generator.BatchAttackGenerator(api_key="placeholder")
    seeds.extend(gen.get_legitimate_samples())
    seeds.extend(gen.get_paymaster_attacks())
    seeds.extend(gen.get_m4_static_attacks())
    return seeds


def build_dataset(source_paths: List[Path], target_count: int, include_legitimate: bool) -> Dict[str, Any]:
    seeds = _seed_pool(source_paths)
    cleaned_seeds, seed_summary = clean_dataset_mod.clean_attacks(
        seeds,
        include_legitimate=include_legitimate,
    )

    expanded: List[Dict[str, Any]] = []
    for index, attack in enumerate(cleaned_seeds):
        expanded.append(attack)
        attack_type = attack.get("attack_type", "unknown")
        userop = attack.get("userop") or {}
        for variant in range(1, 8):
            clone = dict(attack)
            clone["index"] = len(expanded) + 1
            clone["timestamp"] = datetime.now().isoformat()
            clone["description"] = f"{attack.get('description', attack_type)} | variant {variant}"
            clone["userop"] = _mutate_userop(userop, attack_type, variant, index)
            expanded.append(attack_generator.normalize_attack_record(clone, attack_type))

    final_clean, final_summary = clean_dataset_mod.clean_attacks(
        expanded,
        include_legitimate=include_legitimate,
    )

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for attack in final_clean:
        grouped.setdefault(attack.get("attack_type", "unknown"), []).append(attack)

    final_attacks: List[Dict[str, Any]] = []
    attack_types = sorted(grouped.keys())
    cursor = 0
    while len(final_attacks) < target_count and attack_types:
        attack_type = attack_types[cursor % len(attack_types)]
        bucket = grouped.get(attack_type, [])
        if bucket:
            final_attacks.append(bucket.pop(0))
        else:
            attack_types.remove(attack_type)
            continue
        cursor += 1

    for index, attack in enumerate(final_attacks, start=1):
        attack["index"] = index

    final_type_counts: Dict[str, int] = {}
    for attack in final_attacks:
        attack_type = attack.get("attack_type", "unknown")
        final_type_counts[attack_type] = final_type_counts.get(attack_type, 0) + 1

    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "target_count": target_count,
            "actual_count": len(final_attacks),
            "sources": [str(path) for path in source_paths if path.exists()],
            "seed_summary": seed_summary,
            "final_clean_summary": final_summary,
            "final_attack_type_distribution": final_type_counts,
        },
        "attacks": final_attacks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a large clean ERC-4337 attack dataset from curated and AI seeds")
    parser.add_argument("--output", required=True, help="Output dataset path")
    parser.add_argument("--target-count", type=int, default=1200, help="Desired clean dataset size")
    parser.add_argument("--include-legitimate", action="store_true", help="Keep legitimate baseline samples")
    parser.add_argument(
        "--source",
        nargs="*",
        default=[str(ROOT / "attacks_dataset_500.json")],
        help="Seed dataset paths",
    )
    args = parser.parse_args()

    payload = build_dataset(
        [Path(item) for item in args.source],
        target_count=args.target_count,
        include_legitimate=args.include_legitimate,
    )
    output_path = Path(args.output)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Built dataset: {output_path}")
    print(f"Actual count: {payload['metadata']['actual_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())