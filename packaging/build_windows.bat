@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Windows build script to create standalone EXEs using PyInstaller
REM This script ensures it runs from the project root so requirements.txt is found

REM Resolve script directory and project root
set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..
pushd "%ROOT_DIR%"

echo [*] Working directory: %CD%

echo [*] Creating virtual environment (optional)...
python -m venv .venv
call .venv\Scripts\activate

echo [*] Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo [*] Building single-instance executable...
pyinstaller --noconfirm --onefile --name poll_automation ^
  --add-data "README.md;." ^
  poll_automation.py

echo [*] Building multi-instance executable...
pyinstaller --noconfirm --onefile --name multi_instance_automation ^
  --add-data "README.md;." ^
  multi_instance_automation.py

echo [*] Build complete. EXEs located in dist\
echo     - dist\poll_automation.exe
echo     - dist\multi_instance_automation.exe

echo [*] You can copy the dist\ folder to a fresh Windows machine and run the EXEs.

popd
endlocal

