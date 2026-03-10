@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ================================================
echo PC Monitor Launcher
echo ================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "VENV_PYTHON=.venv\Scripts\python.exe"
) else (
    call :find_python || goto :no_python
    echo Creating local Python environment...
    "!BASE_PYTHON_EXE!" !BASE_PYTHON_ARGS! -m venv .venv || goto :setup_failed
    set "VENV_PYTHON=.venv\Scripts\python.exe"
)

call :find_python || goto :setup_failed
"%VENV_PYTHON%" -c "import fastapi, uvicorn, psutil, jinja2" >nul 2>&1
if errorlevel 1 goto install_requirements
goto run_app

:install_requirements
echo Installing required packages...
"!BASE_PYTHON_EXE!" !BASE_PYTHON_ARGS! -m pip --python "%VENV_PYTHON%" install --upgrade pip || goto :setup_failed
"!BASE_PYTHON_EXE!" !BASE_PYTHON_ARGS! -m pip --python "%VENV_PYTHON%" install -r requirements.txt || goto :setup_failed

:run_app
echo Starting monitoring server...
echo.
"%VENV_PYTHON%" -m pc_monitor.app
if errorlevel 1 goto :runtime_failed
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
echo Install Python first, then run start.bat again.
echo Download: https://www.python.org/downloads/windows/
pause
exit /b 1

:setup_failed
echo.
echo Setup failed. Check the error above.
echo Common causes:
echo - Python is missing or incomplete
echo - Internet access is blocked during the first install
echo - Security software blocked package installation
pause
exit /b 1

:runtime_failed
echo.
echo The monitoring server stopped unexpectedly.
echo Common causes:
echo - Port 5000 is already in use by another app or an older monitor window
echo - Another Python error happened during startup
echo.
echo If port 5000 is busy, close the old monitor window first.
echo Or run: netstat -ano ^| findstr :5000
pause
exit /b 1
