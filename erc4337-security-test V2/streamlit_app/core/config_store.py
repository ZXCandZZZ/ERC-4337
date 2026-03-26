from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "rpc_url": "http://127.0.0.1:8545",
    "batch_count": 8,
    "ai_default_count": 50,
    "ai_dataset_output": "ai-attack-generator/attacks_dataset_500.json",
    "ai_clean_dataset_output": "ai-attack-generator/attacks_dataset_1200_clean.json",
    "deepseek_api_key": "",
}


class ConfigStore:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = self.project_root / "streamlit_app" / "config"
        self.config_path = self.config_dir / "runtime_config.json"

    def load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return DEFAULT_CONFIG.copy()

        with self.config_path.open("r", encoding="utf-8") as f:
            loaded = json.load(f)

        merged = DEFAULT_CONFIG.copy()
        merged.update(loaded)
        return merged

    def save(self, config: Dict[str, Any]) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
