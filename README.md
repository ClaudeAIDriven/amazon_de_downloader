# Amazon.de Rechnungs-Downloader

Lädt automatisch alle Rechnungen von amazon.de als PDF herunter.

## Schnellstart

1. ZIP herunterladen und entpacken
2. **`install_and_run.bat`** doppelklicken
3. Alles wird automatisch installiert — Python, Browser, Pakete (~250 MB, einmalig)
4. Im Browser bei Amazon einloggen
5. Fertig — Rechnungen landen im gewählten Ordner

Beim nächsten Mal einfach **`start.bat`** doppelklicken.

## Voraussetzungen

- Windows 10 oder 11
- Internetverbindung (für die erste Installation)
- Ein Amazon.de-Konto

**Kein Python, kein technisches Wissen nötig** — alles wird vollautomatisch eingerichtet, einschließlich Python falls nicht vorhanden.

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



---

## ☕ Unterstützung / Support

**DE:** Dieses Tool ist kostenlos und wird in meiner Freizeit gepflegt. Wer möchte, kann mich gerne mit einem kleinen Betrag unterstützen — das freut mich sehr!

**EN:** This tool is free and maintained in my spare time. If it saved you some work, feel free to buy me a coffee — much appreciated!

[![Donate via PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=RBNJ9PQF7J5T8)

&nbsp;

![QR Code](QR-Code.png)
