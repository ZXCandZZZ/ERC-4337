from pathlib import Path
import sys

import streamlit as st

# Ensure streamlit_app package path is importable when launched from project root.
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from pages import dashboard, environment, deploy, test_runner, ai_generator, results, config


st.set_page_config(
    page_title="ERC-4337 Security Control Panel",
    page_icon="🛡️",
    layout="wide",
)


st.title("🛡️ ERC-4337 Security Unified Frontend")
st.caption("Unified control panel for deployment, testing, AI analysis, and results visualization in ERC-4337 security testing.")

# Session bootstrap
if "project_root" not in st.session_state:
    st.session_state.project_root = str((APP_DIR.parent).resolve())

if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"

PAGES = {
    "Dashboard": dashboard.render,
    "Environment": environment.render,
    "Deploy": deploy.render,
    "Test Runner": test_runner.render,
    "AI Generator": ai_generator.render,
    "Results": results.render,
    "Config": config.render,
}

with st.sidebar:
    st.header("导航")
    selected = st.radio("选择页面", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.active_page))
    st.session_state.active_page = selected

    st.divider()
    st.markdown("**工作目录**")
    st.code(st.session_state.project_root)

PAGES[st.session_state.active_page]()
