from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.history import ManifestHistoryService


def _render_recent_runs(root: Path) -> None:
    st.markdown("### Recent Runs")
    recent = ManifestHistoryService(root).list_recent(limit=20)
    if not recent:
        st.info("暂无运行记录（streamlit_app/runtime/manifests 为空）")
        return

    rows = []
    for item in recent:
        rc = item.get("returncode")
        rows.append(
            {
                "timestamp": item.get("timestamp", "N/A"),
                "module": item.get("module", "unknown"),
                "type": item.get("type", "unknown"),
                "returncode": rc,
                "status": "PASS" if rc == 0 else ("UNKNOWN" if rc is None else "FAIL"),
                "manifest": item.get("manifest_file", ""),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render() -> None:
    st.subheader("Dashboard")
    st.write("统一入口总览：环境状态、部署状态、测试与分析资产。")

    root = Path(st.session_state.project_root)
    deployments = root / "data" / "deployments.json"
    reports = root / "data" / "reports"
    results = root / "data" / "results"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Deployments", "READY" if deployments.exists() else "MISSING")
    with col2:
        report_count = len(list(reports.glob("*"))) if reports.exists() else 0
        st.metric("Report Files", report_count)
    with col3:
        result_count = len(list(results.glob("*"))) if results.exists() else 0
        st.metric("Test Result Files", result_count)

    st.divider()
    _render_recent_runs(root)

    st.divider()
    st.info("治理提醒：当前编译器存在双轨（Hardhat 0.8.19 vs Deploy Script 0.8.28），请在 Config 页面统一口径。")
