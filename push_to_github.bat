@echo off
REM Push AIRP to GitHub (Windows)
REM Usage: push_to_github.bat <github-username> <repository-name>

if "%1"=="" (
    echo Usage: push_to_github.bat ^<github-username^> ^<repository-name^>
    echo Example: push_to_github.bat yourusername AIRP
    exit /b 1
)

setlocal enabledelayedexpansion
set GITHUB_USER=%1
set REPO_NAME=%2
set GITHUB_URL=https://github.com/!GITHUB_USER!/!REPO_NAME!.git

echo ==========================================
echo Pushing AIRP to GitHub
echo ==========================================
echo Repository URL: !GITHUB_URL!
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if remote already exists
git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    echo Remote 'origin' already exists. Setting to: !GITHUB_URL!
    git remote set-url origin !GITHUB_URL!
) else (
    echo Adding GitHub remote...
    git remote add origin !GITHUB_URL!
)

REM Set default branch to main
echo Setting default branch to main...
git branch -M main

REM Push to GitHub
echo Pushing to GitHub (main branch)...
echo NOTE: You may be prompted for GitHub credentials or SSH passphrase
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo ✓ Successfully pushed to GitHub!
    echo ==========================================
    echo Repository: !GITHUB_URL!
) else (
    echo.
    echo ✗ Push failed. Check error messages above.
    echo Make sure:
    echo 1. Repository exists on GitHub
    echo 2. You have push access
    echo 3. Git credentials are configured
)

endlocal
pause
