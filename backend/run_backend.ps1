# Ensure we are in the backend directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "--- Preparing Backend Environment ---" -ForegroundColor Cyan

# Run cleanup script
.\cleanup_port.ps1

Write-Host "Starting FastAPI backend..." -ForegroundColor Green
# Start uvicorn
# Using python -m uvicorn to ensure any virtual environment is used if present, 
# or system python with uvicorn installed.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
