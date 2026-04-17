@echo off
echo ============================================
echo  DiGEM Operator UI - Dependency Installer
echo ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

echo Installing dependencies...
echo.

pip install PyQt5>=5.15 pymodbus>=3.0 "paho-mqtt>=1.6" "matplotlib>=3.5"

if errorlevel 1 (
    echo.
    echo Install failed. Try running this script as Administrator.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  All dependencies installed successfully!
echo  Run the UI with:  python main.py
echo  Run demo mode:    python demo.py
echo ============================================
pause
