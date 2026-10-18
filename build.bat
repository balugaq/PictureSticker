@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

rem ============================================================
rem  PictureSticker build script
rem  1. create .venv if missing (Python 3.14)
rem  2. install deps (PySide6 etc.) + pyinstaller
rem  3. pyinstaller --onefile --windowed -> dist\PictureSticker.exe
rem ============================================================

set "PYTHON=C:\Python314\python.exe"
if not exist "%PYTHON%" (
    echo [warn] C:\Python314\python.exe not found, fallback to PATH python
    set "PYTHON=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo [setup] creating venv with %PYTHON% ...
    "%PYTHON%" -m venv .venv
    if errorlevel 1 (
        echo [error] failed to create venv
        goto :fail
    )
)

set "VPY=.venv\Scripts\python.exe"

echo [setup] checking dependencies ...
"%VPY%" -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [setup] installing pyinstaller ...
    "%VPY%" -m pip install pyinstaller
    if errorlevel 1 goto :fail
)

if exist "requirements.txt" (
    "%VPY%" -m pip install -r requirements.txt
    if errorlevel 1 goto :fail
) else (
    echo [warn] requirements.txt not found, skip deps install
)

echo [build] running pyinstaller ...
"%VPY%" -m PyInstaller --noconfirm --clean --onefile --windowed --name PictureSticker --icon favicon.ico --add-data "favicon.png;." main.py
if errorlevel 1 goto :fail

echo.
echo [done] output: dist\PictureSticker.exe
pause
exit /b 0

:fail
echo.
echo [error] build failed, see messages above
pause
exit /b 1
