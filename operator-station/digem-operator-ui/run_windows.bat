@echo off
echo ============================================
echo  DiGEM Operator UI - Windows Launcher
echo ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

:: Required for PyQt5 on Windows
set QT_QPA_PLATFORM=windows

:: Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo Dependency install failed. Try running as Administrator.
    pause
    exit /b 1
)

echo.
echo Starting DiGEM Operator UI...
echo.

:: Launch - use pythonw to avoid console window, fall back to python
where pythonw >nul 2>&1
if errorlevel 1 (
    python main.py
) else (
    pythonw main.py
)
