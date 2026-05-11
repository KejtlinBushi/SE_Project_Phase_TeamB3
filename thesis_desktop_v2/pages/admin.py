"""
pages/admin.py
Admin pages with full CRUD + Epoka style.
CEN 302 Software Engineering | Group III | Epoka University
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from database import query
from auth import SESSION, hash_password, check_password
from ui import (BG_MAIN, BG_WHITE, BLUE, BLUE2, GREEN, GOLD_TILE, ORANGE,
                WHITE, MUTED, DARK, BORDER, SUCCESS, DANGER, WARNING, INFO,
                TEXT2, label, style_btn, style_entry, card_frame,
                stat_card, page_header, style_treeview, ScrollFrame)


def create_notification(user_role, user_id, notif_type, title, message):
    try:
        query("""INSERT INTO notifications (user_role, user_id, type, title, message)
                 VALUES (%s,%s,%s,%s,%s)""",
              (user_role, user_id, notif_type, title, message))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
class AdminDashboard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        self._parent = parent
        page_header(self, "Admin Dashboard", "System overview")
        try:
            students   = query("SELECT COUNT(*) AS c FROM students",     one=True)
            sups       = query("SELECT COUNT(*) AS c FROM supervisors",  one=True)
            subs       = query("SELECT COUNT(*) AS c FROM submissions",  one=True)
            meetings   = query("SELECT COUNT(*) AS c FROM meetings",     one=True)
            milestones = query("SELECT COUNT(*) AS c FROM milestones",   one=True)
        except Exception as e:
            tk.Label(self, text=f"DB error: {e}", bg=BG_MAIN, fg=DANGER,
                     font=("Segoe UI", 11)).pack(pady=20)
            return

        grid = tk.Frame(self, bg=BG_MAIN)
        grid.pack(fill="x", padx=20, pady=12)

        cards = [
            ("👥", "Students",    str(students["c"]),   BLUE,      "users"),
            ("🎓", "Supervisors", str(sups["c"]),       GREEN,     "users"),
            ("📄", "Submissions", str(subs["c"]),       GOLD_TILE, None),
            ("📅", "Meetings",    str(meetings["c"]),   ORANGE,    None),
            ("🎯", "Milestones",  str(milestones["c"]), "#8e44ad", None),
        ]

        for i, (icon, title, val, color, nav_page) in enumerate(cards):
            f = tk.Frame(grid, bg=color, width=150, height=90,
                         cursor="hand2" if nav_page else "arrow")
            f.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            f.pack_propagate(False)

            icon_lbl  = tk.Label(f, text=icon,  bg=color, fg=WHITE, font=("Segoe UI", 18))
            val_lbl   = tk.Label(f, text=val,   bg=color, fg=WHITE, font=("Segoe UI", 14, "bold"))
            title_lbl = tk.Label(f, text=title, bg=color, fg=WHITE, font=("Segoe UI", 8))
            icon_lbl.pack(pady=(10, 0))
            val_lbl.pack()
            title_lbl.pack()

            if nav_page:
                dark = self._darken(color)
                for widget in (f, icon_lbl, val_lbl, title_lbl):
                    widget.bind("<Enter>",
                        lambda e, w=f, d=dark, c=color: self._on_hover(w, d))
                    widget.bind("<Leave>",
                        lambda e, w=f, d=dark, c=color: self._on_leave(w, c))
                    widget.bind("<Button-1>",
                        lambda e, p=nav_page: self._navigate(p))

                hint = tk.Label(f, text="→", bg=color, fg=WHITE,
                                font=("Segoe UI", 9))
                hint.place(relx=1.0, rely=1.0, anchor="se", x=-4, y=-3)
                hint.bind("<Button-1>", lambda e, p=nav_page: self._navigate(p))
                hint.bind("<Enter>",
                    lambda e, w=f, d=dark: self._on_hover(w, d))
                hint.bind("<Leave>",
                    lambda e, w=f, c=color: self._on_leave(w, c))

            grid.columnconfigure(i, weight=1)

        af = card_frame(self, padx=0, pady=0)
        af.pack(fill="both", expand=True, padx=20, pady=8)
        tk.Label(af, text="Recent Activity", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(af, bg=BORDER, height=1).pack(fill="x")
        cols = ("Role", "Action", "Description", "Time")
        tree = ttk.Treeview(af, columns=cols, show="headings", height=10)
        style_treeview(tree, cols, [90, 120, 300, 130])
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        rows = query("""SELECT actor_role, action_type, description, logged_at
                        FROM activity_log ORDER BY logged_at DESC LIMIT 30""") or []
        for r in rows:
            tree.insert("", "end", values=(
                r["actor_role"], r["action_type"],
                r["description"], str(r["logged_at"])[:16]))

    @staticmethod
    def _darken(hex_color):
        try:
            h = hex_color.lstrip("#")
            r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, int(r * 0.82))
            g = max(0, int(g * 0.82))
            b = max(0, int(b * 0.82))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    @staticmethod
    def _on_hover(frame, dark_color):
        for child in frame.winfo_children():
            try:
                child.configure(bg=dark_color)
            except Exception:
                pass
        frame.configure(bg=dark_color)

    @staticmethod
    def _on_leave(frame, orig_color):
        for child in frame.winfo_children():
            try:
                child.configure(bg=orig_color)
            except Exception:
                pass
        frame.configure(bg=orig_color)

    def _navigate(self, page):
        widget = self._parent
        for _ in range(10):
            if hasattr(widget, "_navigate"):
                widget._navigate(page)
                return
            widget = getattr(widget, "master", None)
            if widget is None:
                break


# ═══════════════════════════════════════════════════════════
class AdminUsers(tk.Frame):
    """Full CRUD for users — Create, Read, Update, Delete."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "User Management", "Create, edit and delete users")
        self.user_map   = {}   # iid → (uid, role, name, email)
        self._btn_map   = {}   # iid → delete Button widget
        self._build()

    # ── layout ───────────────────────────────────────────────
    def _build(self):
        # ── Create form ──────────────────────────────────────
        cf = card_frame(self, padx=16, pady=14)
        cf.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(cf, text="Create New User", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

        row1 = tk.Frame(cf, bg=BG_WHITE)
        row1.pack(fill="x")
        self._uvars = {}
        for lbl_t, key in [("Full Name", "name"), ("Email", "email"),
                            ("Password", "pw"),   ("Role", None)]:
            col = tk.Frame(row1, bg=BG_WHITE)
            col.pack(side="left", padx=(0, 10), expand=True, fill="x")
            tk.Label(col, text=lbl_t, bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            if key:
                v = tk.StringVar()
                e = tk.Entry(col, textvariable=v,
                             show="•" if key == "pw" else "")
                style_entry(e)
                e.pack(fill="x", ipady=5, pady=(4, 0))
                self._uvars[key] = v
            else:
                v = tk.StringVar(value="student")
                ttk.Combobox(col, textvariable=v,
                             values=["student", "supervisor"],
                             state="readonly").pack(fill="x", pady=(4, 0))
                self._uvars["role"] = v

        tk.Button(cf, text="+ Create User", command=self._create_user,
                  bg="#2e8b57", fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=12, pady=5).pack(anchor="w", pady=(12, 0))

        # ── Users table ───────────────────────────────────────
        uf = card_frame(self, padx=0, pady=0)
        uf.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(uf, text="All Users", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(uf, bg=BORDER, height=1).pack(fill="x")

        # ── Split pane: treeview left, delete buttons right ───
        pane = tk.Frame(uf, bg=BG_WHITE)
        pane.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        # Treeview
        tree_f = tk.Frame(pane, bg=BG_WHITE)
        tree_f.pack(side="left", fill="both", expand=True)

        cols = ("ID", "Name", "Email", "Role", "Created")
        self.tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=9)
        style_treeview(self.tree, cols, [50, 160, 200, 90, 130])
        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Delete-buttons column (right of treeview)
        self._del_col = tk.Frame(pane, bg=BG_WHITE, width=44)
        self._del_col.pack(side="right", fill="y")
        self._del_col.pack_propagate(False)

        # Header label to align with treeview heading
        tk.Label(self._del_col, text="Del", bg="#eaf0fb", fg=DARK,
                 font=("Segoe UI", 9, "bold"),
                 width=4, height=1,
                 relief="flat").pack(fill="x")

        # Bottom action bar
        bf = tk.Frame(uf, bg=BG_WHITE, pady=8)
        bf.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(bf, text="✎ Edit Selected",
                  command=self._edit_user,
                  bg=GOLD_TILE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=10, pady=4).pack(side="left", padx=(0, 6))

        # Bind selection so delete buttons highlight row
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self._load()

    # ── data ─────────────────────────────────────────────────
    def _load(self):
        # Clear tree
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.user_map.clear()

        # Clear old delete buttons
        for btn in self._btn_map.values():
            btn.destroy()
        self._btn_map.clear()

        students = query("SELECT student_id AS id, full_name, email, 'student' AS role, created_at FROM students") or []
        sups     = query("SELECT supervisor_id AS id, full_name, email, 'supervisor' AS role, created_at FROM supervisors") or []
        admins   = query("SELECT admin_id AS id, full_name, email, 'admin' AS role, created_at FROM administrators") or []

        all_users = sorted(students + sups + admins,
                           key=lambda x: x["created_at"], reverse=True)

        for r in all_users:
            iid = self.tree.insert("", "end", values=(
                r["id"], r["full_name"], r["email"],
                r["role"], str(r["created_at"])[:16]))
            self.user_map[iid] = (r["id"], r["role"], r["full_name"], r["email"])

            # Red trash button per row
            is_admin = r["role"] == "admin"
            btn = tk.Button(
                self._del_col,
                text="🗑",
                font=("Segoe UI", 13),
                bg="#fff0f0" if not is_admin else "#f5f5f5",
                fg="#c0392b" if not is_admin else "#aaaaaa",
                activebackground="#ffd6d6",
                activeforeground="#922b21",
                relief="flat",
                cursor="hand2" if not is_admin else "arrow",
                width=3,
                pady=3,
                state="normal" if not is_admin else "disabled",
                command=(lambda i=iid: self._delete_row(i)) if not is_admin else None
            )
            btn.pack(fill="x")

            # Hover effect for non-admin
            if not is_admin:
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ffd6d6"))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#fff0f0"))

            self._btn_map[iid] = btn

        # Sync scroll between treeview and button column
        self.tree.bind("<MouseWheel>", self._sync_scroll)

    # ── keep buttons aligned when tree scrolls ───────────────
    def _sync_scroll(self, event):
        for btn in self._btn_map.values():
            btn.pack_forget()
        for child in self._del_col.winfo_children():
            if isinstance(child, tk.Label):
                child.pack(fill="x")
                break
        for iid in self.tree.get_children():
            if iid in self._btn_map:
                self._btn_map[iid].pack(fill="x")

    def _on_select(self, event):
        pass

    # ── actions ──────────────────────────────────────────────
    def _delete_row(self, iid):
        info = self.user_map.get(iid)
        if not info:
            return
        uid, role, name, _ = info
        if role == "admin":
            messagebox.showerror("Error", "Cannot delete admin accounts.")
            return
        if not messagebox.askyesno(
                "Konfirmo fshirjen",
                f"Je i sigurt që dëshiron të fshish:\n\n👤  {name}  ({role})\n\nKjo veprim nuk mund të kthehet!"):
            return
        tbl = "students" if role == "student" else "supervisors"
        pk  = "student_id" if role == "student" else "supervisor_id"
        query(f"DELETE FROM {tbl} WHERE {pk}=%s", (uid,))
        messagebox.showinfo("U fshi", f"Përdoruesi '{name}' u fshi me sukses.")
        self._load()

    def _create_user(self):
        name  = self._uvars["name"].get().strip()
        email = self._uvars["email"].get().strip()
        pw    = self._uvars["pw"].get()
        role  = self._uvars["role"].get()
        if not all([name, email, pw]):
            messagebox.showwarning("Missing", "All fields are required.")
            return
        tbl = "students" if role == "student" else "supervisors"
        if query(f"SELECT email FROM {tbl} WHERE email=%s", (email,), one=True):
            messagebox.showerror("Error", "Email already exists.")
            return
        query(f"INSERT INTO {tbl} (full_name, email, password_hash) VALUES (%s,%s,%s)",
              (name, email, hash_password(pw)))
        messagebox.showinfo("Created", f"{role.capitalize()} '{name}' created.")
        for v in self._uvars.values():
            v.set("")
        self._load()

    def _edit_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a user first.")
            return
        uid, role, old_name, old_email = self.user_map[sel[0]]
        if role == "admin":
            messagebox.showinfo("Info", "Use the Profile page to edit admin accounts.")
            return
        dlg = EditUserDialog(self.master, uid, role, old_name, old_email)
        self.wait_window(dlg)
        self._load()

    def _delete_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a user first.")
            return
        uid, role, name, _ = self.user_map[sel[0]]
        if role == "admin":
            messagebox.showerror("Error", "Cannot delete admin accounts.")
            return
        if not messagebox.askyesno("Confirm", f"Delete user '{name}'?\nThis cannot be undone."):
            return
        tbl = "students" if role == "student" else "supervisors"
        pk  = "student_id" if role == "student" else "supervisor_id"
        query(f"DELETE FROM {tbl} WHERE {pk}=%s", (uid,))
        messagebox.showinfo("Deleted", f"User '{name}' deleted.")
        self._load()


class EditUserDialog(tk.Toplevel):
    """Dialog for editing a user's name, email and optionally resetting password."""

    def __init__(self, master, uid, role, old_name, old_email):
        super().__init__(master)
        self.uid      = uid
        self.role     = role
        self.title(f"Edit {role.capitalize()}")
        self.geometry("400x320")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        self._build(old_name, old_email)

    def _build(self, old_name, old_email):
        f = tk.Frame(self, bg=BG_MAIN, padx=24, pady=20)
        f.pack(fill="both", expand=True)
        tk.Label(f, text=f"Edit {self.role.capitalize()}",
                 bg=BG_MAIN, fg=DARK,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 16))

        self.name_var  = tk.StringVar(value=old_name)
        self.email_var = tk.StringVar(value=old_email)
        self.pw_var    = tk.StringVar()

        for lbl_t, var, hidden in [
            ("Full Name", self.name_var,  False),
            ("Email",     self.email_var, False),
            ("New Password (leave blank to keep)", self.pw_var, True),
        ]:
            tk.Label(f, text=lbl_t, bg=BG_MAIN, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            e = tk.Entry(f, textvariable=var, show="•" if hidden else "")
            style_entry(e)
            e.pack(fill="x", ipady=6, pady=(4, 10))

        self.err = tk.Label(f, text="", bg=BG_MAIN, fg=DANGER,
                            font=("Segoe UI", 9))
        self.err.pack()
        bf = tk.Frame(f, bg=BG_MAIN)
        bf.pack(fill="x", pady=(8, 0))
        tk.Button(bf, text="Save", command=self._save,
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=12, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(bf, text="Cancel", command=self.destroy,
                  bg="#95a5a6", fg=WHITE, relief="flat",
                  font=("Segoe UI", 10),
                  padx=12, pady=5).pack(side="left")

    def _save(self):
        name  = self.name_var.get().strip()
        email = self.email_var.get().strip()
        pw    = self.pw_var.get()
        if not name or not email:
            self.err.config(text="Name and email are required.")
            return
        tbl = "students" if self.role == "student" else "supervisors"
        pk  = "student_id" if self.role == "student" else "supervisor_id"
        query(f"UPDATE {tbl} SET full_name=%s, email=%s WHERE {pk}=%s",
              (name, email, self.uid))
        if pw:
            if len(pw) < 8:
                self.err.config(text="Password must be at least 8 characters.")
                return
            query(f"UPDATE {tbl} SET password_hash=%s WHERE {pk}=%s",
                  (hash_password(pw), self.uid))
        messagebox.showinfo("Saved", "User updated successfully.")
        self.destroy()


# ═══════════════════════════════════════════════════════════
class AdminAssignments(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Assignments", "Assign supervisors to students")
        self._build()

    def _build(self):
        students = query("SELECT student_id, full_name FROM students") or []
        sups     = query("SELECT supervisor_id, full_name FROM supervisors") or []
        self._stu_map = {s["full_name"]: s["student_id"] for s in students}
        self._sup_map = {s["full_name"]: s["supervisor_id"] for s in sups}

        cf = card_frame(self, padx=16, pady=14)
        cf.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(cf, text="Assign Supervisor to Student", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

        row = tk.Frame(cf, bg=BG_WHITE)
        row.pack(fill="x")
        self._stu_var = tk.StringVar()
        self._sup_var = tk.StringVar()
        for lbl_t, var, vals in [
            ("Student",    self._stu_var, list(self._stu_map.keys())),
            ("Supervisor", self._sup_var, list(self._sup_map.keys())),
        ]:
            col = tk.Frame(row, bg=BG_WHITE)
            col.pack(side="left", padx=(0, 16), expand=True, fill="x")
            tk.Label(col, text=lbl_t, bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            ttk.Combobox(col, textvariable=var, values=vals,
                         state="readonly", width=30).pack(fill="x", pady=(4, 0))

        ab = tk.Button(cf, text="Assign", command=self._assign,
                      bg="#2e8b57", fg=WHITE, relief="flat",
                      font=("Segoe UI", 10, "bold"),
                      padx=12, pady=5)
        ab.pack(anchor="w", pady=(12, 0))

        lf = card_frame(self, padx=0, pady=0)
        lf.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(lf, text="Current Assignments", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x")

        tree_f = tk.Frame(lf, bg=BG_WHITE)
        tree_f.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        cols = ("Student", "Supervisor", "Assigned At")
        self.tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=10)
        style_treeview(self.tree, cols, [200, 200, 150])
        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tk.Button(lf, text="Revoke Selected Assignment",
                  command=self._revoke,
                  bg=DANGER, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=10, pady=4).pack(anchor="w", padx=8, pady=(0, 8))
        self.assign_map = {}
        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.assign_map.clear()
        rows = query("""SELECT sa.id, st.full_name AS student, sup.full_name AS supervisor,
                               sa.assigned_at, sa.student_id
                        FROM supervisor_assignments sa
                        JOIN students st    ON sa.student_id=st.student_id
                        JOIN supervisors sup ON sa.supervisor_id=sup.supervisor_id
                        ORDER BY sa.assigned_at DESC""") or []
        for r in rows:
            iid = self.tree.insert("", "end", values=(
                r["student"], r["supervisor"], str(r["assigned_at"])[:16]))
            self.assign_map[iid] = (r["id"], r["student_id"])

    def _assign(self):
        sname  = self._stu_var.get()
        spname = self._sup_var.get()
        if not sname or not spname:
            messagebox.showwarning("Missing", "Select both student and supervisor.")
            return
        st_id    = self._stu_map[sname]
        sup_id   = self._sup_map[spname]
        admin_id = SESSION["user_id"]
        query("UPDATE students SET supervisor_id=%s WHERE student_id=%s", (sup_id, st_id))
        query("""INSERT INTO supervisor_assignments (student_id, supervisor_id, assigned_by)
                 VALUES (%s,%s,%s)
                 ON DUPLICATE KEY UPDATE supervisor_id=%s, assigned_by=%s""",
              (st_id, sup_id, admin_id, sup_id, admin_id))
        create_notification("student", st_id, "assignment",
                            "Supervisor Assigned",
                            f"You have been assigned to {spname}")
        messagebox.showinfo("Assigned", f"{sname} assigned to {spname}.")
        self._load()

    def _revoke(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select an assignment first.")
            return
        aid, st_id = self.assign_map[sel[0]]
        if not messagebox.askyesno("Confirm", "Revoke this assignment?"):
            return
        query("DELETE FROM supervisor_assignments WHERE id=%s", (aid,))
        query("UPDATE students SET supervisor_id=NULL WHERE student_id=%s", (st_id,))
        messagebox.showinfo("Revoked", "Assignment revoked.")
        self._load()


# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
class AdminActivityLog(tk.Frame):


    _PAIR_COLORS = [
        "#c0392b", "#e67e22", "#f39c12", "#27ae60", "#16a085",
        "#b9b229", "#8e44ad", "#2c3e50", "#d35400", "#1abc9c",
        "#e73cc2", "#e91e63", "#9c27b0", "#673ab7", "#3f51b5",
        "#0288d1", "#00796b", "#558b2f", "#5f3714", "#341b12",
    ]

    _DAYS  = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    _HOURS = [f"{h:02d}:00" for h in range(8, 16)]  # 08:00 – 16:00

    _DAY_W  = 110
    _SLOT_W = 120
    _ROW_H  = 90
    _HDR_H  = 36

    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Meeting Schedule", "All student-supervisor meetings")
        self._pair_color_map: dict = {}
        self._color_idx = 0
        self._build()

    def _get_pair_color(self, student_id, supervisor_id):
        key = (student_id, supervisor_id)
        if key not in self._pair_color_map:
            self._pair_color_map[key] = self._PAIR_COLORS[
                self._color_idx % len(self._PAIR_COLORS)]
            self._color_idx += 1
        return self._pair_color_map[key]

    def _fetch_meetings(self):
        return query("""
            SELECT
                m.meeting_id,
                m.meeting_date,
                m.meeting_time,
                m.title,
                m.status,
                m.meeting_type,
                m.student_id,
                m.supervisor_id,
                st.full_name  AS student_name,
                sup.full_name AS supervisor_name
            FROM meetings m
            JOIN students    st  ON m.student_id    = st.student_id
            JOIN supervisors sup ON m.supervisor_id = sup.supervisor_id
            ORDER BY m.meeting_date, m.meeting_time
        """) or []

    def _build(self):
        try:
            meetings = self._fetch_meetings()
        except Exception as e:
            tk.Label(self, text=f"Database error: {e}",
                     bg=BG_MAIN, fg=DANGER,
                     font=("Segoe UI", 11)).pack(pady=30)
            return

        # ── legend label ─────────────────────────────────────
        top = tk.Frame(self, bg=BG_MAIN)
        top.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(top,
                    text="Legend: Each color represents a student-supervisor pair.",
                 bg=BG_MAIN, fg=MUTED,
                 font=("Segoe UI", 9, "italic")).pack(side="left")

        if not meetings:
            tk.Label(self, text="Nuk ka takime të planifikuara.",
                     bg=BG_MAIN, fg=MUTED,
                     font=("Segoe UI", 12)).pack(pady=40)
            return

        # ── scrollable canvas ─────────────────────────────────
        outer = tk.Frame(self, bg=BG_MAIN)
        outer.pack(fill="both", expand=True, padx=20, pady=10)

        total_w = self._DAY_W + self._SLOT_W * len(self._HOURS) + 4
        total_h = self._HDR_H + self._ROW_H  * len(self._DAYS)  + 4

        hscroll = ttk.Scrollbar(outer, orient="horizontal")
        vscroll = ttk.Scrollbar(outer, orient="vertical")
        hscroll.pack(side="bottom", fill="x")
        vscroll.pack(side="right",  fill="y")

        self._canvas = tk.Canvas(
            outer,
            bg=BG_WHITE,
            width=min(total_w, 1100),
            height=min(total_h, 520),
            scrollregion=(0, 0, total_w, total_h),
            xscrollcommand=hscroll.set,
            yscrollcommand=vscroll.set,
            highlightthickness=0,
        )
        self._canvas.pack(side="left", fill="both", expand=True)
        hscroll.config(command=self._canvas.xview)
        vscroll.config(command=self._canvas.yview)

        self._canvas.bind("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._canvas.bind("<Shift-MouseWheel>",
            lambda e: self._canvas.xview_scroll(int(-1*(e.delta/120)), "units"))

        try:
            self._draw_grid()
            self._draw_meetings(meetings)
        except Exception as e:
            tk.Label(self, text=f"Render error: {e}",
                     bg=BG_MAIN, fg=DANGER,
                     font=("Segoe UI", 10)).pack(pady=10)

        self._draw_legend(meetings)

    def _draw_grid(self):
        c  = self._canvas
        dw = self._DAY_W
        sw = self._SLOT_W
        rh = self._ROW_H
        hh = self._HDR_H

        # ── header: top-left corner ───────────────────────────
        c.create_rectangle(0, 0, dw, hh, fill="#1b3a6b", outline="#0d2247")
        c.create_text(dw//2, hh//2, text="Day  /  Time",
                      fill=WHITE, font=("Segoe UI", 9, "bold"))

        # ── hour headers ──────────────────────────────────────
        for i, h in enumerate(self._HOURS):
            x0 = dw + i * sw
            x1 = x0 + sw
            # alternating header shade
            hdr_bg = "#1b3a6b" if i % 2 == 0 else "#1e4080"
            c.create_rectangle(x0, 0, x1, hh, fill=hdr_bg, outline="#0d2247")
            # range label e.g. "09:00 – 10:00"
            hr_int = 8 + i
            label_text = f"{hr_int:02d}:00 – {hr_int+1:02d}:00"
            c.create_text((x0+x1)//2, hh//2, text=label_text,
                          fill=WHITE, font=("Segoe UI", 8, "bold"))

        # ── day rows ──────────────────────────────────────────
        for j, day in enumerate(self._DAYS):
            y0 = hh + j * rh
            y1 = y0 + rh
            day_bg = "#f0f4fa" if j % 2 == 0 else "#e8eef8"

            # day label cell
            c.create_rectangle(0, y0, dw, y1,
                               fill="#1b3a6b", outline="#0d2247")
            c.create_text(dw//2, (y0+y1)//2, text=day,
                          fill=WHITE, font=("Segoe UI", 10, "bold"))

            # hour slot cells
            for i in range(len(self._HOURS)):
                x0 = dw + i * sw
                x1 = x0 + sw
                cell_bg = "#f7f9fd" if (i + j) % 2 == 0 else "#eef2fa"
                c.create_rectangle(x0, y0, x1, y1,
                                   fill=cell_bg, outline="#d0d8e8")

    def _draw_meetings(self, meetings):
        import datetime as _dt

        c  = self._canvas
        dw = self._DAY_W
        sw = self._SLOT_W
        rh = self._ROW_H
        hh = self._HDR_H

        cell_counts: dict = {}

        for m in meetings:
            try:
                # ── parse date ───────────────────────────────
                md = m["meeting_date"]
                mt = m["meeting_time"]
                if md is None or mt is None:
                    continue

                # meeting_date may be a date object or string
                if hasattr(md, "weekday"):
                    wd = md.weekday()
                else:
                    md = _dt.date.fromisoformat(str(md))
                    wd = md.weekday()

                # meeting_time may be timedelta (MySQL) or time or string
                if hasattr(mt, "seconds"):          # timedelta
                    total = int(mt.total_seconds())
                    hr    = total // 3600
                    minute = (total % 3600) // 60
                elif hasattr(mt, "hour"):            # time object
                    hr     = mt.hour
                    minute = mt.minute
                else:                                # string "HH:MM:SS"
                    parts  = str(mt).split(":")
                    hr     = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0

                if wd >= len(self._DAYS):
                    continue
                col_idx = hr - 8
                if col_idx < 0 or col_idx >= len(self._HOURS):
                    continue

                color = self._get_pair_color(m["student_id"], m["supervisor_id"])

                y0_row = hh + wd * rh
                x0_col = dw + col_idx * sw

                cell_key = (wd, col_idx)
                stack    = cell_counts.get(cell_key, 0)
                cell_counts[cell_key] = stack + 1

                # ── block geometry ────────────────────────────
                max_stack   = 3
                block_h     = max(18, (rh - 8) // max(1, stack + 1))
                y0_blk      = y0_row + 4 + stack * block_h
                y1_blk      = y0_blk + block_h - 3
                x0_blk      = x0_col + 4
                x1_blk      = x0_col + sw - 4

                r_tag = f"meet_{m['meeting_id']}"

                # rounded rect with slight shadow
                self._rounded_rect(c, x0_blk+2, y0_blk+2, x1_blk+2, y1_blk+2,
                                   radius=7,
                                   fill=self._darken(color, 0.6),
                                   outline="", tags=r_tag)
                self._rounded_rect(c, x0_blk, y0_blk, x1_blk, y1_blk,
                                   radius=7,
                                   fill=color, outline="", tags=r_tag)

                cx = (x0_blk + x1_blk) // 2
                sup_short   = self._shorten(m["supervisor_name"], 16)
                stu_short   = self._shorten(m["student_name"],    16)
                title_short = self._shorten(m.get("title") or "", 18)
                time_str    = f"{hr:02d}:{minute:02d}"
                type_icon   = "💻" if m.get("meeting_type") == "online" else "🏫"

                # status badge colour
                status      = (m.get("status") or "").lower()
                badge_color = {"confirmed": "#27ae60",
                               "scheduled": "#2980b9",
                               "pending":   "#f39c12",
                               "declined":  "#c0392b",
                               "cancelled": "#7f8c8d"}.get(status, "#555")

                line_h = max(11, (y1_blk - y0_blk) // 4)

                # Line 1 – supervisor (bold white)
                c.create_text(cx, y0_blk + line_h,
                              text=sup_short,
                              fill=WHITE,
                              font=("Segoe UI", 8, "bold"),
                              width=sw - 12, tags=r_tag)
                # Line 2 – student (light blue)
                c.create_text(cx, y0_blk + line_h * 2,
                              text=f"🎓 {stu_short}",
                              fill="#d6eaf8",
                              font=("Segoe UI", 7),
                              width=sw - 12, tags=r_tag)
                # Line 3 – time + type
                c.create_text(cx, y0_blk + line_h * 3,
                              text=f"{type_icon} {time_str}",
                              fill="#aed6f1",
                              font=("Segoe UI", 7, "italic"),
                              width=sw - 12, tags=r_tag)

                # Status dot (top-right corner of block)
                dot_x = x1_blk - 8
                dot_y = y0_blk + 8
                c.create_oval(dot_x-5, dot_y-5, dot_x+5, dot_y+5,
                              fill=badge_color, outline="", tags=r_tag)

                self._bind_tooltip(r_tag,
                                   m["supervisor_name"],
                                   m["student_name"],
                                   str(m["meeting_date"]),
                                   f"{hr:02d}:{minute:02d}",
                                   m.get("title") or "—",
                                   m.get("status") or "—",
                                   m.get("meeting_type") or "—")
            except Exception:
                continue

    # ── helpers ──────────────────────────────────────────────
    @staticmethod
    def _darken(hex_color, factor=0.75):
        try:
            h = hex_color.lstrip("#")
            r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
            return "#{:02x}{:02x}{:02x}".format(
                max(0, int(r*factor)),
                max(0, int(g*factor)),
                max(0, int(b*factor)))
        except Exception:
            return hex_color

    @staticmethod
    def _rounded_rect(canvas, x1, y1, x2, y2, radius=8, **kwargs):
        pts = [
            x1+radius, y1,  x2-radius, y1,
            x2, y1,         x2, y1+radius,
            x2, y2-radius,  x2, y2,
            x2-radius, y2,  x1+radius, y2,
            x1, y2,         x1, y2-radius,
            x1, y1+radius,  x1, y1,
        ]
        return canvas.create_polygon(pts, smooth=True, **kwargs)

    @staticmethod
    def _shorten(name: str, max_chars: int) -> str:
        if not name:
            return "—"
        return name if len(name) <= max_chars else name[:max_chars-1] + "…"

    def _bind_tooltip(self, tag, prof, student, date, time,
                      title, status, mtype):
        status_icon = {"confirmed": "✅", "scheduled": "📅",
                       "pending": "⏳", "declined": "❌",
                       "cancelled": "🚫"}.get(status.lower(), "📌")
        tip_text = (f"👨‍🏫  {prof}\n"
                    f"🎓  {student}\n"
                    f"📅  {date}  🕐 {time}\n"
                    f"📌  {title}\n"
                    f"{status_icon}  {status.capitalize()}  |  "
                    f"{'💻 Online' if mtype=='online' else '🏫 In-person'}")
        tip_win = [None]

        def show(event):
            if tip_win[0]:
                return
            tw = tk.Toplevel(self)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{event.x_root+14}+{event.y_root+12}")
            tk.Label(tw, text=tip_text,
                     bg="#1b3a6b", fg=WHITE,
                     font=("Segoe UI", 9),
                     padx=12, pady=8,
                     justify="left",
                     relief="flat").pack()
            tip_win[0] = tw

        def hide(event):
            if tip_win[0]:
                tip_win[0].destroy()
                tip_win[0] = None

        self._canvas.tag_bind(tag, "<Enter>", show)
        self._canvas.tag_bind(tag, "<Leave>", hide)

    def _draw_legend(self, meetings):
        if not meetings:
            return
        lf = card_frame(self, padx=14, pady=10)
        lf.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(lf, text="Legjenda — Supervisor / Student",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        # status legend
        status_f = tk.Frame(lf, bg=BG_WHITE)
        status_f.pack(anchor="w", pady=(0, 6))
        for label_t, color in [("Confirmed", "#27ae60"), ("Scheduled", "#2980b9"),
                                ("Pending", "#f39c12"),  ("Declined", "#c0392b"),
                                ("Cancelled", "#7f8c8d")]:
            sf = tk.Frame(status_f, bg=BG_WHITE)
            sf.pack(side="left", padx=(0, 14))
            dot = tk.Frame(sf, bg=color, width=10, height=10)
            dot.pack(side="left", padx=(0, 4))
            dot.pack_propagate(False)
            tk.Label(sf, text=label_t, bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 8)).pack(side="left")

        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x", pady=4)

        wrap  = tk.Frame(lf, bg=BG_WHITE)
        wrap.pack(fill="x")
        seen  = set()
        col   = 0
        row_n = 0
        COLS  = 3

        for m in meetings:
            key = (m["student_id"], m["supervisor_id"])
            if key in seen:
                continue
            seen.add(key)
            color = self._get_pair_color(m["student_id"], m["supervisor_id"])

            item = tk.Frame(wrap, bg=BG_WHITE, pady=3)
            item.grid(row=row_n, column=col, padx=(0, 20), sticky="w")

            dot = tk.Frame(item, bg=color, width=14, height=14)
            dot.pack(side="left", padx=(0, 6))
            dot.pack_propagate(False)

            txt_f = tk.Frame(item, bg=BG_WHITE)
            txt_f.pack(side="left")
            tk.Label(txt_f, text=m["supervisor_name"],
                     bg=BG_WHITE, fg=DARK,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            tk.Label(txt_f, text=f"🎓 {m['student_name']}",
                     bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w")

            col += 1
            if col >= COLS:
                col   = 0
                row_n += 1

# ═══════════════════════════════════════════════════════════
class AdminNotifications(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Notifications", "System alerts")
        self._build()

    def _build(self):
        sid  = SESSION["user_id"]
        rows = query("""SELECT * FROM notifications
                        WHERE user_role='admin' AND user_id=%s
                        ORDER BY delivered_at DESC""", (sid,)) or []
        query("UPDATE notifications SET is_read=1 WHERE user_role='admin' AND user_id=%s", (sid,))
        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True, padx=20, pady=12)
        if not rows:
            tk.Label(sf.inner, text="No notifications yet.",
                     bg=BG_MAIN, fg=MUTED, font=("Segoe UI", 11)).pack(pady=20)
            return
        for r in rows:
            nf = card_frame(sf.inner, padx=14, pady=10)
            nf.pack(fill="x", pady=3)
            top = tk.Frame(nf, bg=BG_WHITE)
            top.pack(fill="x")
            tk.Label(top, text=f"🔔  {r['title']}",
                     bg=BG_WHITE, fg=DARK,
                     font=("Segoe UI", 11, "bold")).pack(side="left")
            tk.Label(top, text=str(r["delivered_at"])[:16],
                     bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(side="right")
            tk.Label(nf, text=r["message"], bg=BG_WHITE, fg=TEXT2,
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))


# ═══════════════════════════════════════════════════════════
class AdminProfile(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "My Profile", "Admin account settings")
        self._build()

    def _build(self):
        sid = SESSION["user_id"]
        row = query("SELECT * FROM administrators WHERE admin_id=%s", (sid,), one=True)
        pf  = card_frame(self, padx=20, pady=18)
        pf.pack(fill="x", padx=20, pady=12)
        self.pvars = {}
        for lbl_t, key, ro in [("Full Name", "full_name", False), ("Email", "email", True)]:
            tk.Label(pf, text=lbl_t, bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            v = tk.StringVar(value=row.get(key) or "")
            e = tk.Entry(pf, textvariable=v,
                         state="readonly" if ro else "normal", width=50)
            style_entry(e)
            e.pack(fill="x", ipady=6, pady=(4, 12))
            self.pvars[key] = v
        tk.Frame(pf, bg=BORDER, height=1).pack(fill="x", pady=8)
        tk.Label(pf, text="Change Password", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        for lbl_t, key in [("Current Password", "old_pw"), ("New Password", "new_pw")]:
            tk.Label(pf, text=lbl_t, bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            v = tk.StringVar()
            e = tk.Entry(pf, textvariable=v, show="•", width=50)
            style_entry(e)
            e.pack(fill="x", ipady=6, pady=(4, 12))
            self.pvars[key] = v
        tk.Button(pf, text="Save Changes", command=self._save,
                  bg="#2e8b57", fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6).pack(anchor="w")

    def _save(self):
        sid  = SESSION["user_id"]
        name = self.pvars["full_name"].get().strip()
        if name:
            query("UPDATE administrators SET full_name=%s WHERE admin_id=%s", (name, sid))
        new_pw = self.pvars["new_pw"].get()
        old_pw = self.pvars["old_pw"].get()
        if new_pw:
            row = query("SELECT password_hash FROM administrators WHERE admin_id=%s", (sid,), one=True)
            if not check_password(old_pw, row["password_hash"]):
                messagebox.showerror("Error", "Current password is incorrect.")
                return
            query("UPDATE administrators SET password_hash=%s WHERE admin_id=%s",
                  (hash_password(new_pw), sid))
        messagebox.showinfo("Saved", "Profile updated!")
