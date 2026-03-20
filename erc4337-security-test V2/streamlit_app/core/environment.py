from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from urllib.request import Request, urlopen

from .runner import ProcessRunner


@dataclass
class NodeState:
    rpc_ok: bool
    chain_id: Optional[int]
    error: Optional[str]


class EnvironmentManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.runner = ProcessRunner(project_root)
        self.runtime_dir = project_root / "streamlit_app" / "runtime"
        self.node_pid_file = self.runtime_dir / "hardhat_node_pid.json"

    def check_rpc(self, rpc_url: str) -> NodeState:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_chainId",
            "params": [],
            "id": 1,
        }
        req = Request(
            rpc_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=2) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                chain_hex = raw.get("result")
                chain_id = int(chain_hex, 16) if isinstance(chain_hex, str) else None
                return NodeState(rpc_ok=True, chain_id=chain_id, error=None)
        except Exception as e:
            return NodeState(rpc_ok=False, chain_id=None, error=str(e))

    def check_dependencies(self) -> Dict[str, str]:
        checks: Dict[str, str] = {
            "venv_exists": str((self.project_root / "venv").exists()),
            "requirements_exists": str((self.project_root / "requirements.txt").exists()),
            "node_modules_exists": str((self.project_root / "node_modules").exists()),
            "python_path": sys.executable,
            "which_node": shutil.which("node") or "",
            "which_npm": shutil.which("npm") or "",
            "which_npx": shutil.which("npx") or "",
            "which_npx_cmd": shutil.which("npx.cmd") or "",
        }

        py_res = self.runner.run(["python", "--version"])
        npm_res = self.runner.run(["npm", "--version"])

        checks["python_ok"] = str(py_res.returncode == 0)
        checks["python_version"] = (py_res.stdout or py_res.stderr).strip()

        checks["npm_ok"] = str(npm_res.returncode == 0)
        checks["npm_version_or_error"] = (npm_res.stdout or npm_res.stderr).strip()

        if npm_res.returncode != 0:
            npx_cmd_res = self.runner.run(["npx.cmd", "--version"])
            checks["npx_cmd_ok"] = str(npx_cmd_res.returncode == 0)
            checks["npx_cmd_version_or_error"] = (npx_cmd_res.stdout or npx_cmd_res.stderr).strip()

        return checks

    def start_hardhat_node(self) -> Dict[str, str]:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        diagnostics = {
            "python_executable": sys.executable,
            "cwd": str(self.project_root),
            "path_prefix": os.environ.get("PATH", "")[:300],
            "which_node": shutil.which("node") or "",
            "which_npm": shutil.which("npm") or "",
            "which_npx": shutil.which("npx") or "",
            "which_npx_cmd": shutil.which("npx.cmd") or "",
        }

        # Already running: return quickly
        rpc_state = self.check_rpc("http://127.0.0.1:8545")
        if rpc_state.rpc_ok:
            return {
                "status": "already_running",
                "chain_id": str(rpc_state.chain_id),
                "diagnostics": json.dumps(diagnostics, ensure_ascii=False),
            }

        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0
        attempts = [
            ["npx", "hardhat", "node"],
            ["npx.cmd", "hardhat", "node"],
            ["npm", "exec", "hardhat", "node"],
        ]

        errors = []
        for cmd in attempts:
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(self.project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creation_flags,
                )

                # Wait briefly and verify RPC became reachable
                time.sleep(1.2)
                state = self.check_rpc("http://127.0.0.1:8545")
                if state.rpc_ok:
                    self.node_pid_file.write_text(
                        json.dumps({"pid": proc.pid, "command": cmd}, indent=2),
                        encoding="utf-8",
                    )
                    return {
                        "status": "started",
                        "pid": str(proc.pid),
                        "command": " ".join(cmd),
                        "chain_id": str(state.chain_id),
                        "diagnostics": json.dumps(diagnostics, ensure_ascii=False),
                    }

                errors.append(f"{' '.join(cmd)} launched but RPC not ready")
            except FileNotFoundError as e:
                errors.append(f"{' '.join(cmd)} -> FileNotFoundError: {e}")
            except Exception as e:
                errors.append(f"{' '.join(cmd)} -> {type(e).__name__}: {e}")

        return {
            "status": "error",
            "message": "Failed to start Hardhat node with all fallback commands.",
            "errors": " || ".join(errors),
            "diagnostics": json.dumps(diagnostics, ensure_ascii=False),
        }

    def stop_hardhat_node(self) -> Dict[str, str]:
        if not self.node_pid_file.exists():
            return {"status": "not_found", "message": "No tracked Hardhat PID file."}

        payload = json.loads(self.node_pid_file.read_text(encoding="utf-8"))
        pid = int(payload.get("pid", -1))
        if pid <= 0:
            return {"status": "invalid", "message": "Invalid PID in file."}

        kill_res = self.runner.run(["taskkill", "/PID", str(pid), "/T", "/F"])
        if kill_res.returncode == 0:
            self.node_pid_file.unlink(missing_ok=True)
            return {"status": "stopped", "pid": str(pid)}

        return {"status": "error", "pid": str(pid), "message": kill_res.stderr or kill_res.stdout}
