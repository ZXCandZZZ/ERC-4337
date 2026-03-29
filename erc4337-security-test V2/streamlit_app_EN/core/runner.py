# runner.py
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class CommandResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str


class ProcessRunner:
    def __init__(self, cwd: Path):
        self.cwd = cwd

    def run(self, command: List[str], timeout: Optional[int] = None) -> CommandResult:
        try:
            env = os.environ.copy()
            env.setdefault("PYTHONIOENCODING", "utf-8")
            env.setdefault("PYTHONUTF8", "1")

            proc = subprocess.run(
                command,
                cwd=str(self.cwd),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout,
                shell=False,
                env=env,
            )
            return CommandResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
            )
        except FileNotFoundError as e:
            return CommandResult(
                command=command,
                returncode=127,
                stdout="",
                stderr=f"FileNotFoundError: {e}",
            )
        except Exception as e:
            return CommandResult(
                command=command,
                returncode=1,
                stdout="",
                stderr=f"{type(e).__name__}: {e}",
            )

    def stream(self, command: List[str]):
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")

        proc = subprocess.Popen(
            command,
            cwd=str(self.cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            env=env,
        )

        if proc.stdout is not None:
            for line in proc.stdout:
                yield line.rstrip("\n")

        proc.wait()
        yield f"[exit] {proc.returncode}"