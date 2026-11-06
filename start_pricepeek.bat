@echo off
echo ======================================================================
echo Starting PricePeek - Universal Product Price Comparison Platform
echo ======================================================================

echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "PricePeek Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting Vite React Frontend on http://localhost:5173 ...
start "PricePeek Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo PricePeek is running!
echo Backend Swagger API: http://localhost:8000/docs
echo Frontend Web UI:    http://localhost:5173
echo ======================================================================
pause
