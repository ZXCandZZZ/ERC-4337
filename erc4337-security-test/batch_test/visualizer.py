import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict, Any
from .config import REPORTS_DIR

class Visualizer:
    def __init__(self, results: List[Dict[str, Any]]):
        self.df = pd.DataFrame(results)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def generate_report(self):
        if self.df.empty:
            print("No results to visualize.")
            return

        # 1. Save raw data
        csv_path = REPORTS_DIR / f'batch_test_{self.timestamp}.csv'
        self.df.to_csv(csv_path, index=False)
        print(f"📄 Raw data saved to: {csv_path}")
        
        # 2. Generate Charts
        self._plot_status_distribution()
        self._plot_failure_reasons()
        
        print(f"📊 Charts saved to: {REPORTS_DIR}")

    def _plot_status_distribution(self):
        """Pie chart of Blocked vs Vulnerable"""
        plt.figure(figsize=(10, 6))
        status_counts = self.df['status'].value_counts()
        
        colors = {'BLOCKED': '#4CAF50', 'VULNERABLE': '#F44336', 'ERROR': '#FFC107'}
        # Map colors to existing statuses
        plot_colors = [colors.get(x, '#9E9E9E') for x in status_counts.index]
        
        plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', colors=plot_colors, startangle=90)
        plt.title(f'Attack Simulation Results (N={len(self.df)})')
        
        output_path = REPORTS_DIR / f'status_dist_{self.timestamp}.png'
        plt.savefig(output_path)
        plt.close()

    def _plot_failure_reasons(self):
        """Bar chart of error messages for blocked attacks"""
        blocked_df = self.df[self.df['status'] == 'BLOCKED']
        if blocked_df.empty:
            return
            
        plt.figure(figsize=(12, 8))
        # Extract main error reason (simplify long error strings)
        error_counts = blocked_df['error'].apply(lambda x: str(x)[:50] + '...' if len(str(x)) > 50 else str(x)).value_counts()
        
        error_counts.plot(kind='barh', color='#2196F3')
        plt.title('Top Blocking Reasons (Defense Mechanisms)')
        plt.xlabel('Count')
        plt.tight_layout()
        
        output_path = REPORTS_DIR / f'defense_reasons_{self.timestamp}.png'
        plt.savefig(output_path)
        plt.close()
