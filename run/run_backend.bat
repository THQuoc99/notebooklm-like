@echo off
echo ========================================
echo Starting Backend Server
echo ========================================
cd /d "D:\Dự án TT\notebooklm\backend"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting FastAPI server...
python -m app.main

pause
