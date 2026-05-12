"""
pages/student.py
All student pages with Epoka style + meeting notifications + scrollable meetings.
CEN 302 Software Engineering | Group III | Epoka University
"""

import os, shutil, uuid, sys, subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import fitz

from pages.student_submissions import StudentSubmissions
from database import query
from auth import SESSION, hash_password, check_password
from ui import (BG_MAIN, BG_WHITE, BLUE, BLUE2, GREEN, GOLD_TILE, ORANGE,
                WHITE, MUTED, DARK, BORDER, SUCCESS, DANGER, WARNING, INFO,
                TEXT, TEXT2, label, style_btn, style_entry, card_frame,
                stat_card, page_header, style_treeview, ScrollFrame, open_file)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def create_notification(user_role, user_id, notif_type, title, message, ref_id=None):
    try:
        query("""INSERT INTO notifications (user_role, user_id, type, title, message, ref_id)
                 VALUES (%s,%s,%s,%s,%s,%s)""",
              (user_role, user_id, notif_type, title, message, ref_id))
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
class StudentDashboard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        sid = SESSION["user_id"]
        page_header(self, f"Welcome, {SESSION['name']}", "Student Dashboard")
        try:
            subs  = query("SELECT COUNT(*) AS c FROM submissions WHERE student_id=%s", (sid,), one=True)
            pend  = query("SELECT COUNT(*) AS c FROM submissions WHERE student_id=%s AND status='Pending'", (sid,), one=True)
            appr  = query("SELECT COUNT(*) AS c FROM submissions WHERE student_id=%s AND status='Approved'", (sid,), one=True)
            mdone = query("SELECT COUNT(*) AS c FROM milestones WHERE student_id=%s AND status='Completed'", (sid,), one=True)
            mtot  = query("SELECT COUNT(*) AS c FROM milestones WHERE student_id=%s", (sid,), one=True)
            dl    = query("""SELECT COUNT(*) AS c FROM deadlines d
                             JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                             WHERE da.student_id=%s AND d.due_date>=CURDATE()""", (sid,), one=True)
        except Exception as e:
            label(self, f"Database error: {e}", 11, DANGER).pack(pady=20)
            return

        # Tile grid (Epoka style)
        grid = tk.Frame(self, bg=BG_MAIN)
        grid.pack(fill="x", padx=20, pady=12)
        tiles = [
            ("📄", "Total Submissions", str(subs["c"]),   BLUE),
            ("⏳", "Pending Review",    str(pend["c"]),   GOLD_TILE),
            ("✅", "Approved",           str(appr["c"]),   GREEN),
            ("🎯", "Milestones Done",   f"{mdone['c']}/{mtot['c']}", ORANGE),
            ("📅", "Upcoming Deadlines",str(dl["c"]),     "#8e44ad"),
        ]
        for i, (icon, title, val, color) in enumerate(tiles):
            f = tk.Frame(grid, bg=color, width=150, height=100)
            f.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            f.pack_propagate(False)
            tk.Label(f, text=icon, bg=color, fg=WHITE,
                     font=("Segoe UI", 16)).pack(pady=(10, 0))
            tk.Label(f, text=val, bg=color, fg=WHITE,
                     font=("Segoe UI", 14, "bold")).pack(pady=(2, 0))
            tk.Label(f, text=title, bg=color, fg=WHITE,
                     font=("Segoe UI", 9, "bold"),
                     wraplength=120, justify="center").pack(pady=(2, 8))
            grid.columnconfigure(i, weight=1)

        # Recent submissions
        f2 = card_frame(self, padx=0, pady=0)
        f2.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(f2, text="Recent Submissions", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=14, pady=(10, 6))
        tk.Frame(f2, bg=BORDER, height=1).pack(fill="x")
        cols = ("Version", "File", "Status", "Submitted")
        tree = ttk.Treeview(f2, columns=cols, show="headings", height=5)
        style_treeview(tree, cols, [80, 260, 100, 150])
        tree.pack(fill="x", padx=8, pady=8)
        rows = query("""SELECT version_number, file_name, status, submitted_at
                        FROM submissions WHERE student_id=%s
                        ORDER BY submitted_at DESC LIMIT 5""", (sid,))
        for r in (rows or []):
            tree.insert("", "end", values=(
                f"v{r['version_number']}", r["file_name"],
                r["status"], str(r["submitted_at"])[:16]))


# ═══════════════════════════════════════════════════════════

    
# ═══════════════════════════════════════════════════════════
class StudentDeadlines(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Deadlines", "Your assigned deadlines")
        self._build()

    def _build(self):
        sid  = SESSION["user_id"]
        rows = query("""SELECT d.title, d.description, d.due_date,
                               CASE WHEN d.due_date < CURDATE() THEN 1 ELSE 0 END AS overdue,
                               sup.full_name AS supervisor_name
                        FROM deadlines d
                        JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                        JOIN supervisors sup ON d.supervisor_id=sup.supervisor_id
                        WHERE da.student_id=%s ORDER BY d.due_date ASC""", (sid,)) or []
        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True, padx=20, pady=12)
        if not rows:
            tk.Label(sf.inner, text="No deadlines assigned yet.",
                     bg=BG_MAIN, fg=MUTED, font=("Segoe UI", 11)).pack(pady=20)
            return
        for r in rows:
            df = card_frame(sf.inner, padx=14, pady=12)
            df.pack(fill="x", pady=4)
            top = tk.Frame(df, bg=BG_WHITE)
            top.pack(fill="x")
            tk.Label(top, text=r["title"], bg=BG_WHITE, fg=DARK,
                     font=("Segoe UI", 11, "bold")).pack(side="left")
            color = DANGER if r["overdue"] else SUCCESS
            tag   = " ⚠ OVERDUE" if r["overdue"] else " ✓ On Time"
            tk.Label(top, text=tag, bg=BG_WHITE, fg=color,
                     font=("Segoe UI", 9, "bold")).pack(side="left", padx=8)
            tk.Label(top, text=f"Due: {str(r['due_date'])[:10]}",
                     bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(side="right")
            if r.get("description"):
                tk.Label(df, text=r["description"], bg=BG_WHITE, fg=TEXT2,
                         font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
            tk.Label(df, text=f"Set by: {r['supervisor_name']}",
                     bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))


# ═══════════════════════════════════════════════════════════
class StudentMilestones(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "My Milestones", "Track your thesis progress")
        self._build()

    def _build(self):
        sid  = SESSION["user_id"]
        rows = query("""SELECT m.*, sup.full_name AS supervisor_name
                        FROM milestones m
                        JOIN supervisors sup ON m.supervisor_id=sup.supervisor_id
                        WHERE m.student_id=%s ORDER BY m.due_date ASC""", (sid,)) or []
        total = len(rows)
        done  = sum(1 for r in rows if r["status"] == "Completed")
        pf = card_frame(self, padx=16, pady=14)
        pf.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(pf, text=f"Overall Progress — {done}/{total} milestones completed",
                 bg=BG_WHITE, fg=DARK, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        bar_bg = tk.Frame(pf, bg=BORDER, height=12)
        bar_bg.pack(fill="x")
        pct = int((done / total * 100) if total else 0)
        if pct > 0:
            tk.Frame(pf, bg=GREEN, height=12).place(
                in_=bar_bg, relwidth=pct / 100, relheight=1)
        tk.Label(pf, text=f"{pct}%", bg=BG_WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="e")

        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True, padx=20, pady=12)
        STATUS_COLORS = {"Completed": GREEN, "In Progress": GOLD_TILE,
                         "Not Started": MUTED, "Overdue": DANGER}
        for r in rows:
            mf = card_frame(sf.inner, padx=14, pady=12)
            mf.pack(fill="x", pady=4)
            top = tk.Frame(mf, bg=BG_WHITE)
            top.pack(fill="x")
            tk.Label(top, text=r["title"], bg=BG_WHITE, fg=DARK,
                     font=("Segoe UI", 11, "bold")).pack(side="left")
            sc = STATUS_COLORS.get(r["status"], MUTED)
            tk.Label(top, text=f"  {r['status']}", bg=BG_WHITE, fg=sc,
                     font=("Segoe UI", 9, "bold")).pack(side="left", padx=8)
            tk.Label(top, text=f"Due: {str(r['due_date'])[:10]}",
                     bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(side="right")
            if r.get("description"):
                tk.Label(mf, text=r["description"], bg=BG_WHITE, fg=TEXT2,
                         font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
            bf = tk.Frame(mf, bg=BG_WHITE)
            bf.pack(anchor="w", pady=(8, 0))
            tk.Label(bf, text="Update:", bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
            for st, col in [("Not Started", "#95a5a6"), ("In Progress", GOLD_TILE), ("Completed", GREEN)]:
                tk.Button(bf, text=st,
                          command=lambda s=st, mid=r["milestone_id"]: self._update(mid, s),
                          bg=col, fg=WHITE, relief="flat",
                          font=("Segoe UI", 9), padx=8, pady=3).pack(side="left", padx=2)

    def _update(self, mid, status):
        query("UPDATE milestones SET status=%s WHERE milestone_id=%s AND student_id=%s",
              (status, mid, SESSION["user_id"]))
        messagebox.showinfo("Updated", f"Milestone set to '{status}'")
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ═══════════════════════════════════════════════════════════
class StudentMessages(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Messages", "Chat with your supervisor")
        self._build()

    def _build(self):
        sid = SESSION["user_id"]
        sup = query("""SELECT s.supervisor_id, sup.full_name
                       FROM students s
                       JOIN supervisors sup ON s.supervisor_id=sup.supervisor_id
                       WHERE s.student_id=%s""", (sid,), one=True)
        if not sup:
            tk.Label(self, text="No supervisor assigned yet.",
                     bg=BG_MAIN, fg=MUTED, font=("Segoe UI", 12)).pack(pady=40)
            return
        sup_id   = sup["supervisor_id"]
        sup_name = sup["full_name"]
        tk.Label(self, text=f"Conversation with {sup_name}",
                 bg=BG_MAIN, fg=BLUE, font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=20, pady=(8, 4))

        mf = card_frame(self, padx=0, pady=0)
        mf.pack(fill="both", expand=True, padx=20, pady=(0, 0))
        self.canvas = tk.Canvas(mf, bg=BG_WHITE, highlightthickness=0)
        sb = ttk.Scrollbar(mf, orient="vertical", command=self.canvas.yview)
        self.msg_frame = tk.Frame(self.canvas, bg=BG_WHITE)
        self.msg_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._load_msgs(sid, sup_id)

        inp = tk.Frame(self, bg=BG_MAIN, pady=8)
        inp.pack(fill="x", padx=20)

        # Attach file button
        att = tk.Button(inp, text="📎",
                        command=lambda: self._attach_send(sid, sup_id),
                        bg="#ecf0f1", fg=DARK, relief="flat",
                        font=("Segoe UI", 12), padx=8)
        att.pack(side="left", padx=(0, 6))

        self.msg_var = tk.StringVar()
        me = tk.Entry(inp, textvariable=self.msg_var)
        style_entry(me)
        me.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))
        me.bind("<Return>", lambda e: self._send(sid, sup_id))
        sb2 = tk.Button(inp, text="Send", command=lambda: self._send(sid, sup_id))
        style_btn(sb2, "#2e8b57", WHITE)
        sb2.pack(side="right")

    def _load_msgs(self, sid, sup_id):
        for w in self.msg_frame.winfo_children():
            w.destroy()
        rows = query("""SELECT * FROM messages
                        WHERE (sender_role='student'    AND sender_id=%s AND receiver_id=%s)
                           OR (sender_role='supervisor' AND sender_id=%s AND receiver_id=%s)
                        ORDER BY sent_at ASC""",
                     (sid, sup_id, sup_id, sid)) or []
        for r in rows:
            is_me = r["sender_role"] == "student"
            bg    = "#2e8b57" if is_me else "#ecf0f1"
            fg    = WHITE if is_me else DARK
            side  = "right" if is_me else "left"
            bf = tk.Frame(self.msg_frame, bg=BG_WHITE)
            bf.pack(fill="x", padx=10, pady=3, anchor="e" if is_me else "w")
            tk.Label(bf, text=r["body"], bg=bg, fg=fg,
                     font=("Segoe UI", 10), wraplength=360,
                     padx=10, pady=6, justify="left",
                     relief="flat").pack(side=side)
            # Show attachment if any
            if r.get("attachment_path"):
                full = os.path.join(UPLOAD_FOLDER, r["attachment_path"])
                aname = r.get("attachment_name", "Attachment")
                ab = tk.Button(bf, text=f"📄 {aname}",
                               command=lambda p=full: open_file(p),
                               bg="#dce1e7", fg=BLUE, relief="flat",
                               font=("Segoe UI", 9), cursor="hand2", padx=6, pady=3)
                ab.pack(side=side, pady=2)
            tk.Label(bf, text=str(r["sent_at"])[:16],
                     bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 8)).pack(side=side, padx=4)
        self.after(100, lambda: self.canvas.yview_moveto(1.0))

    def _send(self, sid, sup_id):
        body = self.msg_var.get().strip()
        if not body:
            return
        query("""INSERT INTO messages
                 (sender_role, sender_id, receiver_role, receiver_id, body)
                 VALUES ('student',%s,'supervisor',%s,%s)""",
              (sid, sup_id, body))
        # Notify supervisor
        create_notification("supervisor", sup_id, "message",
                            "New Message", f"{SESSION['name']}: {body[:60]}")
        self.msg_var.set("")
        self._load_msgs(sid, sup_id)

    def _attach_send(self, sid, sup_id):
        path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if not path:
            return
        ext  = path.rsplit(".", 1)[-1].lower()
        safe = f"msg_{sid}_{uuid.uuid4().hex[:8]}.{ext}"
        dest = os.path.join(UPLOAD_FOLDER, safe)
        shutil.copy2(path, dest)
        fname = os.path.basename(path)
        query("""INSERT INTO messages
                 (sender_role, sender_id, receiver_role, receiver_id,
                  body, attachment_path, attachment_name)
                 VALUES ('student',%s,'supervisor',%s,%s,%s,%s)""",
              (sid, sup_id, f"[Attachment: {fname}]", safe, fname))
        create_notification("supervisor", sup_id, "message",
                            "New Attachment", f"{SESSION['name']} sent a file: {fname}")
        self._load_msgs(sid, sup_id)


# ═══════════════════════════════════════════════════════════
class StudentMeetings(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)

        page_header(
            self,
            "Meetings",
            "Request and manage meetings"
        )

        self._build()

    def _build(self):

        sid = SESSION["user_id"]

        sup = query("""
            SELECT supervisor_id
            FROM students
            WHERE student_id=%s
        """, (sid,), one=True)

        sup_id = sup["supervisor_id"] if sup else None

        self.selected_meeting_id = None

        # ================= REQUEST FORM =================
        rf = card_frame(self, padx=16, pady=14)
        rf.pack(fill="x", padx=20, pady=(12, 0))

        tk.Label(
            rf,
            text="Request / Update Meeting",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.fvars = {}

        row = tk.Frame(rf, bg=BG_WHITE)
        row.pack(fill="x")

        for lbl_t, key in [
            ("Title", "title"),
            ("Date (YYYY-MM-DD)", "date"),
            ("Time (HH:MM)", "time")
        ]:

            col = tk.Frame(row, bg=BG_WHITE)
            col.pack(side="left", padx=(0, 12), expand=True, fill="x")

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

            self.fvars[key] = v

        btn_row = tk.Frame(rf, bg=BG_WHITE)
        btn_row.pack(anchor="w", pady=(10, 0))

        req_btn = tk.Button(
            btn_row,
            text="Request Meeting",
            command=lambda: self._request(sup_id)
        )

        style_btn(req_btn)
        req_btn.pack(side="left", padx=(0, 8))

        upd_btn = tk.Button(
            btn_row,
            text="Update Meeting",
            command=self._update_meeting
        )

        style_btn(upd_btn, ORANGE, WHITE)
        upd_btn.pack(side="left", padx=(0, 8))

        del_btn = tk.Button(
            btn_row,
            text="Delete Meeting",
            command=self._delete_meeting
        )

        style_btn(del_btn, DANGER, WHITE)
        del_btn.pack(side="left")

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
            text="My Meetings",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=14, pady=(10, 6))

        tk.Frame(lf, bg=BORDER, height=1).pack(fill="x")

        tree_frame = tk.Frame(lf, bg=BG_WHITE)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

        cols = (
            "Title",
            "Date",
            "Time",
            "Status",
            "Supervisor"
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="headings",
            height=8
        )

        style_treeview(
            self.tree,
            cols,
            [180, 90, 70, 100, 150]
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

        self.meet_map = {}

        self._load_meetings(sid)

    # ==========================================================
    def _validate_meeting_inputs(self):

        import re
        from datetime import datetime

        title = self.fvars["title"].get().strip()
        date = self.fvars["date"].get().strip()
        time = self.fvars["time"].get().strip()

        if not title or not date or not time:

            messagebox.showwarning(
                "Missing",
                "Title, date and time are required."
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

    # ==========================================================
    def _load_meetings(self, sid):

        for r in self.tree.get_children():
            self.tree.delete(r)

        self.meet_map.clear()

        rows = query("""
            SELECT m.meeting_id,
                   m.title,
                   m.meeting_date,
                   m.meeting_time,
                   m.status,
                   sup.full_name AS sup_name
            FROM meetings m
            JOIN supervisors sup
                ON m.supervisor_id = sup.supervisor_id
            WHERE m.student_id=%s
            ORDER BY m.meeting_date DESC
        """, (sid,)) or []

        for r in rows:

            iid = self.tree.insert(
                "",
                "end",
                values=(
                    r["title"],
                    str(r["meeting_date"])[:10],
                    str(r["meeting_time"])[:5],
                    r["status"],
                    r["sup_name"]
                )
            )

            self.meet_map[iid] = {
                "meeting_id": r["meeting_id"],
                "status": r["status"]
            }

    # ==========================================================
    def _fill_form(self, event=None):

        sel = self.tree.selection()

        if not sel:
            return

        iid = sel[0]

        vals = self.tree.item(iid, "values")

        self.selected_meeting_id = self.meet_map[iid]["meeting_id"]

        self.fvars["title"].set(vals[0])
        self.fvars["date"].set(vals[1])
        self.fvars["time"].set(vals[2])

    # ==========================================================
    def _request(self, sup_id):

        sid = SESSION["user_id"]

        if not self._validate_meeting_inputs():
            return

        title = self.fvars["title"].get().strip()
        date = self.fvars["date"].get().strip()
        time = self.fvars["time"].get().strip()

        query("""
            INSERT INTO meetings
            (
                supervisor_id,
                student_id,
                title,
                meeting_date,
                meeting_time,
                requested_by,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,'student','Requested')
        """, (
            sup_id,
            sid,
            title,
            date,
            time
        ))

        create_notification(
            "supervisor",
            sup_id,
            "meeting",
            "Meeting Request",
            f"{SESSION['name']} requested a meeting.\nTOPIC: {title}"
        )

        messagebox.showinfo(
            "Success",
            "Meeting request sent."
        )

        self._clear()

        self._load_meetings(sid)

    # ==========================================================
    def _update_meeting(self):

        if not self.selected_meeting_id:

            messagebox.showwarning(
                "Select",
                "Select a meeting first."
            )

            return

        if not self._validate_meeting_inputs():
            return

        sel = self.tree.selection()

        if not sel:
            return

        iid = sel[0]

        meeting = self.meet_map[iid]

        if meeting["status"] != "Requested":

            messagebox.showwarning(
                "Not Allowed",
                "You can only edit requested meetings."
            )

            return

        title = self.fvars["title"].get().strip()
        date = self.fvars["date"].get().strip()
        time = self.fvars["time"].get().strip()

        query("""
            UPDATE meetings
            SET title=%s,
                meeting_date=%s,
                meeting_time=%s
            WHERE meeting_id=%s
        """, (
            title,
            date,
            time,
            self.selected_meeting_id
        ))

        sup = query("""
            SELECT supervisor_id
            FROM meetings
            WHERE meeting_id=%s
        """, (
            self.selected_meeting_id,
        ), one=True)

        if sup:

            create_notification(
                "supervisor",
                sup["supervisor_id"],
                "meeting",
                "Meeting Updated",
                f"{SESSION['name']} updated a requested meeting.\nTOPIC: {title}"
            )

        messagebox.showinfo(
            "Updated",
            "Meeting updated successfully."
        )

        self._clear()

        self._load_meetings(SESSION["user_id"])

    # ==========================================================
    def _delete_meeting(self):

        if not self.selected_meeting_id:

            messagebox.showwarning(
                "Select",
                "Select a meeting first."
            )

            return

        sel = self.tree.selection()

        if not sel:
            return

        iid = sel[0]

        meeting = self.meet_map[iid]

        if meeting["status"] != "Requested":

            messagebox.showwarning(
                "Not Allowed",
                "You can only delete requested meetings."
            )

            return

        confirm = messagebox.askyesno(
            "Delete Meeting",
            "Are you sure you want to delete this meeting?"
        )

        if not confirm:
            return

        title = self.tree.item(iid, "values")[0]

        sup = query("""
            SELECT supervisor_id
            FROM meetings
            WHERE meeting_id=%s
        """, (
            self.selected_meeting_id,
        ), one=True)

        query(
            "DELETE FROM meetings WHERE meeting_id=%s",
            (self.selected_meeting_id,)
        )

        if sup:

            create_notification(
                "supervisor",
                sup["supervisor_id"],
                "meeting",
                "Meeting Deleted",
                f"{SESSION['name']} deleted a requested meeting.\nTOPIC: {title}"
            )

        messagebox.showinfo(
            "Deleted",
            "Meeting deleted successfully."
        )

        self._clear()

        self._load_meetings(SESSION["user_id"])

    # ==========================================================
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
            WHERE student_id=%s
            AND meeting_date < %s
        """, (
            sid,
            date.today()
        ))

        messagebox.showinfo(
            "Success",
            "Past meetings cleared successfully."
        )

        self._clear()

        self._load_meetings(SESSION["user_id"])

    # ==========================================================
    def _clear(self):

        self.selected_meeting_id = None

        for v in self.fvars.values():
            v.set("")


# ═══════════════════════════════════════════════════════════
class StudentNotifications(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)

        page_header(self, "Notifications", "Your alerts and updates")

        self.filter_type = "all"   # all | meeting | submission
        self._build()

    # ======================================================
    def _build(self):

        sid = SESSION["user_id"]

        # ---------------- TOP BAR ----------------
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

        # ---------------- SCROLL AREA ----------------
        self.sf = ScrollFrame(self, bg=BG_MAIN)
        self.sf.pack(fill="both", expand=True, padx=20, pady=12)

        self.refresh()

    # ======================================================
    def refresh(self):

        sid = SESSION["user_id"]

        sql = """
            SELECT * FROM notifications
            WHERE user_role='student' AND user_id=%s
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
            WHERE user_role='student' AND user_id=%s
        """, (sid,))

        # clear UI
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
            WHERE user_role='student' AND user_id=%s
        """, (sid,))

        self.refresh()



# ═══════════════════════════════════════════════════════════
class StudentProfile(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "My Profile", "View and update your profile")
        self._build()

    def _build(self):
        sid = SESSION["user_id"]
        row = query("""SELECT s.*, sup.full_name AS supervisor_name
                       FROM students s
                       LEFT JOIN supervisors sup ON s.supervisor_id=sup.supervisor_id
                       WHERE s.student_id=%s""", (sid,), one=True)

        # ── Wrap everything in a ScrollFrame so nothing gets clipped ──
        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True, padx=20, pady=12)

        pf = card_frame(sf.inner, padx=20, pady=18)
        pf.pack(fill="x")

        self.pvars = {}

        # ── Profile fields ────────────────────────────────────────────
        for lbl_t, key, ro in [
            ("Full Name",    "full_name",       False),
            ("Email",        "email",           True),
            ("Thesis Title", "thesis_title",    False),
            ("Supervisor",   "supervisor_name", True),
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
        sid   = SESSION["user_id"]
        name  = self.pvars["full_name"].get().strip()
        title = self.pvars["thesis_title"].get().strip()

        if name:
            query("UPDATE students SET full_name=%s WHERE student_id=%s", (name, sid))
            SESSION["name"] = name
        if title:
            query("UPDATE students SET thesis_title=%s WHERE student_id=%s", (title, sid))

        new_pw = self.pvars["new_pw"].get()
        old_pw = self.pvars["old_pw"].get()

        if new_pw:
            if not old_pw:
                messagebox.showerror("Error", "Please enter your current password.")
                return
            row = query("SELECT password_hash FROM students WHERE student_id=%s",
                        (sid,), one=True)
            if not check_password(old_pw, row["password_hash"]):
                messagebox.showerror("Error", "Current password is incorrect.")
                return
            if len(new_pw) < 6:
                messagebox.showerror("Error", "New password must be at least 6 characters.")
                return
            query("UPDATE students SET password_hash=%s WHERE student_id=%s",
                  (hash_password(new_pw), sid))

        messagebox.showinfo("Saved", "Profile updated successfully!")