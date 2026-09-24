@echo off
setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found: venv\Scripts\python.exe
    echo Create it and install requirements first.
    exit /b 1
)

echo [1/3] Installing/updating dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [2/3] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [3/3] Building one-file AvtoDoc.exe...
venv\Scripts\python.exe -m PyInstaller --noconfirm --clean "AvtoDoc.spec"
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

echo.
echo Build complete:
echo %cd%\dist\AvtoDoc.exe
exit /b 0
