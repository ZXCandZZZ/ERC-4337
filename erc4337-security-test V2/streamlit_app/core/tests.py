from __future__ import annotations

from pathlib import Path
from typing import Optional

from .runner import ProcessRunner, CommandResult


class TestService:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.runner = ProcessRunner(project_root)

    def run_batch(self, count: int = 8) -> CommandResult:
        return self.runner.run(["python", "run_batch.py", "--count", str(count)])

    def run_signature(self) -> CommandResult:
        return self.runner.run(["python", "tests/test_signature_security-fixed.py"])

    def run_high_severity(self) -> tuple[CommandResult, CommandResult]:
        deploy_attack_res = self.runner.run(["python", "scripts/deploy_attack.py"])
        vuln_res = self.runner.run(["python", "tests/test_vulnerability.py"])
        return deploy_attack_res, vuln_res

    def run_ai_dataset_test(self, dataset_path: Optional[str] = None) -> CommandResult:
        """M4: Run the AI-generated dataset through the batch validator/test pipeline."""
        input_file = dataset_path or "ai-attack-generator/attacks_dataset_1200_clean.json"
        return self.runner.run([
            "python",
            "ai-attack-generator/attack_generator.py",
            "--mode", "validate",
            "--input", input_file,
            "--no-strict",
        ])

    def run_ai_dataset_chain(
        self,
        dataset_path: Optional[str] = None,
        limit: int = 50,
        include_legitimate: bool = False,
    ) -> CommandResult:
        input_file = dataset_path or "ai-attack-generator/attacks_dataset_1200_clean.json"
        cmd = [
            "python",
            "run_ai_dataset.py",
            "--input", input_file,
            "--limit", str(limit),
        ]
        if include_legitimate:
            cmd.append("--include-legitimate")
        return self.runner.run(cmd)
