@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
color 0A
title MC CTRL Installer

cls

echo ================================================================
echo.
echo   MC CTRL - Professional Dependency Installer

echo.
echo ================================================================
echo.

REM ================================================================
REM Python Check
REM ================================================================

echo [1/6] Checking Python...
echo.

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    color 0C
    echo [ERROR] Python was not found on this system.
    echo.
    echo Install Python 3.11 or newer:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT:
    echo   - Enable "Add Python to PATH"
    echo   - Restart terminal after installation
    echo.
    pause
    exit /b 1
)

python --version

echo.

REM ================================================================
REM Upgrade pip
REM ================================================================

echo [2/6] Upgrading pip...
echo.

python -m pip install --upgrade pip

echo.

REM ================================================================
REM Install Dependencies
REM ================================================================

echo [3/6] Installing required packages...
echo.

set packages=customtkinter psutil matplotlib tkinterdnd2 pillow

for %%p in (%packages%) do (
    echo ------------------------------------------------------------
    echo Installing %%p ...
    echo ------------------------------------------------------------

    python -m pip install %%p

    IF ERRORLEVEL 1 (
        color 0C
        echo FAILED: %%p
        color 0A
    ) ELSE (
        echo SUCCESS: %%p installed.
    )

    echo.
)

REM ================================================================
REM Verify Imports
REM ================================================================

echo [4/6] Verifying modules...
echo.

python -c "import customtkinter, psutil, matplotlib, tkinterdnd2; from PIL import Image; print('All modules verified successfully.')"

IF ERRORLEVEL 1 (
    color 0C
    echo.
    echo WARNING: Some modules failed verification.
    echo Try running as Administrator.
    color 0A
) ELSE (
    echo.
    echo All modules verified successfully.
)

echo.

REM ================================================================
REM Git Check
REM ================================================================

echo [5/6] Checking Git...
echo.

git --version >nul 2>&1

IF ERRORLEVEL 1 (
    color 06
    echo WARNING: Git is not installed.
    echo.
    echo Download Git here:
    echo https://git-scm.com/download/win
    color 0A
) ELSE (
    git --version
)

echo.

REM ================================================================
REM Java Reminder
REM ================================================================

echo [6/6] Java Reminder
echo.
echo Minecraft servers usually require Java 21.
echo.
echo Download Java here:
echo https://adoptium.net/temurin/releases/?version=21

echo.

REM ================================================================
REM Finish
REM ================================================================

color 0B

echo ================================================================
echo.
echo INSTALLATION COMPLETE
echo.
echo You can now launch:
echo.
echo launcher.pyw
echo.
echo Thanks for using MC CTRL!
echo.
echo ================================================================
echo.

pause