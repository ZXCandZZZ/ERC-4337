from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.config_store import ConfigStore
from core.history import append_run_history, ensure_run_history, filter_run_history
from core.manifest import RunManifest
from core.tests import TestService


def _render_history() -> None:
    items = filter_run_history(st.session_state, module="test_runner", limit=50)
    st.markdown("### Test Runner 历史（当前会话）")
    if not items:
        st.info("当前会话暂无 Test Runner 记录")
        return

    for i, item in enumerate(items):
        rc = item.get("returncode")
        status = "✅" if rc == 0 else "❌"
        title = f"{status} {item.get('timestamp', 'N/A')} | {item.get('action', 'test')} | rc={rc}"
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
    st.subheader("Test Runner")
    root = Path(st.session_state.project_root)
    test_service = TestService(root)
    cfg = ConfigStore(root).load()
    manifest = RunManifest(root)
    ensure_run_history(st.session_state)

    batch_count = st.number_input("Batch 随机扩展数量", min_value=0, max_value=1000, value=int(cfg.get("batch_count", 8)))

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("运行 Batch Test"):
            res = test_service.run_batch(batch_count)
            st.code(res.stdout or "(no stdout)")
            if res.stderr:
                st.error(res.stderr)
            path = manifest.record({"module": "test_runner", "type": "batch", "command": res.command, "returncode": res.returncode})
            st.caption(f"Manifest: {path}")

            append_run_history(
                st.session_state,
                module="test_runner",
                action="batch",
                command=res.command,
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                manifest_path=str(path),
                max_items=50,
            )

    with col2:
        if st.button("运行 Signature Test"):
            res = test_service.run_signature()
            st.code(res.stdout or "(no stdout)")
            if res.stderr:
                st.error(res.stderr)
            path = manifest.record({"module": "test_runner", "type": "signature", "command": res.command, "returncode": res.returncode})
            st.caption(f"Manifest: {path}")

            append_run_history(
                st.session_state,
                module="test_runner",
                action="signature",
                command=res.command,
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                manifest_path=str(path),
                max_items=50,
            )

    with col3:
        if st.button("运行 High Severity 场景"):
            dres, tres = test_service.run_high_severity()
            st.markdown("**deploy_attack.py 输出**")
            st.code(dres.stdout or "(no stdout)")
            if dres.stderr:
                st.error(dres.stderr)

            st.markdown("**test_vulnerability.py 输出**")
            st.code(tres.stdout or "(no stdout)")
            if tres.stderr:
                st.error(tres.stderr)

            path = manifest.record(
                {
                    "module": "test_runner",
                    "type": "high_severity",
                    "commands": [dres.command, tres.command],
                    "returncodes": [dres.returncode, tres.returncode],
                }
            )
            st.caption(f"Manifest: {path}")

            combined_stdout = "\n\n".join(
                [
                    "[deploy_attack.py]",
                    dres.stdout or "(no stdout)",
                    "[test_vulnerability.py]",
                    tres.stdout or "(no stdout)",
                ]
            )
            combined_stderr = "\n\n".join(
                [
                    "[deploy_attack.py]",
                    dres.stderr or "",
                    "[test_vulnerability.py]",
                    tres.stderr or "",
                ]
            ).strip()

            append_run_history(
                st.session_state,
                module="test_runner",
                action="high_severity",
                command=["python", "scripts/deploy_attack.py", "&&", "python", "tests/test_vulnerability.py"],
                returncode=max(dres.returncode, tres.returncode),
                stdout=combined_stdout,
                stderr=combined_stderr,
                manifest_path=str(path),
                max_items=50,
            )

    st.divider()
    _render_history()
