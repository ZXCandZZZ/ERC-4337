# ai_generator.py
from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.ai_tools import AIToolService
from core.config_store import ConfigStore
from core.history import append_run_history, ensure_run_history, filter_run_history
from core.manifest import RunManifest


ATTACK_TYPES = [
    "integer_overflow_gas",
    "invalid_address",
    "malformed_calldata",
    "signature_forgery",
    "nonce_manipulation",
    "gas_limit_attack",
    "paymaster_exploit",
    "reentrancy_attack",
    "bundler_griefing",
    "initcode_exploit",
    "cross_chain_replay",
    "aggregator_bypass",
    "access_list_poisoning",
    "calldata_bomb",
    "time_range_abuse",
    "eip7702_auth_bypass",
    "paymaster_postop_griefing",
    "factory_stake_bypass",
    "transient_storage_collision",
    "combo_sig_nonce",
    "combo_gas_paymaster",
    "combo_initcode_invalid_addr",
    "combo_7702_time_range",
    "combo_factory_paymaster",
    "legitimate",
]


def _render_result(stdout: str, stderr: str, command: list[str], manifest_path: str, returncode: int, key_base: str) -> None:
    with st.container(border=True):
        if returncode == 0:
            st.success("Execution Successful")
        else:
            st.error(f"Execution Failed rc={returncode}")

        with st.expander("View Technical Details", expanded=False):
            st.caption("Command")
            st.code(" ".join(command), language="bash")
            st.caption(f"Manifest: {manifest_path}")

        tabs = st.tabs(["stdout", "stderr"])
        with tabs[0]:
            st.text_area(
                "stdout",
                value=stdout or "(no stdout)",
                height=240,
                disabled=True,
                label_visibility="collapsed",
                key=f"{key_base}_stdout",
            )
        with tabs[1]:
            st.text_area(
                "stderr",
                value=stderr or "(no stderr)",
                height=220,
                disabled=True,
                label_visibility="collapsed",
                key=f"{key_base}_stderr",
            )


def _summarize_ai_output(stdout: str, returncode: int) -> None:
    lines = [line.strip() for line in (stdout or "").splitlines() if line.strip()]
    summary_lines = [line for line in lines if line.startswith("Validation:") or line.startswith("Analysis complete.") or line.startswith("Saved") or line.startswith("Report:")]
    if returncode == 0:
        if summary_lines:
            for line in summary_lines[-4:]:
                st.success(line)
        else:
            st.success("Execution Completed")
    else:
        st.error(f"Execution Failed rc={returncode}")


def _render_history() -> None:
    items = filter_run_history(st.session_state, module="ai", limit=50)
    st.markdown("### AI Generator History (Current Session)")
    if not items:
        st.info("No AI Generator records in current session yet.")
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

    st.markdown("#### Generation Configuration")
    count = st.number_input("Batch Generation Count", min_value=1, max_value=2000, value=int(cfg.get("ai_default_count", 50)))
    output = st.text_input("Raw Output File", value=cfg.get("ai_dataset_output", "ai-attack-generator/attacks_dataset_500.json"))
    api_key = st.text_input("DeepSeek API Key (optional, environment variable takes precedence)", type="password", value=cfg.get("deepseek_api_key", ""))
    auto_clean = st.checkbox(
        "Auto-build clean dataset after generation",
        value=True,
        help="Still only one generation button; after enabled, it will automatically normalize, validate, and deduplicate the raw data to produce a ready-to-use clean dataset.",
    )
    prompt_version = st.selectbox(
        "Prompt Version",
        options=["v4", "v3", "v2"],
        index=0,
        help="v4=extended attack categories + combo attacks (recommended), v3=Chain-of-Thought, v2=Few-Shot",
    )
    clean_output = st.text_input(
        "Clean Output File",
        value=cfg.get("ai_clean_dataset_output", "ai-attack-generator/attacks_dataset_1200_clean.json"),
        disabled=not auto_clean,
    )
    clean_target_count = st.number_input(
        "Clean Target Count",
        min_value=100,
        max_value=5000,
        value=max(1000, int(count)),
        disabled=not auto_clean,
    )
    include_static = st.checkbox(
        "Include Static Samples (M3 paymaster + M4 extensions)",
        value=True,
        help="Append predefined static attack samples before AI-generated dataset to increase diversity.",
    )

    st.caption("It is recommended to use the clean output file as the testing target dataset; analysis and validation will also prioritize the clean file by default.")
    analysis_target = clean_output if auto_clean else output

    with st.expander("Generation Strategy Notes", expanded=False):
        st.markdown("- Batch Mode: ~85% single-vector attacks + 15% combo attacks")
        st.markdown("- Raw Output: preserves direct AI-generated results")
        st.markdown("- Clean Output: used for testing, validation, and on-chain execution")

    if st.button("Generate Attack Samples"):
        extra_args: list[str] = ["--prompt-version", prompt_version]
        if not include_static:
            extra_args.append("--no-static")
        res = service.generate_attacks(
            count=count,
            output=output,
            mode="batch",
            api_key=api_key,
            extra_args=extra_args,
            clean_output=clean_output if auto_clean else None,
            clean_target_count=int(clean_target_count),
            include_legitimate=True,
        )
        p = manifest.record({"module": "ai", "type": "generate", "command": res.command, "returncode": res.returncode})

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
        _summarize_ai_output(res.stdout, res.returncode)
        _render_result(res.stdout, res.stderr, res.command, str(p), res.returncode, "ai_generate")

    if st.button("Validate Dataset"):
        res = service.validate_attacks(analysis_target)
        p = manifest.record({"module": "ai", "type": "validate", "command": res.command, "returncode": res.returncode})

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
        _summarize_ai_output(res.stdout, res.returncode)
        _render_result(res.stdout, res.stderr, res.command, str(p), res.returncode, "ai_validate")

    if st.button("Analyze Dataset"):
        out_dir = "ai-attack-generator/analysis_outputs"
        res = service.analyze_dataset(analysis_target, out_dir)
        p = manifest.record({"module": "ai", "type": "analyze", "command": res.command, "returncode": res.returncode})

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
        _summarize_ai_output(res.stdout, res.returncode)
        _render_result(res.stdout, res.stderr, res.command, str(p), res.returncode, "ai_analyze")

    st.divider()
    _render_history()