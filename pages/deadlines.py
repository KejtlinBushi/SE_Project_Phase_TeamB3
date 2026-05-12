"""
pages/deadlines.py
Final submission deadline only — student view with reminder notification.
CEN 302 Software Engineering | Group III | Epoka University
"""

import tkinter as tk
from tkinter import messagebox
from datetime import date

from database import query
from auth import SESSION
from ui import (BG_MAIN, BG_WHITE, BLUE, GREEN, GOLD_TILE, ORANGE,
                WHITE, MUTED, DARK, BORDER, DANGER, WARNING,
                card_frame, page_header, ScrollFrame)


def send_reminder_if_needed(student_id):
    """Send a notification if the deadline is tomorrow and not already sent."""
    try:
        dl = query("""SELECT d.due_date, d.title FROM deadlines d
                      JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                      WHERE da.student_id=%s ORDER BY d.due_date ASC LIMIT 1""",
                   (student_id,), one=True)
        if not dl:
            return
        days_left = (dl["due_date"] - date.today()).days
        if days_left == 1:
            # Check if reminder already sent today
            existing = query("""SELECT notif_id FROM notifications
                                WHERE user_role='student' AND user_id=%s
                                AND type='deadline_reminder'
                                AND DATE(delivered_at)=CURDATE()""",
                             (student_id,), one=True)
            if not existing:
                query("""INSERT INTO notifications
                         (user_role,user_id,type,title,message)
                         VALUES ('student',%s,'deadline_reminder',
                         'Deadline Tomorrow!',
                         'Your final thesis submission is due TOMORROW. Make sure to upload your work!')""",
                      (student_id,))
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
#  STUDENT VIEW
# ════════════════════════════════════════════════════════════
class StudentDeadlines(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Submission Deadline", "Your final thesis submission deadline")
        sid = SESSION["user_id"]
        send_reminder_if_needed(sid)
        self._build(sid)

    def _build(self, sid):
        dl = query("""SELECT d.due_date, d.title, d.description,
                             da.submitted_at
                      FROM deadlines d
                      JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                      WHERE da.student_id=%s ORDER BY d.due_date ASC LIMIT 1""",
                   (sid,), one=True)

        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        if not dl:
            nf = card_frame(inner, padx=20, pady=30)
            nf.pack(fill="x", padx=20, pady=20)
            tk.Label(nf, text="📅", bg=BG_WHITE,
                     font=("Segoe UI", 36)).pack()
            tk.Label(nf, text="No deadline set yet",
                     bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 14, "bold")).pack(pady=(8, 4))
            tk.Label(nf, text="Your supervisor will set the final submission deadline.",
                     bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 10)).pack()
            return

        days_left = (dl["due_date"] - date.today()).days
        if days_left < 0:
            status_text  = "OVERDUE"
            status_color = DANGER
            bg_color     = "#fdf0f0"
        elif days_left == 0:
            status_text  = "DUE TODAY"
            status_color = DANGER
            bg_color     = "#fdf0f0"
        elif days_left == 1:
            status_text  = "DUE TOMORROW ⚠"
            status_color = WARNING
            bg_color     = "#fffbf0"
        elif days_left <= 7:
            status_text  = f"{days_left} days remaining"
            status_color = WARNING
            bg_color     = "#fffbf0"
        else:
            status_text  = f"{days_left} days remaining"
            status_color = GREEN
            bg_color     = "#f0fdf4"

        # Big deadline card
        dc = tk.Frame(inner, bg=bg_color,
                      highlightthickness=2,
                      highlightbackground=status_color)
        dc.pack(fill="x", padx=20, pady=20)

        tk.Label(dc, text="Final Thesis Submission Deadline",
                 bg=bg_color, fg=DARK,
                 font=("Segoe UI", 13, "bold")).pack(pady=(20, 4))

        tk.Label(dc, text=str(dl["due_date"]),
                 bg=bg_color, fg=status_color,
                 font=("Segoe UI", 36, "bold")).pack()

        tk.Label(dc, text=status_text,
                 bg=bg_color, fg=status_color,
                 font=("Segoe UI", 13, "bold")).pack(pady=(4, 0))

        if dl.get("description"):
            tk.Label(dc, text=dl["description"],
                     bg=bg_color, fg=MUTED,
                     font=("Segoe UI", 10)).pack(pady=(8, 0))

        # Countdown visual
        tk.Frame(dc, bg=BORDER, height=1).pack(fill="x", padx=20, pady=16)

        if days_left >= 0:
            bar_f = tk.Frame(dc, bg=bg_color)
            bar_f.pack(padx=20, pady=(0, 8), fill="x")
            tk.Label(bar_f, text="Time remaining:",
                     bg=bg_color, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            # Show days as a simple bar (max 30 days)
            max_days = 30
            pct = min(1.0, days_left / max_days) if days_left > 0 else 0
            bar_bg = tk.Frame(bar_f, bg="#e0e0e0", height=14)
            bar_bg.pack(fill="x", pady=(4, 0))
            if pct > 0:
                tk.Frame(bar_f, bg=status_color, height=14).place(
                    in_=bar_bg, relwidth=pct, relheight=1)

        # Submission status — also check milestones table for final upload
        tk.Frame(dc, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(8, 16))

        # Check if student submitted via milestones final upload
        ms = query("SELECT final_file_name, final_score, grade FROM milestones WHERE student_id=%s ORDER BY milestone_id ASC",
                   (sid,), one=True)
        final_submitted = (ms and ms.get("final_file_name")) or dl.get("submitted_at")

        if final_submitted:
            # Submission closed box
            closed_f = tk.Frame(dc, bg="#d5f5e3",
                                highlightthickness=1, highlightbackground=GREEN)
            closed_f.pack(fill="x", padx=20, pady=(0, 10))
            tk.Label(closed_f,
                     text="✓  Submission Closed",
                     bg="#d5f5e3", fg=GREEN,
                     font=("Segoe UI", 12, "bold"),
                     padx=12, pady=8).pack(anchor="w")
            if ms and ms.get("final_file_name"):
                tk.Label(closed_f,
                         text=f"File: {ms['final_file_name']}",
                         bg="#d5f5e3", fg=DARK,
                         font=("Segoe UI", 9),
                         padx=12, pady=2).pack(anchor="w")
            if dl.get("submitted_at"):
                tk.Label(closed_f,
                         text=f"Submitted on: {str(dl['submitted_at'])[:10]}",
                         bg="#d5f5e3", fg=DARK,
                         font=("Segoe UI", 9),
                         padx=12, pady=2).pack(anchor="w")
            tk.Label(closed_f,
                     text="You cannot upload again. Awaiting supervisor grade.",
                     bg="#d5f5e3", fg=MUTED,
                     font=("Segoe UI", 9),
                     padx=12, pady=(2, 8)).pack(anchor="w")

            # Show grade if available
            if ms and ms.get("final_score") is not None:
                gf = tk.Frame(dc, bg=bg_color)
                gf.pack(pady=(0, 10))
                tk.Label(gf, text=f"  Score: {ms['final_score']}/100  ",
                         bg=BLUE, fg=WHITE,
                         font=("Segoe UI", 12, "bold"),
                         padx=10, pady=4).pack(side="left", padx=(0, 8))
                if ms.get("grade"):
                    gc = GREEN if ms["grade"] in ("A","A+","A-","Excellent") else (
                         DANGER if ms["grade"] in ("F","Fail") else GOLD_TILE)
                    tk.Label(gf, text=f"  Grade: {ms['grade']}  ",
                             bg=gc, fg=WHITE,
                             font=("Segoe UI", 12, "bold"),
                             padx=10, pady=4).pack(side="left")
            tk.Frame(dc, bg=bg_color, height=8).pack()
        else:
            tk.Label(dc,
                     text="You have not submitted yet. Go to Thesis Progress to upload.",
                     bg=bg_color, fg=WARNING,
                     font=("Segoe UI", 10)).pack(pady=(0, 20))


# ════════════════════════════════════════════════════════════
#  SUPERVISOR VIEW  (deadline management is in milestones page)
# ════════════════════════════════════════════════════════════
class SupervisorDeadlines(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Submission Deadline", "Manage the final submission deadline")
        self._build()

    def _build(self):
        sup_id   = SESSION["user_id"]
        students = query("SELECT student_id, full_name FROM students WHERE supervisor_id=%s",
                         (sup_id,)) or []

        # Current deadline
        dl = query("""SELECT d.deadline_id, d.due_date FROM deadlines d
                      JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                      JOIN students st ON da.student_id=st.student_id
                      WHERE st.supervisor_id=%s LIMIT 1""", (sup_id,), one=True)

        dc = card_frame(self, padx=20, pady=20)
        dc.pack(fill="x", padx=20, pady=20)
        tk.Label(dc, text="Set / Update Final Submission Deadline",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 12))

        if dl:
            days = (dl["due_date"] - date.today()).days
            col  = DANGER if days <= 1 else (WARNING if days <= 7 else GREEN)
            tk.Label(dc, text=f"Current deadline: {dl['due_date']}  ({days} days away)",
                     bg=BG_WHITE, fg=col,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 12))

        row_f = tk.Frame(dc, bg=BG_WHITE)
        row_f.pack(fill="x")
        tk.Label(row_f, text="New date (YYYY-MM-DD):",
                 bg=BG_WHITE, fg=MUTED,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
        from ui import style_entry
        self._dl_var = tk.StringVar()
        e = tk.Entry(row_f, textvariable=self._dl_var, width=16)
        style_entry(e)
        e.pack(side="left", ipady=6, padx=(0, 10))
        tk.Button(row_f,
                  text="Set Deadline" if not dl else "Update Deadline",
                  command=lambda: self._save(students, dl),
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=12, pady=5).pack(side="left")

        # Students submission status
        tk.Label(self, text="Student Submission Status",
                 bg=BG_MAIN, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(14, 4))

        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        for stu in students:
            da = query("""SELECT da.submitted_at FROM deadline_assignments da
                          JOIN deadlines d ON da.deadline_id=d.deadline_id
                          JOIN students st ON da.student_id=st.student_id
                          WHERE st.supervisor_id=%s AND da.student_id=%s LIMIT 1""",
                       (sup_id, stu["student_id"]), one=True)
            rf = card_frame(sf.inner, padx=14, pady=10)
            rf.pack(fill="x", pady=4)
            top = tk.Frame(rf, bg=BG_WHITE)
            top.pack(fill="x")
            tk.Label(top, text=f"👤 {stu['full_name']}",
                     bg=BG_WHITE, fg=DARK,
                     font=("Segoe UI", 11, "bold")).pack(side="left")
            submitted = da and da.get("submitted_at")
            status_text  = f"✓ Submitted {str(da['submitted_at'])[:10]}" if submitted else "Not submitted yet"
            status_color = GREEN if submitted else MUTED
            tk.Label(top, text=status_text,
                     bg=BG_WHITE, fg=status_color,
                     font=("Segoe UI", 10, "bold")).pack(side="right")

    def _save(self, students, dl):
        date_str = self._dl_var.get().strip()
        if not date_str:
            messagebox.showwarning("Missing", "Please enter a date.")
            return
        sup_id = SESSION["user_id"]
        if dl:
            query("UPDATE deadlines SET due_date=%s WHERE deadline_id=%s",
                  (date_str, dl["deadline_id"]))
            for stu in students:
                query("""INSERT INTO notifications (user_role,user_id,type,title,message)
                         VALUES ('student',%s,'deadline','Deadline Updated',
                         %s)""",
                      (stu["student_id"],
                       f"Final submission deadline updated to {date_str}"))
            messagebox.showinfo("Updated", f"Deadline updated to {date_str}")
        else:
            did = query("""INSERT INTO deadlines (supervisor_id,title,due_date,description)
                           VALUES (%s,'Final Thesis Submission',%s,
                           'Upload your final thesis document')""",
                        (sup_id, date_str))
            for stu in students:
                query("INSERT IGNORE INTO deadline_assignments (deadline_id,student_id) VALUES (%s,%s)",
                      (did, stu["student_id"]))
                query("""INSERT INTO notifications (user_role,user_id,type,title,message)
                         VALUES ('student',%s,'deadline','Submission Deadline Set',%s)""",
                      (stu["student_id"],
                       f"Your final thesis submission deadline is {date_str}"))
            messagebox.showinfo("Set", f"Deadline set to {date_str}")
        for w in self.winfo_children():
            w.destroy()
        page_header(self, "Submission Deadline", "Manage the final submission deadline")
        self._build()