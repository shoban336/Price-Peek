Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Starting PricePeek - Universal Product Price Comparison Platform" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Start Backend in separate process
$backendScript = @"
cd '$PSScriptRoot\backend'
& '.\venv\Scripts\Activate.ps1'
python -m uvicorn app.main:app --reload --port 8000
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# 2. Start Frontend in separate process
$frontendScript = @"
cd '$PSScriptRoot\frontend'
npm.cmd run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript

Write-Host "Backend API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "Frontend Web UI:  http://localhost:5173" -ForegroundColor Yellow
