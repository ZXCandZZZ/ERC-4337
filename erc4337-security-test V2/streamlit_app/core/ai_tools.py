from __future__ import annotations

import os
from pathlib import Path

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
    ) -> CommandResult:
        cmd = ["python", "ai-attack-generator/attack_generator.py", "--mode", mode]

        if mode == "batch":
            cmd += ["--count", str(count), "--output", output]
        elif mode == "single" and attack_type:
            cmd += ["--attack-type", attack_type]

        env_api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if env_api_key:
            cmd += ["--api-key", env_api_key]

        return self.runner.run(cmd)

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
