@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   VideoCompressor Pro - Installer
echo ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Download Python 3.12+ from https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Check FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [INFO] FFmpeg is not installed or not in PATH.
    echo        The app can download it automatically on first launch.
    echo        Or install manually: winget install FFmpeg
    echo.
)

:: Navigate to backend directory
cd /d "%~dp0backend"
if errorlevel 1 (
    echo [ERROR] Backend directory not found.
    pause
    exit /b 1
)

:: Create virtual environment
echo [1/4] Creating virtual environment...
if exist "venv" (
    echo       Virtual environment already exists, skipping.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo [3/4] Installing dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Install PyInstaller
pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

:: Create .env if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo       Created .env from .env.example
    )
)

:: Update .env for Windows FFmpeg paths
findstr /c:"FFMPEG_PATH" .env >nul 2>&1
if errorlevel 1 (
    echo FFMPEG_PATH=ffmpeg>> .env
    echo FFPROBE_PATH=ffprobe>> .env
)

:: Build portable GUI .exe with PyInstaller
echo [4/4] Building portable GUI executable...
pyinstaller ^
    --name VideoCompressorPro ^
    --onefile ^
    --windowed ^
    --add-data "app;app" ^
    --add-data ".env.example;." ^
    --add-data "%CD%\venv\Lib\site-packages\customtkinter;customtkinter" ^
    --hidden-import customtkinter ^
    --hidden-import darkdetect ^
    --hidden-import app.main ^
    --hidden-import app.core.config ^
    --hidden-import app.core.logging ^
    --hidden-import app.core.exceptions ^
    --hidden-import app.routers.video ^
    --hidden-import app.routers.ai ^
    --hidden-import app.services.video_service ^
    --hidden-import app.services.ai_service ^
    --hidden-import app.services.ffmpeg_downloader ^
    --hidden-import app.models.schemas ^
    --hidden-import multipart ^
    --hidden-import httpx ^
    --hidden-import aiofiles ^
    --hidden-import pydantic_settings ^
    --hidden-import dotenv ^
    --collect-submodules pydantic ^
    --collect-submodules customtkinter ^
    --collect-submodules starlette ^
    --collect-submodules fastapi ^
    ..\gui\app.py

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build Complete!
echo ============================================
echo.
echo   Executable: backend\dist\VideoCompressorPro.exe
echo.
echo   To run:
echo     1. Double-click VideoCompressorPro.exe
echo        or run: dist\VideoCompressorPro.exe
echo     2. If FFmpeg is not installed, the app will offer
echo        to download it automatically on first launch.
echo     3. The app opens fullscreen automatically
echo        Press ESC or F11 to toggle fullscreen
echo.
echo   Configuration: Edit backend\.env to change settings
echo ============================================
echo.
pause
