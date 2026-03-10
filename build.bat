@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "APP_EXE=PCMonitorServer.exe"
set "RELEASE_NAME=LAN-PC-Monitor"
set "RELEASE_DIR=release\%RELEASE_NAME%"
set "RELEASE_ZIP=dist\%RELEASE_NAME%.zip"

echo ================================================
echo PC Monitor Packaging
echo ================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "VENV_PYTHON=.venv\Scripts\python.exe"
) else (
    call :find_python || goto :no_python
    echo Creating local Python environment...
    "!BASE_PYTHON_EXE!" !BASE_PYTHON_ARGS! -m venv .venv || goto :build_failed
    set "VENV_PYTHON=.venv\Scripts\python.exe"
)

call :find_python || goto :build_failed
echo Installing build dependencies...
"!BASE_PYTHON_EXE!" !BASE_PYTHON_ARGS! -m pip --python "%VENV_PYTHON%" install --upgrade pip || goto :build_failed
"!BASE_PYTHON_EXE!" !BASE_PYTHON_ARGS! -m pip --python "%VENV_PYTHON%" install -r requirements.txt pyinstaller || goto :build_failed

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "release" rmdir /s /q "release"

echo Building Windows executable...
"%VENV_PYTHON%" -m PyInstaller --clean --noconfirm pc_monitor.spec || goto :build_failed

if not exist "dist\%APP_EXE%" goto :build_failed

mkdir "%RELEASE_DIR%" || goto :build_failed
copy /Y "dist\%APP_EXE%" "%RELEASE_DIR%\%APP_EXE%" >nul || goto :build_failed
copy /Y "config.json" "%RELEASE_DIR%\config.json" >nul || goto :build_failed
copy /Y "setup.bat" "%RELEASE_DIR%\setup.bat" >nul || goto :build_failed
copy /Y "run_app.bat" "%RELEASE_DIR%\run_app.bat" >nul || goto :build_failed
copy /Y "stop_app.bat" "%RELEASE_DIR%\stop_app.bat" >nul || goto :build_failed
copy /Y "README.md" "%RELEASE_DIR%\README.md" >nul || goto :build_failed

if exist "%RELEASE_ZIP%" del /q "%RELEASE_ZIP%"
tar -a -cf "%RELEASE_ZIP%" -C "release" "%RELEASE_NAME%" >nul 2>&1

echo.
echo Build complete.
echo Release folder : %RELEASE_DIR%
echo Main EXE       : %RELEASE_DIR%\%APP_EXE%
echo Setup script   : %RELEASE_DIR%\setup.bat
echo Run script     : %RELEASE_DIR%\run_app.bat
echo Stop script    : %RELEASE_DIR%\stop_app.bat
if exist "%RELEASE_ZIP%" echo ZIP package    : %RELEASE_ZIP%
echo.
echo Send the entire folder above, or the ZIP package if it was created.
goto :eof

:find_python
if exist "%LocalAppData%\Python\pythoncore-3.14-64\python.exe" (
    "%LocalAppData%\Python\pythoncore-3.14-64\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "BASE_PYTHON_EXE=%LocalAppData%\Python\pythoncore-3.14-64\python.exe"
        set "BASE_PYTHON_ARGS="
        exit /b 0
    )
)

if exist "%LocalAppData%\Python\bin\python.exe" (
    "%LocalAppData%\Python\bin\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "BASE_PYTHON_EXE=%LocalAppData%\Python\bin\python.exe"
        set "BASE_PYTHON_ARGS="
        exit /b 0
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "BASE_PYTHON_EXE=py"
        set "BASE_PYTHON_ARGS=-3"
        exit /b 0
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "BASE_PYTHON_EXE=python"
        set "BASE_PYTHON_ARGS="
        exit /b 0
    )
)

exit /b 1

:no_python
echo Python 3.12 or newer was not found.
echo Install Python first, then run build.bat again.
pause
exit /b 1

:build_failed
echo.
echo Packaging failed. Check the error above.
pause
exit /b 1
