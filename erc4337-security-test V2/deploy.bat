@echo off

call venv\Scripts\activate.bat
python scripts\deploy_contracts.py

pause
