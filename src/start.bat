@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe gui.py
) else (
    echo Bitte zuerst install_and_run.bat ausfuehren!
    pause
)
