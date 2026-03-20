from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.environment import EnvironmentManager
from core.config_store import ConfigStore


def render() -> None:
    st.subheader("Environment")
    root = Path(st.session_state.project_root)
    env_mgr = EnvironmentManager(root)
    cfg = ConfigStore(root).load()

    rpc_url = st.text_input("RPC URL", value=cfg.get("rpc_url", "http://127.0.0.1:8545"))

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("检查 RPC"):
            state = env_mgr.check_rpc(rpc_url)
            if state.rpc_ok:
                st.success(f"RPC 可用，Chain ID = {state.chain_id}")
            else:
                st.error(f"RPC 不可用：{state.error}")

    with col2:
        if st.button("启动 Hardhat 节点"):
            resp = env_mgr.start_hardhat_node()
            st.info(f"{resp}")

    with col3:
        if st.button("停止 Hardhat 节点"):
            resp = env_mgr.stop_hardhat_node()
            st.info(f"{resp}")

    st.divider()
    if st.button("检查依赖状态"):
        checks = env_mgr.check_dependencies()
        st.json(checks)
