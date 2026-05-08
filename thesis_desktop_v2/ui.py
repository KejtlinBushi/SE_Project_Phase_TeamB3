"""
ui.py
Shared UI theme - Epoka Interactive System style (blue/white/green)
CEN 302 Software Engineering | Group III | Epoka University
"""

import tkinter as tk
from tkinter import ttk
import subprocess, sys, os

# ─────────────────────────────────────────────────────────────
# COLOR THEME  (Epoka Interactive System style)
# ─────────────────────────────────────────────────────────────
BG_MAIN   = "#f4f6f9"       # light grey page background
BG_WHITE  = "#ffffff"       # white cards
NAV_BG    = "#2c3e50"       # dark navy sidebar
NAV_HOVER = "#34495e"       # sidebar hover
TOP_BG    = "#1a5276"       # topbar blue
BLUE      = "#2980b9"       # primary blue
BLUE2     = "#1a6fa8"       # darker blue
GREEN     = "#27ae60"       # green tiles
OLIVE     = "#7d8c1f"       # olive/yellow-green tiles
GOLD_TILE = "#c9920a"       # gold tiles
ORANGE    = "#d35400"       # orange tiles
PURPLE    = "#8e44ad"       # purple tiles
WHITE     = "#ffffff"
DARK      = "#2c3e50"
MUTED     = "#7f8c8d"
BORDER    = "#dce1e7"
SUCCESS   = "#27ae60"
DANGER    = "#e74c3c"
WARNING   = "#f39c12"
INFO      = "#2980b9"
TEXT      = "#2c3e50"
TEXT2     = "#555555"
# keep aliases for old references
BG_DARK   = NAV_BG
BG_PANEL  = NAV_BG
BG_CARD   = BG_WHITE
BG_INPUT  = "#ecf0f1"
GOLD      = BLUE
GOLD_DIM  = BLUE2
BORDER_DARK = "#3d5166"


def label(parent, text, size=11, color=TEXT, bold=False, **kw):
    font = ("Segoe UI", size, "bold" if bold else "normal")
    try:
        bg = parent["bg"]
    except Exception:
        bg = BG_MAIN
    return tk.Label(parent, text=text, bg=bg, fg=color, font=font, **kw)


def style_btn(btn, color=BLUE, fg=WHITE):
    btn.configure(bg=color, fg=fg,
                  activebackground=BLUE2, activeforeground=WHITE,
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6)


def style_entry(entry):
    entry.configure(bg=WHITE, fg=DARK,
                    insertbackground=BLUE, relief="solid",
                    font=("Segoe UI", 10),
                    highlightthickness=1,
                    highlightbackground=BORDER,
                    highlightcolor=BLUE)


def card_frame(parent, **kw):
    f = tk.Frame(parent, bg=BG_WHITE, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER)
    if kw:
        f.configure(**kw)
    return f


def stat_card(parent, title, value, color=BLUE):
    f = card_frame(parent, padx=14, pady=14)
    label(f, str(value), 26, color, bold=True).pack(anchor="w")
    label(f, title, 9, MUTED).pack(anchor="w", pady=(2, 0))
    return f


def page_header(parent, title, subtitle=""):
    f = tk.Frame(parent, bg=BG_MAIN, pady=12)
    f.pack(fill="x", padx=20)
    label(f, title, 16, DARK, bold=True).pack(anchor="w")
    if subtitle:
        label(f, subtitle, 9, MUTED).pack(anchor="w", pady=(1, 0))
    tk.Frame(f, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))
    return f


def style_treeview(tree, cols, col_widths=None):
    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
                    background=WHITE, foreground=DARK,
                    fieldbackground=WHITE, rowheight=28,
                    borderwidth=0, font=("Segoe UI", 10))
    style.configure("Treeview.Heading",
                    background="#eaf0fb", foreground=DARK,
                    font=("Segoe UI", 9, "bold"), relief="flat")
    style.map("Treeview",
              background=[("selected", BLUE)],
              foreground=[("selected", WHITE)])
    for i, col in enumerate(cols):
        tree.heading(col, text=col)
        w = col_widths[i] if col_widths else 120
        tree.column(col, width=w, minwidth=50, anchor="w")


class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=BG_MAIN, **kw):
        super().__init__(parent, bg=bg, **kw)
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.inner = tk.Frame(self._canvas, bg=bg)
        self.inner.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._canvas.bind("<Enter>", self._bind_scroll)
        self._canvas.bind("<Leave>", self._unbind_scroll)

    def _bind_scroll(self, e):
        self._canvas.bind_all("<MouseWheel>", self._on_scroll)

    def _unbind_scroll(self, e):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_scroll(self, e):
        self._canvas.yview_scroll(-1 * (e.delta // 120), "units")


class FeedbackDialog(tk.Toplevel):
    def __init__(self, master, title="Feedback"):
        super().__init__(master)
        self.title(title)
        self.geometry("420x220")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._build()

    def _build(self):
        tk.Label(self, text="Enter feedback comment:",
                 bg=BG_MAIN, fg=DARK,
                 font=("Segoe UI", 11)).pack(padx=16, pady=(16, 4), anchor="w")
        self.txt = tk.Text(self, height=5, bg=WHITE, fg=DARK,
                           insertbackground=BLUE,
                           font=("Segoe UI", 10),
                           relief="solid", padx=8, pady=6,
                           highlightthickness=1, highlightbackground=BORDER)
        self.txt.pack(fill="x", padx=16)
        tk.Button(self, text="Submit", command=self._submit,
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold")).pack(pady=10)

    def _submit(self):
        self.result = self.txt.get("1.0", "end").strip()
        self.destroy()


def open_file(filepath):
    """Open a file with the system default application."""
    try:
        if sys.platform == "win32":
            os.startfile(filepath)
        elif sys.platform == "darwin":
            subprocess.run(["open", filepath])
        else:
            subprocess.run(["xdg-open", filepath])
    except Exception as e:
        import tkinter.messagebox as mb
        mb.showerror("Error", f"Cannot open file:\n{e}")
