import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parent


def _load_attack_generator_module():
    module_path = ROOT / "attack_generator.py"
    spec = importlib.util.spec_from_file_location("attack_generator", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_dataset(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("attacks", [])
    return data


def _fingerprint(attack: Dict[str, Any]) -> str:
    userop = attack.get("userop") or {}
    payload = {
        "attack_type": attack.get("attack_type"),
        "should_be_blocked": attack.get("should_be_blocked", True),
        "userop": userop,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def clean_attacks(
    attacks: List[Dict[str, Any]],
    include_legitimate: bool = True,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    attack_generator = _load_attack_generator_module()
    validator = attack_generator.AttackValidator(strict_mode=False)

    cleaned: List[Dict[str, Any]] = []
    seen = set()
    stats = Counter()
    type_counts = Counter()

    for attack in attacks:
        normalized = attack_generator.normalize_attack_record(
            attack,
            attack.get("attack_type"),
        )
        userop = normalized.get("userop")
        if not userop:
            stats["dropped_missing_userop"] += 1
            continue

        if not include_legitimate and normalized.get("should_be_blocked") is False:
            stats["dropped_legitimate"] += 1
            continue

        validation = validator.validate(userop)
        if not validation.is_valid:
            stats["dropped_schema_invalid"] += 1
            continue

        fp = _fingerprint(normalized)
        if fp in seen:
            stats["dropped_duplicate"] += 1
            continue
        seen.add(fp)

        cleaned.append(normalized)
        type_counts[normalized.get("attack_type", "unknown")] += 1
        stats["kept"] += 1

    summary = {
        "total_input": len(attacks),
        "total_clean": len(cleaned),
        "dropped_missing_userop": stats["dropped_missing_userop"],
        "dropped_schema_invalid": stats["dropped_schema_invalid"],
        "dropped_duplicate": stats["dropped_duplicate"],
        "dropped_legitimate": stats["dropped_legitimate"],
        "attack_type_distribution": dict(type_counts),
    }
    return cleaned, summary


def save_clean_dataset(attacks: List[Dict[str, Any]], summary: Dict[str, Any], output_path: Path) -> None:
    payload = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_count": len(attacks),
            "cleaning_summary": summary,
        },
        "attacks": attacks,
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize, validate and deduplicate ERC-4337 AI datasets")
    parser.add_argument("--input", required=True, nargs="+", help="Input dataset JSON files")
    parser.add_argument("--output", required=True, help="Output clean dataset JSON path")
    parser.add_argument("--attacks-only", action="store_true", help="Drop legitimate samples from final dataset")
    args = parser.parse_args()

    merged: List[Dict[str, Any]] = []
    for item in args.input:
        merged.extend(_load_dataset(Path(item)))

    cleaned, summary = clean_attacks(merged, include_legitimate=not args.attacks_only)
    save_clean_dataset(cleaned, summary, Path(args.output))

    print(f"Input attacks: {len(merged)}")
    print(f"Clean attacks: {len(cleaned)}")
    print(f"Dropped missing userop: {summary['dropped_missing_userop']}")
    print(f"Dropped schema invalid: {summary['dropped_schema_invalid']}")
    print(f"Dropped duplicates: {summary['dropped_duplicate']}")
    print(f"Dropped legitimate: {summary['dropped_legitimate']}")
    print(f"Saved clean dataset to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())