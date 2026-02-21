# Victor Institutional Logic (VIL) — Startup & Environment Manager
# This script ensures all dependencies are met and starts the platform with the best available database.

$ErrorActionPreference = "Stop"

Write-Host "`n=== Victor Institutional Logic Startup ===" -ForegroundColor Cyan

# 1. Environment Checks
Write-Host "[1/4] Checking environment..." -ForegroundColor Gray
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Please install Python 3.10+ and add it to your PATH."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js/NPM not found. Please install Node.js and add it to your PATH."
}

# 2. Database Strategy
Write-Host "[2/4] Determining database strategy..." -ForegroundColor Gray
$useSqlite = $true
$dbUrl = "sqlite+aiosqlite:///../vildb.sqlite"

if (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue) {
    Write-Host "      Detected Docker Desktop. Attempting to check PostgreSQL..." -ForegroundColor DarkGray
    $dockerCheck = docker ps --filter "name=vil-postgres" --format "{{.Status}}"
    if ($dockerCheck -like "*Up*") {
        Write-Host "      PostgreSQL container is UP. Using PostgreSQL." -ForegroundColor Green
        $useSqlite = $false
        $dbUrl = "postgresql+asyncpg://vil:vilpass@localhost:5432/vildb"
    } else {
        Write-Host "      PostgreSQL container not found or stopped. Starting it..." -ForegroundColor DarkGray
        try {
            docker-compose up -d postgres redis
            Start-Sleep -Seconds 5
            $dbUrl = "postgresql+asyncpg://vil:vilpass@localhost:5432/vildb"
            $useSqlite = $false
            Write-Host "      PostgreSQL started successfully." -ForegroundColor Green
        } catch {
            Write-Host "      Failed to start Docker containers. Falling back to SQLite." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "      Docker Desktop not running. Falling back to SQLite." -ForegroundColor Yellow
}

$env:DATABASE_URL = $dbUrl
$env:USE_SQLITE_FALLBACK = if ($useSqlite) { "True" } else { "False" }

# 3. Start Backend
Write-Host "[3/4] Starting Backend..." -ForegroundColor Gray
cd backend
Start-Process cmd -ArgumentList "/k title VIL Backend & set DATABASE_URL=$dbUrl & uvicorn app.main:app --host 0.0.0.0 --port 8000"
cd ..

# 4. Start Frontend
Write-Host "[4/4] Starting Frontend..." -ForegroundColor Gray
cd frontend
Start-Process cmd -ArgumentList "/k title VIL Frontend & npm run dev"
cd ..

Write-Host "`nSuccess! VIL Trading Platform is starting." -ForegroundColor Green
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Mode:     $(if ($useSqlite) { 'SQLite (Local)' } else { 'PostgreSQL (Docker)' })" -ForegroundColor Cyan
Write-Host "`nKeep these windows open while trading.`n"
