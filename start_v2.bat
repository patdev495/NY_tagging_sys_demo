@echo off
setlocal
echo ===================================================
echo     NY TAGGING SYSTEM V2 - STARTUP (DEV MODE)
echo ===================================================
echo.

:: 1. Start Backend V2 (Centralized Print Engine)
echo [1/3] Starting Backend V2 (Port 8001)...
start "NY-Backend-V2" cmd /k "cd backend_v2 && uv run uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

:: 2. Start Local Print Agent V2
echo [2/3] Starting Local Print Agent V2 (Port 8080)...
start "NY-Print-Agent-V2" cmd /k "cd print_agent_v2 && uv run agent.py"

:: 3. Wait for services to initialize
ping 127.0.0.1 -n 6 >nul

:: 4. Start Frontend V2
echo [3/3] Starting Frontend V2 (Port 5173)...
start "NY-Frontend-V2" cmd /k "cd frontend_v2 && npm run dev -- --host"

echo.
echo ===================================================
echo  SERVICES LAUNCHED!
echo  - Backend:      http://127.0.0.1:8001
echo  - Frontend:     http://127.0.0.1:5173
echo  - Print Agent:  http://127.0.0.1:8080 (Local Mode)
echo ===================================================
pause
