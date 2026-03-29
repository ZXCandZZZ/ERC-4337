# config.py
from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.config_store import ConfigStore


def render() -> None:
    st.subheader("Config")
    root = Path(st.session_state.project_root)
    store = ConfigStore(root)
    cfg = store.load()

    st.markdown("### Runtime Configuration")
    rpc_url = st.text_input("RPC URL", value=cfg.get("rpc_url", "http://127.0.0.1:8545"))
    batch_count = st.number_input("Default Batch Count", min_value=0, max_value=1000, value=int(cfg.get("batch_count", 8)))
    ai_default_count = st.number_input("Default AI Count", min_value=1, max_value=1000, value=int(cfg.get("ai_default_count", 50)))
    ai_output = st.text_input("Default AI Raw Output Path", value=cfg.get("ai_dataset_output", "ai-attack-generator/attacks_dataset_500.json"))
    ai_clean_output = st.text_input("Default AI Clean Output Path", value=cfg.get("ai_clean_dataset_output", "ai-attack-generator/attacks_dataset_1200_clean.json"))
    deepseek_api_key = st.text_input("DeepSeek API Key", type="password", value=cfg.get("deepseek_api_key", ""))

    if st.button("Save Configuration"):
        new_cfg = {
            "rpc_url": rpc_url,
            "batch_count": int(batch_count),
            "ai_default_count": int(ai_default_count),
            "ai_dataset_output": ai_output,
            "ai_clean_dataset_output": ai_clean_output,
            "deepseek_api_key": deepseek_api_key,
        }
        store.save(new_cfg)
        st.success("Configuration Saved")