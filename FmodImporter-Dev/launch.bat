@echo off
REM ============================================
REM FMOD Importer Tool - Windows Launcher (DEV)
REM ============================================

echo.
echo ========================================
echo    FMOD Importer Tool (Development)
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python detected:
python --version
echo.

REM Launch the application
echo Launching FMOD Importer Tool...
echo.
python fmod_importer.py

REM If error, display and wait
if errorlevel 1 (
    echo.
    echo ERROR launching the application
    echo.
    pause
)
