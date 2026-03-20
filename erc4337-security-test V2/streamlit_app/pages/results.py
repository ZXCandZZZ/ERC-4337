from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.history import ManifestHistoryService
from core.results import ResultsService


def _show_csv_table(title: str, csv_files: list[Path]) -> None:
    st.markdown(f"### {title}")
    if not csv_files:
        st.info("暂无文件")
        return

    selected = st.selectbox(f"选择 {title} CSV", csv_files, format_func=lambda p: p.name)
    df = pd.read_csv(selected)
    st.dataframe(df, width="stretch")


def _show_images(title: str, image_files: list[Path]) -> None:
    st.markdown(f"### {title}")
    if not image_files:
        st.info("暂无图片")
        return

    max_width = st.slider(
        f"{title} 图片宽度(px)",
        min_value=300,
        max_value=1200,
        value=520,
        step=20,
        key=f"img_width_{title.lower().replace(' ', '_')}",
    )

    cols = st.columns(2)
    for i, p in enumerate(image_files[:8]):
        with cols[i % 2]:
            st.image(str(p), caption=p.name, width=max_width)


def _collect_replay_artifacts(root: Path, manifest_row: dict) -> list[Path]:
    payload = manifest_row.get("raw") or {}
    m_type = payload.get("type")
    module = payload.get("module")

    candidates: list[Path] = []

    reports = root / "data" / "reports"
    sig_results = root / "data" / "results"
    ai_outputs = root / "ai-attack-generator" / "analysis_outputs"
    ai_dataset_dir = root / "ai-attack-generator"

    if module == "deploy":
        dep = root / "data" / "deployments.json"
        if dep.exists():
            candidates.append(dep)

    if module == "test_runner" and m_type == "batch":
        if reports.exists():
            candidates.extend(sorted(reports.glob("batch_test_v2_*.csv"), reverse=True)[:3])
            candidates.extend(sorted(reports.glob("*.png"), reverse=True)[:3])

    if module == "test_runner" and m_type == "signature":
        if sig_results.exists():
            candidates.extend(sorted(sig_results.glob("signature_tests_*.csv"), reverse=True)[:3])
            candidates.extend(sorted(sig_results.glob("signature_tests_*.json"), reverse=True)[:3])

    if module == "test_runner" and m_type == "high_severity":
        vuln_report = root / "data" / "reports" / "vulnerability_report.md"
        if vuln_report.exists():
            candidates.append(vuln_report)

    if module == "ai" and m_type in {"analyze", "validate", "generate"}:
        if ai_outputs.exists():
            candidates.extend(sorted(ai_outputs.glob("*.png"), reverse=True)[:3])
            candidates.extend(sorted(ai_outputs.glob("*.md"), reverse=True)[:3])
        if m_type in {"generate", "validate"} and ai_dataset_dir.exists():
            candidates.extend(sorted(ai_dataset_dir.glob("*.json"), reverse=True)[:2])

    dedup: list[Path] = []
    seen = set()
    for p in candidates:
        key = str(p.resolve())
        if key not in seen and p.exists():
            seen.add(key)
            dedup.append(p)

    return dedup


def _preview_artifact(path: Path) -> None:
    st.markdown(f"- `{path}`")
    suffix = path.suffix.lower()

    try:
        if suffix == ".csv":
            st.dataframe(pd.read_csv(path).head(100), width="stretch")
        elif suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            st.image(str(path), caption=path.name, width="stretch")
        elif suffix in {".md", ".json", ".txt", ".log"}:
            st.code(path.read_text(encoding="utf-8")[:3000])
        else:
            st.caption("该文件类型不做内嵌预览，可通过上方路径定位。")
    except Exception as e:
        st.warning(f"预览失败：{type(e).__name__}: {e}")


def _render_manifest_replay(root: Path) -> None:
    st.markdown("### Manifest 回放（只读）")
    rows = ManifestHistoryService(root).list_recent(limit=200)
    if not rows:
        st.info("暂无 manifest 记录")
        return

    selected = st.selectbox(
        "选择一次运行",
        rows,
        format_func=lambda r: f"{r.get('timestamp', 'N/A')} | {r.get('module', 'unknown')}:{r.get('type', 'unknown')} | rc={r.get('returncode')}",
    )

    payload = selected.get("raw") or {}
    st.json(
        {
            "manifest_file": selected.get("manifest_file"),
            "timestamp": selected.get("timestamp"),
            "module": selected.get("module"),
            "type": selected.get("type"),
            "returncode": selected.get("returncode"),
            "command": payload.get("command"),
            "commands": payload.get("commands"),
        }
    )

    artifacts = _collect_replay_artifacts(root, selected)
    if not artifacts:
        st.warning("未找到关联产物（可能该次仅执行过程无落盘，或产物已被覆盖/清理）。")
        return

    st.markdown("#### 关联产物（推断）")
    for p in artifacts:
        _preview_artifact(p)


def render() -> None:
    st.subheader("Results")
    root = Path(st.session_state.project_root)
    svc = ResultsService(root)

    batch_csv = svc.list_batch_csv()
    batch_png = svc.list_batch_png()
    sig_csv = svc.list_signature_csv()
    ai_outputs = svc.list_ai_outputs()

    _show_csv_table("Batch Test", batch_csv)
    _show_images("Batch Charts", batch_png)

    st.divider()
    _show_csv_table("Signature Test", sig_csv)

    st.divider()
    _show_images("AI Analysis Charts", ai_outputs["png"])

    st.markdown("### AI Markdown Reports")
    if ai_outputs["md"]:
        for p in ai_outputs["md"][:5]:
            st.code(p.read_text(encoding="utf-8")[:4000])
    else:
        st.info("暂无 AI 分析报告")

    st.divider()
    _render_manifest_replay(root)
