@echo off
echo ========================================
echo Installing Backend Dependencies
echo ========================================
cd /d "D:\Dự án TT\notebooklm\backend"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing requirements...
pip install -r requirements.txt

echo.
echo ========================================
echo Backend dependencies installed!
echo ========================================
echo.
echo You can now run: run_backend.bat
pause
