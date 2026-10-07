@echo off
echo ===================================================
echo    NY TAGGING SYSTEM V2 - PRODUCTION BUILDER
echo ===================================================
echo.

:: 1. Build Frontend
echo [1/4] Building Frontend V2...
cd frontend_v2
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b
)
cd ..

:: 2. Build Backend
echo [2/4] Building Backend V2 EXE...
cd backend_v2
uv run pyinstaller --noconfirm --onedir --console --name "NY_Tagging_System" ^
    --add-data "src;src" ^
    --collect-all pydantic ^
    --collect-all pydantic_core ^
    --collect-submodules pydantic_core ^
    --hidden-import pydantic_core ^
    --hidden-import pydantic_core._pydantic_core ^
    --hidden-import pyodbc ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    --hidden-import pythoncom ^
    --hidden-import win32gui ^
    --hidden-import win32con ^
    --hidden-import win32print ^
    --hidden-import PIL ^
    main.py
if %errorlevel% neq 0 (
    echo [ERROR] Backend build failed!
    pause
    exit /b
)
cd ..

:: 3. Build Print Agent
echo [3/4] Building Print Agent V2 EXE...
cd print_agent_v2
uv run pyinstaller --noconfirm --onefile --console --name "NY_Print_Agent" ^
    --add-data "scale;scale" ^
    --collect-all pydantic ^
    --collect-all pydantic_core ^
    --hidden-import serial ^
    --hidden-import serial.tools ^
    --hidden-import serial.tools.list_ports ^
    --hidden-import keyboard ^
    --hidden-import win32com ^
    --hidden-import win32com.client ^
    --hidden-import pythoncom ^
    agent.py
if %errorlevel% neq 0 (
    echo [ERROR] Print Agent build failed!
    pause
    exit /b
)
cd ..

:: 4. Finalize Release Structure
echo [4/4] Finalizing build...
if not exist "release" mkdir release
if exist "release\NY_Tagging_System" rmdir /S /Q "release\NY_Tagging_System"
xcopy /E /I /Y "backend_v2\dist\NY_Tagging_System" "release\NY_Tagging_System"
xcopy /E /I /Y "frontend_v2\dist" "release\NY_Tagging_System\static"
copy /Y "print_agent_v2\dist\NY_Print_Agent.exe" "release\NY_Print_Agent.exe"
if exist "print_agent_v2\scale_config.json" copy /Y "print_agent_v2\scale_config.json" "release\scale_config.json"
if exist "backend_v2\resources" xcopy /E /I /Y "backend_v2\resources" "release\NY_Tagging_System\resources"
if exist "backend_v2\.env" copy /Y "backend_v2\.env" "release\NY_Tagging_System\.env"

:: Create Production Launcher Script in release\
(
echo @echo off
echo title NY Tagging System Production Launcher
echo ===================================================
echo     NY TAGGING SYSTEM V2 - PRODUCTION MODE
echo ===================================================
echo.
echo [1/2] Starting Print Agent V2...
echo start "NY Print Agent" "NY_Print_Agent.exe"
echo.
echo [2/2] Starting Server ^& UI...
echo cd NY_Tagging_System
echo start "NY Tagging System" "NY_Tagging_System.exe"
echo cd ..
echo.
echo ===================================================
echo  SERVICES LAUNCHED!
echo  - Server ^& UI:  http://127.0.0.1:8001
echo  - Print Agent:  http://127.0.0.1:8080
echo ===================================================
echo.
echo timeout /t 2 ^>nul
echo start http://127.0.0.1:8001
) > "release\start_production.bat"

echo.
echo ===================================================
echo  BUILD COMPLETE!
echo  Check the "release" folder for your deployment files.
echo  Double-click "release\start_production.bat" to run!
echo ===================================================
pause
