@echo off
REM 检查并创建 Python 虚拟环境
if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装 Python 依赖（仅当 requirements.txt 存在）
if exist requirements.txt (
    echo 安装 Python 依赖...
    pip install -r requirements.txt
)

REM 安装指定版本的 solc 编译器（只安装一次）
python -c "import solcx; import os; \
installed = solcx.get_installed_solc_versions(); \
print('已安装版本:', installed); \
import sys; \
sys.exit(0 if '0.8.19' in [str(v) for v in installed] else 1)" 
if errorlevel 1 (
    echo 安装 solc 0.8.19...
    python -c "from solcx import install_solc; install_solc('0.8.19')"
)

REM 安装 npm 依赖（仅当 node_modules 不存在）
if not exist node_modules (
    echo 安装 npm 依赖...
    npm install
)

REM 启动 Hardhat 本地节点
echo 启动 Hardhat 节点...
npx hardhat node

pause
