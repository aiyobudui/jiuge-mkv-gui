@echo off
chcp 65001 >nul 2>&1
title MKV Batch Muxing Tool - Build Script

echo ========================================
echo   MKV Batch Muxing Tool - Build Script
echo ========================================
echo.

cd /d "%~dp0"

echo [Step 1/6] Closing running program...
taskkill /f /im jiuge-mkv-gui.exe >nul 2>&1
echo     Done!

echo.
echo [Step 2/6] Cleaning temp files...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
if exist __pycache__ rmdir /s /q __pycache__ 2>nul
if exist packages\__pycache__ rmdir /s /q packages\__pycache__ 2>nul
del /q *.spec 2>nul
echo     Done!

echo.
echo [Step 3/6] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python first
    pause
    exit /b 1
)
echo     Python OK

echo.
echo [Step 4/6] Checking dependencies...
pip show PySide6 >nul 2>&1
if errorlevel 1 (
    echo     Installing dependencies...
    pip install PySide6 psutil pyinstaller
) else (
    echo     Dependencies OK
)

echo.
echo [Step 5/6] Building EXE...
echo.

python -m PyInstaller --windowed --name "jiuge-mkv-gui" --clean main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [Step 6/6] Cleaning build temp files...
if exist build rmdir /s /q build 2>nul
del /q jiuge-mkv-gui.spec 2>nul

echo.
echo ========================================
echo          Build Success!
echo ========================================
echo.
echo Output: %~dp0dist\jiuge-mkv-gui\
echo.

pause
