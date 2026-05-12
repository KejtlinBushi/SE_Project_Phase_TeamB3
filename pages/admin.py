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
        for i, (icon, title, val, color) in enumerate([
            ("👥", "Students",    str(students["c"]),   BLUE),
            ("🎓", "Supervisors", str(sups["c"]),       GREEN),
            ("📄", "Submissions", str(subs["c"]),       GOLD_TILE),
            ("📅", "Meetings",    str(meetings["c"]),   ORANGE),
            ("🎯", "Milestones",  str(milestones["c"]), "#8e44ad"),
        ]):
            f = tk.Frame(grid, bg=color, width=150, height=90)
            f.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            f.pack_propagate(False)
            tk.Label(f, text=icon, bg=color, fg=WHITE, font=("Segoe UI", 18)).pack(pady=(10, 0))
            tk.Label(f, text=val,  bg=color, fg=WHITE, font=("Segoe UI", 14, "bold")).pack()
            tk.Label(f, text=title,bg=color, fg=WHITE, font=("Segoe UI", 8)).pack()
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


# ═══════════════════════════════════════════════════════════
class AdminUsers(tk.Frame):
    """Full CRUD for users — Create, Read, Update, Delete."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "User Management", "Create, edit and delete users")
        self.user_map = {}
        self._build()

    def _build(self):
        # ── Top: create form ─────────────────────────────────
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
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=12, pady=5).pack(anchor="w", pady=(12, 0))

        # ── Bottom: users table ───────────────────────────────
        uf = card_frame(self, padx=0, pady=0)
        uf.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(uf, text="All Users", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(uf, bg=BORDER, height=1).pack(fill="x")

        tree_f = tk.Frame(uf, bg=BG_WHITE)
        tree_f.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        cols = ("ID", "Name", "Email", "Role", "Created")
        self.tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=9)
        style_treeview(self.tree, cols, [50, 160, 200, 90, 130])
        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Action buttons
        bf = tk.Frame(uf, bg=BG_WHITE, pady=8)
        bf.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(bf, text="✎ Edit Selected",
                  command=self._edit_user,
                  bg=GOLD_TILE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=10, pady=4).pack(side="left", padx=(0, 6))
        tk.Button(bf, text="✕ Delete Selected",
                  command=self._delete_user,
                  bg=DANGER, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=10, pady=4).pack(side="left")

        self._load()

    def _load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.user_map.clear()
        students = query("SELECT student_id AS id, full_name, email, 'student' AS role, created_at FROM students") or []
        sups     = query("SELECT supervisor_id AS id, full_name, email, 'supervisor' AS role, created_at FROM supervisors") or []
        admins   = query("SELECT admin_id AS id, full_name, email, 'admin' AS role, created_at FROM administrators") or []
        for r in sorted(students + sups + admins,
                        key=lambda x: x["created_at"], reverse=True):
            iid = self.tree.insert("", "end", values=(
                r["id"], r["full_name"], r["email"],
                r["role"], str(r["created_at"])[:16]))
            self.user_map[iid] = (r["id"], r["role"], r["full_name"], r["email"])

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
        # Edit dialog
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

        ab = tk.Button(cf, text="Assign", command=self._assign)
        style_btn(ab)
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

        # Revoke button
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
class AdminActivityLog(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Activity Log", "Full system audit trail")
        self._build()

    def _build(self):
        f = card_frame(self, padx=0, pady=0)
        f.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(f, text="All Activity", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x")
        cols = ("Role", "User ID", "Action", "Description", "Time")
        tree_f = tk.Frame(f, bg=BG_WHITE)
        tree_f.pack(fill="both", expand=True, padx=8, pady=8)
        tree = ttk.Treeview(tree_f, columns=cols, show="headings", height=18)
        style_treeview(tree, cols, [80, 60, 120, 340, 130])
        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        rows = query("""SELECT actor_role, actor_id, action_type, description, logged_at
                        FROM activity_log ORDER BY logged_at DESC LIMIT 300""") or []
        for r in rows:
            tree.insert("", "end", values=(
                r["actor_role"], r["actor_id"] or "—",
                r["action_type"], r["description"],
                str(r["logged_at"])[:16]))


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
                  bg=BLUE, fg=WHITE, relief="flat",
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
