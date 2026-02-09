@echo off
REM ==========================================
REM Otium_wip Backend Startup Script (Windows Batch)
REM Automatically install dependencies and start hot-reload dev server
REM ==========================================

REM Set console to UTF-8 encoding to fix Chinese character issues
chcp 65001 >nul

REM Ensure running in script directory
cd /d "%~dp0"

echo.
echo ==========================================
echo   Otium Backend Startup Script
echo ==========================================
echo.

REM Check if in virtual environment
python -c "import sys; print('VIRTUAL_ENV' in sys.__dict__)" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Already in Python virtual environment
) else (
    echo [INFO] No virtual environment detected, using system Python
    REM Check for venv directory and try to activate
    if exist "..\venv\Scripts\activate.bat" (
        echo [INFO] Found virtual environment, activating...
        call "..\venv\Scripts\activate.bat"
    ) else (
        if exist ".venv\Scripts\activate.bat" (
            echo [INFO] Found virtual environment, activating...
            call ".venv\Scripts\activate.bat"
        ) else (
            echo [INFO] No virtual environment found, continuing with system Python
        )
    )
)

REM Check Python version
echo.
echo [INFO] Checking Python version...
python --version

REM Install/update dependencies
echo.
echo [INFO] Installing/updating Python dependencies...

REM Try to upgrade pip (skip if fails)
echo [INFO] Attempting to upgrade pip...
python -m pip install --upgrade pip >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Pip upgrade failed, continuing with current version
    python -m pip --version
)

if exist requirements.txt (
    echo [INFO] Installing from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [INFO] Dependencies installed successfully
) else (
    echo [ERROR] requirements.txt file not found
    pause
    exit /b 1
)

REM Check environment variables config file
echo.
if exist .env (
    echo [INFO] Found .env file, environment variables loaded
) else (
    echo [WARNING] .env file not found, copy .env.example to .env and configure
    if exist .env.example (
        echo [INFO] Found .env.example template file
    )
)

REM Start FastAPI development server (hot reload)
echo.
echo ==========================================
echo [INFO] Starting FastAPI development server (hot reload mode)
echo [INFO] Server will run at http://localhost:8000
echo [INFO] API docs: http://localhost:8000/docs
echo [INFO] Press Ctrl+C to stop server
echo ==========================================
echo.

REM Use uvicorn to start with hot reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

REM If server stops, pause to view error messages
echo.
echo [INFO] Server has stopped
pause