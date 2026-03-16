from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from .config import REPORTS_DIR


class MetricsComputer:
    RANDOM_SEED = 42

    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self.df = pd.DataFrame(results) if results else pd.DataFrame()

    def compute_all_metrics(self) -> Dict[str, float]:
        attacks = [r for r in self.results if r.get("attack_type") != "legitimate"]
        legit = [r for r in self.results if r.get("attack_type") == "legitimate"]

        total = len(self.results)
        total_attacks = len(attacks)
        total_legit = len(legit)

        tp = sum(1 for a in attacks if a.get("status") == "BLOCKED")
        fn = total_attacks - tp

        fp = sum(1 for l in legit if l.get("status") == "BLOCKED")
        tn = total_legit - fp

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        latencies = [
            r.get("execution_time_ms", 0)
            for r in self.results
            if r.get("execution_time_ms")
        ]
        p95 = np.percentile(latencies, 95) if latencies else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "total_attacks": total_attacks,
            "total_legitimate": total_legit,
            "true_positive": tp,
            "false_negative": fn,
            "true_negative": tn,
            "false_positive": fp,
            "tp_rate": round(tp / total_attacks if total_attacks > 0 else 0, 4),
            "fn_rate": round(fn / total_attacks if total_attacks > 0 else 0, 4),
            "fp_rate": round(fp / total_legit if total_legit > 0 else 0, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "p95_latency_ms": round(p95, 2),
        }

    def save_metrics_csv(self, output_path: Optional[str] = None) -> str:
        metrics = self.compute_all_metrics()
        path = (
            Path(output_path)
            if output_path
            else REPORTS_DIR
            / f"metrics_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write("metric,value\n")
            for k, v in metrics.items():
                f.write(f"{k},{v}\n")

        print(f"📊 Metrics saved to: {path}")
        return str(path)


class Visualizer:
    def __init__(self, results: List[Dict[str, Any]]):
        self.df = pd.DataFrame(results) if results else pd.DataFrame()
        self.results = results
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics_computer = MetricsComputer(results)

    def generate_report(self):
        if self.df.empty:
            print("No results to visualize.")
            return

        csv_path = REPORTS_DIR / f"batch_test_v2_{self.timestamp}.csv"
        self.df.to_csv(csv_path, index=False)
        print(f"📄 Raw data saved to: {csv_path}")

        self._plot_status_distribution()
        self._plot_failure_reasons()
        self._plot_metrics_summary()

        self.metrics_computer.save_metrics_csv()

        print(f"📊 Charts saved to: {REPORTS_DIR}")

    def _plot_status_distribution(self):
        plt.figure(figsize=(10, 6))
        status_counts = self.df["status"].value_counts()

        colors = {
            "BLOCKED": "#4CAF50",
            "VULNERABLE": "#F44336",
            "ERROR": "#FFC107",
        }
        plot_colors = [colors.get(x, "#9E9E9E") for x in status_counts.index]

        plt.pie(
            status_counts,
            labels=status_counts.index,
            autopct="%1.1f%%",
            colors=plot_colors,
            startangle=90,
        )
        plt.title(f"ERC-4337 V2 Batch Results (N={len(self.df)})")

        output_path = REPORTS_DIR / f"status_dist_v2_{self.timestamp}.png"
        plt.savefig(output_path)
        plt.close()

    def _plot_failure_reasons(self):
        blocked_df = self.df[self.df["status"] == "BLOCKED"]
        if blocked_df.empty:
            return

        plt.figure(figsize=(12, 8))

        error_counts = (
            blocked_df["error"]
            .fillna("(no reason)")
            .apply(lambda x: str(x)[:70] + "..." if len(str(x)) > 70 else str(x))
            .value_counts()
        )

        error_counts.plot(kind="barh", color="#2196F3")
        plt.title("Top Blocking Reasons (V2 defenses)")
        plt.xlabel("Count")
        plt.tight_layout()

        output_path = REPORTS_DIR / f"defense_reasons_v2_{self.timestamp}.png"
        plt.savefig(output_path)
        plt.close()

    def _plot_metrics_summary(self):
        metrics = self.metrics_computer.compute_all_metrics()

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        ax1 = axes[0]
        confusion = {
            "TP (Blocked Attacks)": metrics["true_positive"],
            "FN (Passed Attacks)": metrics["false_negative"],
            "TN (Passed Legit)": metrics["true_negative"],
            "FP (Blocked Legit)": metrics["false_positive"],
        }
        colors = ["#4CAF50", "#F44336", "#2196F3", "#FFC107"]
        ax1.bar(confusion.keys(), confusion.values(), color=colors)
        ax1.set_title("Confusion Matrix Results")
        ax1.set_ylabel("Count")
        ax1.tick_params(axis="x", rotation=15)

        for i, (k, v) in enumerate(confusion.items()):
            ax1.text(i, v + 0.5, str(v), ha="center", fontweight="bold")

        ax2 = axes[1]
        perf_metrics = {
            "Precision": metrics["precision"],
            "Recall": metrics["recall"],
            "F1 Score": metrics["f1_score"],
            "TP Rate": metrics["tp_rate"],
        }
        bars = ax2.bar(perf_metrics.keys(), perf_metrics.values(), color="#9C27B0")
        ax2.set_title("Performance Metrics")
        ax2.set_ylabel("Score")
        ax2.set_ylim(0, 1)

        for i, (k, v) in enumerate(perf_metrics.items()):
            ax2.text(i, v + 0.02, f"{v:.2f}", ha="center", fontweight="bold")

        plt.tight_layout()
        output_path = REPORTS_DIR / f"metrics_summary_{self.timestamp}.png"
        plt.savefig(output_path)
        plt.close()

        print(f"📊 Metrics chart saved to: {output_path}")


def generate_before_after_comparison(
    m2_results: List[Dict[str, Any]],
    m3_results: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
) -> str:
    output_path = Path(output_dir) if output_dir else REPORTS_DIR
    output_path.mkdir(parents=True, exist_ok=True)

    m2_metrics = MetricsComputer(m2_results).compute_all_metrics()
    m3_metrics = MetricsComputer(m3_results).compute_all_metrics()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax1 = axes[0]
    categories = ["TP Rate", "Precision", "Recall", "F1 Score"]
    m2_values = [
        m2_metrics["tp_rate"],
        m2_metrics["precision"],
        m2_metrics["recall"],
        m2_metrics["f1_score"],
    ]
    m3_values = [
        m3_metrics["tp_rate"],
        m3_metrics["precision"],
        m3_metrics["recall"],
        m3_metrics["f1_score"],
    ]

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax1.bar(
        x - width / 2, m2_values, width, label="M2 Baseline", color="#FF9800"
    )
    bars2 = ax1.bar(x + width / 2, m3_values, width, label="M3 Result", color="#4CAF50")

    ax1.set_xlabel("Metric")
    ax1.set_ylabel("Score")
    ax1.set_title("Before/After Comparison: M2 vs M3")
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend()
    ax1.set_ylim(0, 1)

    ax2 = axes[1]
    latency_data = ["M2 Baseline", "M3 Result"]
    latency_values = [
        m2_metrics.get("p95_latency_ms", 150),
        m3_metrics.get("p95_latency_ms", 125),
    ]
    colors = ["#FF9800", "#4CAF50"]

    bars = ax2.bar(latency_data, latency_values, color=colors)
    ax2.set_xlabel("Version")
    ax2.set_ylabel("P95 Latency (ms)")
    ax2.set_title("P95 Latency Improvement")

    for i, v in enumerate(latency_values):
        ax2.text(i, v + 2, f"{v:.0f}ms", ha="center", fontweight="bold")

    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chart_path = output_path / f"before_after_comparison_{timestamp}.png"
    plt.savefig(chart_path)
    plt.close()

    print(f"📊 Before/After comparison saved to: {chart_path}")
    return str(chart_path)


def generate_attack_distribution_chart(
    results: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
) -> str:
    output_path = Path(output_dir) if output_dir else REPORTS_DIR
    output_path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(results)

    if df.empty or "attack_type" not in df.columns:
        print("No attack type data to visualize")
        return ""

    plt.figure(figsize=(12, 6))

    attack_counts = df["attack_type"].value_counts()
    colors = plt.cm.Set3(np.linspace(0, 1, len(attack_counts)))

    bars = plt.barh(attack_counts.index, attack_counts.values, color=colors)
    plt.xlabel("Count")
    plt.title("Attack Type Distribution")
    plt.tight_layout()

    for i, (idx, val) in enumerate(attack_counts.items()):
        plt.text(val + 0.5, i, str(val), va="center", fontweight="bold")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chart_path = output_path / f"attack_distribution_{timestamp}.png"
    plt.savefig(chart_path)
    plt.close()

    print(f"📊 Attack distribution chart saved to: {chart_path}")
    return str(chart_path)
