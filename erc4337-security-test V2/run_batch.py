import argparse
import sys
from pathlib import Path

# Add project root to python path to allow imports
sys.path.append(str(Path(__file__).resolve().parent))

from batch_test.ai_generator import FixedCaseGenerator, MockGenerator
from batch_test.batch_runner import BatchRunner
from batch_test.visualizer import Visualizer


def main() -> int:
    """
    Main entry point for ERC-4337 V2 batch security testing.

    Strategy:
    1) Run fixed deterministic cases first (reproducible baseline)
    2) Then append a small random extension batch
    3) Execute and generate CSV/charts report
    """
    parser = argparse.ArgumentParser(description="ERC-4337 V2 Batch Security Test")
    parser.add_argument(
        "--count",
        type=int,
        default=8,
        help="Number of random extension vectors after fixed cases",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Use random mock extension vectors",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🧪 ERC-4337 V2 Batch Security Test")
    print("=" * 60)

    try:
        print("\n[Phase 1] Building attack vectors...")
        fixed = FixedCaseGenerator().generate_batch()

        random_vectors = []
        if args.mock and args.count > 0:
            random_vectors = MockGenerator().generate_batch(args.count)

        attacks = fixed + random_vectors
        print(f"✅ Fixed cases: {len(fixed)}")
        print(f"✅ Random extension cases: {len(random_vectors)}")
        print(f"✅ Total cases: {len(attacks)}")

        print("\n[Phase 2] Executing attacks...")
        runner = BatchRunner()
        results = runner.execute_batch(attacks)

        print("\n[Phase 3] Generating report...")
        viz = Visualizer(results)
        viz.generate_report()

        blocked = sum(1 for r in results if r["status"] == "BLOCKED")
        vulnerable = sum(1 for r in results if r["status"] == "VULNERABLE")
        failed = sum(1 for r in results if r["verdict"] == "FAIL")

        print("\n" + "=" * 60)
        print(f"Summary: BLOCKED={blocked}, VULNERABLE={vulnerable}, VERDICT_FAIL={failed}")
        print("=" * 60)

        # CI rule: any FAIL verdict returns non-zero
        return 1 if failed > 0 else 0

    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
