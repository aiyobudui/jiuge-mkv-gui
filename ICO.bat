@echo off
chcp 65001 >nul 2>&1
title Generate ICO from PNG

echo ========================================
echo   Generate ICO from PNG
echo ========================================
echo.

cd /d "%~dp0"

echo [Step 1/2] Generating icon from PNG...
python -c "from PIL import Image; img = Image.open('Resources/Icons/App.png'); sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (96, 96), (128, 128), (256, 256)]; img.save('Resources/Icons/App.ico', format='ICO', sizes=sizes); print('Icon generated successfully')"
if errorlevel 1 (
    echo [ERROR] Failed to generate icon. Please make sure PIL is installed.
    pause
    exit /b 1
)
echo     Done!

echo.
echo ========================================
echo          ICO Generated Successfully!
echo ========================================
echo.
echo Output: %~dp0Resources\Icons\App.ico
echo.

pause
