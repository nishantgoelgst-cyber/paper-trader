@echo off
echo ========================================
echo   NSE Paper Trader - Starting Up
echo ========================================
echo.
echo Starting backend on http://localhost:8000
start "Paper Trader Backend" cmd /k "cd /d "%~dp0backend" && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo.
echo Starting frontend on http://localhost:5173
start "Paper Trader Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo.
echo ========================================
echo   Backend API:  http://localhost:8000/docs
echo   Frontend UI:  http://localhost:5173
echo ========================================
echo.
echo Close this window or press any key to exit.
pause > nul
