@echo off

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Launch unified Streamlit frontend
streamlit run streamlit_app/app.py

pause
