"""
Amazon.de Rechnungs-Downloader
================================
Verwendung:
    python amazon_de_downloader.py --year=2024
    python amazon_de_downloader.py --year=2024,2025,2026
    python amazon_de_downloader.py --year=2024 --email=du@example.com --password=geheim

Zugangsdaten (Priorität):
    1. Kommandozeile: --email / --password
    2. Umgebungsvariablen: AMAZON_EMAIL / AMAZON_PASSWORD
    3. .env Datei im gleichen Ordner

Rechnungen landen in: ./downloads/
"""

import os, sys, time, random, argparse, re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

def load_dotenv():
    for p in [Path(".env"), Path(__file__).parent / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

load_dotenv()

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("FEHLER: pip install playwright && python -m playwright install")
    sys.exit(1)

DE_MONATE = {
    "Januar":"January","Februar":"February","März":"March","April":"April",
    "Mai":"May","Juni":"June","Juli":"July","August":"August",
    "September":"September","Oktober":"October","November":"November","Dezember":"December"
}

class InvoiceLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href and any(part in href for part in (
            "invoice.pdf",
            "documents/download",
            "gp/css/summary/print",
        )):
            self._href = href
            self._text = []

    def handle_data(self, data):
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            self.links.append({
                "text": " ".join("".join(self._text).split()),
                "href": self._href,
            })
            self._href = None
            self._text = []

def invoice_links_from_html(html):
    parser = InvoiceLinkParser()
    parser.feed(html)
    return parser.links

def warte(a=2, b=4):
    time.sleep(random.uniform(a, b))

def datum_parsen(text):
    text = text.strip()
    for fmt in ("%B %d, %Y", "%d. %B %Y"):
        try: return datetime.strptime(text, fmt)
        except: pass
    t = text
    for de, en in DE_MONATE.items():
        t = t.replace(de, en)
    t = t.replace(".", "").strip()
    for fmt in ("%d %B %Y", "%B %d %Y"):
        try: return datetime.strptime(t, fmt)
        except: pass
    return None

def betrag_bereinigen(text):
    text = text.replace("EUR","").replace("€","").replace("$","").replace("\xa0","").replace(" ","").strip()
    if "," in text and "." in text:
        text = text.replace(".","").replace(",",".")
    elif "," in text:
        text = text.replace(",",".")
    return text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", default=None)
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--output", default=None, help="Zielordner für PDFs")
    parser.add_argument("--invoices", action="store_true", default=False,
                        help="Rechnungs-PDFs herunterladen")
    parser.add_argument("--overview", action="store_true", default=False,
                        help="Bestellübersichten herunterladen")
    parser.add_argument("--daterange", default=None,
                        help="Taggenauer Zeitraum: YYYYMMDD-YYYYMMDD")
    parser.add_argument("--title-words", type=int, default=0,
                        help="Anzahl Wörter des Artikelnamens im Dateinamen (0=deaktiviert)")
    parser.add_argument("--no-pause", action="store_true", default=False,
                        help="Kein Enter-Warten am Ende (für GUI-Modus)")
    args = parser.parse_args()

    # Wenn keine Option angegeben: beide aktivieren (Abwärtskompatibilität)
    if not args.invoices and not args.overview:
        args.invoices = True
        args.overview = True

    email    = args.email    or os.environ.get("AMAZON_EMAIL")
    password = args.password or os.environ.get("AMAZON_PASSWORD")
    # Taggenauer Zeitraum hat Vorrang vor Jahren
    if args.daterange:
        start_str, end_str = args.daterange.split("-", 1)
        global_start = datetime.strptime(start_str, "%Y%m%d")
        global_end   = datetime.strptime(end_str,   "%Y%m%d")
        # Jahre aus Datumsbereich ableiten
        jahre = list(range(global_start.year, global_end.year + 1))
    else:
        global_start = None
        global_end   = None
        jahre = [int(y.strip()) for y in args.year.split(",")] if args.year else [datetime.now().year]

    title_words = getattr(args, "title_words", 0) or 0

    ziel = Path(args.output) if args.output else Path("downloads")
    ziel.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*55}")
    print(f"  Amazon.de Downloader — Jahre: {', '.join(map(str,jahre))}")
    print(f"{'='*55}\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=30)
        ctx = browser.new_context(viewport={"width":1280,"height":900})
        page = ctx.new_page()

        # Cookie-Banner
        page.goto("https://www.amazon.de/", wait_until="domcontentloaded")
        warte(1,2)
        for sel in ['#sp-cc-accept','button:has-text("Alle akzeptieren")','input[name="accept"]']:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible(): el.click(); warte(1,2); break
            except: pass

        # Login
        if email and password:
            print("Automatischer Login...")
            try:
                page.goto("https://www.amazon.de/ap/signin?openid.return_to=https://www.amazon.de/&openid.identity=http://specs.openid.net/auth/2.0/identifier_select&openid.assoc_handle=deflex&openid.mode=checkid_setup&openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select&openid.ns=http://specs.openid.net/auth/2.0", wait_until="domcontentloaded")
                warte()
                for sel in ['input[type="email"]','#ap_email']:
                    try:
                        el = page.wait_for_selector(sel, timeout=5000)
                        el.fill(email); break
                    except: pass
                for btn in ["Weiter","Continue"]:
                    try: page.get_by_role("button",name=btn).click(timeout=3000); break
                    except: pass
                warte()
                for sel in ['input[type="password"]','#ap_password']:
                    try:
                        el = page.wait_for_selector(sel, timeout=5000)
                        el.fill(password); break
                    except: pass
                try: page.query_selector('#rememberMe').check()
                except: pass
                for btn in ["Anmelden","Sign in","Sign-In"]:
                    try: page.get_by_role("button",name=btn).click(timeout=3000); break
                    except: pass
                warte(2,3)
            except Exception as e:
                print(f"  Auto-Login fehlgeschlagen: {e}")

        # Warte auf Login
        print("Warte bis eingeloggt (max. 5 Min)...")
        print("(2FA/CAPTCHA bitte manuell abschließen)\n")
        try:
            page.wait_for_function("""() => {
                const el = document.querySelector('#nav-link-accountList-nav-line-1');
                if (!el) return false;
                const t = el.innerText.trim().toLowerCase();
                return t.length > 0 && !t.includes('anmelden') && !t.includes('sign in');
            }""", timeout=300000)
            print("✓ Eingeloggt!\n")
        except:
            print("WARNUNG: Login-Status unklar, fahre fort.\n")

        gesamt_total = 0
        uebersp_total = 0

        for jahr in jahre:
            if global_start and global_end:
                # Taggenauer Modus: Schnittemenge von Jahr und globalem Bereich
                start_dt = max(datetime(jahr, 1, 1),  global_start)
                end_dt   = min(datetime(jahr, 12, 31), global_end)
                if start_dt > end_dt:
                    continue  # Jahr liegt außerhalb des Bereichs
            else:
                start_dt = datetime(jahr, 1, 1)
                end_dt   = datetime(jahr, 12, 31)
            print(f"{'─'*55}")
            print(f"  Jahr {jahr}")
            print(f"{'─'*55}")

            # Zur Bestellseite für dieses Jahr
            page.goto(f"https://www.amazon.de/your-orders/orders?timeFilter=year-{jahr}&ref_=ppx_yo2ov_dt_b_filter_all_{jahr}", wait_until="domcontentloaded")
            warte(3,5)

            # Warte auf irgendeine Bestellkarte oder "keine Bestellungen"
            try:
                page.wait_for_selector('[data-component="order"], .order, .a-box-group', timeout=15000)
            except:
                print(f"  Keine Bestellseite geladen für {jahr}")
                continue

            gesamt = 0
            uebersp = 0
            seite = 1
            aktuelle_url = page.url

            while True:
                print(f"\n  Seite {seite} — {page.url[:70]}")
                warte(1,2)

                # HTML holen und Bestellkarten identifizieren
                # Verwende JavaScript um die Bestellkarten zu finden
                bestellungen_data = page.evaluate("""() => {
                    const results = [];
                    
                    // Verschiedene Selektoren probieren
                    let cards = Array.from(document.querySelectorAll('[data-component="order"]'));
                    if (cards.length === 0) cards = Array.from(document.querySelectorAll('.order'));
                    if (cards.length === 0) cards = Array.from(document.querySelectorAll('.a-box-group.a-spacing-base'));
                    
                    for (const card of cards) {
                        const text = card.innerText || '';
                        
                        // Datum suchen
                        const datumMatch = text.match(/\\d{1,2}\\.\\s+\\w+\\s+\\d{4}/) || 
                                           text.match(/\\w+ \\d{1,2}, \\d{4}/);
                        
                        // Betrag suchen  
                        const betragMatch = text.match(/(?:EUR|€)\\s*([\\d.,]+)/) ||
                                            text.match(/([\\d]+,[\\d]+)\\s*€/) ||
                                            text.match(/\\$\\s*([\\d.,]+)/);
                        
                        // Bestell-ID suchen
                        const idMatch = text.match(/\\d{3}-\\d{7}-\\d{7}/);
                        
                        // Storniert?
                        const storniert = text.includes('Storniert') || text.includes('Cancelled') || text.includes('storniert');
                        
                        // Rechnungslinks
                        const links = Array.from(card.querySelectorAll('a')).filter(a => {
                            const t = (a.innerText || a.textContent || '').trim();
                            return t.includes('Rechnung') || t.includes('Invoice') || t.includes('invoice');
                        }).map(a => ({text: a.innerText.trim(), href: a.href}));

                        // Artikelname: aus Produkt-Links extrahieren (href enthält /dp/)
                        let artikelName = '';
                        const produktLinks = Array.from(card.querySelectorAll('a')).filter(a =>
                            a.href && (a.href.includes('/dp/') || a.href.includes('/gp/product/'))
                        );
                        if (produktLinks.length > 0) {
                            // Ersten Produktlink nehmen, Text bereinigen
                            artikelName = (produktLinks[0].innerText || produktLinks[0].textContent || '').trim();
                            // Nur erste Zeile falls mehrzeilig
                            artikelName = artikelName.split('\\n')[0].trim();
                        }
                        
                        results.push({
                            datum_raw: datumMatch ? datumMatch[0] : null,
                            betrag_raw: betragMatch ? betragMatch[0] : null,
                            bestell_id: idMatch ? idMatch[0] : null,
                            storniert: storniert,
                            rechnungslinks: links,
                            text_preview: text.substring(0, 100),
                            artikel_name: artikelName
                        });
                    }
                    return results;
                }""")

                if not bestellungen_data:
                    print(f"  Keine Bestellkarten gefunden — Ende für Jahr {jahr}")
                    break

                print(f"  {len(bestellungen_data)} Bestellkarten")

                fertig = False
                for b in bestellungen_data:
                    # Datum parsen
                    if not b['datum_raw']:
                        print(f"  ⚠ Kein Datum gefunden, überspringe: {b['text_preview'][:60]}")
                        uebersp += 1
                        continue

                    datum = datum_parsen(b['datum_raw'])
                    if datum is None:
                        print(f"  ⚠ Datum nicht parsbar: '{b['datum_raw']}'")
                        uebersp += 1
                        continue

                    if datum > end_dt: continue
                    if datum < start_dt:
                        fertig = True
                        break

                    if b['storniert']:
                        print(f"  ↷ {b['bestell_id'] or '?'} — storniert")
                        uebersp += 1
                        continue

                    if not b['bestell_id']:
                        print(f"  ⚠ Keine Bestell-ID — überspringe")
                        uebersp += 1
                        continue

                    # Rechnungslinks aus Bestellkarte als Fallback
                    karten_links = b.get('rechnungslinks', [])
                    bestell_id = b['bestell_id']
                    betrag     = betrag_bereinigen(b['betrag_raw'] or "0")

                    # Artikelname für Dateinamen extrahieren
                    artikel_teil = ""
                    if title_words > 0:
                        try:
                            # Gezielt den Artikelnamen aus dem DOM-Produktlink nutzen
                            artikel_raw = b.get('artikel_name', '') or b.get('text_preview', '')
                            woerter = [w for w in artikel_raw.replace('\n',' ').split()
                                       if len(w) > 2 and not w.replace(',','').replace('.','').replace('€','').replace('$','').isdigit()]
                            if woerter:
                                genommen = woerter[:title_words]
                                teil = '-'.join(re.sub(r'[^\w]','',w) for w in genommen if re.sub(r'[^\w]','',w))
                                if teil:
                                    artikel_teil = '_' + teil[:100]
                        except Exception:
                            artikel_teil = ""

                    # Rechnungs-Popover aufrufen für echte PDF-Download-Links
                    pdf_links = []
                    # Wenn nur Übersicht gewünscht: Popover überspringen
                    if args.invoices:
                        try:
                            pop_url = f"https://www.amazon.de/your-orders/invoice/popover?orderId={bestell_id}&ref_=fed_invoice_ajax"
                            response = ctx.request.get(pop_url, timeout=10000)
                            if response.ok:
                                pdf_links = invoice_links_from_html(response.text())
                        except Exception as e:
                            print(f"  ! Popover fehlgeschlagen ({e}) - nutze Fallback")

                    # Fallback: Links aus Bestellkarte (nur wenn invoices gewünscht)
                    if not pdf_links and karten_links and args.invoices:
                        pdf_links = karten_links

                    # Wenn overview deaktiviert und keine PDFs: überspringen
                    if not pdf_links and not args.overview:
                        print(f"  - {bestell_id} — keine Rechnungs-PDFs, überspringe")
                        uebersp += 1
                        continue

                    if not pdf_links and not args.invoices:
                        # Nur Übersicht gewünscht — direkt Bestellübersicht drucken
                        pass  # fällt durch zum Drucken

                    if not pdf_links and not args.overview and not args.invoices:
                        print(f"  ⚠ {bestell_id} — keine Rechnungslinks")
                        uebersp += 1
                        continue

                    # Jede gefundene Rechnung herunterladen
                    for idx, link in enumerate(pdf_links):
                        suffix = f"_{idx+1}" if len(pdf_links) > 1 else ""
                        dateiname = ziel / f"{datum.strftime('%Y%m%d')}_{betrag}{artikel_teil}_amazon_{bestell_id}{suffix}.pdf"

                        if dateiname.exists():
                            print(f"  ✓ {dateiname.name} — vorhanden")
                            uebersp += 1
                            continue

                        url = link['href'] if isinstance(link, dict) else link
                        if not url.startswith('http'):
                            url = 'https://www.amazon.de' + url

                        label = link['text'] if isinstance(link, dict) else 'Rechnung'
                        print(f"  ↓ {dateiname.name} [{label}]")
                        try:
                            # PDF über Download-Event abfangen (Playwright-Methode)
                            with ctx.expect_download(timeout=15000) as dl_info:
                                dl_page = ctx.new_page()
                                try:
                                    dl_page.goto(url, wait_until="commit")
                                except:
                                    pass
                                dl_page.close()

                            download = dl_info.value
                            download.save_as(str(dateiname))
                            gesamt += 1

                        except Exception:
                            # Fallback: direkt per requests-ähnlichem Weg via Playwright APIRequestContext
                            try:
                                try: dl_page.close()
                                except: pass
                                api_req = ctx.request
                                response = api_req.get(url)
                                body = response.body()
                                if len(body) > 1000 and body[:4] == b'%PDF':
                                    dateiname.write_bytes(body)
                                    gesamt += 1
                                else:
                                    # HTML-Seite → als PDF drucken
                                    pr_page = ctx.new_page()
                                    pr_page.goto(url, wait_until="networkidle")
                                    try:
                                        pr_page.wait_for_selector('#od-subtotals', timeout=12000)
                                    except: pass
                                    try:
                                        pr_page.wait_for_function("""() => {
                                            return Array.from(document.querySelectorAll('img'))
                                                .every(img => !img.src || img.complete);
                                        }""", timeout=8000)
                                    except: pass
                                    warte(3, 5)
                                    pr_page.pdf(path=str(dateiname), format="A4",
                                                margin={"top":"1cm","right":"1cm","bottom":"1cm","left":"1cm"},
                                                print_background=True)
                                    pr_page.close()
                                    gesamt += 1
                            except Exception as e2:
                                print(f"  ✗ Download-Fehler: {e2}")
                                try: pr_page.close()
                                except: pass
                                uebersp += 1
                        warte(1, 2)

                if fertig:
                    print(f"\n  Alle Bestellungen für {jahr} verarbeitet.")
                    break

                # Nächste Seite per JavaScript suchen
                naechste_url = page.evaluate("""() => {
                    // Amazon Pagination: li.a-last > a
                    const el = document.querySelector('ul.a-pagination li.a-last a');
                    if (el && el.href && !el.closest('li').classList.contains('a-disabled')) {
                        return el.href;
                    }
                    return null;
                }""")

                if not naechste_url:
                    print(f"\n  Letzte Seite für {jahr} erreicht.")
                    break

                # Prüfe ob URL sich ändern würde (Endlosschutz)
                if naechste_url == aktuelle_url:
                    print(f"\n  Pagination-URL unverändert — stoppe.")
                    break

                aktuelle_url = naechste_url
                page.goto(naechste_url, wait_until="domcontentloaded")
                warte(2,4)
                seite += 1

            if gesamt == 0 and uebersp == 0:
                print(f"\n  Jahr {jahr}: Keine Bestellungen gefunden.")
            else:
                print(f"\n  Jahr {jahr}: {gesamt} gespeichert, {uebersp} übersprungen")
            gesamt_total += gesamt
            uebersp_total += uebersp

        print(f"\n{'='*55}")
        print(f"  Fertig! {gesamt_total} Rechnungen, {uebersp_total} übersprungen")
        print(f"  Ordner: {ziel.resolve()}")
        print(f"{'='*55}\n")

        if not args.no_pause and sys.stdin.isatty():
            input("Enter drücken zum Schließen...")
        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
