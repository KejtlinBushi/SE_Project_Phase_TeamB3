import os
import tkinter as tk
from tkinter import font as tkfont

# ── Colour Palette (blue + teal/green — matching the dashboard) ─────────────
BG_DARK    = "#1b3a5c"
BG_MAIN    = "#eef3f8"
BG_CARD    = "#ffffff"
TEAL       = "#1d7a6a"
BLUE       = "#1a6eb5"
BLUE_LIGHT = "#2979c8"
GREEN      = "#27865a"
TEXT_DARK  = "#1b3a5c"
TEXT_MID   = "#4a5a6a"
TEXT_LIGHT = "#ffffff"
BORDER     = "#ccdded"
SECTION_BG = "#f4f8fb"

FEATURES = [
    ("📋", "Milestone Tracking",  BLUE,  "Monitor every key step of your thesis journey with clear deadlines and status updates."),
    ("📎", "File Submissions",     TEAL,  "Upload documents securely and receive structured feedback from your supervisor."),
    ("🗓️","Meeting Scheduling",   GREEN, "Plan and manage meetings between students and supervisors effortlessly."),
    ("🔔", "Smart Notifications", "#c47a1e", "Automatic alerts for deadlines, comments, and important system changes."),
]

ROLES = [
    ("🎓", "Students",       BLUE,  "Track milestones, upload thesis work, view feedback from your supervisor, and stay on top of every deadline."),
    ("👨‍🏫","Supervisors",    TEAL,  "Review applications, provide structured feedback, schedule meetings, and monitor student progress."),
    ("🛡️", "Administrators", GREEN, "Manage all users, assignments, and system activity with full administrative control."),
]

CONTACTS = [
    ("📍", "Address",    "Rr. Tiranë-Rinas, Km. 12\n1032 Vorë, Tirana, Albania"),
    ("📞", "Phone",      "+355 42 232 086"),
    ("📠", "Fax",        "+355 42 222 117"),
    ("✉️", "Email",      "info@epoka.edu.al"),
    ("🎓", "Academic Administration", "admin@thesis.edu"),
    ("🌐", "Website",    "www.epoka.edu.al"),
]


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg, **kw):
        container = tk.Frame(parent, bg=bg)
        container.pack(fill="both", expand=True)

        self.canvas   = tk.Canvas(container, bg=bg, highlightthickness=0)
        scrollbar     = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.inner    = tk.Frame(self.canvas, bg=bg)

        self.inner.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(self._win, width=e.width))
        self.canvas.bind("<Enter>", self._bind_scroll)
        self.canvas.bind("<Leave>", self._unbind_scroll)

        super().__init__(self.inner, bg=bg, **kw)
        self.pack(fill="both", expand=True)

    def _bind_scroll(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_scroll)
        self.canvas.bind_all("<Button-4>", self._on_scroll)
        self.canvas.bind_all("<Button-5>", self._on_scroll)

    def _unbind_scroll(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_scroll(self, event):
        if hasattr(event, 'delta'):
            direction = -1 if event.delta > 0 else 1
        elif event.num == 4:
            direction = -1
        elif event.num == 5:
            direction = 1
        else:
            return "break"

        self.canvas.yview_scroll(direction, "units")
        return "break"


class HomePage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_DARK)
        self.master = master
        self._login_win = None

        self.f = {
            "brand":  tkfont.Font(family="Georgia",   size=13, weight="bold"),
            "nav":    tkfont.Font(family="Helvetica", size=9),
            "hero_h": tkfont.Font(family="Georgia",   size=26, weight="bold"),
            "hero_s": tkfont.Font(family="Helvetica", size=11),
            "tag":    tkfont.Font(family="Helvetica", size=8,  weight="bold"),
            "sec_h":  tkfont.Font(family="Georgia",   size=17, weight="bold"),
            "card_t": tkfont.Font(family="Georgia",   size=11, weight="bold"),
            "card_b": tkfont.Font(family="Helvetica", size=9),
            "btn":    tkfont.Font(family="Helvetica", size=9,  weight="bold"),
            "small":  tkfont.Font(family="Helvetica", size=8),
            "input":  tkfont.Font(family="Helvetica", size=10),
            "stat_n": tkfont.Font(family="Georgia",   size=20, weight="bold"),
        }
        self._build()

    # ── NAV ──────────────────────────────────────────────────────────────────
    def _build(self):
        nav = tk.Frame(self, bg=BG_DARK, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        self._logo_img = None
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "epoka_logo.png")
        if os.path.exists(logo_path):
            try:
                self._logo_img = tk.PhotoImage(file=logo_path)
            except tk.TclError:
                self._logo_img = None

        if self._logo_img:
            tk.Label(nav, image=self._logo_img, bg=BG_DARK).pack(side="left", padx=(18,8), pady=6)
        else:
            tk.Label(nav, text=" E ", bg=BLUE, fg=TEXT_LIGHT,
                     font=self.f["brand"], padx=6, pady=4).pack(side="left", padx=(18,8), pady=10)

        tk.Label(nav, text="EPOKA  THESIS TRACKER",
                 bg=BG_DARK, fg=TEXT_LIGHT, font=self.f["brand"]).pack(side="left")

        for label, key in [("Home","hero"),("About","about"),
                            ("Roles","roles"),("Contact","contact")]:
            tk.Button(nav, text=label, bg=BG_DARK, fg="#aac8e0",
                      font=self.f["nav"], bd=0, cursor="hand2",
                      activebackground=BG_DARK, activeforeground=TEXT_LIGHT,
                      command=lambda k=key: self._scroll_to(k)).pack(side="left", padx=14)

        tk.Button(nav, text="  Log In  ", bg=BLUE, fg=TEXT_LIGHT,
                  font=self.f["btn"], bd=0, cursor="hand2",
                  padx=12, pady=6, relief="flat",
                  activebackground=BLUE_LIGHT, activeforeground=TEXT_LIGHT,
                  command=self._open_login).pack(side="right", padx=18, pady=10)

        self._sf = ScrollableFrame(self, bg=BG_MAIN)
        self._sections = {}
        self._build_hero(self._sf)
        self._build_about(self._sf)
        self._build_roles(self._sf)
        self._build_contact(self._sf)
        self._build_footer(self._sf)

    # ── HERO ─────────────────────────────────────────────────────────────────
    def _build_hero(self, parent):
        hero = tk.Frame(parent, bg=BG_DARK)
        hero.pack(fill="x")
        self._sections["hero"] = hero

        inner = tk.Frame(hero, bg=BG_DARK)
        inner.pack(pady=(55, 0), padx=80, anchor="w")

        tk.Label(inner, text="  EPOKA UNIVERSITY — TIRANA, ALBANIA  ",
                 bg=TEAL, fg=TEXT_LIGHT, font=self.f["tag"],
                 pady=4, padx=8).pack(anchor="w", pady=(0, 16))

        tk.Label(inner, text="Track Your Thesis Journey,",
                 bg=BG_DARK, fg=TEXT_LIGHT, font=self.f["hero_h"]).pack(anchor="w")
        tk.Label(inner, text="From First Milestone to Final Defense.",
               bg=BG_DARK, fg="#7ac4f0", font=self.f["hero_h"]).pack(anchor="w", pady=(0, 16))

        tk.Label(inner,
                 text="A centralized academic platform designed to connect students, supervisors, and administrators in one seamless environment.\n"
                      "Manage milestones, submit research documents, schedule meetings, and monitor progress throughout the entire thesis journey.",
                 bg=BG_DARK, fg="#9ab8d0", font=self.f["hero_s"],
                 justify="left").pack(anchor="w", pady=(0, 28))

        btn_row = tk.Frame(inner, bg=BG_DARK)
        btn_row.pack(anchor="w", pady=(0, 46))

        tk.Button(btn_row, text="  Log In to Dashboard  ",
                  bg=BLUE, fg=TEXT_LIGHT, font=self.f["btn"],
                  bd=0, cursor="hand2", padx=16, pady=9, relief="flat",
                  activebackground=BLUE_LIGHT, activeforeground=TEXT_LIGHT,
                  command=self._open_login).pack(side="left", padx=(0, 12))

        tk.Button(btn_row, text="  Learn More  ",
                  bg=BG_DARK, fg="#9ab8d0", font=self.f["btn"],
                  bd=1, cursor="hand2", padx=16, pady=8, relief="solid",
                  highlightbackground="#3a6080", highlightthickness=1,
                  activebackground=BG_DARK, activeforeground=TEXT_LIGHT,
                  command=lambda: self._scroll_to("about")).pack(side="left")

        # stats bar
        stats = tk.Frame(hero, bg="#132d47")
        stats.pack(fill="x")
        for num, lbl in [("3","User Roles"),("∞","Milestones"),("1","Platform"),("100%","Free to Use")]:
            cell = tk.Frame(stats, bg="#132d47")
            cell.pack(side="left", padx=56, pady=14)
            tk.Label(cell, text=num, bg="#132d47", fg="#7ac4f0",
                     font=self.f["stat_n"]).pack()
            tk.Label(cell, text=lbl, bg="#132d47", fg="#5a7a9a",
                     font=self.f["small"]).pack()

    # ── ABOUT ────────────────────────────────────────────────────────────────
    def _build_about(self, parent):
        wrap = tk.Frame(parent, bg=BG_MAIN)
        wrap.pack(fill="x", pady=(30, 0))
        self._sections["about"] = wrap

        self._sec_header(wrap, "About the System",
                         "Designed for Academic Excellence", BG_MAIN)

        inner = tk.Frame(wrap, bg=BG_MAIN)
        inner.pack(padx=60, pady=(0, 44), fill="x")

        # left text
        left = tk.Frame(inner, bg=BG_MAIN)
        left.pack(side="left", fill="both", expand=True, padx=(0, 44))
        for para in [
             "Epoka Thesis Tracker is an integrated academic platform designed to simplify, organise, and digitalize the entire thesis management process at Epoka University. The system creates a centralized environment where students, supervisors, and administrators can collaborate efficiently while maintaining transparency throughout every stage of the academic journey.",

    "Students can explore thesis opportunities, monitor their academic progress, upload important research documents, receive structured supervisor feedback, schedule meetings, and stay informed about upcoming deadlines and milestones. This ensures better communication, improved time management, and continuous academic support.",

    "Supervisors can review submissions, evaluate student performance, approve or reject progress, provide detailed academic guidance, and manage multiple thesis projects in real time. At the same time, administrators maintain full system control by managing users, assigning supervisors, monitoring activities, and generating reports that support academic decision-making across the university."
        ]:
            tk.Label(left, text=para, bg=BG_MAIN, fg=TEXT_MID,
                     font=self.f["hero_s"], wraplength=360,
                     justify="left").pack(anchor="w", pady=7)

        # right: 2×2 feature cards
        right = tk.Frame(inner, bg=BG_MAIN)
        right.pack(side="left", fill="both", expand=True)

        for i, (icon, title, color, desc) in enumerate(FEATURES):
            row, col = divmod(i, 2)
            card = tk.Frame(right, bg=BG_CARD,
                            highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")
            right.grid_columnconfigure(col, weight=1)

            tk.Label(card, text=icon, bg=color, fg=TEXT_LIGHT,
                     font=tkfont.Font(size=15),
                     width=4, pady=7).pack(anchor="w", padx=12, pady=(12, 5))
            tk.Label(card, text=title, bg=BG_CARD, fg=TEXT_DARK,
                     font=self.f["card_t"]).pack(anchor="w", padx=12)
            tk.Label(card, text=desc, bg=BG_CARD, fg=TEXT_MID,
                     font=self.f["card_b"], wraplength=190,
                     justify="left").pack(anchor="w", padx=12, pady=(4, 12))

    # ── ROLES ────────────────────────────────────────────────────────────────
    def _build_roles(self, parent):
        wrap = tk.Frame(parent, bg=BG_DARK)
        wrap.pack(fill="x")
        self._sections["roles"] = wrap

        self._sec_header(wrap, "Who Uses It", "Three Roles, One Platform",
                         BG_DARK, tag_fg=TEAL, h_fg="#7ac4f0", sub_fg="#5a7a9a")

        row_f = tk.Frame(wrap, bg=BG_DARK)
        row_f.pack(padx=60, pady=(0, 50), fill="x")

        for icon, title, color, desc in ROLES:
            card = tk.Frame(row_f, bg="#1e3f5c",
                            highlightbackground="#2a5070", highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=10)

            tk.Label(card, text=icon, bg=color, fg=TEXT_LIGHT,
                     font=tkfont.Font(size=20),
                     width=4, pady=10).pack(fill="x")
            tk.Label(card, text=title, bg="#1e3f5c", fg=TEXT_LIGHT,
                     font=self.f["card_t"]).pack(pady=(14, 4))
            tk.Label(card, text=desc, bg="#1e3f5c", fg="#7a98b0",
                     font=self.f["card_b"], wraplength=240,
                     justify="center").pack(padx=16, pady=(0, 20))

    # ── CONTACT ──────────────────────────────────────────────────────────────
    def _build_contact(self, parent):
        wrap = tk.Frame(parent, bg=SECTION_BG)
        wrap.pack(fill="x")
        self._sections["contact"] = wrap

        self._sec_header(wrap, "Get In Touch",
                         "Epoka University — Contact Information", SECTION_BG)

        outer = tk.Frame(wrap, bg=SECTION_BG)
        outer.pack(padx=60, pady=(0, 50), fill="x")

        # 3×2 contact cards
        grid_f = tk.Frame(outer, bg=SECTION_BG)
        grid_f.pack(side="left", fill="both", expand=True)

        for i, (icon, label, value) in enumerate(CONTACTS):
            row, col = divmod(i, 2)
            card = tk.Frame(grid_f, bg=BG_CARD,
                            highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")
            grid_f.grid_columnconfigure(col, weight=1)

            # coloured top stripe
            tk.Frame(card, bg=BLUE, height=4).pack(fill="x")

            body = tk.Frame(card, bg=BG_CARD)
            body.pack(padx=14, pady=12, fill="x")

            tk.Label(body, text=f"{icon}  {label}", bg=BG_CARD, fg=BLUE,
                     font=self.f["card_t"]).pack(anchor="w")
            tk.Label(body, text=value, bg=BG_CARD, fg=TEXT_MID,
                     font=self.f["input"], justify="left",
                     wraplength=220).pack(anchor="w", pady=(4, 0))

        # map placeholder box
        map_f = tk.Frame(outer, bg="#d8eaf5",
                         highlightbackground=BORDER, highlightthickness=1,
                         width=240)
        map_f.pack(side="left", fill="both", expand=False,
                   padx=(28, 0), pady=7)
        map_f.pack_propagate(False)

        tk.Label(map_f, text="🗺️", bg="#d8eaf5",
                 font=tkfont.Font(size=38)).pack(expand=True)
        tk.Label(map_f,
                 text="Rr. Tiranë-Rinas, Km. 12\n1032 Vorë, Tirana, Albania\n\nNear Tirana International Airport",
                 bg="#d8eaf5", fg=TEXT_MID, font=self.f["small"],
                 justify="center").pack(pady=(0, 24))

    # ── FOOTER ───────────────────────────────────────────────────────────────
    def _build_footer(self, parent):
        footer = tk.Frame(parent, bg=BG_DARK, height=50)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        tk.Label(footer,
                 text="© 2026 Epoka University  ·  Thesis Progress Tracker  ·  Tirana, Albania",
                 bg=BG_DARK, fg="#3a5a7a", font=self.f["small"]).pack(
                     side="left", padx=30, pady=16)
        tk.Label(footer,
                 text="info@epoka.edu.al   |   +355 42 232 086",
                 bg=BG_DARK, fg="#3a5a7a", font=self.f["small"]).pack(
                     side="right", padx=30)

    # ── HELPERS ──────────────────────────────────────────────────────────────
    def _sec_header(self, parent, sub, title, bg,
                    tag_fg=None, h_fg=None, sub_fg=None):
        if tag_fg is None: tag_fg = TEAL
        if h_fg   is None: h_fg   = TEXT_DARK
        tk.Label(parent, text=f"— {sub} —",
                 bg=bg, fg=tag_fg, font=self.f["tag"]).pack(pady=(40, 4))
        tk.Label(parent, text=title,
                 bg=bg, fg=h_fg, font=self.f["sec_h"]).pack(pady=(0, 4))
        tk.Frame(parent, bg=tag_fg, height=2, width=60).pack(pady=(0, 26))

    def _scroll_to(self, key):
        target = self._sections.get(key)
        if not target:
            return
        self.update_idletasks()
        y     = target.winfo_y()
        total = self._sf.inner.winfo_height()
        if total > 0:
            self._sf.canvas.yview_moveto(y / total)

    # ── LOGIN POPUP ─────────────────────────────────────────────────────────
    def _open_login(self):
        self.master.show_login()