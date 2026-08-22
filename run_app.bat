@echo off
echo ===================================================
echo   GoalOS - Executive Life Operating System (Light)
echo ===================================================
echo.
echo Starting FastAPI Backend on http://localhost:8000 ...
start "GoalOS Backend (FastAPI)" cmd /k "python -m uvicorn api.main:app --port 8000 --reload"

echo Starting React Vite Light Frontend on http://localhost:5173 ...
start "GoalOS Frontend (React)" cmd /k "cd frontend && npm run dev"

echo.
echo GoalOS is launching!
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo.
pause
