@echo off
echo ════════════════════════════════════════════════════
echo   AsFin Optimizer — Build Script
echo ════════════════════════════════════════════════════
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

REM Install/upgrade PyInstaller
echo [1/3] Installing PyInstaller...
pip install pyinstaller --quiet

REM Install project dependencies
echo [2/3] Installing project dependencies...
pip install -r requirements.txt --quiet

REM Build the executable
echo [3/3] Building AsFin_Optimizer.exe...
echo.
pyinstaller asfin.spec --clean --noconfirm

echo.
if exist "dist\AsFin_Optimizer.exe" (
    echo ════════════════════════════════════════════════════
    echo   BUILD SUCCESSFUL!
    echo   Output: dist\AsFin_Optimizer.exe
    echo ════════════════════════════════════════════════════
    echo.
    echo   To run: double-click dist\AsFin_Optimizer.exe
    echo   The browser will open automatically.
) else (
    echo [ERROR] Build failed. Check the output above for errors.
)

echo.
pause
