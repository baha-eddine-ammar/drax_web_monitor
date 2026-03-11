@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "APP_NAME=PC Monitor Server"
set "APP_EXE_NAME=PCMonitorServer.exe"
set "APP_EXE_PATH=%~dp0PCMonitorServer.exe"
set "PORT=5000"
set "FOUND_PORT="
set "FIREWALL_RULE=PC Monitor Dashboard Port 5000"

call :load_port
set "FIREWALL_RULE=PC Monitor Dashboard Port %PORT%"

echo ================================================================
echo %APP_NAME% Setup
echo ================================================================
echo.

if not exist "%APP_EXE_NAME%" goto :missing_exe

call :configure_firewall
call :create_shortcuts

echo.
echo Setup is complete.
echo Starting %APP_NAME%...
echo.
call "%~dp0run_app.bat"
exit /b %errorlevel%

:load_port
if exist "config.json" (
    for /f "tokens=2 delims=:, " %%A in ('findstr /i /r "\"port\"[ ]*:" config.json') do (
        if not defined FOUND_PORT set "FOUND_PORT=%%~A"
    )
)
if defined FOUND_PORT set "PORT=%FOUND_PORT%"
exit /b 0

:missing_exe
echo The packaged application file was not found:
echo %APP_EXE_PATH%
echo.
echo If you are preparing the release, run build.bat first.
pause
exit /b 1

:configure_firewall
echo Checking Windows Firewall rule for port %PORT%...
net session >nul 2>&1
if errorlevel 1 (
    echo Firewall rule was not added because setup is not running as administrator.
    echo On first launch, if Windows asks, click Allow access for Private networks.
    exit /b 0
)

netsh advfirewall firewall delete rule name="%FIREWALL_RULE%" >nul 2>&1
netsh advfirewall firewall add rule name="%FIREWALL_RULE%" dir=in action=allow protocol=TCP localport=%PORT% profile=private >nul 2>&1
if errorlevel 1 (
    echo Firewall rule could not be created automatically.
    echo The app can still run, but another PC may be blocked until Windows allows it.
    exit /b 0
)

echo Firewall rule added for TCP port %PORT% on Private networks.
exit /b 0

:create_shortcuts
where wscript >nul 2>&1
if errorlevel 1 (
    echo Desktop shortcut step skipped because Windows Script Host is unavailable.
    exit /b 0
)

set "SHORTCUT_SCRIPT=%TEMP%\pc_monitor_shortcuts_%RANDOM%.vbs"
set "RUN_SHORTCUT=%USERPROFILE%\Desktop\PC Monitor Server.lnk"
set "STOP_SHORTCUT=%USERPROFILE%\Desktop\Stop PC Monitor Server.lnk"

> "%SHORTCUT_SCRIPT%" echo Set shell = CreateObject("WScript.Shell")
>> "%SHORTCUT_SCRIPT%" echo Set runLink = shell.CreateShortcut("%RUN_SHORTCUT%")
>> "%SHORTCUT_SCRIPT%" echo runLink.TargetPath = "%~dp0run_app.bat"
>> "%SHORTCUT_SCRIPT%" echo runLink.WorkingDirectory = "%~dp0"
>> "%SHORTCUT_SCRIPT%" echo runLink.Description = "Start the LAN PC monitor server"
>> "%SHORTCUT_SCRIPT%" echo runLink.IconLocation = "%APP_EXE_PATH%,0"
>> "%SHORTCUT_SCRIPT%" echo runLink.Save
>> "%SHORTCUT_SCRIPT%" echo Set stopLink = shell.CreateShortcut("%STOP_SHORTCUT%")
>> "%SHORTCUT_SCRIPT%" echo stopLink.TargetPath = "%~dp0stop_app.bat"
>> "%SHORTCUT_SCRIPT%" echo stopLink.WorkingDirectory = "%~dp0"
>> "%SHORTCUT_SCRIPT%" echo stopLink.Description = "Stop the LAN PC monitor server"
>> "%SHORTCUT_SCRIPT%" echo stopLink.IconLocation = "%APP_EXE_PATH%,0"
>> "%SHORTCUT_SCRIPT%" echo stopLink.Save

cscript //nologo "%SHORTCUT_SCRIPT%" >nul 2>&1
del /q "%SHORTCUT_SCRIPT%" >nul 2>&1

echo Desktop shortcuts created.
exit /b 0
