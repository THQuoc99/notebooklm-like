@echo off
echo ========================================
echo Installing Frontend Dependencies
echo ========================================
cd /d "D:\Dự án TT\notebooklm\frontend"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo.
echo ========================================
echo Frontend dependencies installed!
echo ========================================
pause
