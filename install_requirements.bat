@echo off

if not exist install_requirements.py (
    echo.
    echo ERROR: install_requirements.py was not found!
    echo Make sure this file is in the same folder.
    echo.
    pause
    exit /b 1
)

python install_requirements.py

pause