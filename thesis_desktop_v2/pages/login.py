"""
pages/login.py
Login screen with animated school items background.
CEN 302 Software Engineering | Group III | Epoka University
"""

import tkinter as tk
import math
import random
from database import query
from auth import login_user, hash_password, check_password
from ui import (TOP_BG, BLUE, BLUE2, BG_MAIN, WHITE, MUTED,
                DARK, BORDER, DANGER, style_entry)


# ── Animated school items background ─────────────────────────────────────────
class AnimatedBackground(tk.Canvas):
    """Canvas that draws slowly drifting school-themed items."""

    # Each item: (draw_function_name, weight)
    ITEM_TYPES = [
        "pencil", "pencil", "pencil",
        "book",   "book",
        "ruler",
        "pen",    "pen",
        "star",   "star",
        "graduation_cap",
        "magnifier",
        "paper",
    ]

    def __init__(self, master, **kw):
        super().__init__(master, bd=0, highlightthickness=0, **kw)
        self._items  = []
        self._running = True
        self.bind("<Configure>", self._on_resize)
        self._init_items()
        self._animate()

    def _init_items(self):
        self._items.clear()
        self.delete("item")
        w = self.winfo_width()  or 1150
        h = self.winfo_height() or 700
        for _ in range(22):
            self._items.append(self._make_item(w, h, random_pos=True))

    def _make_item(self, w, h, random_pos=False):
        kind  = random.choice(self.ITEM_TYPES)
        scale = random.uniform(0.6, 1.5)
        x     = random.uniform(0, w) if random_pos else random.choice([-60, w + 60])
        y     = random.uniform(0, h) if random_pos else random.uniform(0, h)
        speed = random.uniform(0.2, 0.6)
        drift = random.uniform(-0.15, 0.15)
        angle = random.uniform(0, 360)
        rot_s = random.uniform(-0.4, 0.4)
        # soft color tones that blend with navy background
        palettes = {
            "pencil":         ("#f5cba7", "#d4ac0d", "#e8d5b7"),
            "book":           ("#85c1e9", "#5dade2", "#aed6f1"),
            "ruler":          ("#a9cce3", "#7fb3d3", "#d6eaf8"),
            "pen":            ("#a9dfbf", "#52be80", "#d5f5e3"),
            "star":           ("#f9e79f", "#f4d03f", "#fef9e7"),
            "graduation_cap": ("#d7bde2", "#bb8fce", "#f4ecf7"),
            "magnifier":      ("#abebc6", "#58d68d", "#eafaf1"),
            "paper":          ("#fdfefe", "#d5dbdb", "#eaecee"),
        }
        colors = palettes.get(kind, ("#aaaaaa", "#888888", "#cccccc"))
        # lower alpha → soft overlay
        alpha = random.uniform(0.12, 0.30)
        c1 = self._mix(colors[0], "#1a5276", 1 - alpha)
        c2 = self._mix(colors[1], "#1a5276", 1 - alpha)
        c3 = self._mix(colors[2], "#1a5276", 1 - alpha)
        return {
            "kind": kind, "x": x, "y": y, "scale": scale,
            "vy": -speed, "vx": drift,
            "angle": angle, "rot_s": rot_s,
            "c1": c1, "c2": c2, "c3": c3,
        }

    @staticmethod
    def _mix(hex1, hex2, t):
        def h2r(h): return tuple(int(h.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        r1,g1,b1 = h2r(hex1); r2,g2,b2 = h2r(hex2)
        r = int(r1 + (r2-r1)*(1-t)); g = int(g1+(g2-g1)*(1-t)); b = int(b1+(b2-b1)*(1-t))
        return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"

    def _on_resize(self, _event):
        self._init_items()

    def _animate(self):
        if not self._running:
            return
        w = self.winfo_width()  or 1150
        h = self.winfo_height() or 700
        self.delete("item")
        for s in self._items:
            s["x"]     += s["vx"]
            s["y"]     += s["vy"]
            s["angle"]  = (s["angle"] + s["rot_s"]) % 360
            if s["y"] < -120:
                s["y"] = h + 60
                s["x"] = random.uniform(0, w)
            if s["x"] < -120: s["x"] = w + 60
            if s["x"] > w+120: s["x"] = -60
            self._draw(s)
        self.after(30, self._animate)

    # ── helpers ──────────────────────────────────────────────
    def _rot(self, pts, cx, cy, deg):
        r = math.radians(deg)
        out = []
        for px, py in pts:
            dx, dy = px-cx, py-cy
            out.append((cx + dx*math.cos(r) - dy*math.sin(r),
                        cy + dx*math.sin(r) + dy*math.cos(r)))
        return out

    def _poly(self, pts, fill, outline="", width=1):
        flat = [c for p in pts for c in p]
        self.create_polygon(flat, fill=fill, outline=outline,
                            width=width, tags="item")

    def _rect_pts(self, x, y, w, h):
        return [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]

    # ── drawers ──────────────────────────────────────────────
    def _draw(self, s):
        getattr(self, f"_draw_{s['kind']}")(s)

    def _draw_pencil(self, s):
        x, y, sc, a = s["x"], s["y"], s["scale"], s["angle"]
        c1, c2, c3  = s["c1"], s["c2"], s["c3"]
        W, H = 8*sc, 46*sc
        # body
        body = self._rect_pts(-W/2, -H/2, W, H*0.75)
        pts  = self._rot(body, 0, 0, a)
        pts  = [(p[0]+x, p[1]+y) for p in pts]
        self._poly(pts, c1)
        # tip triangle
        tip_y = -H/2 + H*0.75
        tip = [(-W/2, tip_y),(W/2, tip_y),(0, -H/2+H)]
        pts2 = self._rot(tip, 0, 0, a)
        pts2 = [(p[0]+x, p[1]+y) for p in pts2]
        self._poly(pts2, c3)
        # eraser top
        eraser = self._rect_pts(-W/2, H/2-H*0.12, W, H*0.12)
        pts3   = self._rot(eraser, 0, 0, a)
        pts3   = [(p[0]+x, p[1]+y) for p in pts3]
        self._poly(pts3, c2)

    def _draw_pen(self, s):
        x, y, sc, a = s["x"], s["y"], s["scale"], s["angle"]
        c1, c2, c3  = s["c1"], s["c2"], s["c3"]
        W, H = 5*sc, 48*sc
        # barrel
        body = self._rect_pts(-W/2, -H/2, W, H*0.8)
        pts  = self._rot(body, 0, 0, a)
        pts  = [(p[0]+x, p[1]+y) for p in pts]
        self._poly(pts, c1)
        # nib
        nib = [(-W/2, -H/2+H*0.8),(W/2,-H/2+H*0.8),(0,-H/2+H)]
        pts2 = self._rot(nib, 0, 0, a)
        pts2 = [(p[0]+x, p[1]+y) for p in pts2]
        self._poly(pts2, c2)
        # clip
        clip = self._rect_pts(W/2-W*0.15, -H/2, W*0.15, H*0.6)
        pts3 = self._rot(clip, 0, 0, a)
        pts3 = [(p[0]+x, p[1]+y) for p in pts3]
        self._poly(pts3, c3)

    def _draw_book(self, s):
        x, y, sc, a = s["x"], s["y"], s["scale"], s["angle"]
        c1, c2, c3  = s["c1"], s["c2"], s["c3"]
        W, H = 32*sc, 40*sc
        # cover
        cover = self._rect_pts(-W/2, -H/2, W, H)
        pts   = self._rot(cover, 0, 0, a)
        pts   = [(p[0]+x, p[1]+y) for p in pts]
        self._poly(pts, c1)
        # spine
        spine = self._rect_pts(-W/2, -H/2, W*0.12, H)
        pts2  = self._rot(spine, 0, 0, a)
        pts2  = [(p[0]+x, p[1]+y) for p in pts2]
        self._poly(pts2, c2)
        # pages lines
        for i in range(1, 4):
            lx = -W/2 + W*0.2 + (W*0.65/4)*i
            line = self._rect_pts(lx, -H/2+H*0.15, W*0.04, H*0.7)
            pts3 = self._rot(line, 0, 0, a)
            pts3 = [(p[0]+x, p[1]+y) for p in pts3]
            self._poly(pts3, c3)

    def _draw_ruler(self, s):
        x, y, sc, a = s["x"], s["y"], s["scale"], s["angle"]
        c1, c2, _   = s["c1"], s["c2"], s["c3"]
        W, H = 60*sc, 12*sc
        body = self._rect_pts(-W/2, -H/2, W, H)
        pts  = self._rot(body, 0, 0, a)
        pts  = [(p[0]+x, p[1]+y) for p in pts]
        self._poly(pts, c1)
        # tick marks
        for i in range(11):
            tx = -W/2 + (W/10)*i
            th = H*0.5 if i % 5 == 0 else H*0.3
            tick = self._rect_pts(tx, -H/2, W*0.02, th)
            pts2 = self._rot(tick, 0, 0, a)
            pts2 = [(p[0]+x, p[1]+y) for p in pts2]
            self._poly(pts2, c2)

    def _draw_star(self, s):
        x, y, sc, a = s["x"], s["y"], s["scale"], s["angle"]
        c1 = s["c1"]
        outer, inner = 18*sc, 8*sc
        pts = []
        for i in range(10):
            r   = outer if i % 2 == 0 else inner
            ang = math.radians(a + i*36 - 90)
            pts.append((x + r*math.cos(ang), y + r*math.sin(ang)))
        self._poly(pts, c1)

    def _draw_graduation_cap(self, s):
        x, y, sc, a = s["x"], s["y"], s["scale"], s["angle"]
        c1, c2, _   = s["c1"], s["c2"], s["c3"]
        # board (diamond)
        size = 22*sc
        diamond = [(0,-size),(size*0.7,0),(0,size*0.5),(-size*0.7,0)]
        pts = self._rot(diamond, 0, 0, a)
        pts = [(p[0]+x, p[1]+y) for p in pts]
        self._poly(pts, c1)
        # top knob
        knob_r = 4*sc
        self.create_oval(x-knob_r, y-size-knob_r,
                         x+knob_r, y-size+knob_r,
                         fill=c2, outline="", tags="item")
        # tassel line
        tassel_pts = self._rot([(size*0.6, 0),(size*0.6+4*sc, 14*sc)], 0, 0, a)
        tassel_pts = [(p[0]+x, p[1]+y) for p in tassel_pts]
        if len(tassel_pts) == 2:
            self.create_line(tassel_pts[0][0], tassel_pts[0][1],
                             tassel_pts[1][0], tassel_pts[1][1],
                             fill=c2, width=max(1, int(2*sc)), tags="item")

    def _draw_magnifier(self, s):
        x, y, sc, a = s["x"], s["y"], s["scale"], s["angle"]
        c1, c2, _   = s["c1"], s["c2"], s["c3"]
        r    = 14*sc
        # lens circle
        self.create_oval(x-r, y-r, x+r, y+r,
                         fill="", outline=c1,
                         width=max(2, int(3*sc)), tags="item")
        # handle
        ang = math.radians(a + 45)
        hx1 = x + r*math.cos(ang)
        hy1 = y + r*math.sin(ang)
        hx2 = x + (r + 16*sc)*math.cos(ang)
        hy2 = y + (r + 16*sc)*math.sin(ang)
        self.create_line(hx1, hy1, hx2, hy2,
                         fill=c2, width=max(2, int(3*sc)),
                         capstyle="round", tags="item")

    def _draw_paper(self, s):
        x, y, sc, a = s["x"], s["y"], s["scale"], s["angle"]
        c1, c2, c3  = s["c1"], s["c2"], s["c3"]
        W, H = 28*sc, 36*sc
        # sheet
        body = self._rect_pts(-W/2, -H/2, W, H)
        pts  = self._rot(body, 0, 0, a)
        pts  = [(p[0]+x, p[1]+y) for p in pts]
        self._poly(pts, c1)
        # folded corner
        fold = [(-W/2+W*0.65,-H/2),(-W/2+W,-H/2),(-W/2+W*0.65,-H/2+H*0.22)]
        pts2 = self._rot(fold, 0, 0, a)
        pts2 = [(p[0]+x, p[1]+y) for p in pts2]
        self._poly(pts2, c3)
        # lines on paper
        for i in range(1, 5):
            lx1 = -W/2 + W*0.15
            lx2 = -W/2 + W*0.75
            ly  = -H/2 + H*(0.25 + 0.15*i)
            lpts = self._rot([(lx1,ly),(lx2,ly),(lx2,ly+H*0.04),(lx1,ly+H*0.04)],0,0,a)
            lpts = [(p[0]+x, p[1]+y) for p in lpts]
            self._poly(lpts, c2)

    def stop(self):
        self._running = False


# ── Login page ────────────────────────────────────────────────────────────────
class LoginPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=TOP_BG)
        self.master = master
        self._bg    = None
        self._build()

    def _build(self):
        # top bar
        topbar = tk.Frame(self, bg=TOP_BG, height=50)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Label(topbar, text="E  EPOKA  THESIS TRACKER",
                 bg=TOP_BG, fg=WHITE,
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=20, pady=12)

        # animated canvas
        container = tk.Frame(self, bg=TOP_BG)
        container.pack(fill="both", expand=True)

        self._bg = AnimatedBackground(container, bg=TOP_BG)
        self._bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        # card
        card = tk.Frame(container, bg=WHITE, padx=36, pady=32,
                        relief="flat",
                        highlightthickness=1,
                        highlightbackground=BORDER)
        card.place(relx=0.5, rely=0.5, anchor="center", width=420)

        # accent bar
        tk.Frame(card, bg=BLUE, height=4).pack(fill="x", pady=(0, 16))

        # Header
        tk.Label(card, text="Welcome back",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 20, "bold")).pack(pady=(0, 4))
        tk.Label(card, text="Sign in to your account",
                 bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 10)).pack(pady=(0, 22))

        # role
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

        # email
        tk.Label(card, text="Email", bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.email_var = tk.StringVar()
        e1 = tk.Entry(card, textvariable=self.email_var, width=36)
        style_entry(e1)
        e1.pack(fill="x", ipady=7, pady=(4, 14))
        
        # password
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

    def destroy(self):
        if self._bg:
            self._bg.stop()
        super().destroy()

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
