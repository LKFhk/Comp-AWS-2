@echo off
echo Starting RiskIntel360 Competition Demo Servers
echo ===============================================

REM Start backend server in a new window
echo Starting backend server on port 8000...
start "Backend Server" cmd /k "uvicorn riskintel360.api.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend server in a new window
echo Starting frontend server on port 3000...
cd frontend
start "Frontend Server" cmd /k "npm start"
cd ..

echo.
echo ===============================================
echo Servers are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Competition Demo: http://localhost:3000/competition-demo
echo ===============================================
echo.
echo Press any key to continue...
pause >nul