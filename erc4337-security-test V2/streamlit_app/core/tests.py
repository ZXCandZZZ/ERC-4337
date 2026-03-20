from __future__ import annotations

from pathlib import Path

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
