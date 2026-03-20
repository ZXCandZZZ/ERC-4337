from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.ai_tools import AIToolService
from core.config_store import ConfigStore
from core.history import append_run_history, ensure_run_history, filter_run_history
from core.manifest import RunManifest


def _render_history() -> None:
    items = filter_run_history(st.session_state, module="ai", limit=50)
    st.markdown("### AI Generator 历史（当前会话）")
    if not items:
        st.info("当前会话暂无 AI Generator 记录")
        return

    for i, item in enumerate(items):
        rc = item.get("returncode")
        status = "✅" if rc == 0 else "❌"
        title = f"{status} {item.get('timestamp', 'N/A')} | {item.get('action', 'ai')} | rc={rc}"
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
    st.subheader("AI Generator")
    root = Path(st.session_state.project_root)
    service = AIToolService(root)
    cfg = ConfigStore(root).load()
    manifest = RunManifest(root)
    ensure_run_history(st.session_state)

    count = st.number_input("Batch 生成数量", min_value=1, max_value=1000, value=int(cfg.get("ai_default_count", 50)))
    output = st.text_input("输出文件", value=cfg.get("ai_dataset_output", "ai-attack-generator/attacks_dataset_50plus.json"))
    api_key = st.text_input("DeepSeek API Key（可留空，优先环境变量）", type="password", value=cfg.get("deepseek_api_key", ""))

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("生成攻击样本"):
            res = service.generate_attacks(count=count, output=output, mode="batch", api_key=api_key)
            st.code(res.stdout or "(no stdout)")
            if res.stderr:
                st.error(res.stderr)
            p = manifest.record({"module": "ai", "type": "generate", "command": res.command, "returncode": res.returncode})
            st.caption(f"Manifest: {p}")

            append_run_history(
                st.session_state,
                module="ai",
                action="generate",
                command=res.command,
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                manifest_path=str(p),
                max_items=50,
            )

    with col2:
        if st.button("校验数据集"):
            res = service.validate_attacks(output)
            st.code(res.stdout or "(no stdout)")
            if res.stderr:
                st.error(res.stderr)
            p = manifest.record({"module": "ai", "type": "validate", "command": res.command, "returncode": res.returncode})
            st.caption(f"Manifest: {p}")

            append_run_history(
                st.session_state,
                module="ai",
                action="validate",
                command=res.command,
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                manifest_path=str(p),
                max_items=50,
            )

    with col3:
        if st.button("分析数据集"):
            out_dir = "ai-attack-generator/analysis_outputs"
            res = service.analyze_dataset(output, out_dir)
            st.code(res.stdout or "(no stdout)")
            if res.stderr:
                st.error(res.stderr)
            p = manifest.record({"module": "ai", "type": "analyze", "command": res.command, "returncode": res.returncode})
            st.caption(f"Manifest: {p}")

            append_run_history(
                st.session_state,
                module="ai",
                action="analyze",
                command=res.command,
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                manifest_path=str(p),
                max_items=50,
            )

    st.divider()
    _render_history()
