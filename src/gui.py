"""
Amazon.de Rechnungs-Downloader - GUI
"""

import json
import os
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


BG = "#111827"
BG_PANEL = "#172033"
BG_CARD = "#1f2937"
BG_INPUT = "#0f172a"
ACCENT = "#f59e0b"
ACCENT_HOVER = "#fbbf24"
TEXT = "#f8fafc"
TEXT_DIM = "#a7b0c0"
SUCCESS = "#34d399"
ERROR = "#fb7185"
BORDER = "#334155"
PAYPAL = "#003087"

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_BTN = ("Segoe UI", 11, "bold")
FONT_CAP = ("Segoe UI", 8, "bold")
FONT_MONO = ("Consolas", 9)

APP_DIR = Path(__file__).parent
VERSION = "1.1.0"
_appdata = Path(os.environ.get("APPDATA", "")) / "AmazonInvoiceDL"
_appdata.mkdir(parents=True, exist_ok=True) if _appdata.parent.exists() else None
SETTINGS_FILE = _appdata / "settings.json" if _appdata.exists() else APP_DIR / "settings.json"
DONATE_URL = "https://www.paypal.com/donate/?hosted_button_id=RBNJ9PQF7J5T8"


def card(parent, **kwargs):
    return tk.Frame(
        parent,
        bg=BG_CARD,
        highlightbackground=BORDER,
        highlightthickness=1,
        **kwargs,
    )


class AmazonDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Amazon Rechnungs-Downloader v{VERSION}")
        self.root.geometry("760x860")
        self.root.minsize(680, 700)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.settings = self._load_settings()
        self.first_run = not SETTINGS_FILE.exists()
        self.proc = None
        self.is_running = False
        self.last_output_folder = self.settings.get("folder", self._default_folder())

        self._build_ui()
        self._apply_settings()
        if self.first_run:
            self.root.after(500, self._show_first_run_hint)

    def _build_ui(self):
        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.outer = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.outer, anchor="nw")
        self.outer.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_canvas_window)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        header = tk.Frame(self.outer, bg=BG, pady=18)
        header.pack(fill="x", padx=28)

        title_frame = tk.Frame(header, bg=BG)
        title_frame.pack(side="left", fill="x", expand=True)
        tk.Label(title_frame, text="Amazon Rechnungen", font=FONT_TITLE, bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(
            title_frame,
            text="PDFs laden, Fortschritt sehen, Einstellungen behalten.",
            font=FONT_SMALL,
            bg=BG,
            fg=TEXT_DIM,
        ).pack(anchor="w")

        self.open_folder_top_btn = tk.Button(
            header,
            text="Ordner oeffnen",
            font=FONT_SMALL,
            bg=BORDER,
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
            activebackground=ACCENT,
            activeforeground=BG,
            command=self._open_output_folder,
        )
        self.open_folder_top_btn.pack(side="right")

        self._sep(self.outer)

        main = tk.Frame(self.outer, bg=BG)
        main.pack(fill="both", expand=True, padx=28, pady=6)

        self._build_period(main)
        self._build_folder(main)
        self._build_options(main)
        self._build_status(main)
        self._build_log(main)
        self._build_footer()

    def _build_period(self, parent):
        self._cap(parent, "ZEITRAUM")
        quick = tk.Frame(parent, bg=BG)
        quick.pack(fill="x", pady=(4, 4))

        cur = datetime.now().year
        presets = [
            ("Dieses Jahr", str(cur)),
            ("Letztes Jahr", str(cur - 1)),
            ("2 Jahre", f"{cur-1},{cur}"),
            ("3 Jahre", f"{cur-2},{cur-1},{cur}"),
            ("Alle 2018+", ",".join(str(y) for y in range(2018, cur + 1))),
        ]
        for label, years in presets:
            tk.Button(
                quick,
                text=label,
                font=FONT_SMALL,
                bg=BORDER,
                fg=TEXT_DIM,
                relief="flat",
                padx=9,
                pady=4,
                cursor="hand2",
                activebackground=ACCENT,
                activeforeground=BG,
                command=lambda y=years: self._set_years_preset(y),
            ).pack(side="left", padx=(0, 6), pady=2)

        box = card(parent)
        box.pack(fill="x", pady=(4, 4))
        tk.Label(box, text="Jahre:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_DIM, width=7, anchor="w").pack(
            side="left", padx=(12, 0), pady=9
        )
        self.year_var = tk.StringVar(value=str(cur))
        tk.Entry(
            box,
            textvariable=self.year_var,
            font=FONT_BOLD,
            bg=BG_CARD,
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            width=28,
        ).pack(side="left", padx=8, pady=9)
        tk.Label(box, text="z.B. 2024 oder 2023,2024,2025", font=FONT_SMALL, bg=BG_CARD, fg=TEXT_DIM).pack(
            side="left", padx=(0, 12)
        )

        self.daterange_open = False
        self.daterange_btn = tk.Button(
            parent,
            text="> Taggenauer Zeitraum",
            font=FONT_SMALL,
            bg=BG,
            fg=TEXT_DIM,
            relief="flat",
            anchor="w",
            cursor="hand2",
            activebackground=BG,
            activeforeground=ACCENT,
            command=self._toggle_daterange,
        )
        self.daterange_btn.pack(fill="x", pady=(2, 0))

        self.daterange_frame = card(parent)
        row = tk.Frame(self.daterange_frame, bg=BG_CARD)
        row.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(row, text="Von:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_DIM, width=5, anchor="w").pack(side="left")
        self.date_from_var = tk.StringVar(value=f"01.01.{cur}")
        tk.Entry(
            row,
            textvariable=self.date_from_var,
            font=FONT_BOLD,
            bg=BG_CARD,
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            width=12,
        ).pack(side="left", padx=(6, 16))
        tk.Label(row, text="Bis:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_DIM, width=4, anchor="w").pack(side="left")
        self.date_to_var = tk.StringVar(value=datetime.now().strftime("%d.%m.%Y"))
        tk.Entry(
            row,
            textvariable=self.date_to_var,
            font=FONT_BOLD,
            bg=BG_CARD,
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            width=12,
        ).pack(side="left", padx=6)
        tk.Label(row, text="TT.MM.JJJJ", font=FONT_SMALL, bg=BG_CARD, fg=TEXT_DIM).pack(side="left", padx=4)
        tk.Label(
            self.daterange_frame,
            text="Der genaue Zeitraum ersetzt die Jahresauswahl.",
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT_DIM,
            anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 8))

    def _build_folder(self, parent):
        self._cap(parent, "SPEICHERORT")
        box = card(parent)
        box.pack(fill="x", pady=(4, 12))
        tk.Label(box, text="Ordner:", font=FONT_LABEL, bg=BG_CARD, fg=TEXT_DIM, width=7, anchor="w").pack(
            side="left", padx=(12, 0), pady=10
        )
        self.folder_var = tk.StringVar(value=self._default_folder())
        tk.Entry(
            box,
            textvariable=self.folder_var,
            font=FONT_SMALL,
            bg=BG_CARD,
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
        ).pack(side="left", fill="x", expand=True, padx=8, pady=10)
        tk.Button(
            box,
            text="...",
            font=FONT_SMALL,
            bg=BORDER,
            fg=TEXT,
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            activebackground=ACCENT,
            activeforeground=BG,
            command=self._browse,
        ).pack(side="right", padx=(0, 8), pady=6)

    def _build_options(self, parent):
        self._cap(parent, "OPTIONEN")
        box = card(parent)
        box.pack(fill="x", pady=(4, 12))

        self.invoices_var = tk.BooleanVar(value=True)
        self.overview_var = tk.BooleanVar(value=True)
        self.open_when_done_var = tk.BooleanVar(value=True)
        self.remember_settings_var = tk.BooleanVar(value=True)

        self._check(box, "Rechnungs-PDFs herunterladen", self.invoices_var)
        self._check(box, "Bestelluebersicht als PDF, falls keine Rechnung vorhanden", self.overview_var)
        self._check(box, "Ordner nach erfolgreichem Download oeffnen", self.open_when_done_var)
        self._check(box, "Einstellungen merken", self.remember_settings_var)

        row = tk.Frame(box, bg=BG_CARD)
        row.pack(fill="x", padx=12, pady=(8, 10))
        self.title_words_var = tk.BooleanVar(value=True)
        self._check(row, "Erste", self.title_words_var, side="left", padx=0, pady=0)
        self.title_words_count = tk.Spinbox(
            row,
            from_=1,
            to=10,
            width=3,
            font=FONT_BOLD,
            bg=BG_INPUT,
            fg=TEXT,
            buttonbackground=BORDER,
            relief="flat",
            insertbackground=ACCENT,
        )
        self.title_words_count.delete(0, "end")
        self.title_words_count.insert(0, "3")
        self.title_words_count.pack(side="left", padx=6)
        tk.Label(row, text="Woerter des Artikelnamens im Dateinamen", font=FONT_LABEL, bg=BG_CARD, fg=TEXT).pack(
            side="left", padx=4
        )

    def _build_status(self, parent):
        self._cap(parent, "DOWNLOAD")
        self.status_var = tk.StringVar(value="Bereit.")
        self.status_lbl = tk.Label(parent, textvariable=self.status_var, font=FONT_SMALL, bg=BG, fg=TEXT_DIM, anchor="w")
        self.status_lbl.pack(fill="x", pady=(0, 6))

        self.progress = ttk.Progressbar(parent, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 10))
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TProgressbar", troughcolor=BG_CARD, background=ACCENT, thickness=5)

        actions = tk.Frame(parent, bg=BG)
        actions.pack(fill="x")
        self.start_btn = tk.Button(
            actions,
            text="Login & Download starten",
            font=FONT_BTN,
            bg=ACCENT,
            fg=BG,
            relief="flat",
            padx=18,
            pady=13,
            cursor="hand2",
            activebackground=ACCENT_HOVER,
            activeforeground=BG,
            command=self._start,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.stop_btn = tk.Button(
            actions,
            text="Stop",
            font=FONT_BTN,
            bg=BORDER,
            fg=TEXT,
            relief="flat",
            padx=18,
            pady=13,
            cursor="hand2",
            activebackground=ERROR,
            activeforeground=BG,
            command=self._stop,
        )
        # Stop-Button initial nicht sichtbar — wird beim Start eingeblendet

    def _build_log(self, parent):
        self._cap(parent, "PROTOKOLL")
        box = card(parent)
        box.pack(fill="both", expand=True, pady=(4, 12))

        toolbar = tk.Frame(box, bg=BG_CARD)
        toolbar.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(toolbar, text="Live-Ausgabe", font=FONT_BOLD, bg=BG_CARD, fg=TEXT).pack(side="left")
        tk.Button(
            toolbar,
            text="Leeren",
            font=FONT_SMALL,
            bg=BORDER,
            fg=TEXT,
            relief="flat",
            padx=8,
            pady=3,
            cursor="hand2",
            command=self._clear_log,
        ).pack(side="right")

        log_frame = tk.Frame(box, bg=BG_CARD)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text = tk.Text(
            log_frame,
            height=10,
            wrap="word",
            bg=BG_INPUT,
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            font=FONT_MONO,
            state="disabled",
        )
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        # Farb-Tags
        self.log_text.tag_configure("error",   foreground=ERROR)
        self.log_text.tag_configure("success", foreground=SUCCESS)
        self.log_text.tag_configure("warn",    foreground=ACCENT)

    def _build_footer(self):
        self._sep(self.outer)
        footer = tk.Frame(self.outer, bg=BG, pady=10)
        footer.pack(fill="x", padx=28)

        try:
            from PIL import Image, ImageTk

            qr = APP_DIR / "QR-Code.png"
            if qr.exists():
                img = Image.open(qr).resize((54, 54), Image.LANCZOS)
                self._qr = ImageTk.PhotoImage(img)
                tk.Label(footer, image=self._qr, bg=BG).pack(side="left", padx=(0, 14))
        except Exception:
            pass

        text = tk.Frame(footer, bg=BG)
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text="Kostenloses Open-Source-Tool.", font=FONT_BOLD, bg=BG, fg=TEXT, anchor="w").pack(anchor="w")
        tk.Label(text, text="Unterstuetzung freut mich sehr.", font=FONT_SMALL, bg=BG, fg=TEXT_DIM, anchor="w").pack(
            anchor="w", pady=(1, 6)
        )
        tk.Button(
            text,
            text="Spenden via PayPal",
            font=FONT_SMALL,
            bg=PAYPAL,
            fg="white",
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            activebackground="#001f5b",
            activeforeground="white",
            command=lambda: webbrowser.open(DONATE_URL),
        ).pack(anchor="w")

    def _check(self, parent, text, var, side=None, padx=12, pady=(8, 0)):
        widget = tk.Checkbutton(
            parent,
            text=f"  {text}",
            variable=var,
            font=FONT_LABEL,
            bg=BG_CARD,
            fg=TEXT,
            selectcolor=BG_INPUT,
            activebackground=BG_CARD,
            activeforeground=ACCENT,
            highlightthickness=0,
            cursor="hand2",
        )
        if side:
            widget.pack(side=side, padx=padx, pady=pady)
        else:
            widget.pack(anchor="w", padx=padx, pady=pady)
        return widget

    def _sep(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=28, pady=2)

    def _cap(self, parent, text):
        tk.Label(parent, text=text, font=FONT_CAP, bg=BG, fg=ACCENT, anchor="w").pack(fill="x", pady=(8, 2))

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_canvas_window(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _default_folder(self):
        return str(Path.home() / "Downloads" / "Amazon-Rechnungen")

    def _load_settings(self):
        try:
            if SETTINGS_FILE.exists():
                return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_settings(self):
        if not self.remember_settings_var.get():
            return
        data = {
            "years": self.year_var.get().strip(),
            "folder": self.folder_var.get().strip(),
            "invoices": self.invoices_var.get(),
            "overview": self.overview_var.get(),
            "open_when_done": self.open_when_done_var.get(),
            "remember_settings": self.remember_settings_var.get(),
            "title_words": self.title_words_var.get(),
            "title_words_count": self.title_words_count.get(),
            "daterange_open": self.daterange_open,
            "date_from": self.date_from_var.get().strip(),
            "date_to": self.date_to_var.get().strip(),
        }
        try:
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _apply_settings(self):
        s = self.settings
        if s.get("years"):
            self.year_var.set(s["years"])
        if s.get("folder"):
            self.folder_var.set(s["folder"])
            self.last_output_folder = s["folder"]
        for key, var in [
            ("invoices", self.invoices_var),
            ("overview", self.overview_var),
            ("open_when_done", self.open_when_done_var),
            ("remember_settings", self.remember_settings_var),
            ("title_words", self.title_words_var),
        ]:
            if key in s:
                var.set(bool(s[key]))
        if s.get("title_words_count"):
            self.title_words_count.delete(0, "end")
            self.title_words_count.insert(0, str(s["title_words_count"]))
        if s.get("date_from"):
            self.date_from_var.set(s["date_from"])
        if s.get("date_to"):
            self.date_to_var.set(s["date_to"])
        if s.get("daterange_open"):
            self._toggle_daterange()

    def _show_first_run_hint(self):
        folder = self._default_folder()
        self._append_log(
            f"Willkommen! Einstellungen werden in %APPDATA%\\AmazonInvoiceDL gespeichert.\n"
            f"PDFs werden standardmaessig gespeichert in:\n  {folder}\n"
            f"Du kannst den Ordner oben aendern.\n"
        )

    def _set_years_preset(self, years):
        self.year_var.set(years)
        cur = datetime.now().year
        self.date_from_var.set(f"01.01.{cur}")
        self.date_to_var.set(datetime.now().strftime("%d.%m.%Y"))

    def _toggle_daterange(self):
        self.daterange_open = not self.daterange_open
        if self.daterange_open:
            self.daterange_frame.pack(fill="x", pady=(0, 8))
            self.daterange_btn.configure(text="v Taggenauer Zeitraum", fg=ACCENT)
        else:
            self.daterange_frame.pack_forget()
            self.daterange_btn.configure(text="> Taggenauer Zeitraum", fg=TEXT_DIM)
        self._update_scroll_region()

    def _browse(self):
        folder = filedialog.askdirectory(title="Speicherordner waehlen", initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)
            self.last_output_folder = folder

    def _open_output_folder(self):
        folder = self.folder_var.get().strip() or self.last_output_folder
        if not folder:
            return
        path = Path(folder)
        try:
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(str(path))
        except Exception as exc:
            messagebox.showerror("Fehler", f"Ordner konnte nicht geoeffnet werden:\n{exc}")

    def _set_status(self, msg, color=TEXT_DIM):
        self.status_var.set(msg)
        self.status_lbl.configure(fg=color)

    def _append_log(self, text):
        if not text:
            return
        self.log_text.configure(state="normal")
        # Farbe je nach Inhalt
        tag = None
        tl = text.lower()
        if any(w in tl for w in ["fehler", "error", "traceback", "exception", "✗"]):
            tag = "error"
        elif any(w in tl for w in ["fertig", "gespeichert", "✓", "↓"]):
            tag = "success"
        elif any(w in tl for w in ["warn", "⚠", "überspringe"]):
            tag = "warn"
        if tag:
            self.log_text.insert("end", text if text.endswith("\n") else text + "\n", tag)
        else:
            self.log_text.insert("end", text)
            if not text.endswith("\n"):
                self.log_text.insert("end", "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _validate(self):
        years = self.year_var.get().strip()
        folder = self.folder_var.get().strip()
        if not years:
            messagebox.showerror("Fehler", "Bitte mindestens ein Jahr eingeben.")
            return None
        for y in years.split(","):
            try:
                year = int(y.strip())
                if year < 2010 or year > datetime.now().year + 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Fehler", f"Ungueltiges Jahr: '{y.strip()}'")
                return None
        if not folder:
            messagebox.showerror("Fehler", "Bitte einen Speicherordner waehlen.")
            return None
        if not self.invoices_var.get() and not self.overview_var.get():
            messagebox.showerror("Fehler", "Bitte mindestens eine Download-Option waehlen.")
            return None

        date_range = None
        if self.daterange_open:
            try:
                start = datetime.strptime(self.date_from_var.get().strip(), "%d.%m.%Y")
                end = datetime.strptime(self.date_to_var.get().strip(), "%d.%m.%Y")
                if start > end:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Fehler", "Bitte einen gueltigen Zeitraum im Format TT.MM.JJJJ eingeben.")
                return None
            date_range = f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"

        try:
            title_words_count = int(self.title_words_count.get())
        except ValueError:
            title_words_count = 0

        return {
            "years": years,
            "folder": folder,
            "invoices": self.invoices_var.get(),
            "overview": self.overview_var.get(),
            "date_range": date_range,
            "title_words": self.title_words_var.get(),
            "title_words_count": max(0, title_words_count),
            "open_when_done": self.open_when_done_var.get(),
        }

    def _start(self):
        options = self._validate()
        if not options:
            return
        self._save_settings()
        self.last_output_folder = options["folder"]
        self._clear_log()
        self._append_log("Starte Downloader...")
        self.is_running = True
        self.start_btn.configure(state="disabled", text="Laeuft...")
        self.stop_btn.pack(side="right")
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.progress.start(12)
        self._set_status("Browser wird geoeffnet...", ACCENT)
        threading.Thread(target=self._run, args=(options,), daemon=True).start()

    def _build_command(self, options):
        script = APP_DIR / "amazon_de_downloader.py"
        venv_py = APP_DIR / ".venv" / "Scripts" / "python.exe"
        python = str(venv_py) if venv_py.exists() else sys.executable
        cmd = [python, "-u", str(script), f"--year={options['years']}", f"--output={options['folder']}"]
        if options["invoices"]:
            cmd.append("--invoices")
        if options["overview"]:
            cmd.append("--overview")
        if options["date_range"]:
            cmd.append(f"--daterange={options['date_range']}")
        if options["title_words"] and options["title_words_count"] > 0:
            cmd.append(f"--title-words={options['title_words_count']}")
        cmd.append("--no-pause")  # GUI übernimmt Steuerung
        return cmd

    def _run(self, options):
        cmd = self._build_command(options)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self.root.after(0, self._set_status, "Download laeuft - Amazon im Browser beobachten...", SUCCESS)
            self.proc = subprocess.Popen(
                cmd,
                cwd=str(APP_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                creationflags=creationflags,
            )
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.root.after(0, self._append_log, line)
            returncode = self.proc.wait()
            self.root.after(0, self._finish, returncode, options)
        except Exception as exc:
            self.root.after(0, self._append_log, f"Fehler: {exc}")
            self.root.after(0, self._set_status, f"Fehler: {exc}", ERROR)
            self.root.after(0, self._reset_ui)
        finally:
            self.proc = None

    def _finish(self, returncode, options):
        if returncode == 0:
            self._set_status(f"Fertig! PDFs gespeichert in: {options['folder']}", SUCCESS)
            self._append_log("Fertig.")
            if options["open_when_done"]:
                self._open_output_folder()
            messagebox.showinfo("Fertig", f"Download abgeschlossen!\n\nRechnungen gespeichert in:\n{options['folder']}")
        elif returncode == -1:
            self._set_status("Download gestoppt.", ERROR)
            self._append_log("Download gestoppt.")
        else:
            self._set_status("Fehler beim Download. Details stehen im Protokoll.", ERROR)
            self._append_log(f"Downloader beendet mit Fehlercode {returncode}.")
        self._reset_ui()

    def _stop(self):
        if not self.proc or self.proc.poll() is not None:
            return
        if not messagebox.askyesno("Stoppen", "Download wirklich stoppen?"):
            return
        self._set_status("Stoppe Download...", ERROR)
        self._append_log("Stoppe Download...")
        try:
            self.proc.terminate()
        except Exception:
            pass

    def _reset_ui(self):
        self.is_running = False
        self.progress.stop()
        self.start_btn.configure(state="normal", text="Login & Download starten")
        self.stop_btn.pack_forget()
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 0))

    def _on_close(self):
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno("Beenden", "Der Download laeuft noch. Trotzdem beenden?"):
                return
            try:
                self.proc.terminate()
            except Exception:
                pass
        self._save_settings()
        self.root.destroy()


def main():
    root = tk.Tk()
    AmazonDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
