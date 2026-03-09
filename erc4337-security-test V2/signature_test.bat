@echo off

call venv\Scripts\activate.bat
python tests\test_signature_security-fixed.py

pause
