# ==========================================
# Otium_wip Backend Startup Script (PowerShell)
# Automatically install dependencies and start hot-reload dev server
# ==========================================

# Set working directory to script directory
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Otium Backend Startup Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if in virtual environment
$inVenv = python -c "import sys; print('VIRTUAL_ENV' in sys.__dict__)" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[INFO] Already in Python virtual environment" -ForegroundColor Green
} else {
    Write-Host "[INFO] No virtual environment detected, using system Python" -ForegroundColor Yellow

    # Check for venv directory and try to activate
    $venvPaths = @("..\venv", ".venv")
    $activated = $false

    foreach ($venvPath in $venvPaths) {
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            Write-Host "[INFO] Found virtual environment, activating..." -ForegroundColor Green
            & $activateScript
            $activated = $true
            break
        }
    }

    if (-not $activated) {
        Write-Host "[INFO] No virtual environment found, continuing with system Python" -ForegroundColor Yellow
    }
}

# Check Python version
Write-Host ""
Write-Host "[INFO] Checking Python version..." -ForegroundColor Cyan
python --version

# Install/update dependencies
Write-Host ""
Write-Host "[INFO] Installing/updating Python dependencies..." -ForegroundColor Cyan

# Try to upgrade pip (skip if fails)
Write-Host "[INFO] Attempting to upgrade pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Pip upgrade failed, continuing with current version" -ForegroundColor Yellow
    python -m pip --version
}

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[INFO] Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] requirements.txt file not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check environment variables config file
Write-Host ""
if (Test-Path ".env") {
    Write-Host "[INFO] Found .env file, environment variables loaded" -ForegroundColor Green
} else {
    Write-Host "[WARNING] .env file not found, copy .env.example to .env and configure" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Write-Host "[INFO] Found .env.example template file" -ForegroundColor Cyan
    }
}

# Start FastAPI development server (hot reload)
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[INFO] Starting FastAPI development server (hot reload mode)" -ForegroundColor Green
Write-Host "[INFO] Server will run at http://localhost:8000" -ForegroundColor Cyan
Write-Host "[INFO] API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "[INFO] Press Ctrl+C to stop server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Use uvicorn to start with hot reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# If server stops
Write-Host ""
Write-Host "[INFO] Server has stopped" -ForegroundColor Yellow
Read-Host "Press Enter to exit"