# AutoAnalyst Dev Runner
# Runs FastAPI Backend on port 8000 and Vite Frontend on port 5173 concurrently

$ErrorActionPreference = "Stop"

# Ensure modern Node.js is on PATH
$env:PATH = "C:\Program Files\nodejs;" + $env:PATH
$env:PYTHONPATH = "."

Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Starting AutoAnalyst Autonomous Engine          " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green

# Start Backend in background process
Write-Host "[1/2] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.app.main:app --port 8000 --reload" -PassThru -NoNewWindow

Start-Sleep -Seconds 2

# Start Frontend
Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Gray
Write-Host ">> AutoAnalyst Engine:   http://localhost:5173/analyst" -ForegroundColor Cyan
Write-Host ">> Primary Root URL:      http://localhost:5173/" -ForegroundColor Green
Write-Host ">> Interactive API Docs:  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor Gray

try {
    Set-Location frontend
    & "C:\Program Files\nodejs\npm.cmd" run dev
}
finally {
    Write-Host ""
    Write-Host "Stopping backend process..." -ForegroundColor Red
    if ($backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
