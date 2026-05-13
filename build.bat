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

REM Try to remove previous build artifacts to avoid permission issues with --clean
if exist "build" (
    echo [INFO] Removing old build directory...
    rd /s /q "build" 2>nul
)

pyinstaller asfin.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed. 
    echo [HINT] If you see "Access Denied", try:
    echo   1. Closing any running instances of AsFin_Optimizer.
    echo   2. Pausing OneDrive sync temporarily.
    echo   3. Running this script as Administrator.
    pause
    exit /b 1
)

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
