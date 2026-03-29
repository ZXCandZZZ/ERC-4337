# ERC-4337 Streamlit Unified Frontend

统一入口用于管理 `erc4337-security-test V2` 的部署、测试、AI 生成与结果分析。

## 功能

- Environment：RPC 检查、Hardhat 节点启动/停止、依赖检查
- Deploy：执行 `scripts/deploy_contracts.py` 并展示关键地址
- Test Runner：批测 / 签名专项 / 高危场景测试
- AI Generator：攻击样本生成、校验、分析
- Results：读取并展示 CSV/PNG/Markdown 报告
- Config：统一配置管理（RPC、批测数量、AI 参数、API Key）

## 启动

1. 准备依赖

```bash
pip install -r requirements.txt
```

2. 启动前端

```bash
streamlit run streamlit_app/app.py
```

或使用 Windows 脚本：

```bat
run_streamlit.bat
```

## 目录结构

- `streamlit_app/app.py`：总入口
- `streamlit_app/core/`：执行/环境/部署/测试/AI/结果/配置/manifest 服务层
- `streamlit_app/pages/`：页面渲染层
- `streamlit_app/config/runtime_config.json`：运行配置
- `streamlit_app/runtime/manifests/`：每次执行记录
