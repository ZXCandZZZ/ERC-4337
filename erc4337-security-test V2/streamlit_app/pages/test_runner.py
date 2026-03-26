from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.config_store import ConfigStore
from core.history import append_run_history, ensure_run_history, filter_run_history
from core.manifest import RunManifest
from core.tests import TestService


def _apply_test_runner_style() -> None:
    st.markdown(
        """
        <style>
        .stButton > button {
            width: 100%;
        }
        .result-card {
            padding: 0.25rem 0 0.25rem 0;
        }
        .stTextArea textarea {
            white-space: pre-wrap !important;
        }
        div[data-testid="stCodeBlock"] pre {
            white-space: pre-wrap !important;
            word-break: break-word !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_result_block(
    title: str,
    stdout: str,
    stderr: str = "",
    command: list[str] | None = None,
    manifest_path: str | None = None,
    returncode: int | None = None,
    key_base: str | None = None,
) -> None:
    with st.container(border=True):
        st.markdown(f"### {title}")
        if returncode is not None:
            if returncode == 0:
                st.success("执行成功")
            else:
                st.error(f"执行失败 rc={returncode}")

        if command or manifest_path:
            with st.expander("查看技术细节", expanded=False):
                if command:
                    st.caption("命令")
                    st.code(" ".join(command), language="bash")
                if manifest_path:
                    st.caption(f"Manifest: {manifest_path}")

        output_tabs = st.tabs(["stdout", "stderr"])
        stdout_key = f"{key_base or title}_stdout"
        stderr_key = f"{key_base or title}_stderr"
        with output_tabs[0]:
            st.text_area(
                "stdout",
                value=stdout or "(no stdout)",
                height=260,
                disabled=True,
                label_visibility="collapsed",
                key=stdout_key,
            )
        with output_tabs[1]:
            st.text_area(
                "stderr",
                value=stderr or "(no stderr)",
                height=220,
                disabled=True,
                label_visibility="collapsed",
                key=stderr_key,
            )


def _render_test_guide() -> None:
    st.markdown("### 测试说明")
    st.caption("保留原有测试职责，不强行把旧测试改造成统一数据集入口。")

    with st.expander("为什么这些测试看起来像重复，但不建议直接合并", expanded=False):
        st.markdown(
            "\n".join(
                [
                    "- 这几个测试都和 ERC-4337 的 handleOps 相关，但关注层级不同。",
                    "- Signature Test 和 High Severity 属于专项回归测试，目标是验证固定安全假设，不是通用样本执行器。",
                    "- Batch Test 属于基线批量测试，输入是项目内部 AttackVector，不是外部 JSON 数据集。",
                    "- AI Dataset 验证 / 链上执行才是面向外部攻击数据集设计的入口。",
                    "- 直接把旧测试全部改成数据集驱动，会改变原作者写测试时的边界和断言语义。",
                ]
            )
        )

    columns = st.columns(2)
    guides = [
        {
            "title": "Batch Test",
            "goal": "固定基线 + 少量扩展样本，快速看整体拦截率和结果分布。",
            "input": "项目内部 FixedCaseGenerator / MockGenerator 生成的 AttackVector。",
            "dataset": "否。不是外部数据集入口。",
            "when": "想快速看本地部署是否基本正常、报表是否正常产出时运行。",
        },
        {
            "title": "Signature Test",
            "goal": "验证签名校验相关安全逻辑，属于专项回归测试。",
            "input": "脚本内固定构造的 PackedUserOperation。",
            "dataset": "否。不是按通用 JSON 样本协议写的。",
            "when": "改了签名校验、owner、hash、nonce 相关逻辑后运行。",
        },
        {
            "title": "High Severity 场景",
            "goal": "验证特定高危攻击剧本和攻击合约交互结果。",
            "input": "固定脚本 + 预部署攻击合约 + 特定 callData。",
            "dataset": "否。依赖场景前置状态，不是通用样本执行器。",
            "when": "改了攻击合约、部署脚本、关键防护逻辑后运行。",
        },
        {
            "title": "AI Dataset 验证 / 链上执行",
            "goal": "消费外部攻击数据集，做结构校验和链上抽样执行。",
            "input": "外部 JSON 数据集，例如清洗后的 1200 条数据集。",
            "dataset": "是。当前前端唯一的数据集测试入口。",
            "when": "生成新数据集后，先跑验证，再跑链上抽样执行。",
        },
    ]

    for index, guide in enumerate(guides):
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{guide['title']}**")
                st.write(f"测试目标：{guide['goal']}")
                st.write(f"输入来源：{guide['input']}")
                st.write(f"是否支持外部攻击数据集：{guide['dataset']}")
                st.write(f"适用时机：{guide['when']}")

    st.info(
        "建议使用顺序：1) Batch 看基线是否正常 2) Signature / High Severity 看专项安全回归 3) AI Dataset 验证与链上执行看生成数据集是否可用。"
    )


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
            _render_result_block(
                title="历史记录详情",
                stdout=item.get("stdout") or "",
                stderr=item.get("stderr") or "",
                command=cmd,
                manifest_path=item.get("manifest_path"),
                returncode=rc,
                key_base=f"history_{i}_{item.get('timestamp', 'na')}",
            )


def _summarize_output(stdout: str, returncode: int | None) -> None:
    lines = [line.strip() for line in (stdout or "").splitlines() if line.strip()]
    summary_lines = [line for line in lines if line.startswith("Summary:") or line.startswith("Validation:") or line.startswith("Loaded dataset:")]
    if returncode == 0:
        if summary_lines:
            for line in summary_lines[-3:]:
                st.success(line)
        else:
            st.success("执行完成")
    else:
        if summary_lines:
            for line in summary_lines[-3:]:
                st.warning(line)


def render() -> None:
    _apply_test_runner_style()
    st.subheader("Test Runner")
    root = Path(st.session_state.project_root)
    test_service = TestService(root)
    cfg = ConfigStore(root).load()
    manifest = RunManifest(root)
    ensure_run_history(st.session_state)

    st.info(
        "当前前端已接入 5 条测试路径：Batch、Signature、High Severity、AI Dataset 验证、AI Dataset 链上执行。"
    )
    _render_test_guide()

    baseline_tab, regression_tab, dataset_tab = st.tabs(["基线批量", "专项回归", "数据集测试"])

    with baseline_tab:
        with st.container(border=True):
            st.markdown("### Batch Test")
            st.caption("固定基线样本 + 少量扩展样本，快速判断本地部署和基础防护是否正常。")
            batch_count = st.number_input(
                "Batch 随机扩展数量",
                min_value=0,
                max_value=1000,
                value=int(cfg.get("batch_count", 8)),
            )
            if st.button("运行 Batch Test"):
                res = test_service.run_batch(batch_count)
                path = manifest.record({"module": "test_runner", "type": "batch", "command": res.command, "returncode": res.returncode})
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
                _render_result_block(
                    title="Batch Test 结果",
                    stdout=res.stdout,
                    stderr=res.stderr,
                    command=res.command,
                    manifest_path=str(path),
                    returncode=res.returncode,
                    key_base="batch_result",
                )

    with regression_tab:
        with st.container(border=True):
            st.markdown("### Signature Test")
            st.caption("固定签名攻击向量回归。适合在修改签名校验、owner、nonce 逻辑后执行。")
            if st.button("运行 Signature Test"):
                res = test_service.run_signature()
                path = manifest.record({"module": "test_runner", "type": "signature", "command": res.command, "returncode": res.returncode})
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
                _summarize_output(res.stdout, res.returncode)
                _render_result_block(
                    title="Signature Test 结果",
                    stdout=res.stdout,
                    stderr=res.stderr,
                    command=res.command,
                    manifest_path=str(path),
                    returncode=res.returncode,
                    key_base="signature_result",
                )

        with st.container(border=True):
            st.markdown("### High Severity 场景")
            st.caption("先部署攻击合约，再执行固定高危攻击剧本。适合检查特定 exploit 路径。")
            if st.button("运行 High Severity 场景"):
                dres, tres = test_service.run_high_severity()
                path = manifest.record(
                    {
                        "module": "test_runner",
                        "type": "high_severity",
                        "commands": [dres.command, tres.command],
                        "returncodes": [dres.returncode, tres.returncode],
                    }
                )
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
                _summarize_output(combined_stdout, max(dres.returncode, tres.returncode))
                result_tabs = st.tabs(["部署输出", "漏洞场景输出"])
                with result_tabs[0]:
                    _render_result_block(
                        title="deploy_attack.py 结果",
                        stdout=dres.stdout,
                        stderr=dres.stderr,
                        command=dres.command,
                        manifest_path=str(path),
                        returncode=dres.returncode,
                        key_base="deploy_attack_result",
                    )
                with result_tabs[1]:
                    _render_result_block(
                        title="test_vulnerability.py 结果",
                        stdout=tres.stdout,
                        stderr=tres.stderr,
                        command=tres.command,
                        manifest_path=str(path),
                        returncode=tres.returncode,
                        key_base="vulnerability_result",
                    )

    with dataset_tab:
        with st.container(border=True):
            st.markdown("### AI Dataset Test")
            st.caption("面向外部攻击数据集。建议先跑结构验证，再跑链上抽样执行。")
            dataset_path = st.text_input(
                "数据集路径",
                value=cfg.get("ai_clean_dataset_output", "ai-attack-generator/attacks_dataset_1200_clean.json"),
                key="ai_dataset_path_test",
            )

            ai_chain_limit = st.number_input(
                "链上执行数量上限",
                min_value=1,
                max_value=500,
                value=50,
                key="ai_dataset_chain_limit",
            )
            include_legitimate = st.checkbox(
                "链上执行时包含 legitimate 样本",
                value=False,
                key="ai_dataset_chain_include_legitimate",
                help="默认只执行 should_be_blocked=true 的攻击样本，避免合法样本因本地部署环境不匹配而污染结果。",
            )
            if st.button("运行 AI Dataset 验证"):
                res = test_service.run_ai_dataset_test(dataset_path)
                path = manifest.record({"module": "test_runner", "type": "ai_dataset", "command": res.command, "returncode": res.returncode})
                append_run_history(
                    st.session_state,
                    module="test_runner",
                    action="ai_dataset",
                    command=res.command,
                    returncode=res.returncode,
                    stdout=res.stdout,
                    stderr=res.stderr,
                    manifest_path=str(path),
                    max_items=50,
                )
                _summarize_output(res.stdout, res.returncode)
                _render_result_block(
                    title="AI Dataset 验证结果",
                    stdout=res.stdout,
                    stderr=res.stderr,
                    command=res.command,
                    manifest_path=str(path),
                    returncode=res.returncode,
                    key_base="ai_dataset_validate_result",
                )

            if st.button("运行 AI Dataset 链上测试"):
                res = test_service.run_ai_dataset_chain(
                    dataset_path=dataset_path,
                    limit=int(ai_chain_limit),
                    include_legitimate=include_legitimate,
                )
                path = manifest.record({"module": "test_runner", "type": "ai_dataset_chain", "command": res.command, "returncode": res.returncode})
                append_run_history(
                    st.session_state,
                    module="test_runner",
                    action="ai_dataset_chain",
                    command=res.command,
                    returncode=res.returncode,
                    stdout=res.stdout,
                    stderr=res.stderr,
                    manifest_path=str(path),
                    max_items=50,
                )
                _summarize_output(res.stdout, res.returncode)
                _render_result_block(
                    title="AI Dataset 链上测试结果",
                    stdout=res.stdout,
                    stderr=res.stderr,
                    command=res.command,
                    manifest_path=str(path),
                    returncode=res.returncode,
                    key_base="ai_dataset_chain_result",
                )

    st.divider()
    _render_history()
