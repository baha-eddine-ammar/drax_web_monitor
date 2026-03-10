@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PORT=5000"
set "FOUND_PORT="
set "FOUND_ANY="
set "PIDS="

if exist "config.json" (
    for /f "tokens=2 delims=:, " %%A in ('findstr /i /r "\"port\"[ ]*:" config.json') do (
        if not defined FOUND_PORT set "FOUND_PORT=%%~A"
    )
)

if defined FOUND_PORT set "PORT=%FOUND_PORT%"

echo ================================================
echo PC Monitor Stopper
echo ================================================
echo Looking for a server on port %PORT%...
echo.

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do (
    if not defined PIDS (
        set "PIDS=%%P"
    ) else (
        echo !PIDS! | findstr /w "%%P" >nul || set "PIDS=!PIDS! %%P"
    )
    set "FOUND_ANY=1"
)

if not defined FOUND_ANY (
    echo No running monitor process was found on port %PORT%.
    pause
    exit /b 0
)

for %%P in (!PIDS!) do (
    echo Stopping PID %%P...
    taskkill /PID %%P /F >nul 2>&1
    if errorlevel 1 (
        echo Failed to stop PID %%P.
    ) else (
        echo PID %%P stopped successfully.
    )
)

echo.
echo Stop command finished.
pause
exit /b 0
