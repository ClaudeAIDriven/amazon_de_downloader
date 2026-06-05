# Amazon.de Rechnungs-Downloader

Lädt automatisch alle Rechnungen von amazon.de als PDF herunter.

## Schnellstart

1. Diesen Ordner herunterladen (grüner "Code"-Button → "Download ZIP")
2. ZIP entpacken
3. **`install_and_run.bat`** doppelklicken
4. Bei der ersten Ausführung wird alles automatisch installiert (~200 MB, einmalig)
5. Im Browser bei Amazon einloggen wenn das Fenster aufgeht
6. Fertig — Rechnungen landen im Ordner `downloads\`

## Voraussetzungen

- Windows 10 oder 11
- Internetverbindung (für die erste Installation)
- Ein Amazon.de-Konto

Kein Python, kein technisches Wissen nötig — alles wird automatisch eingerichtet.

## Verwendung

```
install_and_run.bat
```

Das Script fragt nach dem Jahr (z.B. `2025` oder `2024,2025,2026`).

Alternativ direkt mit Parametern (für Fortgeschrittene):

```
.venv\Scripts\python.exe amazon_de_downloader.py --year=2025,2026
```

## Was wird heruntergeladen?

- Echte Rechnungs-PDFs (von `documents/download/...invoice.pdf`)
- Bei Bestellungen ohne direkte PDF-Rechnung: Druckbare Bestellübersicht

## Dateinamen

```
YYYYMMDD_<Betrag>_amazon_<BestellID>.pdf
```

Beispiel: `20250315_49.99_amazon_302-1234567-8901234.pdf`

## Hinweise

- Beim ersten Start dauert die Installation 2–3 Minuten
- Bei 2FA oder CAPTCHA: einfach manuell im Browser ausfüllen, das Script wartet
- Bereits vorhandene Dateien werden übersprungen
- Stornierte Bestellungen werden übersprungen

## Technik

Verwendet [Playwright](https://playwright.dev/) zur Browser-Automatisierung und [uv](https://docs.astral.sh/uv/) als Python-Paketmanager. Keine externen APIs, kein Cloud-Upload — alles läuft lokal.
