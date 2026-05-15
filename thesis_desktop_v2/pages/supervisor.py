"""
pages/supervisor.py
All supervisor pages with Epoka style + chat notifications + file opening.
CEN 302 Software Engineering | Group III | Epoka University
"""

import os, shutil, uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .supervisor_review import SupervisorReviewWindow
from database import query
from auth import SESSION, hash_password, check_password
from ui import (BG_MAIN, BG_WHITE, BLUE, BLUE2, GREEN, GOLD_TILE, ORANGE,
                WHITE, MUTED, DARK, BORDER, SUCCESS, DANGER, WARNING, INFO,
                TEXT, TEXT2, label, style_btn, style_entry, card_frame,
                stat_card, page_header, style_treeview, ScrollFrame,
                FeedbackDialog, open_file)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")

# ── nice accent colours used in the Messages page ──────────────────────────
_BTN_SEND      = "#2e8b57"   # dark green
_BTN_SEND_HVR  = "#1a4d2e"   # darker green on hover
_BTN_ATTACH    = "#B60B0B"   # sky blue
_BTN_LOAD      = "#F9F14A"   # violet – stands out from the blue sidebar
_BTN_LOAD_HVR  = "#D0D928"


def create_notification(user_role, user_id, notif_type, title, message, ref_id=None):
    try:
        query("""INSERT INTO notifications (user_role, user_id, type, title, message, ref_id)
                 VALUES (%s,%s,%s,%s,%s,%s)""",
              (user_role, user_id, notif_type, title, message, ref_id))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
class SupervisorDashboard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        sid = SESSION["user_id"]
        page_header(self, f"Welcome, {SESSION['name']}", "Supervisor Dashboard")
        try:
            students  = query("SELECT COUNT(*) AS c FROM students WHERE supervisor_id=%s", (sid,), one=True)
            pending   = query("""SELECT COUNT(*) AS c FROM submissions s
                                 JOIN students st ON s.student_id=st.student_id
                                 WHERE st.supervisor_id=%s AND s.status='Pending'""", (sid,), one=True)
            meetings  = query("SELECT COUNT(*) AS c FROM meetings WHERE supervisor_id=%s AND status='Confirmed'", (sid,), one=True)
            deadlines = query("SELECT COUNT(*) AS c FROM deadlines WHERE supervisor_id=%s", (sid,), one=True)
        except Exception as e:
            tk.Label(self, text=f"DB error: {e}", bg=BG_MAIN, fg=DANGER,
                     font=("Segoe UI", 11)).pack(pady=20)
            return

        grid = tk.Frame(self, bg=BG_MAIN)
        grid.pack(fill="x", padx=20, pady=12)
        for i, (icon, title, val, color) in enumerate([
            ("👥", "My Students",        str(students["c"]),  BLUE),
            ("📋", "Pending Reviews",    str(pending["c"]),   GOLD_TILE),
            ("✅", "Confirmed Meetings", str(meetings["c"]),  GREEN),
            ("📅", "Active Deadlines",  str(deadlines["c"]), ORANGE),
        ]):
            f = tk.Frame(grid, bg=color, width=160, height=90)
            f.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            f.pack_propagate(False)
            tk.Label(f, text=icon, bg=color, fg=WHITE, font=("Segoe UI", 18)).pack(pady=(10, 0))
            tk.Label(f, text=val, bg=color, fg=WHITE, font=("Segoe UI", 14, "bold")).pack()
            tk.Label(f, text=title, bg=color, fg=WHITE, font=("Segoe UI", 8)).pack()
            grid.columnconfigure(i, weight=1)

        sf = card_frame(self, padx=0, pady=0)
        sf.pack(fill="both", expand=True, padx=20, pady=8)
        tk.Label(sf, text="My Students", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(sf, bg=BORDER, height=1).pack(fill="x")
        cols = ("Name", "Email", "Thesis Title", "Submissions")
        tree = ttk.Treeview(sf, columns=cols, show="headings", height=8)
        style_treeview(tree, cols, [160, 200, 220, 80])
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        rows = query("""SELECT st.full_name, st.email, st.thesis_title,
                               COUNT(sub.submission_id) AS subs
                        FROM students st
                        LEFT JOIN submissions sub ON st.student_id=sub.student_id
                        WHERE st.supervisor_id=%s GROUP BY st.student_id""", (sid,)) or []
        for r in rows:
            tree.insert("", "end", values=(
                r["full_name"], r["email"], r["thesis_title"] or "—", r["subs"]))


# ═══════════════════════════════════════════════════════════
class SupervisorReviews(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)

        page_header(self, "Submission Reviews", "Review student submissions")

        self.sub_map = {}
        self.file_map = {}
        self.data_map = {}

        self._build()

    def _build(self):
        sid = SESSION["user_id"]

        f = card_frame(self, padx=0, pady=0)
        f.pack(fill="both", expand=True, padx=20, pady=12)

        tk.Label(
            f,
            text="Student Submissions",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=14, pady=(10, 6))

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x")

        cols = ("Student", "Version", "File", "Type", "Size (KB)", "Submitted", "Status")

        self.tree = ttk.Treeview(f, columns=cols, show="headings", height=12)
        style_treeview(self.tree, cols, [140, 60, 220, 60, 80, 130, 90])
        self.tree.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        self.tree.bind("<Double-1>", self._open_review_window)

        bf = tk.Frame(f, bg=BG_WHITE, pady=8)
        bf.pack(fill="x", padx=8, pady=(0, 8))

        open_review_btn = tk.Button(
            bf,
            text="Open Review Preview",
            command=self._open_review_window
        )
        style_btn(open_review_btn, BLUE, WHITE)
        open_review_btn.pack(side="left", padx=(0, 6))

        open_file_btn = tk.Button(
            bf,
            text="Open File Only",
            command=self._open_selected_file
        )
        style_btn(open_file_btn, "#2e8b57", WHITE)
        open_file_btn.pack(side="left", padx=(0, 6))

        self._load(sid)

    def _load(self, sid):
        for r in self.tree.get_children():
            self.tree.delete(r)

        self.sub_map.clear()
        self.file_map.clear()
        self.data_map.clear()

        rows = query("""
            SELECT 
                s.submission_id,
                s.student_id,
                st.full_name,
                s.version_number,
                s.file_name,
                s.file_type,
                s.file_size_kb,
                s.submitted_at,
                s.status,
                s.file_path,
                f.comment AS feedback
            FROM submissions s
            JOIN students st ON s.student_id = st.student_id
            LEFT JOIN feedback f ON s.submission_id = f.submission_id
            WHERE st.supervisor_id = %s
            ORDER BY s.submitted_at DESC
        """, (sid,)) or []

        for r in rows:
            iid = self.tree.insert(
                "",
                "end",
                values=(
                    r["full_name"],
                    f"v{r['version_number']}",
                    r["file_name"],
                    r["file_type"],
                    r["file_size_kb"],
                    str(r["submitted_at"])[:16],
                    r["status"]
                )
            )

            self.sub_map[iid] = r["submission_id"]
            self.file_map[iid] = r["file_path"]
            self.data_map[iid] = r

    def _get_selected_submission(self):
        sel = self.tree.selection()

        if not sel:
            messagebox.showwarning("Select", "Please select a submission first.")
            return None

        return self.data_map.get(sel[0])

    def _open_review_window(self, event=None):
        submission = self._get_selected_submission()

        if not submission:
            return

        SupervisorReviewWindow(
            self,
            submission,
            refresh_callback=lambda: self._load(SESSION["user_id"])
        )

    def _open_selected_file(self):
        submission = self._get_selected_submission()

        if not submission:
            return

        fp = submission.get("file_path")

        if not fp:
            messagebox.showerror("Error", "File path not found.")
            return

        full = os.path.join(UPLOAD_FOLDER, fp)

        if not os.path.exists(full):
            messagebox.showerror("Not Found", f"File not found on disk:\n{full}")
            return

        open_file(full)
# ═══════════════════════════════════════════════════════════
class SupervisorDeadlines(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Deadlines", "Create and manage deadlines")
        self._build()

    def _build(self):
        sid      = SESSION["user_id"]
        students = query("SELECT student_id, full_name FROM students WHERE supervisor_id=%s", (sid,)) or []
        cf = card_frame(self, padx=16, pady=14)
        cf.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(cf, text="Create New Deadline", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
        self._title_v = tk.StringVar()
        self._date_v  = tk.StringVar()
        self._desc_v  = tk.StringVar()
        row_f = tk.Frame(cf, bg=BG_WHITE)
        row_f.pack(fill="x")
        for lbl_t, var in [("Title", self._title_v), ("Due Date (YYYY-MM-DD)", self._date_v), ("Description", self._desc_v)]:
            col = tk.Frame(row_f, bg=BG_WHITE)
            col.pack(side="left", padx=(0, 10), expand=True, fill="x")
            tk.Label(col, text=lbl_t, bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
            e = tk.Entry(col, textvariable=var)
            style_entry(e)
            e.pack(fill="x", ipady=5, pady=(4, 0))

        tk.Label(cf, text="Assign to students:", bg=BG_WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 2))
        self.student_vars = {}
        sf2 = tk.Frame(cf, bg=BG_WHITE)
        sf2.pack(anchor="w")
        for s in students:
            v = tk.BooleanVar()
            tk.Checkbutton(sf2, text=s["full_name"], variable=v,
                           bg=BG_WHITE, fg=DARK, selectcolor=BG_WHITE,
                           activebackground=BG_WHITE,
                           font=("Segoe UI", 10)).pack(side="left", padx=8)
            self.student_vars[s["student_id"]] = v
        cb = tk.Button(cf, text="Create Deadline", command=self._create)
        style_btn(cb, "#2e8b57", WHITE)
        cb.pack(anchor="w", pady=(10, 0))

        lf = card_frame(self, padx=0, pady=0)
        lf.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(lf, text="My Deadlines", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x")
        cols = ("Title", "Due Date", "Description", "Assigned To")
        self.tree = ttk.Treeview(lf, columns=cols, show="headings", height=7)
        style_treeview(self.tree, cols, [160, 100, 180, 200])
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self._load(sid)

    def _load(self, sid):
        for r in self.tree.get_children():
            self.tree.delete(r)
        rows = query("""SELECT d.title, d.due_date, d.description,
                               GROUP_CONCAT(st.full_name SEPARATOR ', ') AS assigned_to
                        FROM deadlines d
                        LEFT JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                        LEFT JOIN students st ON da.student_id=st.student_id
                        WHERE d.supervisor_id=%s GROUP BY d.deadline_id
                        ORDER BY d.due_date ASC""", (sid,)) or []
        for r in rows:
            self.tree.insert("", "end", values=(
                r["title"], str(r["due_date"])[:10],
                r["description"] or "—", r["assigned_to"] or "None"))

    def _create(self):
        sid   = SESSION["user_id"]
        title = self._title_v.get().strip()
        date  = self._date_v.get().strip()
        desc  = self._desc_v.get().strip()
        if not title or not date:
            messagebox.showwarning("Missing", "Title and due date are required.")
            return
        did = query("INSERT INTO deadlines (supervisor_id, title, description, due_date) VALUES (%s,%s,%s,%s)",
                    (sid, title, desc, date))
        for st_id, var in self.student_vars.items():
            if var.get():
                query("INSERT IGNORE INTO deadline_assignments (deadline_id, student_id) VALUES (%s,%s)", (did, st_id))
                create_notification("student", st_id, "deadline",
                                    "New Deadline", f"Deadline '{title}' due {date}")
        messagebox.showinfo("Created", "Deadline created and assigned.")
        self._title_v.set(""); self._date_v.set(""); self._desc_v.set("")
        self._load(sid)


# ═══════════════════════════════════════════════════════════
class SupervisorMilestones(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Milestones", "Create and manage milestones")
        self._build()

    def _build(self):
        sid      = SESSION["user_id"]
        students = query("SELECT student_id, full_name FROM students WHERE supervisor_id=%s", (sid,)) or []
        cf = card_frame(self, padx=16, pady=14)
        cf.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(cf, text="Create Milestone", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
        self._stu_map = {s["full_name"]: s["student_id"] for s in students}
        self.stu_var  = tk.StringVar()
        tk.Label(cf, text="Student", bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Combobox(cf, textvariable=self.stu_var,
                     values=list(self._stu_map.keys()),
                     state="readonly", width=40).pack(anchor="w", pady=(4, 10))
        self._mtitle = tk.StringVar()
        self._mdate  = tk.StringVar()
        self._mdesc  = tk.StringVar()
        row_f = tk.Frame(cf, bg=BG_WHITE)
        row_f.pack(fill="x")
        for lbl_t, var in [("Title", self._mtitle), ("Due Date (YYYY-MM-DD)", self._mdate), ("Description", self._mdesc)]:
            col = tk.Frame(row_f, bg=BG_WHITE)
            col.pack(side="left", padx=(0, 10), expand=True, fill="x")
            tk.Label(col, text=lbl_t, bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
            e = tk.Entry(col, textvariable=var)
            style_entry(e)
            e.pack(fill="x", ipady=5, pady=(4, 0))
        tb = tk.Button(cf, text="Create Milestone", command=self._create)
        style_btn(tb, "#2e8b57", WHITE)
        tb.pack(anchor="w", pady=(10, 0))

        lf = card_frame(self, padx=0, pady=0)
        lf.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(lf, text="All Milestones", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x")
        cols = ("Student", "Title", "Due Date", "Status", "Description")
        self.tree = ttk.Treeview(lf, columns=cols, show="headings", height=8)
        style_treeview(self.tree, cols, [140, 160, 100, 100, 200])
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self._load(sid)

    def _load(self, sid):
        for r in self.tree.get_children():
            self.tree.delete(r)
        rows = query("""SELECT st.full_name, m.title, m.due_date, m.status, m.description
                        FROM milestones m
                        JOIN students st ON m.student_id=st.student_id
                        WHERE m.supervisor_id=%s ORDER BY m.due_date ASC""", (sid,)) or []
        for r in rows:
            self.tree.insert("", "end", values=(
                r["full_name"], r["title"],
                str(r["due_date"])[:10], r["status"], r["description"] or "—"))

    def _create(self):
        sid   = SESSION["user_id"]
        sname = self.stu_var.get()
        if not sname:
            messagebox.showwarning("Missing", "Please select a student.")
            return
        st_id = self._stu_map[sname]
        title = self._mtitle.get().strip()
        date  = self._mdate.get().strip()
        desc  = self._mdesc.get().strip()
        if not title or not date:
            messagebox.showwarning("Missing", "Title and due date are required.")
            return
        query("""INSERT INTO milestones (supervisor_id, student_id, title, description, due_date)
                 VALUES (%s,%s,%s,%s,%s)""", (sid, st_id, title, desc, date))
        create_notification("student", st_id, "milestone",
                            "New Milestone", f"Milestone '{title}' due {date}")
        messagebox.showinfo("Created", "Milestone created!")
        self._mtitle.set(""); self._mdate.set(""); self._mdesc.set("")
        self._load(sid)


# ═══════════════════════════════════════════════════════════
class SupervisorMeetings(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)

        page_header(
            self,
            "Meetings",
            "Schedule and manage meetings"
        )

        self.meet_map = {}

        self._build()

    # ======================================================
    def _build(self):

        sid = SESSION["user_id"]

        students = query("""
            SELECT student_id, full_name
            FROM students
            WHERE supervisor_id=%s
        """, (sid,)) or []

        # ================= FORM =================
        cf = card_frame(self, padx=16, pady=14)
        cf.pack(fill="x", padx=20, pady=(12, 0))

        tk.Label(
            cf,
            text="Schedule / Update Meeting",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # ================= STUDENTS =================
        self._stu_map = {
            "All Students": "all"
        }

        for s in students:
            self._stu_map[s["full_name"]] = s["student_id"]

        self.stu_var = tk.StringVar()

        tk.Label(
            cf,
            text="Student",
            bg=BG_WHITE,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w")

        self.student_cb = ttk.Combobox(
            cf,
            textvariable=self.stu_var,
            values=list(self._stu_map.keys()),
            state="readonly",
            width=40
        )

        self.student_cb.pack(anchor="w", pady=(4, 10))

        self._fvars = {}

        row_f = tk.Frame(cf, bg=BG_WHITE)
        row_f.pack(fill="x")

        for lbl_t, key in [
            ("Title", "title"),
            ("Date (YYYY-MM-DD)", "date"),
            ("Time (HH:MM)", "time"),
            ("Location", "loc")
        ]:

            col = tk.Frame(row_f, bg=BG_WHITE)
            col.pack(side="left", padx=(0, 10), expand=True, fill="x")

            tk.Label(
                col,
                text=lbl_t,
                bg=BG_WHITE,
                fg=MUTED,
                font=("Segoe UI", 9)
            ).pack(anchor="w")

            v = tk.StringVar()

            e = tk.Entry(col, textvariable=v)

            style_entry(e)

            e.pack(fill="x", ipady=5, pady=(4, 0))

            self._fvars[key] = v

        # ================= BUTTONS =================
        btn_row = tk.Frame(cf, bg=BG_WHITE)
        btn_row.pack(anchor="w", pady=(10, 0))

        self.selected_meeting_id = None

        add_btn = tk.Button(
            btn_row,
            text="Schedule Meeting",
            command=self._schedule
        )

        style_btn(add_btn)
        add_btn.pack(side="left", padx=(0, 8))

        upd_btn = tk.Button(
            btn_row,
            text="Update Meeting",
            command=self._update_meeting
        )

        style_btn(upd_btn, ORANGE, WHITE)
        upd_btn.pack(side="left", padx=(0, 8))

        del_btn = tk.Button(
            btn_row,
            text="Cancel Meeting",
            command=self._delete_meeting
        )

        style_btn(del_btn, DANGER, WHITE)
        del_btn.pack(side="left")

        approve_btn = tk.Button(
            btn_row,
            text="Approve Meeting",
            command=self._approve_meeting
        )

        style_btn(approve_btn, GREEN, WHITE)
        approve_btn.pack(side="left", padx=(8, 0))

        clear_btn = tk.Button(
            btn_row,
            text="Clear Past Meetings",
            command=self._clear_old_meetings
        )

        style_btn(clear_btn, DARK, WHITE)
        clear_btn.pack(side="left", padx=(8, 0))

        # ================= TABLE =================
        lf = card_frame(self, padx=0, pady=0)
        lf.pack(fill="both", expand=True, padx=20, pady=12)

        tk.Label(
            lf,
            text="All Meetings",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=14, pady=(10, 6))

        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x")

        tree_frame = tk.Frame(lf, bg=BG_WHITE)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        cols = (
            "Student",
            "Title",
            "Date",
            "Time",
            "Status",
            "Location"
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="headings",
            height=10
        )

        style_treeview(
            self.tree,
            cols,
            [140, 180, 100, 80, 120, 140]
        )

        vsb = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._fill_form
        )

        # ================= REQUEST BUTTON =================
        af = tk.Frame(lf, bg=BG_WHITE, pady=8)
        af.pack(fill="x", padx=8)

        confirm_btn = tk.Button(
            af,
            text="Confirm / Cancel Request",
            command=self._update_status
        )

        style_btn(confirm_btn, GREEN, WHITE)
        confirm_btn.pack(side="left", padx=4)

        self._load(sid)

    # ======================================================
    def _validate_meeting_inputs(self):

        import re
        from datetime import datetime

        title = self._fvars["title"].get().strip()
        date = self._fvars["date"].get().strip()
        time = self._fvars["time"].get().strip()
        loc = self._fvars["loc"].get().strip()

        if not title or not date or not time or not loc:

            messagebox.showwarning(
                "Missing",
                "Title, date, time and location are required."
            )

            return False

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):

            messagebox.showwarning(
                "Invalid Date",
                "Enter date again in YYYY-MM-DD format."
            )

            return False

        try:

            meeting_date = datetime.strptime(
                date,
                "%Y-%m-%d"
            )

        except:

            messagebox.showwarning(
                "Invalid Date",
                "Enter date again in YYYY-MM-DD format."
            )

            return False

        if meeting_date.year < 2026:

            messagebox.showwarning(
                "Invalid Date",
                "Enter date again starting from year 2026."
            )

            return False

        if not re.match(r"^\d{2}:\d{2}$", time):

            messagebox.showwarning(
                "Invalid Time",
                "Enter time again in HH:MM format."
            )

            return False

        try:

            datetime.strptime(
                time,
                "%H:%M"
            )

        except:

            messagebox.showwarning(
                "Invalid Time",
                "Enter time again in HH:MM format."
            )

            return False

        return True

    # ======================================================
    def _load(self, sid):

        for r in self.tree.get_children():
            self.tree.delete(r)

        self.meet_map.clear()

        rows = query("""
            SELECT
                m.meeting_id,
                st.student_id,
                st.full_name,
                m.title,
                m.meeting_date,
                m.meeting_time,
                m.status,
                m.location
            FROM meetings m
            JOIN students st
                ON m.student_id = st.student_id
            WHERE m.supervisor_id=%s
            ORDER BY m.meeting_date DESC
        """, (sid,)) or []

        for r in rows:

            iid = self.tree.insert(
                "",
                "end",
                values=(
                    r["full_name"],
                    r["title"],
                    str(r["meeting_date"])[:10],
                    str(r["meeting_time"])[:5],
                    r["status"],
                    r["location"] or "—"
                )
            )

            self.meet_map[iid] = {
                "meeting_id": r["meeting_id"],
                "student_id": r["student_id"],
                "status": r["status"]
            }

    # ======================================================
    def _fill_form(self, event=None):

        sel = self.tree.selection()

        if not sel:
            return

        iid = sel[0]

        values = self.tree.item(iid, "values")

        self.selected_meeting_id = self.meet_map[iid]["meeting_id"]

        self.stu_var.set(values[0])

        self._fvars["title"].set(values[1])
        self._fvars["date"].set(values[2])
        self._fvars["time"].set(values[3])
        self._fvars["loc"].set(values[5])

    # ======================================================
    def _schedule(self):

        sid = SESSION["user_id"]

        sname = self.stu_var.get()

        if not sname:
            messagebox.showwarning(
                "Missing",
                "Please select a student."
            )
            return

        if not self._validate_meeting_inputs():
            return

        title = self._fvars["title"].get().strip()
        date = self._fvars["date"].get().strip()
        time = self._fvars["time"].get().strip()
        loc = self._fvars["loc"].get().strip()

        # ================= ALL STUDENTS =================
        if self._stu_map[sname] == "all":

            students = query("""
                SELECT student_id
                FROM students
                WHERE supervisor_id=%s
            """, (sid,)) or []

            for st in students:

                query("""
                    INSERT INTO meetings
                    (
                        supervisor_id,
                        student_id,
                        title,
                        meeting_date,
                        meeting_time,
                        location,
                        requested_by,
                        status
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,'supervisor','Scheduled')
                """, (
                    sid,
                    st["student_id"],
                    title,
                    date,
                    time,
                    loc
                ))

                create_notification(
                    "student",
                    st["student_id"],
                    "meeting",
                    "Meeting Scheduled",
                    f"{SESSION['name']} scheduled a meeting on {date} at {time}.\nTOPIC: {title}"
                )

            messagebox.showinfo(
                "Success",
                "Meeting scheduled for all students."
            )

        # ================= ONE STUDENT =================
        else:

            st_id = self._stu_map[sname]

            query("""
                INSERT INTO meetings
                (
                    supervisor_id,
                    student_id,
                    title,
                    meeting_date,
                    meeting_time,
                    location,
                    requested_by,
                    status
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,'supervisor','Scheduled')
            """, (
                sid,
                st_id,
                title,
                date,
                time,
                loc
            ))

            create_notification(
                "student",
                st_id,
                "meeting",
                "Meeting Scheduled",
                f"{SESSION['name']} scheduled a meeting on {date} at {time}.\nTOPIC: {title}"
            )

            messagebox.showinfo(
                "Success",
                "Meeting scheduled successfully."
            )

        self._clear_form()
        self._load(sid)

    # ======================================================
    def _update_meeting(self):

        if not self.selected_meeting_id:
            messagebox.showwarning(
                "Select",
                "Please select a meeting."
            )
            return

        if not self._validate_meeting_inputs():
            return

        sel = self.tree.selection()

        if not sel:
            return

        iid = sel[0]

        st_id = self.meet_map[iid]["student_id"]

        title = self._fvars["title"].get().strip()
        date = self._fvars["date"].get().strip()
        time = self._fvars["time"].get().strip()
        loc = self._fvars["loc"].get().strip()

        query("""
            UPDATE meetings
            SET title=%s,
                meeting_date=%s,
                meeting_time=%s,
                location=%s
            WHERE meeting_id=%s
        """, (
            title,
            date,
            time,
            loc,
            self.selected_meeting_id
        ))

        create_notification(
            "student",
            st_id,
            "meeting",
            "Meeting Updated",
            f"{SESSION['name']} updated your meeting.\nTOPIC: {title}"
        )

        messagebox.showinfo(
            "Updated",
            "Meeting updated successfully."
        )

        self._clear_form()
        self._load(SESSION["user_id"])

    # ======================================================
    def _delete_meeting(self):

        sel = self.tree.selection()

        if not sel:
            messagebox.showwarning(
                "Select",
                "Please select a meeting."
            )
            return

        confirm = messagebox.askyesno(
            "Delete Meeting",
            "Are you sure you want to cancel this meeting?"
        )

        if not confirm:
            return

        iid = sel[0]

        mid = self.meet_map[iid]["meeting_id"]
        st_id = self.meet_map[iid]["student_id"]

        title = self.tree.item(iid, "values")[1]

        query(
            "DELETE FROM meetings WHERE meeting_id=%s",
            (mid,)
        )

        create_notification(
            "student",
            st_id,
            "meeting",
            "Meeting Deleted",
            f"{SESSION['name']} cancelled your meeting.\nTOPIC: {title}"
        )

        messagebox.showinfo(
            "Deleted",
            "Meeting cancelled successfully."
        )

        self._clear_form()
        self._load(SESSION["user_id"])

    # ======================================================
    def _update_status(self):

        sel = self.tree.selection()

        if not sel:
            messagebox.showwarning(
                "Select",
                "Please select a meeting."
            )
            return

        iid = sel[0]

        meeting = self.meet_map[iid]

        title = self.tree.item(iid, "values")[1]

        if meeting["status"] != "Requested":

            messagebox.showwarning(
                "Invalid",
                "Only requested meetings can be confirmed."
            )

            return

        confirm = messagebox.askyesno(
            "Confirm Meeting",
            "Do you want to confirm this meeting request?"
        )

        # ================= YES =================
        if confirm:

            new_status = "Scheduled"

            notif_title = "Meeting Accepted"

            notif_msg = (
                f"{SESSION['name']} accepted your meeting request.\nTOPIC: {title}"
            )

        # ================= NO =================
        else:

            new_status = "Cancelled"

            notif_title = "Meeting Cancelled"

            notif_msg = (
                f"{SESSION['name']} cancelled your meeting request.\nTOPIC: {title}"
            )

        query(
            "UPDATE meetings SET status=%s WHERE meeting_id=%s",
            (
                new_status,
                meeting["meeting_id"]
            )
        )

        create_notification(
            "student",
            meeting["student_id"],
            "meeting",
            notif_title,
            notif_msg
        )

        messagebox.showinfo(
            "Updated",
            f"Meeting marked as {new_status}."
        )

        self._load(SESSION["user_id"])

    # ======================================================
    def _approve_meeting(self):

        sel = self.tree.selection()

        if not sel:
            messagebox.showwarning(
                "Select",
                "Please select a meeting."
            )
            return

        iid = sel[0]

        meeting = self.meet_map[iid]

        title = self.tree.item(iid, "values")[1]

        if meeting["status"] != "Requested":

            messagebox.showwarning(
                "Invalid",
                "Only requested meetings can be approved."
            )
            return

        query("""
            UPDATE meetings
            SET status=%s
            WHERE meeting_id=%s
        """, (
            "Scheduled",
            meeting["meeting_id"]
        ))

        create_notification(
            "student",
            meeting["student_id"],
            "meeting",
            "Meeting Approved",
            f"{SESSION['name']} approved your meeting request.\nTOPIC: {title}"
        )

        messagebox.showinfo(
            "Success",
            "You successfully approved the meeting."
        )

        self._load(SESSION["user_id"])

    # ======================================================
    def _clear_old_meetings(self):

        from datetime import date

        sid = SESSION["user_id"]

        confirm = messagebox.askyesno(
            "Clear Meetings",
            "Delete all meetings from yesterday and older?"
        )

        if not confirm:
            return

        query("""
            DELETE FROM meetings
            WHERE supervisor_id=%s
            AND meeting_date < %s
        """, (
            sid,
            date.today()
        ))

        messagebox.showinfo(
            "Success",
            "Past meetings cleared successfully."
        )

        self._load(sid)

    # ======================================================
    def _clear_form(self):

        self.selected_meeting_id = None

        self.stu_var.set("")

        for v in self._fvars.values():
            v.set("")
# ═══════════════════════════════════════════════════════════
# class SupervisorMessages(tk.Frame):
#     def __init__(self, parent):
#         super().__init__(parent, bg=BG_MAIN)
#         page_header(self, "Messages", "Chat with your students")
#         self._build()

#     # ── helper: create a coloured button with hover effect ──────────────
#     @staticmethod
#     def _make_btn(parent, text, command, bg, hover_bg, fg=WHITE):
#         b = tk.Button(parent, text=text, command=command,
#                       bg=bg, fg=fg, relief="flat",
#                       font=("Segoe UI", 10, "bold"),
#                       padx=14, pady=6, cursor="hand2",
#                       activebackground=hover_bg, activeforeground=fg,
#                       bd=0)
#         b.bind("<Enter>", lambda _: b.config(bg=hover_bg))
#         b.bind("<Leave>", lambda _: b.config(bg=bg))
#         return b

#     def _build(self):
#         sid      = SESSION["user_id"]
#         students = query("SELECT student_id, full_name FROM students WHERE supervisor_id=%s",
#                          (sid,)) or []
#         if not students:
#             tk.Label(self, text="No students assigned yet.",
#                      bg=BG_MAIN, fg=MUTED, font=("Segoe UI", 12)).pack(pady=40)
#             return

#         # ── top bar ──────────────────────────────────────────────────────
#         top = tk.Frame(self, bg=BG_MAIN)
#         top.pack(fill="x", padx=20, pady=(8, 4))
#         tk.Label(top, text="Select student:", bg=BG_MAIN, fg=DARK,
#                  font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))

#         self._stu_map = {s["full_name"]: s["student_id"] for s in students}
#         self.stu_var  = tk.StringVar(value=students[0]["full_name"])
#         cb = ttk.Combobox(top, textvariable=self.stu_var,
#                           values=list(self._stu_map.keys()),
#                           state="readonly", width=30)
#         cb.pack(side="left")

#         # Violet "Load Chat" button – eye-catching, different from blue sidebar
#         load_btn = self._make_btn(top, "💬  Load Chat", self._load_chat,
#                                   bg="#7C3AED", hover_bg="#6D28D9")
#         load_btn.pack(side="left", padx=8)

#         self.chat_area = tk.Frame(self, bg=BG_MAIN)
#         self.chat_area.pack(fill="both", expand=True, padx=20)

#         # Auto-load whenever selection changes + on first open
#         cb.bind("<<ComboboxSelected>>", lambda _: self._load_chat())
#         self._load_chat()

#     def _load_chat(self):
#         for w in self.chat_area.winfo_children():
#             w.destroy()
#         sname  = self.stu_var.get()
#         st_id  = self._stu_map.get(sname)
#         sup_id = SESSION["user_id"]
#         if not st_id:
#             return

#         mf = card_frame(self.chat_area, padx=0, pady=0)
#         mf.pack(fill="both", expand=True)
#         self.canvas = tk.Canvas(mf, bg=BG_WHITE, highlightthickness=0)
#         sb = ttk.Scrollbar(mf, orient="vertical", command=self.canvas.yview)
#         self.msg_frame = tk.Frame(self.canvas, bg=BG_WHITE)
#         self.msg_frame.bind("<Configure>",
#             lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
#         self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")
#         self.canvas.configure(yscrollcommand=sb.set)
#         self.canvas.pack(side="left", fill="both", expand=True)
#         sb.pack(side="right", fill="y")
#         self._refresh_msgs(sup_id, st_id)

#         # ── input bar ────────────────────────────────────────────────────
#         inp = tk.Frame(self.chat_area, bg="#F1F5F9", pady=8)
#         inp.pack(fill="x")

#         # 📎 Attach – sky blue
#         att = self._make_btn(inp, "📎", lambda: self._attach_send(sup_id, st_id),
#                              bg=_BTN_ATTACH, hover_bg="#0284C7")
#         att.pack(side="left", padx=(0, 6))

#         # Text entry
#         self.msg_var = tk.StringVar()
#         me = tk.Entry(inp, textvariable=self.msg_var,
#                       font=("Segoe UI", 10), relief="flat",
#                       bg=WHITE, fg=DARK,
#                       highlightthickness=1, highlightcolor="#2563EB",
#                       highlightbackground="#CBD5E1")
#         me.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
#         me.bind("<Return>", lambda e: self._send(sup_id, st_id))

#         # ➤ Send – vivid blue
#         send_btn = self._make_btn(inp, "➤  Send",
#                                   lambda: self._send(sup_id, st_id),
#                                   bg=_BTN_SEND, hover_bg=_BTN_SEND_HVR)
#         send_btn.pack(side="right")

#     def _refresh_msgs(self, sup_id, st_id):
#         for w in self.msg_frame.winfo_children():
#             w.destroy()
#         rows = query("""SELECT * FROM messages
#                         WHERE (sender_role='supervisor' AND sender_id=%s AND receiver_id=%s)
#                            OR (sender_role='student'    AND sender_id=%s AND receiver_id=%s)
#                         ORDER BY sent_at ASC""",
#                      (sup_id, st_id, st_id, sup_id)) or []
#         for r in rows:
#             is_me = r["sender_role"] == "supervisor"
#             bg    = _BTN_SEND if is_me else "#E2E8F0"
#             fg    = WHITE     if is_me else DARK
#             side  = "right"   if is_me else "left"
#             bf = tk.Frame(self.msg_frame, bg=BG_WHITE)
#             bf.pack(fill="x", padx=10, pady=3, anchor="e" if is_me else "w")
#             tk.Label(bf, text=r["body"], bg=bg, fg=fg,
#                      font=("Segoe UI", 10), wraplength=360,
#                      padx=10, pady=6, justify="left").pack(side=side)
#             if r.get("attachment_path"):
#                 full  = os.path.join(UPLOAD_FOLDER, r["attachment_path"])
#                 aname = r.get("attachment_name", "Attachment")
#                 tk.Button(bf, text=f"📄 {aname}",
#                           command=lambda p=full: open_file(p),
#                           bg="#DBEAFE", fg=_BTN_SEND, relief="flat",
#                           font=("Segoe UI", 9), cursor="hand2",
#                           padx=6, pady=3).pack(side=side, pady=2)
#             tk.Label(bf, text=str(r["sent_at"])[:16],
#                      bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 8)).pack(side=side, padx=4)
#         self.after(100, lambda: self.canvas.yview_moveto(1.0))

#     def _send(self, sup_id, st_id):
#         body = self.msg_var.get().strip()
#         if not body:
#             return
#         query("""INSERT INTO messages
#                  (sender_role, sender_id, receiver_role, receiver_id, body)
#                  VALUES ('supervisor',%s,'student',%s,%s)""",
#               (sup_id, st_id, body))
#         create_notification("student", st_id, "message",
#                             "New Message", f"{SESSION['name']}: {body[:60]}")
#         self.msg_var.set("")
#         self._refresh_msgs(sup_id, st_id)

#     def _attach_send(self, sup_id, st_id):
#         path = filedialog.askopenfilename(
#             filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
#         if not path:
#             return
#         ext  = path.rsplit(".", 1)[-1].lower()
#         safe = f"msg_{sup_id}_{uuid.uuid4().hex[:8]}.{ext}"
#         dest = os.path.join(UPLOAD_FOLDER, safe)
#         shutil.copy2(path, dest)
#         fname = os.path.basename(path)
#         query("""INSERT INTO messages
#                  (sender_role, sender_id, receiver_role, receiver_id,
#                   body, attachment_path, attachment_name)
#                  VALUES ('supervisor',%s,'student',%s,%s,%s,%s)""",
#               (sup_id, st_id, f"[Attachment: {fname}]", safe, fname))
#         create_notification("student", st_id, "message",
#                             "New Attachment", f"{SESSION['name']} sent a file: {fname}")
#         self._refresh_msgs(sup_id, st_id)


# ═══════════════════════════════════════════════════════════
class SupervisorNotifications(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)

        page_header(self, "Notifications", "Your alerts and updates")

        self.filter_type = "all"   # all | meeting | submission
        self._build()

    # ======================================================
    def _build(self):

        sid = SESSION["user_id"]

        # ---------------- TOP ACTION BAR ----------------
        top_bar = tk.Frame(self, bg=BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=(5, 10))

        def set_filter(f):
            self.filter_type = f
            self.refresh()

        tk.Button(top_bar, text="All", command=lambda: set_filter("all")).pack(side="left", padx=5)
        tk.Button(top_bar, text="Meetings", command=lambda: set_filter("meeting")).pack(side="left", padx=5)
        tk.Button(top_bar, text="Submissions", command=lambda: set_filter("submission")).pack(side="left", padx=5)

        tk.Button(
            top_bar,
            text="Clear All",
            bg="#ff4d4d",
            fg="white",
            command=self.clear_all
        ).pack(side="right", padx=5)

        # ---------------- NOTIFICATIONS LOAD ----------------
        self.sf = ScrollFrame(self, bg=BG_MAIN)
        self.sf.pack(fill="both", expand=True, padx=20, pady=12)

        self.refresh()

    # ======================================================
    def refresh(self):

        sid = SESSION["user_id"]

        # base query
        sql = """
            SELECT * FROM notifications
            WHERE user_role='supervisor' AND user_id=%s
        """

        params = [sid]

        if self.filter_type in ("meeting", "submission"):
            sql += " AND type=%s"
            params.append(self.filter_type)

        sql += " ORDER BY delivered_at DESC"

        rows = query(sql, tuple(params)) or []

        # mark as read
        query("""
            UPDATE notifications
            SET is_read=1
            WHERE user_role='supervisor' AND user_id=%s
        """, (sid,))

        # clear frame
        for w in self.sf.inner.winfo_children():
            w.destroy()

        if not rows:
            tk.Label(
                self.sf.inner,
                text="No notifications yet.",
                bg=BG_MAIN,
                fg=MUTED,
                font=("Segoe UI", 11)
            ).pack(pady=20)
            return

        TYPE_ICONS = {
            "meeting": "📅",
            "message": "✉",
            "submission": "📄",
            "deadline": "⏰",
            "milestone": "🎯"
        }

        for r in rows:
            nf = card_frame(self.sf.inner, padx=14, pady=10)
            nf.pack(fill="x", pady=3)

            top = tk.Frame(nf, bg=BG_WHITE)
            top.pack(fill="x")

            icon = TYPE_ICONS.get(r["type"], "🔔")

            tk.Label(
                top,
                text=f"{icon}  {r['title']}",
                bg=BG_WHITE,
                fg=DARK,
                font=("Segoe UI", 11, "bold")
            ).pack(side="left")

            tk.Label(
                top,
                text=str(r["delivered_at"])[:16],
                bg=BG_WHITE,
                fg=MUTED,
                font=("Segoe UI", 9)
            ).pack(side="right")

            tk.Label(
                nf,
                text=r["message"],
                bg=BG_WHITE,
                fg=TEXT2,
                font=("Segoe UI", 10)
            ).pack(anchor="w", pady=(4, 0))

    # ======================================================
    def clear_all(self):

        sid = SESSION["user_id"]

        query("""
            DELETE FROM notifications
            WHERE user_role='supervisor' AND user_id=%s
        """, (sid,))

        self.refresh()


# ═══════════════════════════════════════════════════════════
class SupervisorProfile(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "My Profile", "View and update your profile")
        self._build()

    def _build(self):
        sid = SESSION["user_id"]
        row = query("SELECT * FROM supervisors WHERE supervisor_id=%s", (sid,), one=True)

        # ── Wrap everything in a ScrollFrame so nothing gets clipped ──
        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True, padx=20, pady=12)

        pf = card_frame(sf.inner, padx=20, pady=18)
        pf.pack(fill="x")

        self.pvars = {}

        # ── Profile fields ────────────────────────────────────────────
        for lbl_t, key, ro in [
            ("Full Name",  "full_name",  False),
            ("Email",      "email",      True),
            ("Department", "department", False),
        ]:
            tk.Label(pf, text=lbl_t, bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            v = tk.StringVar(value=row.get(key) or "")
            e = tk.Entry(pf, textvariable=v,
                         state="readonly" if ro else "normal", width=50)
            style_entry(e)
            e.pack(fill="x", ipady=6, pady=(4, 12))
            self.pvars[key] = v

        # ── Divider ───────────────────────────────────────────────────
        tk.Frame(pf, bg=BORDER, height=1).pack(fill="x", pady=8)

        # ── Change Password section ───────────────────────────────────
        tk.Label(pf, text="Change Password", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

        for lbl_t, key in [
            ("Current Password", "old_pw"),
            ("New Password",     "new_pw"),
        ]:
            tk.Label(pf, text=lbl_t, bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            v = tk.StringVar()
            e = tk.Entry(pf, textvariable=v, show="•", width=50)
            style_entry(e)
            e.pack(fill="x", ipady=6, pady=(4, 12))
            self.pvars[key] = v

        # ── Save button ───────────────────────────────────────────────
        sb = tk.Button(pf, text="Save Changes", command=self._save)
        style_btn(sb, "#2e8b57", WHITE)
        sb.pack(anchor="w", pady=(4, 0))

    def _save(self):
        sid  = SESSION["user_id"]
        name = self.pvars["full_name"].get().strip()
        dept = self.pvars["department"].get().strip()

        if name:
            query("UPDATE supervisors SET full_name=%s WHERE supervisor_id=%s", (name, sid))
            SESSION["name"] = name
        if dept:
            query("UPDATE supervisors SET department=%s WHERE supervisor_id=%s", (dept, sid))

        new_pw = self.pvars["new_pw"].get()
        old_pw = self.pvars["old_pw"].get()

        if new_pw:
            if not old_pw:
                messagebox.showerror("Error", "Please enter your current password.")
                return
            row = query("SELECT password_hash FROM supervisors WHERE supervisor_id=%s",
                        (sid,), one=True)
            if not check_password(old_pw, row["password_hash"]):
                messagebox.showerror("Error", "Current password is incorrect.")
                return
            if len(new_pw) < 6:
                messagebox.showerror("Error", "New password must be at least 6 characters.")
                return
            query("UPDATE supervisors SET password_hash=%s WHERE supervisor_id=%s",
                  (hash_password(new_pw), sid))

        messagebox.showinfo("Saved", "Profile updated successfully!")