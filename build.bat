@echo off
chcp 65001 >nul 2>&1
title MKV Batch Muxing Tool - Build Script

echo ========================================
echo   MKV Batch Muxing Tool - Build Script
echo ========================================
echo.

cd /d "%~dp0"

echo [Step 1/8] Closing running program...
taskkill /f /im jiuge-mkv-gui.exe >nul 2>&1
echo     Done!

echo.
echo [Step 2/8] Cleaning temp files...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
if exist __pycache__ rmdir /s /q __pycache__ 2>nul
del /q *.spec 2>nul
echo     Done!

echo.
echo [Step 3/8] Cleaning PyInstaller cache...
if exist "%LOCALAPPDATA%\pyinstaller" rmdir /s /q "%LOCALAPPDATA%\pyinstaller" 2>nul
if exist "%TEMP%\pyinstaller*" (
    for /d %%d in ("%TEMP%\pyinstaller*") do @rmdir /s /q "%%d" 2>nul
)
echo     Done!

echo.
echo [Step 4/8] Cleaning Python cache...
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
echo     Done!

echo.
echo [Step 5/8] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python first
    pause
    exit /b 1
)
echo     Python OK

echo.
echo [Step 6/8] Checking dependencies...
pip show PySide6 >nul 2>&1
if errorlevel 1 (
    echo     Installing dependencies...
    pip install PySide6 psutil pyinstaller
) else (
    echo     Dependencies OK
)

echo.
echo [Step 7/9] Building EXE...
echo.

python -m PyInstaller --windowed --name "jiuge-mkv-gui" --icon="Resources\Icons\App.ico" --add-data "Resources;Resources" --hidden-import PySide6.QtMultimedia --hidden-import PySide6.QtMultimediaWidgets --clean main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [Step 7/8] Copying additional files...
if not exist "dist\jiuge-mkv-gui\Resources\Icons" mkdir "dist\jiuge-mkv-gui\Resources\Icons"
xcopy /Y /Q "Resources\Icons\*.*" "dist\jiuge-mkv-gui\Resources\Icons\"
echo     Done!

echo.
echo [Step 8/8] Cleaning build temp files...
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
