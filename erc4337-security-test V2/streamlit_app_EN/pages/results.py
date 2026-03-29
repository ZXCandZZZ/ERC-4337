# results.py
from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import streamlit as st

from core.history import ManifestHistoryService
from core.results import ResultsService


def _apply_results_style() -> None:
    st.markdown(
        """
        <style>
        .results-hero {
            padding: 1rem 1.1rem;
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 16px;
            background: linear-gradient(180deg, rgba(248,249,252,0.95) 0%, rgba(255,255,255,0.98) 100%);
            margin-bottom: 1rem;
        }
        .results-card {
            padding: 0.9rem 1rem;
            border: 1px solid rgba(49, 51, 63, 0.10);
            border-radius: 14px;
            background: #ffffff;
            min-height: 132px;
        }
        .results-label {
            font-size: 0.92rem;
            color: #6b7280;
            margin-bottom: 0.35rem;
        }
        .results-value {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 0.25rem;
            color: #111827;
        }
        .results-note {
            font-size: 0.9rem;
            color: #4b5563;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _extract_stamp(path: Path) -> str:
    match = re.search(r"(\d{8}_\d{6})", path.name)
    if not match:
        return "Unknown"
    stamp = match.group(1)
    return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]} {stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}"


def _render_intro(batch_csv: list[Path], sig_csv: list[Path], ai_chain_csv: list[Path], ai_outputs: dict[str, list[Path]]) -> None:
    st.markdown(
        """
        <div class="results-hero">
            <h3 style="margin:0 0 0.35rem 0;">Results Center</h3>
            <div style="color:#4b5563; font-size:0.98rem; line-height:1.6;">
                Centralized view for various test and analysis artifacts.<br>
                Page is divided by test type: baseline batch, signature focus, AI dataset on-chain execution, AI analysis, and full run record replay.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = st.columns(4)
    summaries = [
        ("Batch Results", str(len(batch_csv)), batch_csv[0].name if batch_csv else "No batch test artifacts"),
        ("Signature Results", str(len(sig_csv)), sig_csv[0].name if sig_csv else "No signature test artifacts"),
        ("AI Chain Results", str(len(ai_chain_csv)), ai_chain_csv[0].name if ai_chain_csv else "No on-chain execution artifacts"),
        (
            "AI Analysis Artifacts",
            str(len(ai_outputs.get("png", [])) + len(ai_outputs.get("md", []))),
            (ai_outputs.get("md", []) or ai_outputs.get("png", []) or [Path("None")])[0].name if (ai_outputs.get("md") or ai_outputs.get("png")) else "No analysis artifacts",
        ),
    ]

    for column, (label, value, note) in zip(cards, summaries):
        column.markdown(
            f"""
            <div class="results-card">
                <div class="results-label">{label}</div>
                <div class="results-value">{value}</div>
                <div class="results-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_section_intro(title: str, desc: str, latest: list[Path] | None = None) -> None:
    st.markdown(f"### {title}")
    st.caption(desc)
    if latest:
        st.info(f"Latest artifact: {latest[0].name} | Time: {_extract_stamp(latest[0])}")


def _show_csv_table(title: str, csv_files: list[Path]) -> None:
    if not csv_files:
        st.info("No files yet")
        return

    selected = st.selectbox(f"Select {title} CSV", csv_files, format_func=lambda p: p.name)
    df = pd.read_csv(selected)
    summary_cols = st.columns(3)
    summary_cols[0].metric("Record Count", str(len(df)))
    summary_cols[1].metric("Field Count", str(len(df.columns)))
    summary_cols[2].metric("File Time", _extract_stamp(selected))
    st.dataframe(df, width="stretch", height=460)


def _show_images(title: str, image_files: list[Path]) -> None:
    if not image_files:
        st.info("No images yet")
        return

    max_width = st.slider(
        f"{title} Image Width(px)",
        min_value=300,
        max_value=1200,
        value=520,
        step=20,
        key=f"img_width_{title.lower().replace(' ', '_')}",
    )

    cols = st.columns(2)
    for i, path in enumerate(image_files[:8]):
        with cols[i % 2]:
            st.image(str(path), caption=path.name, width=max_width)


def _show_json_preview(title: str, json_files: list[Path]) -> None:
    if not json_files:
        st.info("No files yet")
        return

    selected = st.selectbox(f"Select {title} JSON", json_files, format_func=lambda p: p.name)
    st.caption(f"File Time: {_extract_stamp(selected)}")
    st.code(selected.read_text(encoding="utf-8")[:5000])


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

    if module == "test_runner" and m_type == "batch" and reports.exists():
        candidates.extend(sorted(reports.glob("batch_test_v2_*.csv"), reverse=True)[:3])
        candidates.extend(sorted(reports.glob("*.png"), reverse=True)[:3])

    if module == "test_runner" and m_type == "signature" and sig_results.exists():
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

    if module == "test_runner" and m_type == "ai_dataset_chain" and reports.exists():
        candidates.extend(sorted(reports.glob("ai_dataset_chain_*.csv"), reverse=True)[:3])
        candidates.extend(sorted(reports.glob("ai_dataset_chain_*.json"), reverse=True)[:3])

    dedup: list[Path] = []
    seen = set()
    for path in candidates:
        key = str(path.resolve())
        if key not in seen and path.exists():
            seen.add(key)
            dedup.append(path)

    return dedup


def _preview_artifact(path: Path) -> None:
    st.markdown(f"- {path}")
    suffix = path.suffix.lower()

    try:
        if suffix == ".csv":
            st.dataframe(pd.read_csv(path).head(100), width="stretch")
        elif suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            st.image(str(path), caption=path.name, width="stretch")
        elif suffix in {".md", ".json", ".txt", ".log"}:
            st.code(path.read_text(encoding="utf-8")[:3000])
        else:
            st.caption("This file type is not previewed inline; locate via the path above.")
    except Exception as exc:
        st.warning(f"Preview failed: {type(exc).__name__}: {exc}")


def _render_manifest_replay(root: Path) -> None:
    rows = ManifestHistoryService(root).list_recent(limit=200)
    if not rows:
        st.info("No manifest records yet")
        return

    selected = st.selectbox(
        "Select a Run",
        rows,
        format_func=lambda row: f"{row.get('timestamp', 'N/A')} | {row.get('module', 'unknown')}:{row.get('type', 'unknown')} | rc={row.get('returncode')}",
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
        st.warning("No related artifacts found; this run may not have saved outputs, or artifacts may have been overwritten or cleaned up.")
        return

    st.markdown("#### Related Artifacts")
    for path in artifacts:
        _preview_artifact(path)


def render() -> None:
    _apply_results_style()
    st.subheader("Results")
    root = Path(st.session_state.project_root)
    svc = ResultsService(root)

    batch_csv = svc.list_batch_csv()
    batch_png = svc.list_batch_png()
    sig_csv = svc.list_signature_csv()
    sig_json = svc.list_signature_json()
    ai_chain_csv = svc.list_ai_chain_csv()
    ai_chain_json = svc.list_ai_chain_json()
    ai_outputs = svc.list_ai_outputs()

    _render_intro(batch_csv, sig_csv, ai_chain_csv, ai_outputs)

    tabs = st.tabs(["Baseline Batch", "Signature Focus", "AI On-Chain Execution", "AI Analysis", "Run Replay"])

    with tabs[0]:
        _render_section_intro(
            "Batch Test",
            "View raw CSV and charts from baseline batch testing. Good for quickly checking if the protection baseline is stable.",
            batch_csv,
        )
        _show_csv_table("Batch Test", batch_csv)
        st.divider()
        st.markdown("#### Charts")
        st.caption("Display status distribution, reason distribution, and metric summary charts here.")
        _show_images("Batch Charts", batch_png)

    with tabs[1]:
        _render_section_intro(
            "Signature Test",
            "View signature-focused regression test results. CSV for quick browsing, JSON for full details.",
            sig_csv,
        )
        _show_csv_table("Signature Test", sig_csv)
        st.divider()
        st.markdown("#### Raw JSON")
        _show_json_preview("Signature Test", sig_json)

    with tabs[2]:
        _render_section_intro(
            "AI Dataset Chain",
            "View on-chain execution results for AI attack datasets. CSV for summaries, JSON for individual sample inspection.",
            ai_chain_csv,
        )
        _show_csv_table("AI Dataset Chain", ai_chain_csv)
        st.divider()
        st.markdown("#### Raw JSON")
        _show_json_preview("AI Dataset Chain", ai_chain_json)

    with tabs[3]:
        latest_ai = ai_outputs["md"] or ai_outputs["png"]
        _render_section_intro(
            "AI Analysis",
            "View AI dataset analysis charts and Markdown reports, suitable for seeing attack type distribution and overall quality overview.",
            latest_ai,
        )
        st.markdown("#### Charts")
        _show_images("AI Analysis Charts", ai_outputs["png"])
        st.divider()
        st.markdown("#### Markdown Reports")
        if ai_outputs["md"]:
            selected_md = st.selectbox(
                "Select AI Markdown Report",
                ai_outputs["md"][:10],
                format_func=lambda p: p.name,
            )
            st.caption("Text reports generated by analysis scripts, good for quick conclusions.")
            st.markdown(selected_md.read_text(encoding="utf-8")[:6000])
        else:
            st.info("No AI analysis reports yet")

    with tabs[4]:
        _render_section_intro(
            "Manifest Replay",
            "Replay all run records, including Batch, Signature, High Severity, AI Generator, and dataset tests. Useful for investigating what was produced in a particular run.",
        )
        _render_manifest_replay(root)