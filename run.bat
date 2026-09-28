@echo off
REM ============================================================
REM  AI Misuse Prevention System - one-click run script
REM  Double-click this file, or run:  run.bat
REM ============================================================

cd /d "%~dp0"

echo.
echo  [1/2] Checking dependencies...
REM Fast path: if the core packages already import, skip the slow pip install.
REM (pip backtracks for minutes trying to match exact version pins on Python 3.13.)
py -c "import flask, sklearn, joblib, numpy, PIL" 1>nul 2>nul
if errorlevel 1 (
    echo        Missing packages - installing from requirements.txt ...
    py -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo  ERROR: dependency install failed. Is Python installed? Try:  py --version
        pause
        exit /b 1
    )
) else (
    echo        All core dependencies present - skipping install.
)

echo  [2/2] Starting server...
echo.
echo  ============================================================
echo   Open your browser at:  http://127.0.0.1:5000
echo   Press Ctrl+C in this window to stop the server.
echo  ============================================================
echo.

py app.py

pause
