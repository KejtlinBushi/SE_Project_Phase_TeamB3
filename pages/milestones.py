"""
pages/milestones.py
Thesis progress tracker with 6-phase pipeline, donut chart,
final submission upload, and grading by supervisor.
CEN 302 Software Engineering | Group III | Epoka University
"""

import os, shutil, uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime, timedelta

from database import query
from auth import SESSION
from ui import (BG_MAIN, BG_WHITE, BLUE, BLUE2, GREEN, GOLD_TILE, ORANGE,
                WHITE, MUTED, DARK, BORDER, SUCCESS, DANGER, WARNING,
                TEXT2, style_entry, card_frame, page_header, ScrollFrame)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── The 6 thesis phases (fixed order) ────────────────────────
PHASES = [
    "Abstract",
    "Introduction",
    "Literature Review",
    "Methodology",
    "Results",
    "Conclusion & Final",
]
PHASE_COLORS = [BLUE, "#8e44ad", GOLD_TILE, ORANGE, GREEN, "#27ae60"]


def notify(user_role, user_id, ntype, title, message):
    try:
        query("""INSERT INTO notifications (user_role,user_id,type,title,message)
                 VALUES (%s,%s,%s,%s,%s)""",
              (user_role, user_id, ntype, title, message))
    except Exception:
        pass


# ─── Ensure DB columns exist (runs silently) ─────────────────
def _ensure_columns():
    try:
        query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS progress_pct INT NOT NULL DEFAULT 0")
        query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS supervisor_comment TEXT DEFAULT NULL")
        query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS grade VARCHAR(10) DEFAULT NULL")
        query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS phase_index INT NOT NULL DEFAULT 0")
        query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS phase_status VARCHAR(20) DEFAULT 'Not Started'")
        query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS final_file_path VARCHAR(500) DEFAULT NULL")
        query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS final_file_name VARCHAR(255) DEFAULT NULL")
        query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS final_score INT DEFAULT NULL")
    except Exception:
        pass

_ensure_columns()


# ─── Get or create milestone row for a student ───────────────
def get_or_create_milestone(student_id, supervisor_id):
    row = query("SELECT * FROM milestones WHERE student_id=%s ORDER BY milestone_id ASC",
                (student_id,), one=True)
    if not row:
        mid = query("""INSERT INTO milestones
                       (supervisor_id, student_id, title, due_date, status, progress_pct)
                       VALUES (%s,%s,'Thesis Progress',CURDATE(),'In Progress',0)""",
                    (supervisor_id, student_id))
        row = query("SELECT * FROM milestones WHERE milestone_id=%s", (mid,), one=True)
    return row


# ── Donut chart ───────────────────────────────────────────────
def draw_donut(canvas, pct, color=GREEN, size=160):
    canvas.delete("all")
    cx = cy = size // 2
    r  = size // 2 - 10
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                       outline="#e0e0e0", width=18, fill="")
    if pct > 0:
        import math
        extent = min(359.9, pct / 100 * 359.9)
        canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                          start=90, extent=-extent,
                          style="arc", outline=color, width=18)
    canvas.create_text(cx, cy - 10, text=f"{pct}%",
                       font=("Segoe UI", 20, "bold"), fill=DARK)
    canvas.create_text(cx, cy + 14, text="Complete",
                       font=("Segoe UI", 9), fill=MUTED)


# ════════════════════════════════════════════════════════════
#  STUDENT VIEW
# ════════════════════════════════════════════════════════════
class StudentMilestones(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Thesis Progress", "Track your thesis phases and submit your final work")
        self._build()

    def _build(self):
        sid = SESSION["user_id"]
        # Get supervisor
        stu = query("SELECT supervisor_id FROM students WHERE student_id=%s", (sid,), one=True)
        if not stu or not stu["supervisor_id"]:
            tk.Label(self, text="No supervisor assigned yet. Contact admin.",
                     bg=BG_MAIN, fg=WARNING,
                     font=("Segoe UI", 12)).pack(pady=40)
            return

        sup_id = stu["supervisor_id"]
        row    = get_or_create_milestone(sid, sup_id)
        mid    = row["milestone_id"]

        # Phase statuses stored as pipe-separated string in phase_status
        # e.g. "Done|In Progress|Not Started|Not Started|Not Started|Not Started"
        raw_phases = (row.get("phase_status") or "")
        phase_list = raw_phases.split("|") if raw_phases and "|" in raw_phases else ["Not Started"] * 6
        while len(phase_list) < 6:
            phase_list.append("Not Started")

        # Compute overall %
        done_count = sum(1 for p in phase_list if p == "Done")
        pct = int(done_count / 6 * 100)

        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        # ── Top row: donut + submission deadline ──────────────
        top = tk.Frame(inner, bg=BG_MAIN)
        top.pack(fill="x", padx=20, pady=(10, 0))

        # Donut
        donut_card = card_frame(top, padx=20, pady=16)
        donut_card.pack(side="left", padx=(0, 12))
        tk.Label(donut_card, text="Overall Progress",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack()
        c = tk.Canvas(donut_card, width=160, height=160,
                      bg=BG_WHITE, highlightthickness=0)
        c.pack(pady=8)
        draw_donut(c, pct)
        tk.Label(donut_card, text=f"{done_count} of 6 phases complete",
                 bg=BG_WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack()

        # Deadline info
        dl = query("""SELECT d.due_date FROM deadlines d
                      JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                      WHERE da.student_id=%s ORDER BY d.due_date ASC LIMIT 1""", (sid,), one=True)
        info_card = card_frame(top, padx=20, pady=16)
        info_card.pack(side="left", fill="both", expand=True)
        tk.Label(info_card, text="Final Submission Deadline",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        if dl:
            days_left = (dl["due_date"] - date.today()).days
            color = DANGER if days_left <= 1 else (WARNING if days_left <= 7 else GREEN)
            tk.Label(info_card, text=str(dl["due_date"]),
                     bg=BG_WHITE, fg=color,
                     font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(8, 0))
            if days_left < 0:
                msg = "OVERDUE!"
            elif days_left == 0:
                msg = "Due TODAY!"
            elif days_left == 1:
                msg = "Due TOMORROW!"
            else:
                msg = f"{days_left} days remaining"
            tk.Label(info_card, text=msg, bg=BG_WHITE, fg=color,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w")
        else:
            tk.Label(info_card, text="No deadline set yet",
                     bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 13)).pack(anchor="w", pady=8)

        # ── 6-phase pipeline ──────────────────────────────────
        ph_card = card_frame(inner, padx=16, pady=16)
        ph_card.pack(fill="x", padx=20, pady=14)
        tk.Label(ph_card, text="Thesis Phases",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 12))

        # Determine which phase is unlocked
        # A phase is unlocked if all previous phases are "Done"
        def is_unlocked(idx):
            if idx == 0:
                return True
            return all(phase_list[i] == "Done" for i in range(idx))

        pipeline = tk.Frame(ph_card, bg=BG_WHITE)
        pipeline.pack(fill="x")

        for i, (phase, color) in enumerate(zip(PHASES, PHASE_COLORS)):
            status   = phase_list[i]
            unlocked = is_unlocked(i)

            col = tk.Frame(pipeline, bg=BG_WHITE)
            col.grid(row=0, column=i, padx=4, sticky="nsew")
            pipeline.columnconfigure(i, weight=1)

            # Phase box
            box_color = color if status == "Done" else (
                        BLUE if status == "In Progress" else "#bdc3c7")
            box = tk.Frame(col, bg=box_color, height=70,
                           highlightthickness=1,
                           highlightbackground=BORDER)
            box.pack(fill="x")
            box.pack_propagate(False)
            tk.Label(box, text=phase, bg=box_color, fg=WHITE,
                     font=("Segoe UI", 8, "bold"),
                     wraplength=90, justify="center").pack(expand=True)

            # Status label
            tk.Label(col, text=status, bg=BG_WHITE,
                     fg=GREEN if status == "Done" else (
                        BLUE if status == "In Progress" else MUTED),
                     font=("Segoe UI", 8, "bold")).pack(pady=(4, 2))

            # Dropdown (only if unlocked and not done)
            if unlocked and status != "Done":
                var = tk.StringVar(value=status)
                opts = ["Not Started", "In Progress", "Done"]
                # Can only mark Done if this is the last one or previous is done
                cb = ttk.Combobox(col, textvariable=var,
                                  values=opts, state="readonly", width=12)
                cb.pack()
                cb.bind("<<ComboboxSelected>>",
                        lambda e, idx=i, v=var, pl=phase_list, m=mid, s=sid:
                        self._update_phase(m, s, idx, v.get(), pl))
            elif not unlocked:
                tk.Label(col, text="🔒 Locked", bg=BG_WHITE, fg=MUTED,
                         font=("Segoe UI", 8)).pack()
            else:
                tk.Label(col, text="✓ Done", bg=BG_WHITE, fg=GREEN,
                         font=("Segoe UI", 8, "bold")).pack()

            # Arrow between phases
            if i < 5:
                tk.Label(pipeline, text="→", bg=BG_WHITE, fg=MUTED,
                         font=("Segoe UI", 14)).grid(row=0, column=i,
                                                      sticky="e", padx=(0, 0))

        # ── Final submission ──────────────────────────────────
        final_card = card_frame(inner, padx=16, pady=16)
        final_card.pack(fill="x", padx=20, pady=(0, 14))
        tk.Label(final_card, text="Final Submission",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        all_done = all(p == "Done" for p in phase_list)
        if not all_done:
            tk.Label(final_card,
                     text="⚠  Complete all 6 phases before submitting your final thesis.",
                     bg=BG_WHITE, fg=WARNING,
                     font=("Segoe UI", 10)).pack(anchor="w")
        else:
            # Show existing upload if any
            if row.get("final_file_name"):
                tk.Label(final_card,
                         text=f"✓ Uploaded: {row['final_file_name']}",
                         bg=BG_WHITE, fg=GREEN,
                         font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 8))

            # Grade display
            if row.get("final_score") is not None:
                grade = row.get("grade") or ""
                gf = tk.Frame(final_card, bg=BG_WHITE)
                gf.pack(anchor="w", pady=(0, 10))
                tk.Label(gf, text=f"  Score: {row['final_score']}/100  ",
                         bg=BLUE, fg=WHITE,
                         font=("Segoe UI", 12, "bold"),
                         padx=10, pady=4).pack(side="left", padx=(0, 8))
                if grade:
                    gc = GREEN if grade in ("A","A+","A-","Excellent") else (
                         DANGER if grade in ("F","Fail") else GOLD_TILE)
                    tk.Label(gf, text=f"  Grade: {grade}  ",
                             bg=gc, fg=WHITE,
                             font=("Segoe UI", 12, "bold"),
                             padx=10, pady=4).pack(side="left")
                if row.get("supervisor_comment"):
                    tk.Label(final_card,
                             text=f"Supervisor feedback: {row['supervisor_comment']}",
                             bg="#eaf4fb", fg=DARK,
                             font=("Segoe UI", 10),
                             wraplength=540, padx=10, pady=6).pack(fill="x", pady=(0, 8))

            # Upload button
            upload_btn = tk.Button(final_card, text="📁 Upload Final Thesis (PDF/DOCX)",
                                   command=lambda m=mid, s=sup_id: self._upload_final(m, s),
                                   bg=BLUE, fg=WHITE, relief="flat",
                                   font=("Segoe UI", 10, "bold"),
                                   padx=14, pady=7)
            upload_btn.pack(anchor="w")

    def _update_phase(self, mid, sid, idx, new_status, phase_list):
        phase_list[idx] = new_status
        new_str = "|".join(phase_list)
        done_count = sum(1 for p in phase_list if p == "Done")
        pct = int(done_count / 6 * 100)
        status = "Completed" if pct == 100 else "In Progress"
        query("""UPDATE milestones SET phase_status=%s, progress_pct=%s, status=%s
                 WHERE milestone_id=%s""",
              (new_str, pct, status, mid))
        # Rebuild
        for w in self.winfo_children():
            w.destroy()
        page_header(self, "Thesis Progress", "Track your thesis phases and submit your final work")
        self._build()

    def _upload_final(self, mid, sup_id):
        path = filedialog.askopenfilename(
            filetypes=[("Documents", "*.pdf *.docx"), ("All files", "*.*")])
        if not path:
            return
        ext  = path.rsplit(".", 1)[-1].lower()
        safe = f"final_{SESSION['user_id']}_{uuid.uuid4().hex[:8]}.{ext}"
        shutil.copy2(path, os.path.join(UPLOAD_FOLDER, safe))
        fname = os.path.basename(path)
        query("UPDATE milestones SET final_file_path=%s, final_file_name=%s WHERE milestone_id=%s",
              (safe, fname, mid))
        notify("supervisor", sup_id, "submission",
               "Final Thesis Submitted",
               f"{SESSION['name']} uploaded their final thesis: {fname}")
        messagebox.showinfo("Uploaded", f"Final thesis '{fname}' uploaded successfully!")
        for w in self.winfo_children():
            w.destroy()
        page_header(self, "Thesis Progress", "Track your thesis phases and submit your final work")
        self._build()


# ════════════════════════════════════════════════════════════
#  SUPERVISOR VIEW
# ════════════════════════════════════════════════════════════
class SupervisorMilestones(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Thesis Progress", "Monitor students and grade final submissions")
        self._build()

    def _build(self):
        sup_id   = SESSION["user_id"]
        students = query("SELECT student_id, full_name FROM students WHERE supervisor_id=%s",
                         (sup_id,)) or []

        if not students:
            tk.Label(self, text="No students assigned yet.",
                     bg=BG_MAIN, fg=MUTED,
                     font=("Segoe UI", 12)).pack(pady=40)
            return

        # ── Submission deadline setter ────────────────────────
        dl_card = card_frame(self, padx=16, pady=14)
        dl_card.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(dl_card, text="Final Submission Deadline",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

        # Current deadline
        dl_row = query("""SELECT d.deadline_id, d.due_date FROM deadlines d
                          JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                          JOIN students st ON da.student_id=st.student_id
                          WHERE st.supervisor_id=%s LIMIT 1""", (sup_id,), one=True)

        row_f = tk.Frame(dl_card, bg=BG_WHITE)
        row_f.pack(fill="x")
        tk.Label(row_f, text="Date (YYYY-MM-DD):",
                 bg=BG_WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 8))
        self._dl_var = tk.StringVar(value=str(dl_row["due_date"]) if dl_row else "")
        dl_entry = tk.Entry(row_f, textvariable=self._dl_var, width=16)
        style_entry(dl_entry)
        dl_entry.pack(side="left", ipady=5, padx=(0, 8))
        tk.Button(row_f,
                  text="Set Deadline" if not dl_row else "Update Deadline",
                  command=lambda: self._set_deadline(students, dl_row),
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=10, pady=4).pack(side="left")
        if dl_row:
            days = (dl_row["due_date"] - date.today()).days
            col  = DANGER if days <= 1 else (WARNING if days <= 7 else GREEN)
            tk.Label(row_f, text=f"  {days} days away",
                     bg=BG_WHITE, fg=col,
                     font=("Segoe UI", 10, "bold")).pack(side="left", padx=8)

        # ── Student list ──────────────────────────────────────
        tk.Label(self, text="My Students",
                 bg=BG_MAIN, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(14, 4))

        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        for stu in students:
            row = get_or_create_milestone(stu["student_id"], sup_id)
            self._student_card(sf.inner, stu, row, sup_id)

    def _student_card(self, parent, stu, row, sup_id):
        raw    = row.get("phase_status") or ""
        phases = raw.split("|") if "|" in raw else ["Not Started"] * 6
        while len(phases) < 6:
            phases.append("Not Started")
        done   = sum(1 for p in phases if p == "Done")
        pct    = int(done / 6 * 100)
        mid    = row["milestone_id"]

        sc = card_frame(parent, padx=0, pady=0)
        sc.pack(fill="x", pady=6)
        # Color bar on left based on progress
        bar_col = GREEN if pct == 100 else (GOLD_TILE if pct > 0 else "#bdc3c7")
        tk.Frame(sc, bg=bar_col, width=6).pack(side="left", fill="y")

        body = tk.Frame(sc, bg=BG_WHITE, padx=14, pady=12)
        body.pack(side="left", fill="both", expand=True)

        # Header row
        hdr = tk.Frame(body, bg=BG_WHITE)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"👤 {stu['full_name']}",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(hdr, text=f"{pct}% complete  ({done}/6 phases)",
                 bg=BG_WHITE, fg=bar_col,
                 font=("Segoe UI", 10, "bold")).pack(side="right")

        # Progress bar
        pb = tk.Frame(body, bg=BORDER, height=8)
        pb.pack(fill="x", pady=(6, 8))
        if pct > 0:
            tk.Frame(body, bg=bar_col, height=8).place(
                in_=pb, relwidth=pct/100, relheight=1)

        # Phase mini-chips
        chip_f = tk.Frame(body, bg=BG_WHITE)
        chip_f.pack(fill="x", pady=(0, 8))
        for i, (ph, st) in enumerate(zip(PHASES, phases)):
            col = GREEN if st == "Done" else (BLUE if st == "In Progress" else "#bdc3c7")
            tk.Label(chip_f, text=ph[:6],
                     bg=col, fg=WHITE,
                     font=("Segoe UI", 7, "bold"),
                     padx=4, pady=2).pack(side="left", padx=2)

        # Final submission section
        if row.get("final_file_name"):
            ff = tk.Frame(body, bg=BG_WHITE)
            ff.pack(fill="x", pady=(4, 0))
            tk.Label(ff, text=f"📄 Final: {row['final_file_name']}",
                     bg=BG_WHITE, fg=DARK,
                     font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

            # Grade display
            if row.get("final_score") is not None:
                gc = GREEN if (row.get("grade") or "") in ("A","A+","A-","Excellent") else (
                     DANGER if (row.get("grade") or "") in ("F","Fail") else GOLD_TILE)
                tk.Label(ff, text=f"Score: {row['final_score']}/100",
                         bg=BLUE, fg=WHITE,
                         font=("Segoe UI", 9, "bold"),
                         padx=6, pady=2).pack(side="left", padx=(0, 4))
                if row.get("grade"):
                    tk.Label(ff, text=f"Grade: {row['grade']}",
                             bg=gc, fg=WHITE,
                             font=("Segoe UI", 9, "bold"),
                             padx=6, pady=2).pack(side="left")

            # Grade button
            tk.Button(body, text="✎ Grade Final Submission",
                      command=lambda m=mid, s=stu["student_id"]: self._grade_dialog(m, s),
                      bg=GOLD_TILE, fg=WHITE, relief="flat",
                      font=("Segoe UI", 9, "bold"),
                      padx=10, pady=4).pack(anchor="w", pady=(6, 0))
        else:
            tk.Label(body, text="No final submission yet",
                     bg=BG_WHITE, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))

    def _set_deadline(self, students, dl_row):
        date_str = self._dl_var.get().strip()
        if not date_str:
            messagebox.showwarning("Missing", "Please enter a date.")
            return
        sup_id = SESSION["user_id"]
        if dl_row:
            # Update existing deadline
            query("UPDATE deadlines SET due_date=%s WHERE deadline_id=%s",
                  (date_str, dl_row["deadline_id"]))
            # Notify all students
            for stu in students:
                notify("student", stu["student_id"], "deadline",
                       "Deadline Updated",
                       f"Final submission deadline updated to {date_str}")
            messagebox.showinfo("Updated", f"Deadline updated to {date_str}")
        else:
            # Create new deadline
            did = query("""INSERT INTO deadlines (supervisor_id, title, due_date, description)
                           VALUES (%s,'Final Thesis Submission',%s,'Submit your final thesis document')""",
                        (sup_id, date_str))
            for stu in students:
                query("INSERT IGNORE INTO deadline_assignments (deadline_id, student_id) VALUES (%s,%s)",
                      (did, stu["student_id"]))
                notify("student", stu["student_id"], "deadline",
                       "Submission Deadline Set",
                       f"Your final thesis submission deadline is {date_str}")
            messagebox.showinfo("Set", f"Deadline set to {date_str} for all your students")
        # Rebuild
        for w in self.winfo_children():
            w.destroy()
        page_header(self, "Thesis Progress", "Monitor students and grade final submissions")
        self._build()

    def _grade_dialog(self, mid, st_id):
        dlg = FinalGradeDialog(self.master, mid, st_id)
        self.wait_window(dlg)
        for w in self.winfo_children():
            w.destroy()
        page_header(self, "Thesis Progress", "Monitor students and grade final submissions")
        self._build()


class FinalGradeDialog(tk.Toplevel):
    """Dialog for supervisor to give score/100 and grade for final submission."""
    def __init__(self, master, mid, st_id):
        super().__init__(master)
        self.mid   = mid
        self.st_id = st_id
        self.title("Grade Final Submission")
        self.geometry("440x340")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.grab_set()
        row = query("SELECT final_score, grade, supervisor_comment FROM milestones WHERE milestone_id=%s",
                    (mid,), one=True) or {}
        self._build(row.get("final_score") or 0,
                    row.get("grade") or "",
                    row.get("supervisor_comment") or "")

    def _build(self, old_score, old_grade, old_comment):
        f = tk.Frame(self, bg=BG_MAIN, padx=24, pady=20)
        f.pack(fill="both", expand=True)
        tk.Label(f, text="Grade Final Submission",
                 bg=BG_MAIN, fg=DARK,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 16))

        # Score out of 100
        tk.Label(f, text="Score (0–100)", bg=BG_MAIN, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.score_var = tk.IntVar(value=old_score)
        score_frame = tk.Frame(f, bg=BG_MAIN)
        score_frame.pack(fill="x", pady=(4, 4))
        self.score_lbl = tk.Label(score_frame, text=f"{old_score}/100",
                                   bg=BG_MAIN, fg=BLUE,
                                   font=("Segoe UI", 16, "bold"))
        self.score_lbl.pack(side="left", padx=(0, 12))
        slider = ttk.Scale(score_frame, from_=0, to=100,
                           variable=self.score_var, orient="horizontal",
                           command=lambda v: self.score_lbl.config(
                               text=f"{int(float(v))}/100"))
        slider.pack(side="left", fill="x", expand=True)

        # Grade letter
        tk.Label(f, text="Grade", bg=BG_MAIN, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))
        self.grade_var = tk.StringVar(value=old_grade)
        ttk.Combobox(f, textvariable=self.grade_var,
                     values=["A+","A","A-","B+","B","B-",
                             "C+","C","C-","D","F",
                             "Excellent","Good","Satisfactory","Pass","Fail"],
                     width=20).pack(anchor="w", pady=(4, 10))

        # Comment
        tk.Label(f, text="Feedback comment", bg=BG_MAIN, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.comment = tk.Text(f, height=4, bg=BG_WHITE, fg=DARK,
                               font=("Segoe UI", 10), relief="solid",
                               padx=8, pady=6,
                               highlightthickness=1,
                               highlightbackground=BORDER)
        self.comment.pack(fill="x", pady=(4, 14))
        if old_comment:
            self.comment.insert("1.0", old_comment)

        bf = tk.Frame(f, bg=BG_MAIN)
        bf.pack()
        tk.Button(bf, text="Save Grade", command=self._save,
                  bg=GREEN, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"),
                  padx=14, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(bf, text="Cancel", command=self.destroy,
                  bg="#95a5a6", fg=WHITE, relief="flat",
                  font=("Segoe UI", 10),
                  padx=14, pady=5).pack(side="left")

    def _save(self):
        score   = int(self.score_var.get())
        grade   = self.grade_var.get().strip()
        comment = self.comment.get("1.0", "end").strip()
        query("""UPDATE milestones SET final_score=%s, grade=%s, supervisor_comment=%s
                 WHERE milestone_id=%s""",
              (score, grade or None, comment or None, self.mid))
        notify("student", self.st_id, "milestone",
               "Final Thesis Graded",
               f"Your thesis received {score}/100 — Grade: {grade}")
        messagebox.showinfo("Saved", f"Grade saved: {score}/100 — {grade}")
        self.destroy()