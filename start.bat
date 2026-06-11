@echo off
title Amazon Rechnungs-Downloader
cd /d "%~dp0"

set SRC=%~dp0src
set VENV=%~dp0src\.venv
set PY=%VENV%\Scripts\python.exe
set PYW=%VENV%\Scripts\pythonw.exe

REM ── Brauchen wir Setup? ───────────────────────────────────────
if exist "%PY%" goto check_playwright

echo.
echo  ================================================
echo   Erster Start - Einmalige Installation
echo  ================================================
echo.

REM ── uv finden ────────────────────────────────────────────────
set UV=
for /f "delims=" %%i in ('where uv 2^>nul') do (
    if "%UV%"=="" set UV=%%i
)
if "%UV%"=="" if exist "%USERPROFILE%\.local\bin\uv.exe" set UV=%USERPROFILE%\.local\bin\uv.exe
if "%UV%"=="" if exist "%USERPROFILE%\.cargo\bin\uv.exe" set UV=%USERPROFILE%\.cargo\bin\uv.exe

if "%UV%"=="" (
    echo [1/4] Installiere uv...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if exist "%USERPROFILE%\.local\bin\uv.exe" set UV=%USERPROFILE%\.local\bin\uv.exe
    if exist "%USERPROFILE%\.cargo\bin\uv.exe" set UV=%USERPROFILE%\.cargo\bin\uv.exe
    if "%UV%"=="" (
        echo FEHLER: uv konnte nicht installiert werden.
        pause
        exit /b 1
    )
    echo [1/4] uv installiert.
) else (
    echo [1/4] uv gefunden.
)

REM ── Python-Umgebung ───────────────────────────────────────────
echo [2/4] Erstelle Python-Umgebung...
"%UV%" venv "%VENV%" --python 3.12
if errorlevel 1 (
    REM Python 3.12 nicht verfuegbar - direkt herunterladen
    echo       Python 3.12 nicht gefunden. Lade herunter (ca. 25 MB)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP%\python312.exe'"
    if exist "%TEMP%\python312.exe" (
        "%TEMP%\python312.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
        del "%TEMP%\python312.exe"
    )
    "%UV%" venv "%VENV%" --python 3.12
    if errorlevel 1 (
        echo FEHLER: Python-Umgebung konnte nicht erstellt werden.
        pause
        exit /b 1
    )
)
echo [2/4] Python-Umgebung erstellt.

REM ── Pakete ────────────────────────────────────────────────────
echo [3/4] Installiere Pakete (einmalig, ca. 2-3 Min)...
"%UV%" pip install --python "%PY%" greenlet playwright Pillow
echo [3/4] Pakete installiert.

REM ── Chromium ─────────────────────────────────────────────────
echo [4/4] Installiere Chromium (ca. 200 MB, einmalig)...
"%PY%" -m playwright install chromium
echo [4/4] Chromium installiert.

echo.
echo  Installation abgeschlossen!
echo.
goto create_shortcut

:check_playwright
REM Pruefen ob Playwright-Browser vorhanden, sonst nachinstallieren
set CHROMIUM_FOUND=0
for /d %%d in ("%LOCALAPPDATA%\ms-playwright\chromium-*") do set CHROMIUM_FOUND=1
if %CHROMIUM_FOUND%==0 (
    echo Installiere Chromium-Browser...
    "%PY%" -m playwright install chromium
)

REM Pakete updaten (schnell, da gecacht)
set UV=
for /f "delims=" %%i in ('where uv 2^>nul') do (
    if "%UV%"=="" set UV=%%i
)
if "%UV%"=="" if exist "%USERPROFILE%\.local\bin\uv.exe" set UV=%USERPROFILE%\.local\bin\uv.exe
if "%UV%"=="" if exist "%USERPROFILE%\.cargo\bin\uv.exe" set UV=%USERPROFILE%\.cargo\bin\uv.exe
if not "%UV%"=="" (
    "%UV%" pip install --python "%PY%" --upgrade greenlet playwright Pillow >nul 2>&1
)

:create_shortcut
REM ── Desktop-Shortcut anlegen (einmalig) ──────────────────────
set SHORTCUT=%USERPROFILE%\Desktop\Amazon Rechnungen.lnk
if not exist "%SHORTCUT%" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ws = New-Object -ComObject WScript.Shell; ^
         $s = $ws.CreateShortcut('%SHORTCUT%'); ^
         $s.TargetPath = '%~dp0start.bat'; ^
         $s.WorkingDirectory = '%~dp0'; ^
         $s.IconLocation = 'shell32.dll,13'; ^
         $s.Description = 'Amazon Rechnungs-Downloader'; ^
         $s.Save()"
    if exist "%SHORTCUT%" (
        echo Desktop-Verknuepfung erstellt!
    )
)

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
