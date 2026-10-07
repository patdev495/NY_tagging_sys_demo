@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo           NY TAGGING SYSTEM - AUTOMATED TEST SUITE
echo ============================================================

set BACKEND_STATUS=0
set FRONTEND_STATUS=0

echo.
echo [1/2] Running BACKEND tests (Pytest)...
cd backend_v2
uv run pytest -v
if %errorlevel% neq 0 (
    set BACKEND_STATUS=1
    echo.
    echo [!] BACKEND TESTS FAILED
) else (
    echo.
    echo [v] BACKEND TESTS PASSED
)
cd ..

echo.
echo ------------------------------------------------------------
echo.

echo [2/2] Running FRONTEND tests (Vitest)...
cd frontend_v2
call npm run test
if %errorlevel% neq 0 (
    set FRONTEND_STATUS=1
    echo.
    echo [!] FRONTEND TESTS FAILED
) else (
    echo.
    echo [v] FRONTEND TESTS PASSED
)
cd ..

echo.
echo ============================================================
echo                     FINAL TEST REPORT
echo ============================================================

if %BACKEND_STATUS% equ 0 (
    echo Backend:  PASSED
) else (
    echo Backend:  FAILED
)

if %FRONTEND_STATUS% equ 0 (
    echo Frontend: PASSED
) else (
    echo Frontend: FAILED
)

echo ============================================================

if %BACKEND_STATUS% neq 0 (
    exit /b 1
)
if %FRONTEND_STATUS% neq 0 (
    exit /b 1
)

echo All tests completed successfully!
pause
