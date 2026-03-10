@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "APP_NAME=PC Monitor Server"
set "APP_EXE=%~dp0PCMonitorServer.exe"
set "PORT=5000"
set "FOUND_PORT="
set "ACTIVE_PID="

call :load_port
call :detect_port_in_use

echo ================================================================
echo %APP_NAME%
echo ================================================================
echo.

if not exist "%APP_EXE%" (
    echo The packaged application file was not found:
    echo %APP_EXE%
    echo.
    echo If you are using the source project, run build.bat first.
    pause
    exit /b 1
)

if defined ACTIVE_PID (
    echo Port %PORT% is already in use by PID %ACTIVE_PID%.
    echo.
    echo If the monitor is already running, open:
    echo http://127.0.0.1:%PORT%
    echo.
    echo To restart it cleanly, close the old monitor window or run stop_app.bat.
    pause
    exit /b 1
)

echo Launching the packaged monitoring server...
echo.
"%APP_EXE%"
if errorlevel 1 goto :runtime_failed
exit /b 0

:load_port
if exist "config.json" (
    for /f "tokens=2 delims=:, " %%A in ('findstr /i /r "\"port\"[ ]*:" config.json') do (
        if not defined FOUND_PORT set "FOUND_PORT=%%~A"
    )
)
if defined FOUND_PORT set "PORT=%FOUND_PORT%"
exit /b 0

:detect_port_in_use
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do (
    set "ACTIVE_PID=%%P"
    goto :eof
)
exit /b 0

:runtime_failed
echo.
echo %APP_NAME% stopped unexpectedly.
echo.
echo Common causes:
echo - The chosen port is already in use
echo - Windows Firewall blocked part of the startup flow
echo - Another startup error appears above
echo.
echo Use stop_app.bat if you need to stop an older instance first.
pause
exit /b 1

