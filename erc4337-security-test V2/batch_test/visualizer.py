from datetime import datetime
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd

from .config import REPORTS_DIR


class Visualizer:
    def __init__(self, results: List[Dict[str, Any]]):
        self.df = pd.DataFrame(results)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_report(self):
        if self.df.empty:
            print("No results to visualize.")
            return

        csv_path = REPORTS_DIR / f"batch_test_v2_{self.timestamp}.csv"
        self.df.to_csv(csv_path, index=False)
        print(f"📄 Raw data saved to: {csv_path}")

        self._plot_status_distribution()
        self._plot_failure_reasons()

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

        error_counts = blocked_df["error"].fillna("(no reason)").apply(
            lambda x: str(x)[:70] + "..." if len(str(x)) > 70 else str(x)
        ).value_counts()

        error_counts.plot(kind="barh", color="#2196F3")
        plt.title("Top Blocking Reasons (V2 defenses)")
        plt.xlabel("Count")
        plt.tight_layout()

        output_path = REPORTS_DIR / f"defense_reasons_v2_{self.timestamp}.png"
        plt.savefig(output_path)
        plt.close()
