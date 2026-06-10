@echo off
title Amazon Rechnungs-Downloader - Setup
cd /d "%~dp0"

echo.
echo  ================================================
echo   Amazon.de Rechnungs-Downloader
echo  ================================================
echo.

set SRC=%~dp0src
set VENV=%~dp0src\.venv
set PY=%VENV%\Scripts\python.exe
set PYW=%VENV%\Scripts\pythonw.exe

REM ── Schritt 1: Python pruefen / installieren ──────────────────
set PYEXE=
for /f "delims=" %%i in ('where python 2^>nul') do (
    if "!PYEXE!"=="" set PYEXE=%%i
)

REM Versuche python3 falls python nicht gefunden
if "%PYEXE%"=="" (
    for /f "delims=" %%i in ('where python3 2^>nul') do (
        if "%PYEXE%"=="" set PYEXE=%%i
    )
)

if "%PYEXE%"=="" (
    echo [1/5] Python nicht gefunden. Installiere Python 3.12...
    echo       (Download von python.org, ca. 25 MB)
    
    set PYPKG=%TEMP%\python312.exe
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP%\python312.exe'"
    
    if not exist "%TEMP%\python312.exe" (
        echo FEHLER: Python konnte nicht heruntergeladen werden.
        echo Bitte manuell installieren: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    "%TEMP%\python312.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    del "%TEMP%\python312.exe"
    
    REM PATH neu laden
    for /f "delims=" %%i in ('where python 2^>nul') do set PYEXE=%%i
    
    if "%PYEXE%"=="" (
        echo FEHLER: Python-Installation fehlgeschlagen.
        echo Bitte manuell installieren: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo [1/5] Python installiert.
) else (
    echo [1/5] Python gefunden.
)

REM ── Schritt 2: uv installieren ────────────────────────────────
set UV=
for /f "delims=" %%i in ('where uv 2^>nul') do (
    if "%UV%"=="" set UV=%%i
)
if "%UV%"=="" if exist "%USERPROFILE%\.local\bin\uv.exe" set UV=%USERPROFILE%\.local\bin\uv.exe
if "%UV%"=="" if exist "%USERPROFILE%\.cargo\bin\uv.exe" set UV=%USERPROFILE%\.cargo\bin\uv.exe

if "%UV%"=="" (
    echo [2/5] Installiere uv...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if exist "%USERPROFILE%\.local\bin\uv.exe" set UV=%USERPROFILE%\.local\bin\uv.exe
    if exist "%USERPROFILE%\.cargo\bin\uv.exe" set UV=%USERPROFILE%\.cargo\bin\uv.exe
    if "%UV%"=="" (
        echo FEHLER: uv konnte nicht installiert werden.
        pause
        exit /b 1
    )
    echo [2/5] uv installiert.
) else (
    echo [2/5] uv gefunden.
)

REM ── Schritt 3: Python-Umgebung ────────────────────────────────
if exist "%PY%" goto py_exists
echo [3/5] Erstelle Python-Umgebung...
"%UV%" venv "%VENV%" --python 3.12
if errorlevel 1 (
    echo FEHLER: Python-Umgebung konnte nicht erstellt werden.
    pause
    exit /b 1
)
echo [3/5] Python-Umgebung erstellt.
goto py_done
:py_exists
echo [3/5] Python-Umgebung vorhanden.
:py_done

REM ── Schritt 4: Pakete ─────────────────────────────────────────
if exist "%VENV%\Lib\site-packages\playwright" goto pkgs_exists
echo [4/5] Installiere Pakete (einmalig, ca. 2-3 Min)...
"%UV%" pip install --python "%PY%" greenlet playwright Pillow
echo [4/5] Pakete installiert.
goto pkgs_done
:pkgs_exists
echo [4/5] Pruefe Pakete auf Updates...
"%UV%" pip install --python "%PY%" --upgrade greenlet playwright Pillow
:pkgs_done

REM ── Schritt 5: Chromium ───────────────────────────────────────
set CHROMIUM_FOUND=0
for /d %%d in ("%LOCALAPPDATA%\ms-playwright\chromium-*") do set CHROMIUM_FOUND=1
if %CHROMIUM_FOUND%==0 (
    echo [5/5] Installiere Chromium (ca. 200 MB, einmalig)...
    "%PY%" -m playwright install chromium
    echo [5/5] Chromium installiert.
) else (
    echo [5/5] Chromium vorhanden.
)

echo.
echo  Setup abgeschlossen. Starte Programm...
echo.

REM ── GUI starten ───────────────────────────────────────────────
if not exist "%SRC%\gui.py" (
    echo FEHLER: src\gui.py nicht gefunden.
    pause
    exit /b 1
)

if exist "%PYW%" (
    "%PYW%" "%SRC%\gui.py"
) else (
    "%PY%" "%SRC%\gui.py"
)
