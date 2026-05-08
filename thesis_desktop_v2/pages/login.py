"""
pages/login.py
Login screen only (Register removed per requirements).
CEN 302 Software Engineering | Group III | Epoka University
"""

import tkinter as tk
from database import query
from auth import login_user, hash_password, check_password
from ui import (TOP_BG, BLUE, BLUE2, BG_MAIN, WHITE, MUTED,
                DARK, BORDER, DANGER, style_entry)


class LoginPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=TOP_BG)
        self.master = master
        self._build()

    def _build(self):
        # Top bar
        topbar = tk.Frame(self, bg=TOP_BG, height=50)
        topbar.pack(fill="x")
        tk.Label(topbar, text="E  EPOKA  THESIS TRACKER",
                 bg=TOP_BG, fg=WHITE,
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=20, pady=12)

        # Center card
        center = tk.Frame(self, bg=TOP_BG)
        center.pack(fill="both", expand=True)

        card = tk.Frame(center, bg=WHITE, padx=36, pady=32,
                        relief="flat",
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", width=400)

        # Header
        tk.Label(card, text="Welcome back",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 20, "bold")).pack(pady=(0, 4))
        tk.Label(card, text="Sign in to your account",
                 bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 10)).pack(pady=(0, 22))

        # Role tabs
        tk.Label(card, text="Role", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.role_var = tk.StringVar(value="student")
        role_f = tk.Frame(card, bg="#eaf0fb",
                          highlightthickness=1, highlightbackground=BORDER)
        role_f.pack(fill="x", pady=(4, 16))
        for r in ("student", "supervisor", "admin"):
            tk.Radiobutton(role_f, text=r.capitalize(),
                           variable=self.role_var, value=r,
                           bg="#eaf0fb", fg=DARK, selectcolor=WHITE,
                           activebackground="#eaf0fb",
                           font=("Segoe UI", 10)).pack(
                side="left", padx=14, pady=8)

        # Email
        tk.Label(card, text="Email", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.email_var = tk.StringVar()
        e1 = tk.Entry(card, textvariable=self.email_var, width=36)
        style_entry(e1)
        e1.pack(fill="x", ipady=7, pady=(4, 14))

        # Password
        tk.Label(card, text="Password", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.pw_var = tk.StringVar()
        e2 = tk.Entry(card, textvariable=self.pw_var, show="•", width=36)
        style_entry(e2)
        e2.pack(fill="x", ipady=7, pady=(4, 20))
        e2.bind("<Return>", lambda e: self._login())

        # Sign in button
        tk.Button(card, text="Sign In",
                  command=self._login,
                  bg=BLUE, fg=WHITE,
                  activebackground=BLUE2,
                  relief="flat", cursor="hand2",
                  font=("Segoe UI", 11, "bold"),
                  pady=8).pack(fill="x")

        self.err_lbl = tk.Label(card, text="", bg=WHITE, fg=DANGER,
                                font=("Segoe UI", 10))
        self.err_lbl.pack(pady=(10, 0))

        # Footer note — no register button
        tk.Label(card,
                 text="Contact your administrator to create an account.",
                 bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(pady=(8, 0))

    def _login(self):
        role  = self.role_var.get()
        email = self.email_var.get().strip()
        pw    = self.pw_var.get()
        if not email or not pw:
            self.err_lbl.config(text="Please enter email and password")
            return
        tables = {
            "student":    ("students",       "student_id"),
            "supervisor": ("supervisors",    "supervisor_id"),
            "admin":      ("administrators", "admin_id"),
        }
        tbl, pk = tables[role]
        try:
            row = query(f"SELECT * FROM {tbl} WHERE email=%s", (email,), one=True)
        except Exception as ex:
            self.err_lbl.config(text=f"DB error: {ex}")
            return
        if not row or not check_password(pw, row["password_hash"]):
            self.err_lbl.config(text="Invalid email or password")
            return
        login_user(row[pk], role, row["full_name"])
        self.master.show_main()
