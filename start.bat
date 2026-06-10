@echo off
cd /d "%~dp0"
set PY=%~dp0src\.venv\Scripts\python.exe
set GUI=%~dp0src\gui.py

if not exist "%PY%" (
    echo Bitte zuerst install_and_run.bat ausfuehren!
    pause
    exit /b 1
)
"%PY%" "%GUI%"
