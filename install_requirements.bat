@echo off
title MC Server Controller - Dependency Installer
color 0A

echo.
echo  =====================================================
echo    MC Server Controller - Dependency Installer
echo  =====================================================
echo.

:: ── Check Python ──────────────────────────────────────────
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Python not found in PATH.
    echo  [!] Please download and install Python 3.x from:
    echo      https://www.python.org/downloads/
    echo      Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  [OK] Found %%i
echo.

:: ── Upgrade pip ───────────────────────────────────────────
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo  [!] Failed to upgrade pip. Continuing anyway...
) else (
    echo  [OK] pip is up to date.
)
echo.

:: ── Install Python packages ───────────────────────────────
echo [3/4] Installing Python packages...
echo.

echo  Installing customtkinter...
python -m pip install customtkinter
if errorlevel 1 (
    echo  [!] Failed to install customtkinter.
) else (
    echo  [OK] customtkinter installed.
)
echo.

echo  Installing psutil...
python -m pip install psutil
if errorlevel 1 (
    echo  [!] Failed to install psutil.
) else (
    echo  [OK] psutil installed.
)
echo.

echo  Installing matplotlib...
python -m pip install matplotlib
if errorlevel 1 (
    echo  [!] Failed to install matplotlib.
) else (
    echo  [OK] matplotlib installed.
)
echo.

:: ── Check Git ─────────────────────────────────────────────
echo [4/4] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Git not found in PATH.
    echo  [!] Please download and install Git from:
    echo      https://git-scm.com/download/win
    echo      Make sure to select "Add Git to PATH" during install.
    echo.
) else (
    for /f "tokens=*" %%i in ('git --version 2^>^&1') do echo  [OK] Found %%i
)
echo.

:: ── Java reminder ─────────────────────────────────────────
echo  -------------------------------------------------------
echo   REMINDER: Java 21 is required to run the Minecraft
echo   server. If not installed, download it from:
echo   https://adoptium.net/temurin/releases/?version=21
echo  -------------------------------------------------------
echo.

:: ── Done ──────────────────────────────────────────────────
echo  All done! You can now run launcher.pyw
echo.
pause
