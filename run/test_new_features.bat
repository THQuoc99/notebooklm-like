@echo off
echo ========================================
echo  TESTING NOTEBOOKLM NEW FEATURES
echo ========================================
echo.

echo [1/5] Checking OCR dependencies...
echo.

echo Testing Tesseract...
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Tesseract not found! Install from OCR_SETUP.md
    pause
    exit /b 1
) else (
    echo [OK] Tesseract installed
)

echo.
echo Testing Poppler...
pdftoppm -h >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Poppler not found! Install from OCR_SETUP.md
    echo OCR for PDFs will not work without Poppler
    pause
) else (
    echo [OK] Poppler installed
)

echo.
echo [2/5] Checking Python packages...
cd /d "%~dp0\..\backend"
call venv\Scripts\activate.bat

python -c "import pytesseract" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pytesseract not installed
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
) else (
    echo [OK] pytesseract installed
)

python -c "import pdf2image" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pdf2image not installed
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
) else (
    echo [OK] pdf2image installed
)

python -c "from app.services.rag_service import rag_service" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Cannot import rag_service
    echo Check backend code for errors
    pause
    exit /b 1
) else (
    echo [OK] rag_service import successful
)

echo.
echo [3/5] All dependencies OK!
echo.

echo [4/5] Starting backend server...
echo Check http://localhost:8000/health
echo.

echo Starting in 3 seconds...
timeout /t 3 >nul

start cmd /k "cd /d %~dp0\..\backend && venv\Scripts\activate && python -m app.main"

echo.
echo [5/5] Waiting for server to start...
timeout /t 5 >nul

echo.
echo Testing health endpoint...
curl http://localhost:8000/health 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Server may not be ready yet
) else (
    echo [OK] Server is running
)

echo.
echo ========================================
echo  READY TO TEST!
echo ========================================
echo.
echo Test scenarios:
echo 1. Upload PDF scan - should auto OCR
echo 2. Upload 2 different files
echo 3. Ask question with file_ids filter
echo 4. Check answer for [1], [2] citations
echo 5. Delete a file - check MongoDB and FAISS
echo.
echo Open frontend: streamlit run ..\frontend\app.py
echo.
pause
