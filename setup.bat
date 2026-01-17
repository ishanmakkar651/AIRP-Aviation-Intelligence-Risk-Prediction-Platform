@echo off
REM Quick Setup Script for Windows
REM Aviation Intelligence & Risk Prediction Platform

echo ========================================
echo 🚀 AIRP - Quick Setup Script
echo ========================================
echo.

REM Check Python
echo 📋 Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found. Please install Python 3.8+
    echo    Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ %PYTHON_VERSION% found
echo.

REM Check PostgreSQL
echo 📋 Checking PostgreSQL...
psql --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  PostgreSQL not found. Please install PostgreSQL 13+
    echo    Download: https://www.postgresql.org/download/windows/
) else (
    for /f "tokens=*" %%i in ('psql --version') do set PSQL_VERSION=%%i
    echo ✅ !PSQL_VERSION! found
)
echo.

REM Create virtual environment
echo 📦 Creating virtual environment...
if exist ".venv" (
    echo ⚠️  Virtual environment already exists
    set /p RECREATE="   Recreate? (y/n): "
    if /i "%RECREATE%"=="y" (
        rmdir /s /q .venv
        python -m venv .venv
        echo ✅ Virtual environment recreated
    )
) else (
    python -m venv .venv
    echo ✅ Virtual environment created
)
echo.

REM Activate and install dependencies
echo 📥 Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo ✅ Dependencies installed
echo.

REM Check config
echo ⚙️  Checking configuration...
if exist "config.yaml" (
    echo ✅ config.yaml found
) else (
    echo ⚠️  config.yaml not found
    if exist "config.yaml.example" (
        copy config.yaml.example config.yaml >nul
        echo    Created from example - please edit with your settings
    )
)
echo.

REM Summary
echo ========================================
echo ✅ Setup Complete!
echo ========================================
echo.
echo 📝 Next steps:
echo    1. Edit config.yaml with your database credentials
echo    2. Run: .venv\Scripts\activate
echo    3. Initialize database: python 2_database/db_setup.py
echo    4. Load airports: python 1_data_ingestion/airport_loader.py
echo    5. Launch dashboard: streamlit run 6_dashboard/app.py
echo.
echo 📖 Full guide: See SETUP_GUIDE.md
echo.
pause
