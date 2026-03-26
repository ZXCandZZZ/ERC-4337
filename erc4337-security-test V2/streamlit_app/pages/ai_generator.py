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
            st.success("执行成功")
        else:
            st.error(f"执行失败 rc={returncode}")

        with st.expander("查看技术细节", expanded=False):
            st.caption("命令")
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
            st.success("执行完成")
    else:
        st.error(f"执行失败 rc={returncode}")


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

    st.markdown("#### 生成配置")
    count = st.number_input("Batch 生成数量", min_value=1, max_value=2000, value=int(cfg.get("ai_default_count", 50)))
    output = st.text_input("原始输出文件", value=cfg.get("ai_dataset_output", "ai-attack-generator/attacks_dataset_500.json"))
    api_key = st.text_input("DeepSeek API Key（可留空，优先环境变量）", type="password", value=cfg.get("deepseek_api_key", ""))
    auto_clean = st.checkbox(
        "生成后自动构建 clean dataset",
        value=True,
        help="仍然只有一个生成按钮；勾选后会在生成原始数据后自动做规范化、校验和去重，产出可直接用于测试的 clean dataset。",
    )
    prompt_version = st.selectbox(
        "Prompt 版本",
        options=["v4", "v3", "v2"],
        index=0,
        help="v4=扩展攻击类别+组合攻击(推荐), v3=Chain-of-Thought, v2=Few-Shot",
    )
    clean_output = st.text_input(
        "Clean 输出文件",
        value=cfg.get("ai_clean_dataset_output", "ai-attack-generator/attacks_dataset_1200_clean.json"),
        disabled=not auto_clean,
    )
    clean_target_count = st.number_input(
        "Clean 目标数量",
        min_value=100,
        max_value=5000,
        value=max(1000, int(count)),
        disabled=not auto_clean,
    )
    include_static = st.checkbox(
        "包含静态样本（M3 paymaster + M4 扩展）",
        value=True,
        help="在 AI 生成的数据集前追加预定义静态攻击样本，增加数据集多样性",
    )

    st.caption("当前推荐测试目标数据集使用 clean 输出文件；分析和校验默认也会优先针对 clean 文件。")
    analysis_target = clean_output if auto_clean else output

    with st.expander("生成策略说明", expanded=False):
        st.markdown("- Batch 模式：约 85% 单向量攻击 + 15% 组合攻击")
        st.markdown("- 原始输出用于保留 AI 直接生成结果")
        st.markdown("- Clean 输出用于测试、验证和链上执行")

    if st.button("生成攻击样本"):
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

    if st.button("校验数据集"):
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

    if st.button("分析数据集"):
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
