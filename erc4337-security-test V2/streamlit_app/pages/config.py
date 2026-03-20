from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.config_store import ConfigStore


def render() -> None:
    st.subheader("Config")
    root = Path(st.session_state.project_root)
    store = ConfigStore(root)
    cfg = store.load()

    st.markdown("### 运行配置")
    rpc_url = st.text_input("RPC URL", value=cfg.get("rpc_url", "http://127.0.0.1:8545"))
    batch_count = st.number_input("默认 Batch Count", min_value=0, max_value=1000, value=int(cfg.get("batch_count", 8)))
    ai_default_count = st.number_input("默认 AI Count", min_value=1, max_value=1000, value=int(cfg.get("ai_default_count", 50)))
    ai_output = st.text_input("默认 AI 输出路径", value=cfg.get("ai_dataset_output", "ai-attack-generator/attacks_dataset_50plus.json"))
    deepseek_api_key = st.text_input("DeepSeek API Key", type="password", value=cfg.get("deepseek_api_key", ""))

    if st.button("保存配置"):
        new_cfg = {
            "rpc_url": rpc_url,
            "batch_count": int(batch_count),
            "ai_default_count": int(ai_default_count),
            "ai_dataset_output": ai_output,
            "deepseek_api_key": deepseek_api_key,
        }
        store.save(new_cfg)
        st.success("配置已保存")

