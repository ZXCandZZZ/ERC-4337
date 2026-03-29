# deploy.py
from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.deploy import DeployService
from core.history import append_run_history, ensure_run_history, filter_run_history
from core.manifest import RunManifest


def _render_history() -> None:
    items = filter_run_history(st.session_state, module="deploy", limit=50)
    st.markdown("### Deploy History (Current Session)")
    if not items:
        st.info("No Deploy records in current session yet.")
        return

    for i, item in enumerate(items):
        rc = item.get("returncode")
        status = "✅" if rc == 0 else "❌"
        title = f"{status} {item.get('timestamp', 'N/A')} | {item.get('action', 'deploy')} | rc={rc}"
        with st.expander(title, expanded=(i == 0)):
            cmd = item.get("command") or []
            if cmd:
                st.code(" ".join(cmd), language="bash")
            if item.get("manifest_path"):
                st.caption(f"Manifest: {item['manifest_path']}")

            st.markdown("**stdout**")
            st.code(item.get("stdout") or "(no stdout)")
            if item.get("stderr"):
                st.markdown("**stderr**")
                st.code(item.get("stderr"))


def render() -> None:
    st.subheader("Deploy")
    root = Path(st.session_state.project_root)
    deploy_service = DeployService(root)
    manifest = RunManifest(root)
    ensure_run_history(st.session_state)

    if st.button("Run Deployment Script (scripts/deploy_contracts.py)"):
        res = deploy_service.run_deploy()

        st.code(res.stdout or "(no stdout)")
        if res.stderr:
            st.error(res.stderr)

        entry = {
            "module": "deploy",
            "type": "deploy_contracts",
            "command": res.command,
            "returncode": res.returncode,
        }
        path = manifest.record(entry)
        st.caption(f"Manifest: {path}")

        append_run_history(
            st.session_state,
            module="deploy",
            action="deploy_contracts",
            command=res.command,
            returncode=res.returncode,
            stdout=res.stdout,
            stderr=res.stderr,
            manifest_path=str(path),
            max_items=50,
        )

    deployments = deploy_service.load_deployments()
    if deployments:
        st.markdown("### Current Deployment Addresses")
        st.json(deploy_service.extract_key_addresses(deployments))
    else:
        st.warning("data/deployments.json not found yet.")

    st.divider()
    _render_history()