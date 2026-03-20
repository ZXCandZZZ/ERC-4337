from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from .runner import ProcessRunner, CommandResult


class DeployService:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.runner = ProcessRunner(project_root)
        self.deployments_path = self.project_root / "data" / "deployments.json"

    def run_deploy(self) -> CommandResult:
        return self.runner.run(["python", "scripts/deploy_contracts.py"])

    def load_deployments(self) -> Dict[str, Any]:
        if not self.deployments_path.exists():
            return {}

        with self.deployments_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def extract_key_addresses(self, deployments: Dict[str, Any]) -> Dict[str, str]:
        contracts = deployments.get("contracts", {})
        return {
            "entryPoint": contracts.get("entryPoint", {}).get("address", "N/A"),
            "simpleAccountFactory": contracts.get("simpleAccountFactory", {}).get("address", "N/A"),
            "simpleAccount": contracts.get("simpleAccount", {}).get("address", "N/A"),
        }
