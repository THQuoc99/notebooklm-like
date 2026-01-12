@echo off
echo ========================================
echo Starting BOTH Backend and Frontend
echo ========================================
echo.
echo This will open 2 terminal windows:
echo 1. Backend (FastAPI) on port 8000
echo 2. Frontend (Streamlit) on port 8501
echo.
pause

start cmd /k "cd /d D:\Dự án TT\notebooklm\backend && venv\Scripts\activate.bat && python -m app.main"

timeout /t 5

start cmd /k "cd /d D:\Dự án TT\notebooklm\frontend && venv\Scripts\activate.bat && streamlit run app.py"

echo.
echo ========================================
echo Both servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:8501
echo ========================================
