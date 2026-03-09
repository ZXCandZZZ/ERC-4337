@echo off

call venv\Scripts\activate.bat
python scripts\deploy_attack.py
python tests\test_vulnerability.py

pause
