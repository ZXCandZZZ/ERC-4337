@echo off
REM Check and create Python virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install Python dependencies (only if requirements.txt exists)
if exist requirements.txt (
    echo Installing Python dependencies...
    pip install -r requirements.txt
)

REM Install specified version of solc compiler (install only once)
echo Checking for solc 0.8.28...
python -c "import solcx; installed = solcx.get_installed_solc_versions(); print('Installed versions:', installed); import sys; sys.exit(0 if '0.8.28' in [str(v) for v in installed] else 1)"
if errorlevel 1 (
    echo Installing solc 0.8.28...
    python -c "from solcx import install_solc; install_solc('0.8.28')"
)

REM Install npm dependencies (only if node_modules doesn't exist)
if not exist node_modules (
    echo Installing npm dependencies...
    npm install
)

REM Start Hardhat local node
echo Starting Hardhat node...
npx hardhat node

pause