# Changelog

## v1.1.0 (2026-06-11)
### Neu
- Taggenauer Zeitraum (Von/Bis) als Alternative zur Jahresauswahl
- Artikelname im Dateinamen (erste N Wörter, konfigurierbar)
- Live-Protokoll während des Downloads
- Stop-Button zum Abbrechen laufender Downloads
- Ordner öffnen — direkt aus der GUI
- Auto-öffnen nach erfolgreichem Download
- Einstellungen werden in %APPDATA%\AmazonInvoiceDL gespeichert
- Farbiges Protokoll (Fehler rot, Erfolg grün, Warnungen orange)
- Versionsnummer im Fenstertitel
- Hinweis beim ersten Start

### Geändert
- Scrollbares, veränderbares Fenster
- Stop-Button wird nur während eines Downloads angezeigt
- Python wird bei Bedarf automatisch installiert (kein manueller Schritt)
- Pakete werden bei jedem Start auf Updates geprüft

### Behoben
- CMD-Fenster öffnet sich nicht mehr beim GUI-Start
- Download blockiert nicht mehr nach Abschluss (kein "Enter drücken")

## v1.0.0 (2026-06-05)
### Erstveröffentlichung
- Amazon.de Rechnungs-Download
- Jahresauswahl mit Schnellauswahl-Buttons
- Rechnungs-PDFs und Bestellübersichten
- Grafische Oberfläche
