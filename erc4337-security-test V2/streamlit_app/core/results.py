from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


class ResultsService:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = self.project_root / "data" / "reports"
        self.signature_results_dir = self.project_root / "data" / "results"
        self.ai_analysis_dir = self.project_root / "ai-attack-generator" / "analysis_outputs"

    def list_batch_csv(self) -> List[Path]:
        if not self.reports_dir.exists():
            return []
        return sorted(self.reports_dir.glob("batch_test_v2_*.csv"), reverse=True)

    def list_batch_png(self) -> List[Path]:
        if not self.reports_dir.exists():
            return []
        return sorted(self.reports_dir.glob("*.png"), reverse=True)

    def list_signature_csv(self) -> List[Path]:
        if not self.signature_results_dir.exists():
            return []
        return sorted(self.signature_results_dir.glob("signature_tests_*.csv"), reverse=True)

    def list_signature_json(self) -> List[Path]:
        if not self.signature_results_dir.exists():
            return []
        return sorted(self.signature_results_dir.glob("signature_tests_*.json"), reverse=True)

    def list_ai_outputs(self) -> Dict[str, List[Path]]:
        out = {"png": [], "md": []}
        if not self.ai_analysis_dir.exists():
            return out
        out["png"] = sorted(self.ai_analysis_dir.glob("*.png"), reverse=True)
        out["md"] = sorted(self.ai_analysis_dir.glob("*.md"), reverse=True)
        return out

    @staticmethod
    def load_csv(path: Path) -> pd.DataFrame:
        return pd.read_csv(path)
