from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class RunManifest:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.manifest_dir = self.project_root / "streamlit_app" / "runtime" / "manifests"
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

    def record(self, entry: Dict[str, Any]) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.manifest_dir / f"run_{ts}.json"

        payload = {
            "timestamp": datetime.now().isoformat(),
            **entry,
        }

        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
