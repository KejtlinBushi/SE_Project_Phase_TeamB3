"""
base_app.py
Epoka-style sidebar + topbar shell with notification bell.
CEN 302 Software Engineering | Group III | Epoka University
"""

import tkinter as tk
from tkinter import messagebox
from ui import (NAV_BG, NAV_HOVER, TOP_BG, BLUE, BG_MAIN,
                WHITE, MUTED, DARK, BORDER, DANGER, TEXT)
from auth import SESSION
from database import query


def get_unread_count():
    """Get unread notification count for current user."""
    try:
        row = query(
            "SELECT COUNT(*) AS c FROM notifications WHERE user_role=%s AND user_id=%s AND is_read=0",
            (SESSION["role"], SESSION["user_id"]), one=True)
        return row["c"] if row else 0
    except Exception:
        return 0


class BaseApp(tk.Frame):
    NAV_ITEMS = []
    PAGES     = {}

    def __init__(self, master):
        super().__init__(master, bg=BG_MAIN)
        self.master  = master
        self.content = None

        # ── Navigation history ────────────────────────────────
        self._history      = []    # stack of previous page names
        self._current_page = None  # name of page shown right now

        self._build_shell()
        if self.NAV_ITEMS:
            self._navigate(self.NAV_ITEMS[0][0])
        self._poll_notifications()

    # ─────────────────────────────────────────────────────────
    def _build_shell(self):
        # ── Top bar ───────────────────────────────────────────
        topbar = tk.Frame(self, bg=TOP_BG, height=50)
        topbar.pack(side="top", fill="x")
        topbar.pack_propagate(False)

        # ── Left side: Back + Logo (Home button REMOVED) ──────
        left_f = tk.Frame(topbar, bg=TOP_BG)
        left_f.pack(side="left", padx=8)

        # ← Back button
        self.back_btn = tk.Button(
            left_f,
            text="← Back",
            command=self._go_back,
            bg=TOP_BG, fg=WHITE,
            activebackground=NAV_HOVER,
            activeforeground=WHITE,
            relief="flat", cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=6, pady=0, bd=0
        )
        self.back_btn.pack(side="left")
        self.back_btn.pack_forget()   # hidden until there is history

        # Logo
        tk.Label(left_f, text="E  EPOKA  THESIS TRACKER",
                 bg=TOP_BG, fg=WHITE,
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=4)

        # ── Right side: bell + user name ──────────────────────
        right_f = tk.Frame(topbar, bg=TOP_BG)
        right_f.pack(side="right", padx=12)

        # Notification bell
        bell_f = tk.Frame(right_f, bg=TOP_BG)
        bell_f.pack(side="left", padx=(0, 14))
        self.bell_btn = tk.Label(bell_f, text="🔔",
                                 bg=TOP_BG, fg=WHITE,
                                 font=("Segoe UI", 14),
                                 cursor="hand2")
        self.bell_btn.pack(side="left")
        self.bell_btn.bind("<Button-1>", lambda e: self._navigate("notifications"))

        self.notif_badge = tk.Label(bell_f, text="",
                                    bg="#e74c3c", fg=WHITE,
                                    font=("Segoe UI", 7, "bold"),
                                    padx=3, pady=0)
        # badge placed on top of bell
        self.notif_badge.place_forget()

        # User name
        initials = "".join(w[0].upper() for w in SESSION["name"].split()[:2])
        tk.Label(right_f,
                 text=f"  {initials}  {SESSION['name']}  ▾",
                 bg=TOP_BG, fg=WHITE,
                 font=("Segoe UI", 10)).pack(side="left")

        # ── Sidebar ───────────────────────────────────────────
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(side="bottom", fill="both", expand=True)

        self.sidebar = tk.Frame(body, bg=NAV_BG, width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Nav items
        self.nav_buttons = {}
        tk.Frame(self.sidebar, bg=NAV_BG, height=8).pack()
        for page, icon, text in self.NAV_ITEMS:
            btn = tk.Button(
                self.sidebar,
                text=f"  {icon}   {text}",
                anchor="w",
                command=lambda p=page: self._navigate(p),
                bg=NAV_BG, fg="#bdc3c7",
                activebackground=NAV_HOVER,
                activeforeground=WHITE,
                relief="flat", cursor="hand2",
                font=("Segoe UI", 10),
                padx=10, pady=9, bd=0
            )
            btn.pack(fill="x")
            self.nav_buttons[page] = btn

        # ── Logout button — bold red, at the very bottom ──────
        tk.Frame(self.sidebar, bg="#1a252f", height=1).pack(
            fill="x", side="bottom")

        logout_btn = tk.Button(
            self.sidebar,
            text="⇤  Logout",
            command=self.master.logout,
            anchor="w",
            bg="#c0392b",          # solid red background
            fg=WHITE,
            activebackground="#922b21",
            activeforeground=WHITE,
            relief="flat", cursor="hand2",
            font=("Segoe UI", 11, "bold"),   # bold + slightly larger
            padx=10, pady=11, bd=0
        )
        logout_btn.pack(side="bottom", fill="x")

        # Hover effect for logout
        logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg="#922b21"))
        logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg="#c0392b"))

        # ── Main content area ─────────────────────────────────
        self.main = tk.Frame(body, bg=BG_MAIN)
        self.main.pack(side="right", fill="both", expand=True)

    # ─────────────────────────────────────────────────────────
    def _navigate(self, page, push_history=True):
        """
        Navigate to a page.
        push_history=True  -> forward navigation (saves current to stack)
        push_history=False -> back navigation (does NOT push)
        """
        if page not in self.PAGES:
            return

        if push_history and self._current_page and self._current_page != page:
            self._history.append(self._current_page)

        for p, btn in self.nav_buttons.items():
            btn.configure(bg=BLUE if p == page else NAV_BG,
                          fg=WHITE if p == page else "#bdc3c7")

        # Highlight the notification bell if on notifications page
        if page == "notifications":
            self.bell_btn.configure(fg=BLUE)
        else:
            self.bell_btn.configure(fg=WHITE)

        if self.content:
            self.content.destroy()

        self.content = self.PAGES[page](self.main)
        self.content.pack(fill="both", expand=True)
        self._current_page = page
        self._update_back_btn()

    # ─────────────────────────────────────────────────────────
    def _go_back(self):
        """Go to the previous page, or login if no history left."""
        if self._history:
            previous = self._history.pop()
            self._navigate(previous, push_history=False)
        else:
            self.master.logout()

    # ─────────────────────────────────────────────────────────
    def _update_back_btn(self):
        """Show ← Back only when there is history."""
        if self._history:
            self.back_btn.pack(side="left")
        else:
            self.back_btn.pack_forget()

    # ─────────────────────────────────────────────────────────
    def _poll_notifications(self):
        """Update notification badge every 15 seconds."""
        try:
            count = get_unread_count()
            if count > 0:
                self.notif_badge.config(text=str(count))
                self.notif_badge.place(in_=self.bell_btn,
                                       relx=0.6, rely=-0.1, anchor="nw")
            else:
                self.notif_badge.place_forget()
        except Exception:
            pass
        self.after(15000, self._poll_notifications)
