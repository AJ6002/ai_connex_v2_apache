@echo off
TITLE AIConnex Autonomous MLOps Platform - Single Click Launcher
COLOR 0A

echo =======================================================================
echo          🤖 AIConnex Autonomous MLOps Platform (USB Launch)
echo =======================================================================
echo.

set MODEL_DIR=

REM 1. Auto-Detect External USB Drive or External Models Directory
if exist "..\aiconnex_models" set MODEL_DIR=..\aiconnex_models
if exist "E:\aiconnex_models" set MODEL_DIR=E:\aiconnex_models
if exist "D:\aiconnex_models" set MODEL_DIR=D:\aiconnex_models
if exist "F:\aiconnex_models" set MODEL_DIR=F:\aiconnex_models
if exist "C:\aiconnex_models" set MODEL_DIR=C:\aiconnex_models

if not "%MODEL_DIR%"=="" (
    echo [OK] External USB/Folder Models Detected at: %MODEL_DIR%
    set EXTERNAL_GGUF_DIR=%MODEL_DIR%
) else (
    echo [NOTICE] No external USB drive found. Using internal models directory.
)

echo.
echo [1/2] Starting Python Flask Backend Server (Port 8000)...
start "AIConnex Backend Engine" /min cmd /c "python backend/app.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend React Application (Port 3002)...
start "AIConnex Web Frontend" /min cmd /c "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo =======================================================================
echo [SUCCESS] AIConnex is running!
echo Web Application: http://localhost:3002
echo Backend API:     http://localhost:8000
echo =======================================================================
echo Opening browser...
explorer "http://localhost:3002"

pause
