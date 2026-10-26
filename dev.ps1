# TrendPulse Development Runner
# Runs FastAPI Backend on port 8000 and Vite Frontend on port 5173 concurrently

$ErrorActionPreference = "Stop"

$env:PATH = "C:\Program Files\nodejs;" + $env:PATH
$env:PYTHONPATH = "."

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Starting TrendPulse Retail BI Platform                  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green

# 1. Start FastAPI Backend in background
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "backend\run.py" -PassThru -NoNewWindow

Start-Sleep -Seconds 2

# 2. Start Vite Frontend
Write-Host "[2/2] Starting Vite Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host ">> Executive Dashboard:  http://127.0.0.1:5173/" -ForegroundColor Green
Write-Host ">> Actionable Insights:  http://127.0.0.1:5173/insights" -ForegroundColor Cyan
Write-Host ">> API Health Check:     http://127.0.0.1:8000/api/v1/health" -ForegroundColor Yellow
Write-Host ">> Interactive API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor Gray

try {
    Set-Location frontend
    & "npm.cmd" run dev
}
finally {
    Write-Host ""
    Write-Host "Shutting down backend process..." -ForegroundColor Red
    if ($backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
