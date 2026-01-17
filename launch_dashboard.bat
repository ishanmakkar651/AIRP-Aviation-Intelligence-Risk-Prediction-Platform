@echo off
REM Quick Launch Script - Dashboard
REM Aviation Intelligence & Risk Prediction Platform

echo ========================================
echo ✈️  AIRP Dashboard Launcher
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Virtual environment not found
    echo    Run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if streamlit is installed
streamlit --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Streamlit not installed
    echo    Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo 🚀 Launching dashboard...
echo    URL: http://localhost:8501
echo.
echo    Press Ctrl+C to stop
echo.

REM Launch dashboard
streamlit run 6_dashboard/app.py
