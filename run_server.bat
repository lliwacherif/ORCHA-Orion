@echo off
echo ========================================
echo   ORCHA Server Startup
echo ========================================
echo.

cd /d "%~dp0"

echo [INFO] Starting server on port 8000...
echo [INFO] Main URL: http://localhost:8000
echo [INFO] API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

