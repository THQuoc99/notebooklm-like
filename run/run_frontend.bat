@echo off
echo ========================================
echo Starting Frontend (Streamlit)
echo ========================================
cd /d "D:\Dự án TT\notebooklm\frontend"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting Streamlit app...
streamlit run app.py

pause
