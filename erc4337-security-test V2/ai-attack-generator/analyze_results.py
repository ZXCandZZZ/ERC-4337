import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd


def load_dataset(file_path: Path) -> Dict[str, Any]:
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def analyze_attacks(attacks: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not attacks:
        return {
            "total_attacks": 0,
            "success_count": 0,
            "failure_count": 0,
            "success_rate": 0.0,
            "attack_type_distribution": pd.Series(dtype="int64"),
            "attack_type_percentage": pd.Series(dtype="float64"),
            "success_by_type": pd.DataFrame(),
        }

    df = pd.DataFrame(attacks)

    if "success" not in df.columns:
        df["success"] = False
    if "attack_type" not in df.columns:
        df["attack_type"] = "unknown"

    # Normalize success values to strict booleans for stable aggregation
    df["success"] = df["success"].astype(str).str.lower().map({"true": True, "false": False})
    df["success"] = df["success"].fillna(False).astype(bool)

    total_attacks = len(df)
    success_count = int(df["success"].sum())
    failure_count = total_attacks - success_count
    success_rate = (success_count / total_attacks) * 100 if total_attacks > 0 else 0.0

    attack_type_distribution = df["attack_type"].value_counts().sort_values(ascending=False)
    attack_type_percentage = (attack_type_distribution / total_attacks * 100).round(2)

    success_by_type = (
        df.groupby(["attack_type", "success"]).size().unstack(fill_value=0).sort_index()
    )

    # Reindex columns explicitly to avoid boolean mask interpretation in pandas
    success_by_type = success_by_type.reindex(columns=[True, False], fill_value=0)
    success_by_type.columns = ["success", "failure"]

    return {
        "total_attacks": total_attacks,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": round(success_rate, 2),
        "attack_type_distribution": attack_type_distribution,
        "attack_type_percentage": attack_type_percentage,
        "success_by_type": success_by_type,
    }


def generate_attack_distribution_pie(attack_distribution: pd.Series, output_path: Path) -> None:
    plt.figure(figsize=(10, 8))
    plt.pie(
        attack_distribution.values,
        labels=attack_distribution.index,
        autopct="%1.1f%%",
        startangle=140,
        textprops={"fontsize": 9},
    )
    plt.title("Attack Type Distribution")
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def generate_success_failure_bar(success_count: int, failure_count: int, output_path: Path) -> None:
    plt.figure(figsize=(8, 6))
    labels = ["Success", "Failure"]
    values = [success_count, failure_count]
    colors = ["#2ca02c", "#d62728"]

    bars = plt.bar(labels, values, color=colors)
    plt.title("Success vs Failure Count")
    plt.ylabel("Number of Attacks")

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def generate_markdown_report(
    dataset_path: Path,
    metadata: Dict[str, Any],
    analysis: Dict[str, Any],
    pie_chart_path: Path,
    bar_chart_path: Path,
    report_path: Path,
) -> None:
    lines = []
    lines.append("# M2 Batch Generation Analysis Report")
    lines.append("")
    lines.append("## Test Execution & Data Analyst Summary")
    lines.append("")
    lines.append(f"- **Dataset:** `{dataset_path.name}`")
    lines.append(f"- **Generation Date:** `{metadata.get('generation_date', 'N/A')}`")
    lines.append(f"- **Prompt Version:** `{metadata.get('prompt_version', 'N/A')}`")
    lines.append(f"- **Configured Total Count:** `{metadata.get('total_count', 'N/A')}`")
    lines.append(f"- **Valid Count (metadata):** `{metadata.get('valid_count', 'N/A')}`")
    lines.append("")

    lines.append("## Key Statistics")
    lines.append("")
    lines.append(f"- **Total Attacks Analyzed:** {analysis['total_attacks']}")
    lines.append(f"- **Success Count:** {analysis['success_count']}")
    lines.append(f"- **Failure Count:** {analysis['failure_count']}")
    lines.append(f"- **Success Rate:** {analysis['success_rate']:.2f}%")
    lines.append("")

    lines.append("## Attack Type Distribution")
    lines.append("")
    lines.append("| Attack Type | Count | Percentage |")
    lines.append("|---|---:|---:|")
    for attack_type, count in analysis["attack_type_distribution"].items():
        pct = analysis["attack_type_percentage"].loc[attack_type]
        lines.append(f"| `{attack_type}` | {int(count)} | {pct:.2f}% |")
    lines.append("")

    lines.append("## Success/Failure by Attack Type")
    lines.append("")
    lines.append("| Attack Type | Success | Failure |")
    lines.append("|---|---:|---:|")
    for attack_type, row in analysis["success_by_type"].iterrows():
        lines.append(f"| `{attack_type}` | {int(row['success'])} | {int(row['failure'])} |")
    lines.append("")

    lines.append("## Visualizations")
    lines.append("")
    lines.append(f"- Pie Chart (Attack Distribution): `{pie_chart_path.name}`")
    lines.append(f"- Bar Chart (Success/Failure): `{bar_chart_path.name}`")
    lines.append("")

    lines.append("## Analyst Notes")
    lines.append("")
    lines.append(
        "This report summarizes attack generation outcomes for M2 and highlights attack diversity and execution quality metrics required for test execution review."
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="Analyze M2 batch generation results and produce charts/report.")
    parser.add_argument(
        "--input",
        type=Path,
        default=script_dir / "attacks_dataset_50plus.json",
        help="Path to attacks dataset JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=script_dir / "analysis_outputs",
        help="Directory to store generated charts and report",
    )
    args = parser.parse_args()

    input_path = args.input if args.input.is_absolute() else (script_dir / args.input).resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else (script_dir / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_dataset(input_path)
    metadata = data.get("metadata", {})
    attacks = data.get("attacks", [])

    analysis = analyze_attacks(attacks)

    pie_chart_path = output_dir / "attack_distribution_pie.png"
    bar_chart_path = output_dir / "success_failure_bar.png"
    report_path = output_dir / "analysis_summary_report.md"

    if analysis["total_attacks"] > 0:
        generate_attack_distribution_pie(analysis["attack_type_distribution"], pie_chart_path)
        generate_success_failure_bar(
            analysis["success_count"],
            analysis["failure_count"],
            bar_chart_path,
        )

    generate_markdown_report(
        dataset_path=input_path,
        metadata=metadata,
        analysis=analysis,
        pie_chart_path=pie_chart_path,
        bar_chart_path=bar_chart_path,
        report_path=report_path,
    )

    print("Analysis complete.")
    print(f"Report: {report_path}")
    print(f"Pie chart: {pie_chart_path}")
    print(f"Bar chart: {bar_chart_path}")


if __name__ == "__main__":
    main()
