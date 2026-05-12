"""
pages/supervisor.py
All supervisor pages with Epoka style + chat notifications + file opening.
CEN 302 Software Engineering | Group III | Epoka University
"""

import os, shutil, uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from database import query
from auth import SESSION, hash_password, check_password
from ui import (BG_MAIN, BG_WHITE, BLUE, BLUE2, GREEN, GOLD_TILE, ORANGE,
                WHITE, MUTED, DARK, BORDER, SUCCESS, DANGER, WARNING, INFO,
                TEXT, TEXT2, label, style_btn, style_entry, card_frame,
                stat_card, page_header, style_treeview, ScrollFrame,
                FeedbackDialog, open_file)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")


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
        self.sub_map  = {}
        self.file_map = {}
        self._build()

    def _build(self):
        sid = SESSION["user_id"]
        f   = card_frame(self, padx=0, pady=0)
        f.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(f, text="Student Submissions", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x")

        cols = ("Student", "Version", "File", "Type", "Size (KB)", "Submitted", "Status")
        self.tree = ttk.Treeview(f, columns=cols, show="headings", height=12)
        style_treeview(self.tree, cols, [140, 60, 200, 60, 70, 130, 80])
        self.tree.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        bf = tk.Frame(f, bg=BG_WHITE, pady=8)
        bf.pack(fill="x", padx=8, pady=(0, 8))
        ab = tk.Button(bf, text="✓ Approve", command=lambda: self._review("Approved"))
        style_btn(ab, GREEN, WHITE)
        ab.pack(side="left", padx=(0, 6))
        rb = tk.Button(bf, text="✗ Reject", command=lambda: self._review("Rejected"))
        style_btn(rb, DANGER, WHITE)
        rb.pack(side="left", padx=(0, 6))
        ob = tk.Button(bf, text="📄 Open File", command=self._open_selected)
        style_btn(ob, BLUE, WHITE)
        ob.pack(side="left")
        self._load(sid)

    def _load(self, sid):
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.sub_map.clear()
        self.file_map.clear()
        rows = query("""SELECT s.submission_id, st.full_name, s.version_number,
                               s.file_name, s.file_type, s.file_size_kb,
                               s.submitted_at, s.status, s.file_path
                        FROM submissions s
                        JOIN students st ON s.student_id=st.student_id
                        WHERE st.supervisor_id=%s ORDER BY s.submitted_at DESC""", (sid,)) or []
        for r in rows:
            iid = self.tree.insert("", "end", values=(
                r["full_name"], f"v{r['version_number']}",
                r["file_name"], r["file_type"], r["file_size_kb"],
                str(r["submitted_at"])[:16], r["status"]))
            self.sub_map[iid]  = r["submission_id"]
            self.file_map[iid] = r["file_path"]

    def _open_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a submission first.")
            return
        fp = self.file_map.get(sel[0])
        if not fp:
            messagebox.showerror("Error", "File path not found.")
            return
        full = os.path.join(UPLOAD_FOLDER, fp)
        if not os.path.exists(full):
            messagebox.showerror("Not Found", f"File not found on disk:\n{full}")
            return
        open_file(full)

    def _review(self, status):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a submission first.")
            return
        sub_id  = self.sub_map.get(sel[0])
        comment = ""
        if status == "Rejected":
            dlg = FeedbackDialog(self.master, "Rejection Feedback")
            self.wait_window(dlg)
            comment = dlg.result or ""
        query("UPDATE submissions SET status=%s WHERE submission_id=%s", (status, sub_id))
        if comment:
            query("""INSERT INTO feedback (submission_id, supervisor_id, comment)
                     VALUES (%s,%s,%s)""", (sub_id, SESSION["user_id"], comment))
        # Notify student
        sub_row = query("SELECT student_id, file_name FROM submissions WHERE submission_id=%s",
                        (sub_id,), one=True)
        if sub_row:
            create_notification("student", sub_row["student_id"], "submission",
                                f"Submission {status}",
                                f"Your file '{sub_row['file_name']}' was {status.lower()}.")
        messagebox.showinfo("Done", f"Submission {status.lower()}.")
        self._load(SESSION["user_id"])


# ═══════════════════════════════════════════════════════════
class SupervisorMeetings(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Meetings", "Schedule and manage meetings")
        self.meet_map = {}
        self._build()

    def _build(self):
        sid      = SESSION["user_id"]
        students = query("SELECT student_id, full_name FROM students WHERE supervisor_id=%s", (sid,)) or []
        cf = card_frame(self, padx=16, pady=14)
        cf.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(cf, text="Schedule Meeting", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
        self._stu_map = {s["full_name"]: s["student_id"] for s in students}
        self.stu_var  = tk.StringVar()
        tk.Label(cf, text="Student", bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Combobox(cf, textvariable=self.stu_var,
                     values=list(self._stu_map.keys()),
                     state="readonly", width=40).pack(anchor="w", pady=(4, 10))
        self._fvars = {}
        row_f = tk.Frame(cf, bg=BG_WHITE)
        row_f.pack(fill="x")
        for lbl_t, key in [("Title", "title"), ("Date (YYYY-MM-DD)", "date"), ("Time (HH:MM)", "time"), ("Location", "loc")]:
            col = tk.Frame(row_f, bg=BG_WHITE)
            col.pack(side="left", padx=(0, 10), expand=True, fill="x")
            tk.Label(col, text=lbl_t, bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
            v = tk.StringVar()
            e = tk.Entry(col, textvariable=v)
            style_entry(e)
            e.pack(fill="x", ipady=5, pady=(4, 0))
            self._fvars[key] = v
        tb = tk.Button(cf, text="Schedule Meeting", command=self._schedule)
        style_btn(tb)
        tb.pack(anchor="w", pady=(10, 0))

        lf = card_frame(self, padx=0, pady=0)
        lf.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(lf, text="All Meetings", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x")

        # Scrollable meetings treeview
        tree_frame = tk.Frame(lf, bg=BG_WHITE)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        cols = ("Student", "Title", "Date", "Time", "Status", "Location")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=7)
        style_treeview(self.tree, cols, [130, 150, 90, 70, 90, 130])
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        af = tk.Frame(lf, bg=BG_WHITE, pady=6)
        af.pack(fill="x", padx=8, pady=(0, 8))
        for txt, st, col in [("✓ Confirm", "Confirmed", GREEN),
                              ("✗ Decline", "Declined",  DANGER),
                              ("Cancel",    "Cancelled", WARNING)]:
            b = tk.Button(af, text=txt, command=lambda s=st: self._update_status(s))
            style_btn(b, col, WHITE)
            b.pack(side="left", padx=4)
        self._load(sid)

    def _load(self, sid):
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.meet_map.clear()
        rows = query("""SELECT m.meeting_id, st.full_name, m.title,
                               m.meeting_date, m.meeting_time, m.status, m.location,
                               m.student_id
                        FROM meetings m
                        JOIN students st ON m.student_id=st.student_id
                        WHERE m.supervisor_id=%s ORDER BY m.meeting_date DESC""", (sid,)) or []
        for r in rows:
            iid = self.tree.insert("", "end", values=(
                r["full_name"], r["title"],
                str(r["meeting_date"])[:10], str(r["meeting_time"])[:5],
                r["status"], r["location"] or "—"))
            self.meet_map[iid] = (r["meeting_id"], r["student_id"])

    def _schedule(self):
        sid   = SESSION["user_id"]
        sname = self.stu_var.get()
        if not sname:
            messagebox.showwarning("Missing", "Please select a student.")
            return
        st_id = self._stu_map[sname]
        title = self._fvars["title"].get().strip()
        date  = self._fvars["date"].get().strip()
        time  = self._fvars["time"].get().strip()
        loc   = self._fvars["loc"].get().strip()
        if not title or not date or not time:
            messagebox.showwarning("Missing", "Title, date and time are required.")
            return
        query("""INSERT INTO meetings
                 (supervisor_id, student_id, title, meeting_date, meeting_time,
                  location, requested_by, status)
                 VALUES (%s,%s,%s,%s,%s,%s,'supervisor','Scheduled')""",
              (sid, st_id, title, date, time, loc))
        create_notification("student", st_id, "meeting",
                            "Meeting Scheduled",
                            f"{SESSION['name']} scheduled a meeting on {date} at {time}")
        messagebox.showinfo("Scheduled", "Meeting scheduled!")
        for v in self._fvars.values():
            v.set("")
        self._load(sid)

    def _update_status(self, status):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a meeting.")
            return
        mid, st_id = self.meet_map.get(sel[0], (None, None))
        if not mid:
            return
        query("UPDATE meetings SET status=%s WHERE meeting_id=%s", (status, mid))
        # Notify student
        create_notification("student", st_id, "meeting",
                            f"Meeting {status}",
                            f"Your meeting was {status.lower()} by {SESSION['name']}")
        self._load(SESSION["user_id"])


# ═══════════════════════════════════════════════════════════
class SupervisorMessages(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Messages", "Chat with your students")
        self._build()

    def _build(self):
        sid      = SESSION["user_id"]
        students = query("SELECT student_id, full_name FROM students WHERE supervisor_id=%s",
                         (sid,)) or []
        if not students:
            tk.Label(self, text="No students assigned yet.",
                     bg=BG_MAIN, fg=MUTED, font=("Segoe UI", 12)).pack(pady=40)
            return

        top = tk.Frame(self, bg=BG_MAIN)
        top.pack(fill="x", padx=20, pady=(8, 4))
        tk.Label(top, text="Select student:", bg=BG_MAIN, fg=DARK,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
        self._stu_map = {s["full_name"]: s["student_id"] for s in students}
        self.stu_var  = tk.StringVar(value=students[0]["full_name"])
        cb = ttk.Combobox(top, textvariable=self.stu_var,
                          values=list(self._stu_map.keys()),
                          state="readonly", width=30)
        cb.pack(side="left")
        tk.Button(top, text="Load Chat", command=self._load_chat,
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10), padx=10).pack(side="left", padx=8)

        self.chat_area = tk.Frame(self, bg=BG_MAIN)
        self.chat_area.pack(fill="both", expand=True, padx=20)
        self._load_chat()

    def _load_chat(self):
        for w in self.chat_area.winfo_children():
            w.destroy()
        sname  = self.stu_var.get()
        st_id  = self._stu_map.get(sname)
        sup_id = SESSION["user_id"]
        if not st_id:
            return

        mf = card_frame(self.chat_area, padx=0, pady=0)
        mf.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(mf, bg=BG_WHITE, highlightthickness=0)
        sb = ttk.Scrollbar(mf, orient="vertical", command=self.canvas.yview)
        self.msg_frame = tk.Frame(self.canvas, bg=BG_WHITE)
        self.msg_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._refresh_msgs(sup_id, st_id)

        inp = tk.Frame(self.chat_area, bg=BG_MAIN, pady=8)
        inp.pack(fill="x")
        att = tk.Button(inp, text="📎",
                        command=lambda: self._attach_send(sup_id, st_id),
                        bg="#ecf0f1", fg=DARK, relief="flat",
                        font=("Segoe UI", 12), padx=8)
        att.pack(side="left", padx=(0, 6))
        self.msg_var = tk.StringVar()
        me = tk.Entry(inp, textvariable=self.msg_var)
        style_entry(me)
        me.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))
        me.bind("<Return>", lambda e: self._send(sup_id, st_id))
        tk.Button(inp, text="Send",
                  command=lambda: self._send(sup_id, st_id),
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=12, pady=6).pack(side="right")

    def _refresh_msgs(self, sup_id, st_id):
        for w in self.msg_frame.winfo_children():
            w.destroy()
        rows = query("""SELECT * FROM messages
                        WHERE (sender_role='supervisor' AND sender_id=%s AND receiver_id=%s)
                           OR (sender_role='student'    AND sender_id=%s AND receiver_id=%s)
                        ORDER BY sent_at ASC""",
                     (sup_id, st_id, st_id, sup_id)) or []
        for r in rows:
            is_me = r["sender_role"] == "supervisor"
            bg    = BLUE if is_me else "#ecf0f1"
            fg    = WHITE if is_me else DARK
            side  = "right" if is_me else "left"
            bf = tk.Frame(self.msg_frame, bg=BG_WHITE)
            bf.pack(fill="x", padx=10, pady=3, anchor="e" if is_me else "w")
            tk.Label(bf, text=r["body"], bg=bg, fg=fg,
                     font=("Segoe UI", 10), wraplength=360,
                     padx=10, pady=6, justify="left").pack(side=side)
            if r.get("attachment_path"):
                full  = os.path.join(UPLOAD_FOLDER, r["attachment_path"])
                aname = r.get("attachment_name", "Attachment")
                tk.Button(bf, text=f"📄 {aname}",
                          command=lambda p=full: open_file(p),
                          bg="#dce1e7", fg=BLUE, relief="flat",
                          font=("Segoe UI", 9), cursor="hand2",
                          padx=6, pady=3).pack(side=side, pady=2)
            tk.Label(bf, text=str(r["sent_at"])[:16],
                     bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 8)).pack(side=side, padx=4)
        self.after(100, lambda: self.canvas.yview_moveto(1.0))

    def _send(self, sup_id, st_id):
        body = self.msg_var.get().strip()
        if not body:
            return
        query("""INSERT INTO messages
                 (sender_role, sender_id, receiver_role, receiver_id, body)
                 VALUES ('supervisor',%s,'student',%s,%s)""",
              (sup_id, st_id, body))
        create_notification("student", st_id, "message",
                            "New Message", f"{SESSION['name']}: {body[:60]}")
        self.msg_var.set("")
        self._refresh_msgs(sup_id, st_id)

    def _attach_send(self, sup_id, st_id):
        path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if not path:
            return
        ext  = path.rsplit(".", 1)[-1].lower()
        safe = f"msg_{sup_id}_{uuid.uuid4().hex[:8]}.{ext}"
        dest = os.path.join(UPLOAD_FOLDER, safe)
        shutil.copy2(path, dest)
        fname = os.path.basename(path)
        query("""INSERT INTO messages
                 (sender_role, sender_id, receiver_role, receiver_id,
                  body, attachment_path, attachment_name)
                 VALUES ('supervisor',%s,'student',%s,%s,%s,%s)""",
              (sup_id, st_id, f"[Attachment: {fname}]", safe, fname))
        create_notification("student", st_id, "message",
                            "New Attachment", f"{SESSION['name']} sent a file: {fname}")
        self._refresh_msgs(sup_id, st_id)


# ═══════════════════════════════════════════════════════════
class SupervisorNotifications(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Notifications", "Your alerts and updates")
        self._build()

    def _build(self):
        sid  = SESSION["user_id"]
        rows = query("""SELECT * FROM notifications
                        WHERE user_role='supervisor' AND user_id=%s
                        ORDER BY delivered_at DESC""", (sid,)) or []
        query("UPDATE notifications SET is_read=1 WHERE user_role='supervisor' AND user_id=%s", (sid,))
        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True, padx=20, pady=12)
        if not rows:
            tk.Label(sf.inner, text="No notifications yet.",
                     bg=BG_MAIN, fg=MUTED, font=("Segoe UI", 11)).pack(pady=20)
            return
        TYPE_ICONS = {"meeting": "📅", "message": "✉", "submission": "📄",
                      "deadline": "⏰", "milestone": "🎯"}
        for r in rows:
            nf = card_frame(sf.inner, padx=14, pady=10)
            nf.pack(fill="x", pady=3)
            top = tk.Frame(nf, bg=BG_WHITE)
            top.pack(fill="x")
            icon = TYPE_ICONS.get(r["type"], "🔔")
            tk.Label(top, text=f"{icon}  {r['title']}",
                     bg=BG_WHITE, fg=DARK,
                     font=("Segoe UI", 11, "bold")).pack(side="left")
            tk.Label(top, text=str(r["delivered_at"])[:16],
                     bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(side="right")
            tk.Label(nf, text=r["message"], bg=BG_WHITE, fg=TEXT2,
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))


# ═══════════════════════════════════════════════════════════
class SupervisorProfile(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "My Profile", "View and update your profile")
        self._build()

    def _build(self):
        sid = SESSION["user_id"]
        row = query("SELECT * FROM supervisors WHERE supervisor_id=%s", (sid,), one=True)
        pf  = card_frame(self, padx=20, pady=18)
        pf.pack(fill="x", padx=20, pady=12)
        self.pvars = {}
        for lbl_t, key, ro in [("Full Name", "full_name", False),
                                ("Email",     "email",     True),
                                ("Department","department",False)]:
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
        dept = self.pvars["department"].get().strip()
        if name:
            query("UPDATE supervisors SET full_name=%s WHERE supervisor_id=%s", (name, sid))
        if dept:
            query("UPDATE supervisors SET department=%s WHERE supervisor_id=%s", (dept, sid))
        new_pw = self.pvars["new_pw"].get()
        old_pw = self.pvars["old_pw"].get()
        if new_pw:
            row = query("SELECT password_hash FROM supervisors WHERE supervisor_id=%s", (sid,), one=True)
            if not check_password(old_pw, row["password_hash"]):
                messagebox.showerror("Error", "Current password is incorrect.")
                return
            query("UPDATE supervisors SET password_hash=%s WHERE supervisor_id=%s",
                  (hash_password(new_pw), sid))
        messagebox.showinfo("Saved", "Profile updated!")