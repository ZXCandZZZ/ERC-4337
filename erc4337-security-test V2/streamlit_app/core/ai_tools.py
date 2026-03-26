from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from .runner import ProcessRunner, CommandResult


class AIToolService:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.runner = ProcessRunner(project_root)
        self.ai_dir = self.project_root / "ai-attack-generator"

    def generate_attacks(
        self,
        count: int,
        output: str,
        mode: str = "batch",
        attack_type: str | None = None,
        api_key: str | None = None,
        extra_args: Optional[List[str]] = None,
        clean_output: str | None = None,
        clean_target_count: int | None = None,
        include_legitimate: bool = True,
    ) -> CommandResult:
        cmd = ["python", "ai-attack-generator/attack_generator.py", "--mode", mode]

        if mode == "batch":
            cmd += ["--count", str(count), "--output", output]
        elif mode == "single" and attack_type:
            cmd += ["--attack-type", attack_type]

        if extra_args:
            cmd += extra_args

        env_api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if env_api_key:
            cmd += ["--api-key", env_api_key]

        primary = self.runner.run(cmd)
        if primary.returncode != 0 or not clean_output or mode != "batch":
            return primary

        clean_cmd = [
            "python",
            "ai-attack-generator/build_attack_dataset.py",
            "--output",
            clean_output,
            "--target-count",
            str(clean_target_count or count),
            "--source",
            output,
        ]
        if include_legitimate:
            clean_cmd.append("--include-legitimate")

        cleaned = self.runner.run(clean_cmd)
        return CommandResult(
            command=primary.command + ["&&"] + cleaned.command,
            returncode=max(primary.returncode, cleaned.returncode),
            stdout=(primary.stdout or "") + "\n\n[clean_dataset]\n" + (cleaned.stdout or ""),
            stderr="\n\n".join(part for part in [primary.stderr, cleaned.stderr] if part),
        )

    def validate_attacks(self, input_file: str) -> CommandResult:
        return self.runner.run(
            [
                "python",
                "ai-attack-generator/attack_generator.py",
                "--mode",
                "validate",
                "--input",
                input_file,
            ]
        )

    def analyze_dataset(self, input_file: str, output_dir: str) -> CommandResult:
        # analyze_results.py resolves relative paths against its own script_dir.
        # If we pass "ai-attack-generator/xxx.json", it becomes duplicated:
        # ai-attack-generator/ai-attack-generator/xxx.json.
        input_arg = input_file.replace("\\", "/")
        output_arg = output_dir.replace("\\", "/")

        if input_arg.startswith("ai-attack-generator/"):
            input_arg = input_arg[len("ai-attack-generator/") :]
        if output_arg.startswith("ai-attack-generator/"):
            output_arg = output_arg[len("ai-attack-generator/") :]

        return self.runner.run(
            [
                "python",
                "ai-attack-generator/analyze_results.py",
                "--input",
                input_arg,
                "--output-dir",
                output_arg,
            ]
        )
