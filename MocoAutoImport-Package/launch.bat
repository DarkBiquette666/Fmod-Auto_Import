@echo off
REM ============================================
REM Moco Auto Import - Lanceur Windows
REM ============================================

echo.
echo ========================================
echo    Moco Auto Import pour FMOD Studio
echo ========================================
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH
    echo.
    echo Veuillez installer Python depuis: https://www.python.org/downloads/
    echo N'oubliez pas de cocher "Add Python to PATH" lors de l'installation
    echo.
    pause
    exit /b 1
)

echo Python detecte:
python --version
echo.

REM Lancer l'application
echo Lancement de Moco Auto Import...
echo.
python moco_auto_import.py

REM Si erreur, afficher et attendre
if errorlevel 1 (
    echo.
    echo ERREUR lors du lancement de l'application
    echo.
    pause
)
