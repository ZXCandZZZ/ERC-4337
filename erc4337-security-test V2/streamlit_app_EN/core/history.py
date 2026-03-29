# history.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, MutableMapping


def _safe_iso(ts: str | None) -> datetime:
    if not ts:
        return datetime.min
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return datetime.min


def ensure_run_history(state: MutableMapping[str, Any]) -> List[Dict[str, Any]]:
    if "run_history" not in state or not isinstance(state.get("run_history"), list):
        state["run_history"] = []
    return state["run_history"]


def append_run_history(
    state: MutableMapping[str, Any],
    *,
    module: str,
    action: str,
    command: List[str] | None = None,
    returncode: int | None = None,
    stdout: str = "",
    stderr: str = "",
    manifest_path: str | None = None,
    max_items: int = 50,
) -> Dict[str, Any]:
    history = ensure_run_history(state)

    item = {
        "timestamp": datetime.now().isoformat(),
        "module": module,
        "action": action,
        "command": command or [],
        "returncode": returncode,
        "stdout": stdout or "",
        "stderr": stderr or "",
        "manifest_path": manifest_path or "",
    }
    history.insert(0, item)

    if len(history) > max_items:
        del history[max_items:]

    state["run_history"] = history
    return item


def filter_run_history(state: MutableMapping[str, Any], module: str, limit: int = 50) -> List[Dict[str, Any]]:
    history = ensure_run_history(state)
    return [h for h in history if h.get("module") == module][:limit]


class ManifestHistoryService:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.manifest_dir = self.project_root / "streamlit_app" / "runtime" / "manifests"

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.manifest_dir.exists():
            return []

        rows: List[Dict[str, Any]] = []
        for p in self.manifest_dir.glob("run_*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    continue
            except Exception:
                continue

            ts = data.get("timestamp")
            row = {
                "manifest_file": p.name,
                "manifest_path": str(p),
                "timestamp": ts,
                "module": data.get("module", "unknown"),
                "type": data.get("type", data.get("action", "unknown")),
                "returncode": self._extract_returncode(data),
                "raw": data,
            }
            rows.append(row)

        rows.sort(key=lambda x: _safe_iso(x.get("timestamp")), reverse=True)
        return rows[:limit]

    @staticmethod
    def _extract_returncode(payload: Dict[str, Any]) -> int | None:
        if isinstance(payload.get("returncode"), int):
            return payload["returncode"]

        rcs = payload.get("returncodes")
        if isinstance(rcs, list) and rcs:
            int_rcs = [r for r in rcs if isinstance(r, int)]
            if not int_rcs:
                return None
            return max(int_rcs)

        return None