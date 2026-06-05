@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Amazon Rechnungs-Downloader

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║      Amazon.de Rechnungs-Downloader                  ║
echo  ║      github.com/YOUR_USERNAME/amazon-invoice-dl      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

REM ── Arbeitsverzeichnis = Ordner dieser .bat Datei ──────────────
cd /d "%~dp0"

REM ── Prüfe ob uv installiert ist ────────────────────────────────
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo  [1/4] Installiere uv (Python-Paketmanager)...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
    REM PATH aktualisieren
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
    where uv >nul 2>&1
    if !errorlevel! neq 0 (
        echo  FEHLER: uv konnte nicht installiert werden.
        echo  Bitte manuell installieren: https://docs.astral.sh/uv/
        pause
        exit /b 1
    )
    echo  [1/4] uv installiert!
) else (
    echo  [1/4] uv bereits vorhanden.
)

REM ── Virtuelle Umgebung erstellen ───────────────────────────────
if not exist ".venv" (
    echo  [2/4] Erstelle Python-Umgebung (Python 3.12)...
    uv venv .venv --python 3.12 >nul 2>&1
    if !errorlevel! neq 0 (
        echo  FEHLER: Python-Umgebung konnte nicht erstellt werden.
        pause
        exit /b 1
    )
    echo  [2/4] Python-Umgebung erstellt!
) else (
    echo  [2/4] Python-Umgebung bereits vorhanden.
)

REM ── Abhängigkeiten installieren ────────────────────────────────
if not exist ".venv\Lib\site-packages\playwright" (
    echo  [3/4] Installiere Abhängigkeiten (Playwright etc.)...
    echo        (Das kann 2-3 Minuten dauern beim ersten Mal)
    uv pip install --python .venv\Scripts\python.exe "greenlet>=3.0.0" >nul 2>&1
    uv pip install --python .venv\Scripts\python.exe "playwright>=1.40.0" >nul 2>&1
    echo  [3/4] Abhängigkeiten installiert!
) else (
    echo  [3/4] Abhängigkeiten bereits vorhanden.
)

REM ── Playwright Browser installieren ───────────────────────────
if not exist "%USERPROFILE%\AppData\Local\ms-playwright" (
    echo  [4/4] Installiere Chromium-Browser (~200 MB)...
    echo        (Nur beim ersten Mal nötig)
    .venv\Scripts\python.exe -m playwright install chromium
    echo  [4/4] Browser installiert!
) else (
    echo  [4/4] Browser bereits vorhanden.
)

echo.
echo  ══════════════════════════════════════════════════════
echo.

REM ── Jahr abfragen ──────────────────────────────────────────────
set /p JAHR="  Welches Jahr(e) herunterladen? (z.B. 2025 oder 2024,2025,2026): "
if "%JAHR%"=="" set JAHR=%date:~6,4%

echo.
echo  Starte Download für Jahr(e): %JAHR%
echo  Rechnungen werden gespeichert in: %~dp0downloads\
echo.

REM ── Script starten ─────────────────────────────────────────────
.venv\Scripts\python.exe amazon_de_downloader.py --year=%JAHR%

echo.
echo  ══════════════════════════════════════════════════════
echo  Fertig! Rechnungen findest du im Ordner: downloads\
echo  ══════════════════════════════════════════════════════
echo.
pause
