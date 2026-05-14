# """
# pages/milestones.py
# Thesis progress tracker with 6-phase pipeline, donut chart,
# final submission upload, and grading by supervisor.
# CEN 302 Software Engineering | Group III | Epoka University
# """

# import os, shutil, uuid
# import tkinter as tk
# from tkinter import ttk, messagebox, filedialog
# from datetime import date, datetime, timedelta

# from database import query
# from auth import SESSION
# from ui import (BG_MAIN, BG_WHITE, BLUE, BLUE2, GREEN, GOLD_TILE, ORANGE,
#                 WHITE, MUTED, DARK, BORDER, SUCCESS, DANGER, WARNING,
#                 TEXT2, style_entry, card_frame, page_header, ScrollFrame)

# UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # ── The 6 thesis phases (fixed order) ────────────────────────
# PHASES = [
#     "Abstract",
#     "Introduction",
#     "Literature Review",
#     "Methodology",
#     "Results",
#     "Conclusion & Final",
# ]
# PHASE_COLORS = [BLUE, "#8e44ad", GOLD_TILE, ORANGE, GREEN, "#27ae60"]


# def notify(user_role, user_id, ntype, title, message):
#     try:
#         query("""INSERT INTO notifications (user_role,user_id,type,title,message)
#                  VALUES (%s,%s,%s,%s,%s)""",
#               (user_role, user_id, ntype, title, message))
#     except Exception:
#         pass


# # ─── Ensure DB columns exist (runs silently) ─────────────────
# def _ensure_columns():
#     try:
#         query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS progress_pct INT NOT NULL DEFAULT 0")
#         query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS supervisor_comment TEXT DEFAULT NULL")
#         query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS grade VARCHAR(10) DEFAULT NULL")
#         query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS phase_index INT NOT NULL DEFAULT 0")
#         query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS phase_status VARCHAR(20) DEFAULT 'Not Started'")
#         query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS final_file_path VARCHAR(500) DEFAULT NULL")
#         query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS final_file_name VARCHAR(255) DEFAULT NULL")
#         query("ALTER TABLE milestones ADD COLUMN IF NOT EXISTS final_score INT DEFAULT NULL")
#     except Exception:
#         pass

# _ensure_columns()


# # ─── Get or create milestone row for a student ───────────────
# def get_or_create_milestone(student_id, supervisor_id):
#     row = query("SELECT * FROM milestones WHERE student_id=%s ORDER BY milestone_id ASC",
#                 (student_id,), one=True)
#     if not row:
#         mid = query("""INSERT INTO milestones
#                        (supervisor_id, student_id, title, due_date, status, progress_pct)
#                        VALUES (%s,%s,'Thesis Progress',CURDATE(),'In Progress',0)""",
#                     (supervisor_id, student_id))
#         row = query("SELECT * FROM milestones WHERE milestone_id=%s", (mid,), one=True)
#     return row


# # ── Donut chart ───────────────────────────────────────────────
# def draw_donut(canvas, pct, color=GREEN, size=160):
#     canvas.delete("all")
#     cx = cy = size // 2
#     r  = size // 2 - 10
#     canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
#                        outline="#e0e0e0", width=18, fill="")
#     if pct > 0:
#         import math
#         extent = min(359.9, pct / 100 * 359.9)
#         canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
#                           start=90, extent=-extent,
#                           style="arc", outline=color, width=18)
#     canvas.create_text(cx, cy - 10, text=f"{pct}%",
#                        font=("Segoe UI", 20, "bold"), fill=DARK)
#     canvas.create_text(cx, cy + 14, text="Complete",
#                        font=("Segoe UI", 9), fill=MUTED)


# # ════════════════════════════════════════════════════════════
# #  STUDENT VIEW
# # ════════════════════════════════════════════════════════════
# class StudentMilestones(tk.Frame):
#     def __init__(self, parent):
#         super().__init__(parent, bg=BG_MAIN)
#         page_header(self, "Thesis Progress", "Track your thesis phases and submit your final work")
#         self._build()

#     def _build(self):
#         try:
#             self._build_inner()
#         except Exception as e:
#             import traceback
#             tk.Label(self, text=f"Error loading milestones:\n{e}",
#                      bg=BG_MAIN, fg=DANGER,
#                      font=("Segoe UI", 10),
#                      wraplength=600, justify="left").pack(pady=20, padx=20)
#             traceback.print_exc()

#     def _build_inner(self):
#         sid = SESSION["user_id"]
#         # Get supervisor
#         stu = query("SELECT supervisor_id FROM students WHERE student_id=%s", (sid,), one=True)
#         if not stu or not stu["supervisor_id"]:
#             tk.Label(self, text="No supervisor assigned yet. Contact admin.",
#                      bg=BG_MAIN, fg=WARNING,
#                      font=("Segoe UI", 12)).pack(pady=40)
#             return

#         sup_id = stu["supervisor_id"]
#         row    = get_or_create_milestone(sid, sup_id)
#         mid    = row["milestone_id"]

#         # Phase statuses stored as pipe-separated string in phase_status
#         # e.g. "Done|In Progress|Not Started|Not Started|Not Started|Not Started"
#         raw_phases = (row.get("phase_status") or "")
#         phase_list = raw_phases.split("|") if raw_phases and "|" in raw_phases else ["Not Started"] * 6
#         while len(phase_list) < 6:
#             phase_list.append("Not Started")

#         # Compute overall %
#         done_count = sum(1 for p in phase_list if p == "Done")
#         pct = int(done_count / 6 * 100)

#         sf = ScrollFrame(self, bg=BG_MAIN)
#         sf.pack(fill="both", expand=True)
#         inner = sf.inner

#         # ── Top row: donut + submission deadline ──────────────
#         top = tk.Frame(inner, bg=BG_MAIN)
#         top.pack(fill="x", padx=20, pady=(10, 0))

#         # Donut
#         donut_card = card_frame(top, padx=20, pady=16)
#         donut_card.pack(side="left", padx=(0, 12))
#         tk.Label(donut_card, text="Overall Progress",
#                  bg=BG_WHITE, fg=DARK,
#                  font=("Segoe UI", 11, "bold")).pack()
#         c = tk.Canvas(donut_card, width=160, height=160,
#                       bg=BG_WHITE, highlightthickness=0)
#         c.pack(pady=8)
#         draw_donut(c, pct)
#         tk.Label(donut_card, text=f"{done_count} of 6 phases complete",
#                  bg=BG_WHITE, fg=MUTED,
#                  font=("Segoe UI", 9)).pack()

#         # Deadline info
#         dl = query("""SELECT d.due_date FROM deadlines d
#                       JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
#                       WHERE da.student_id=%s ORDER BY d.due_date ASC LIMIT 1""", (sid,), one=True)
#         info_card = card_frame(top, padx=20, pady=16)
#         info_card.pack(side="left", fill="both", expand=True)
#         tk.Label(info_card, text="Final Submission Deadline",
#                  bg=BG_WHITE, fg=DARK,
#                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
#         if dl:
#             days_left = (dl["due_date"] - date.today()).days
#             color = DANGER if days_left <= 1 else (WARNING if days_left <= 7 else GREEN)
#             tk.Label(info_card, text=str(dl["due_date"]),
#                      bg=BG_WHITE, fg=color,
#                      font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(8, 0))
#             if days_left < 0:
#                 msg = "OVERDUE!"
#             elif days_left == 0:
#                 msg = "Due TODAY!"
#             elif days_left == 1:
#                 msg = "Due TOMORROW!"
#             else:
#                 msg = f"{days_left} days remaining"
#             tk.Label(info_card, text=msg, bg=BG_WHITE, fg=color,
#                      font=("Segoe UI", 10, "bold")).pack(anchor="w")
#         else:
#             tk.Label(info_card, text="No deadline set yet",
#                      bg=BG_WHITE, fg=MUTED,
#                      font=("Segoe UI", 13)).pack(anchor="w", pady=8)

#         # ── 6-phase pipeline ──────────────────────────────────
#         ph_card = card_frame(inner, padx=16, pady=16)
#         ph_card.pack(fill="x", padx=20, pady=14)
#         tk.Label(ph_card, text="Thesis Phases",
#                  bg=BG_WHITE, fg=DARK,
#                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 12))

#         # Determine which phase is unlocked
#         # A phase is unlocked if all previous phases are "Done"
#         def is_unlocked(idx):
#             if idx == 0:
#                 return True
#             return all(phase_list[i] == "Done" for i in range(idx))

#         pipeline = tk.Frame(ph_card, bg=BG_WHITE)
#         pipeline.pack(fill="x")

#         for i, (phase, color) in enumerate(zip(PHASES, PHASE_COLORS)):
#             status   = phase_list[i]
#             unlocked = is_unlocked(i)

#             col = tk.Frame(pipeline, bg=BG_WHITE)
#             col.grid(row=0, column=i, padx=4, sticky="nsew")
#             pipeline.columnconfigure(i, weight=1)

#             # Phase box
#             box_color = color if status == "Done" else (
#                         BLUE if status == "In Progress" else "#bdc3c7")
#             box = tk.Frame(col, bg=box_color, height=70,
#                            highlightthickness=1,
#                            highlightbackground=BORDER)
#             box.pack(fill="x")
#             box.pack_propagate(False)
#             tk.Label(box, text=phase, bg=box_color, fg=WHITE,
#                      font=("Segoe UI", 8, "bold"),
#                      wraplength=90, justify="center").pack(expand=True)

#             # Status label
#             tk.Label(col, text=status, bg=BG_WHITE,
#                      fg=GREEN if status == "Done" else (
#                         BLUE if status == "In Progress" else MUTED),
#                      font=("Segoe UI", 8, "bold")).pack(pady=(4, 2))

#             # Dropdown (only if unlocked and not done)
#             if unlocked and status != "Done":
#                 var = tk.StringVar(value=status)
#                 opts = ["Not Started", "In Progress", "Done"]
#                 # Can only mark Done if this is the last one or previous is done
#                 cb = ttk.Combobox(col, textvariable=var,
#                                   values=opts, state="readonly", width=12)
#                 cb.pack()
#                 cb.bind("<<ComboboxSelected>>",
#                         lambda e, idx=i, v=var, pl=phase_list, m=mid, s=sid:
#                         self._update_phase(m, s, idx, v.get(), pl))
#             elif not unlocked:
#                 tk.Label(col, text="🔒 Locked", bg=BG_WHITE, fg=MUTED,
#                          font=("Segoe UI", 8)).pack()
#             else:
#                 tk.Label(col, text="✓ Done", bg=BG_WHITE, fg=GREEN,
#                          font=("Segoe UI", 8, "bold")).pack()

#             # Arrow between phases
#             if i < 5:
#                 tk.Label(pipeline, text="→", bg=BG_WHITE, fg=MUTED,
#                          font=("Segoe UI", 14)).grid(row=0, column=i,
#                                                       sticky="e", padx=(0, 0))

#         # ── Final submission ──────────────────────────────────
#         final_card = card_frame(inner, padx=16, pady=16)
#         final_card.pack(fill="x", padx=20, pady=(0, 14))
#         tk.Label(final_card, text="Final Submission",
#                  bg=BG_WHITE, fg=DARK,
#                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

#         all_done    = all(p == "Done" for p in phase_list)
#         submitted   = bool(row.get("final_file_name"))   # True once submitted
#         graded      = row.get("final_score") is not None

#         if not all_done:
#             # Phases not complete yet
#             tk.Label(final_card,
#                      text="⚠  Complete all 6 phases before submitting your final thesis.",
#                      bg=BG_WHITE, fg=WARNING,
#                      font=("Segoe UI", 10)).pack(anchor="w")

#         elif not submitted:
#             # All phases done — show upload + submit
#             tk.Label(final_card,
#                      text="All phases complete! Choose your thesis file then click Submit.",
#                      bg=BG_WHITE, fg=GREEN,
#                      font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

#             # File picker state
#             self._chosen_path  = tk.StringVar(value="")
#             self._chosen_label = tk.Label(final_card,
#                                           text="No file chosen",
#                                           bg=BG_WHITE, fg=MUTED,
#                                           font=("Segoe UI", 9))
#             self._chosen_label.pack(anchor="w", pady=(0, 6))

#             btn_row = tk.Frame(final_card, bg=BG_WHITE)
#             btn_row.pack(anchor="w")

#             tk.Button(btn_row, text="📁 Choose File (PDF / DOCX)",
#                       command=lambda: self._choose_file(),
#                       bg="#ecf0f1", fg=DARK, relief="flat",
#                       font=("Segoe UI", 10), padx=10, pady=6).pack(side="left", padx=(0, 10))

#             self._submit_btn = tk.Button(btn_row, text="✔ Submit Final Thesis",
#                       command=lambda m=mid, s=sup_id: self._submit_final(m, s),
#                       bg=GREEN, fg=WHITE, relief="flat",
#                       font=("Segoe UI", 10, "bold"), padx=14, pady=6,
#                       state="disabled")
#             self._submit_btn.pack(side="left")

#             tk.Label(final_card,
#                      text="⚠  Once submitted you cannot upload again.",
#                      bg=BG_WHITE, fg=DANGER,
#                      font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))

#         else:
#             # Already submitted — locked
#             lock_f = tk.Frame(final_card, bg="#f0fdf4",
#                               highlightthickness=1, highlightbackground=GREEN)
#             lock_f.pack(fill="x", pady=(0, 10))
#             tk.Label(lock_f,
#                      text=f"✓  Submitted: {row['final_file_name']}",
#                      bg="#f0fdf4", fg=GREEN,
#                      font=("Segoe UI", 11, "bold"),
#                      padx=12, pady=8).pack(anchor="w")
#             tk.Label(lock_f,
#                      text="Submission is closed. Awaiting supervisor grade.",
#                      bg="#f0fdf4", fg=MUTED,
#                      font=("Segoe UI", 9),
#                      padx=12, pady=4).pack(anchor="w", pady=(0, 8))

#             # Show grade if available
#             if graded:
#                 grade = row.get("grade") or ""
#                 gf = tk.Frame(final_card, bg=BG_WHITE)
#                 gf.pack(anchor="w", pady=(6, 0))
#                 tk.Label(gf, text=f"  Score: {row['final_score']}/100  ",
#                          bg=BLUE, fg=WHITE,
#                          font=("Segoe UI", 13, "bold"),
#                          padx=12, pady=6).pack(side="left", padx=(0, 8))
#                 if grade:
#                     gc = GREEN if grade in ("A","A+","A-","Excellent") else (
#                          DANGER if grade in ("F","Fail") else GOLD_TILE)
#                     tk.Label(gf, text=f"  Grade: {grade}  ",
#                              bg=gc, fg=WHITE,
#                              font=("Segoe UI", 13, "bold"),
#                              padx=12, pady=6).pack(side="left")
#                 if row.get("supervisor_comment"):
#                     tk.Label(final_card,
#                              text=f"Supervisor feedback: {row['supervisor_comment']}",
#                              bg="#eaf4fb", fg=DARK,
#                              font=("Segoe UI", 10),
#                              wraplength=540, padx=12, pady=8).pack(fill="x", pady=(8, 0))
#             else:
#                 tk.Label(final_card,
#                          text="⏳  Waiting for supervisor to grade your submission...",
#                          bg=BG_WHITE, fg=MUTED,
#                          font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 0))

#     def _update_phase(self, mid, sid, idx, new_status, phase_list):
#         phase_list[idx] = new_status
#         new_str = "|".join(phase_list)
#         done_count = sum(1 for p in phase_list if p == "Done")
#         pct = int(done_count / 6 * 100)
#         status = "Completed" if pct == 100 else "In Progress"
#         query("""UPDATE milestones SET phase_status=%s, progress_pct=%s, status=%s
#                  WHERE milestone_id=%s""",
#               (new_str, pct, status, mid))
#         # Rebuild
#         for w in self.winfo_children():
#             w.destroy()
#         page_header(self, "Thesis Progress", "Track your thesis phases and submit your final work")
#         self._build()

#     def _choose_file(self):
#         """Let student pick a file — enables the Submit button."""
#         path = filedialog.askopenfilename(
#             filetypes=[("Documents", "*.pdf *.docx"), ("All files", "*.*")])
#         if not path:
#             return
#         self._chosen_path.set(path)
#         self._chosen_label.config(
#             text=f"Selected: {os.path.basename(path)}", fg=BLUE)
#         self._submit_btn.config(state="normal")

#     def _submit_final(self, mid, sup_id):
#         """Copy file, lock submission, notify supervisor."""
#         path = self._chosen_path.get()
#         if not path or not os.path.exists(path):
#             messagebox.showerror("No File", "Please choose a file first.")
#             return
#         if not messagebox.askyesno(
#                 "Confirm Submission",
#                 "Once submitted you CANNOT upload again.\n\nSubmit your final thesis now?"):
#             return
#         ext  = path.rsplit(".", 1)[-1].lower()
#         safe = f"final_{SESSION['user_id']}_{uuid.uuid4().hex[:8]}.{ext}"
#         shutil.copy2(path, os.path.join(UPLOAD_FOLDER, safe))
#         fname = os.path.basename(path)
#         query("""UPDATE milestones
#                  SET final_file_path=%s, final_file_name=%s, status='Completed'
#                  WHERE milestone_id=%s""",
#               (safe, fname, mid))
#         query("""UPDATE deadline_assignments da
#                  JOIN deadlines d ON da.deadline_id=d.deadline_id
#                  JOIN students st ON da.student_id=st.student_id
#                  SET da.submitted_at=NOW()
#                  WHERE st.supervisor_id=%s AND da.student_id=%s""",
#               (sup_id, SESSION["user_id"]))
#         notify("supervisor", sup_id, "submission",
#                "Final Thesis Submitted",
#                f"{SESSION['name']} submitted their final thesis: {fname}")
#         messagebox.showinfo("Submitted",
#                             f"'{fname}' submitted successfully!\n\n"
#                             "Your submission is now closed. "
#                             "Awaiting supervisor grade.")
#         for w in self.winfo_children():
#             w.destroy()
#         page_header(self, "Thesis Progress",
#                     "Track your thesis phases and submit your final work")
#         self._build()


# # ════════════════════════════════════════════════════════════
# #  SUPERVISOR VIEW
# # ════════════════════════════════════════════════════════════
# class SupervisorMilestones(tk.Frame):
#     def __init__(self, parent):
#         super().__init__(parent, bg=BG_MAIN)
#         page_header(self, "Thesis Progress", "Monitor students, set deadlines and grade submissions")
#         self._sel_student_id = None
#         self._build()

#     def _build(self):
#         sup_id   = SESSION["user_id"]
#         students = query("SELECT student_id, full_name FROM students WHERE supervisor_id=%s",
#                          (sup_id,)) or []
#         if not students:
#             tk.Label(self, text="No students assigned yet.",
#                      bg=BG_MAIN, fg=MUTED,
#                      font=("Segoe UI", 12)).pack(pady=40)
#             return
#         self._students  = students
#         self._stu_map   = {s["full_name"]: s["student_id"] for s in students}
#         self._sup_id    = sup_id

#         # ── Student selector ──────────────────────────────────
#         sel_card = card_frame(self, padx=16, pady=12)
#         sel_card.pack(fill="x", padx=20, pady=(12, 0))
#         sf = tk.Frame(sel_card, bg=BG_WHITE)
#         sf.pack(fill="x")
#         tk.Label(sf, text="Select student:",
#                  bg=BG_WHITE, fg=DARK,
#                  font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
#         self._stu_var = tk.StringVar(value=students[0]["full_name"])
#         cb = ttk.Combobox(sf, textvariable=self._stu_var,
#                           values=[s["full_name"] for s in students],
#                           state="readonly", width=28)
#         cb.pack(side="left")
#         tk.Button(sf, text="Load Student",
#                   command=self._load_student,
#                   bg=BLUE, fg=WHITE, relief="flat",
#                   font=("Segoe UI", 10, "bold"),
#                   padx=12, pady=4).pack(side="left", padx=8)

#         # Content area — filled when student selected
#         self._content = tk.Frame(self, bg=BG_MAIN)
#         self._content.pack(fill="both", expand=True, padx=20, pady=10)
#         # Auto-load first student
#         self._load_student()

#     def _load_student(self):
#         for w in self._content.winfo_children():
#             w.destroy()
#         sname  = self._stu_var.get()
#         st_id  = self._stu_map.get(sname)
#         if not st_id:
#             return
#         self._sel_student_id = st_id
#         sup_id = self._sup_id
#         row    = get_or_create_milestone(st_id, sup_id)
#         mid    = row["milestone_id"]

#         raw    = row.get("phase_status") or ""
#         phases = raw.split("|") if "|" in raw else ["Not Started"] * 6
#         while len(phases) < 6:
#             phases.append("Not Started")
#         done   = sum(1 for p in phases if p == "Done")
#         pct    = int(done / 6 * 100)
#         bar_col= GREEN if pct == 100 else (GOLD_TILE if pct > 0 else "#bdc3c7")

#         sf = ScrollFrame(self._content, bg=BG_MAIN)
#         sf.pack(fill="both", expand=True)
#         inner = sf.inner

#         # ── Progress overview card ────────────────────────────
#         pc = card_frame(inner, padx=16, pady=14)
#         pc.pack(fill="x", pady=(0, 10))
#         hdr = tk.Frame(pc, bg=BG_WHITE)
#         hdr.pack(fill="x")
#         tk.Label(hdr, text=f"👤  {sname}",
#                  bg=BG_WHITE, fg=DARK,
#                  font=("Segoe UI", 13, "bold")).pack(side="left")
#         tk.Label(hdr, text=f"{pct}%  ({done}/6 phases complete)",
#                  bg=BG_WHITE, fg=bar_col,
#                  font=("Segoe UI", 11, "bold")).pack(side="right")
#         pb = tk.Frame(pc, bg=BORDER, height=10)
#         pb.pack(fill="x", pady=(8, 6))
#         if pct > 0:
#             tk.Frame(pc, bg=bar_col, height=10).place(
#                 in_=pb, relwidth=pct/100, relheight=1)

#         # Phase chips
#         chip_f = tk.Frame(pc, bg=BG_WHITE)
#         chip_f.pack(fill="x", pady=(0, 4))
#         for ph, st in zip(PHASES, phases):
#             col = GREEN if st == "Done" else (BLUE if st == "In Progress" else "#bdc3c7")
#             tk.Label(chip_f, text=ph[:7],
#                      bg=col, fg=WHITE,
#                      font=("Segoe UI", 8, "bold"),
#                      padx=5, pady=2).pack(side="left", padx=2)

#         # ── Deadline for this student ─────────────────────────
#         dc = card_frame(inner, padx=16, pady=14)
#         dc.pack(fill="x", pady=(0, 10))
#         tk.Label(dc, text="Submission Deadline for this Student",
#                  bg=BG_WHITE, fg=DARK,
#                  font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

#         dl = query("""SELECT d.deadline_id, d.due_date FROM deadlines d
#                       JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
#                       WHERE da.student_id=%s ORDER BY d.due_date ASC LIMIT 1""",
#                    (st_id,), one=True)

#         dl_row = tk.Frame(dc, bg=BG_WHITE)
#         dl_row.pack(fill="x")
#         if dl:
#             days = (dl["due_date"] - date.today()).days
#             dcol = DANGER if days <= 1 else (WARNING if days <= 7 else GREEN)
#             tk.Label(dl_row, text=f"Current: {dl['due_date']}",
#                      bg=BG_WHITE, fg=dcol,
#                      font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 14))

#         tk.Label(dl_row, text="New date:",
#                  bg=BG_WHITE, fg=MUTED,
#                  font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
#         self._dl_var = tk.StringVar(value=str(dl["due_date"]) if dl else "")
#         dl_e = tk.Entry(dl_row, textvariable=self._dl_var, width=14)
#         style_entry(dl_e)
#         dl_e.pack(side="left", ipady=5, padx=(0, 8))
#         tk.Button(dl_row,
#                   text="Set" if not dl else "Update",
#                   command=lambda s=st_id, d=dl: self._save_deadline(s, d),
#                   bg=BLUE, fg=WHITE, relief="flat",
#                   font=("Segoe UI", 10, "bold"),
#                   padx=10, pady=4).pack(side="left")

#         # ── Final submission review ───────────────────────────
#         rc = card_frame(inner, padx=16, pady=14)
#         rc.pack(fill="x", pady=(0, 10))
#         tk.Label(rc, text="Final Submission",
#                  bg=BG_WHITE, fg=DARK,
#                  font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

#         if row.get("final_file_name"):
#             # File submitted
#             ff = tk.Frame(rc, bg="#f0fdf4",
#                           highlightthickness=1, highlightbackground=GREEN)
#             ff.pack(fill="x", pady=(0, 10))
#             # File name + Open button on same row
#             ff_row = tk.Frame(ff, bg="#f0fdf4")
#             ff_row.pack(fill="x", padx=10, pady=6)
#             tk.Label(ff_row, text=f"✓  {row['final_file_name']}",
#                      bg="#f0fdf4", fg=GREEN,
#                      font=("Segoe UI", 10, "bold")).pack(side="left")
#             # Open document button
#             file_path = os.path.join(UPLOAD_FOLDER, row.get("final_file_path",""))
#             tk.Button(ff_row, text="📄 Open Document",
#                       command=lambda fp=file_path: self._open_doc(fp),
#                       bg=BLUE, fg=WHITE, relief="flat",
#                       font=("Segoe UI", 9, "bold"),
#                       padx=10, pady=3).pack(side="right")

#             # Grade display
#             if row.get("final_score") is not None:
#                 gf = tk.Frame(rc, bg=BG_WHITE)
#                 gf.pack(anchor="w", pady=(0, 8))
#                 tk.Label(gf, text=f"  Score: {row['final_score']}/100  ",
#                          bg=BLUE, fg=WHITE,
#                          font=("Segoe UI", 11, "bold"),
#                          padx=10, pady=4).pack(side="left", padx=(0, 8))
#                 if row.get("grade"):
#                     gc = GREEN if row["grade"] in ("A","A+","A-","Excellent") else (
#                          DANGER if row["grade"] in ("F","Fail") else GOLD_TILE)
#                     tk.Label(gf, text=f"  Grade: {row['grade']}  ",
#                              bg=gc, fg=WHITE,
#                              font=("Segoe UI", 11, "bold"),
#                              padx=10, pady=4).pack(side="left")
#                 if row.get("supervisor_comment"):
#                     tk.Label(rc,
#                              text=f"Your feedback: {row['supervisor_comment']}",
#                              bg=BG_WHITE, fg=DARK,
#                              font=("Segoe UI", 9),
#                              wraplength=520).pack(anchor="w", pady=(0, 8))

#             tk.Button(rc,
#                       text="✎ Grade Final Submission" if row.get("final_score") is None else "✎ Update Grade",
#                       command=lambda m=mid, s=st_id: self._grade_dialog(m, s),
#                       bg=GOLD_TILE, fg=WHITE, relief="flat",
#                       font=("Segoe UI", 10, "bold"),
#                       padx=12, pady=6).pack(anchor="w")
#         else:
#             tk.Label(rc,
#                      text="⏳  Student has not submitted yet.",
#                      bg=BG_WHITE, fg=MUTED,
#                      font=("Segoe UI", 10)).pack(anchor="w")

#     def _open_doc(self, file_path):
#         """Open the submitted thesis document with the system viewer."""
#         if not file_path or not os.path.exists(file_path):
#             messagebox.showerror("File Not Found",
#                                  f"Cannot find the file:\n{file_path}\n\n"
#                                  "Make sure the uploads folder is intact.")
#             return
#         try:
#             import sys, subprocess
#             if sys.platform == "win32":
#                 os.startfile(file_path)
#             elif sys.platform == "darwin":
#                 subprocess.run(["open", file_path])
#             else:
#                 subprocess.run(["xdg-open", file_path])
#         except Exception as e:
#             messagebox.showerror("Error", f"Could not open file:\n{e}")

#     def _save_deadline(self, st_id, dl):
#         date_str = self._dl_var.get().strip()
#         if not date_str:
#             messagebox.showwarning("Missing", "Please enter a date.")
#             return
#         sup_id = self._sup_id
#         if dl:
#             query("UPDATE deadlines SET due_date=%s WHERE deadline_id=%s",
#                   (date_str, dl["deadline_id"]))
#             notify("student", st_id, "deadline",
#                    "Deadline Updated",
#                    f"Your final submission deadline was updated to {date_str}")
#             messagebox.showinfo("Updated", f"Deadline updated to {date_str}")
#         else:
#             did = query("""INSERT INTO deadlines (supervisor_id, title, due_date, description)
#                            VALUES (%s,'Final Thesis Submission',%s,
#                            'Submit your final thesis document')""",
#                         (sup_id, date_str))
#             query("INSERT IGNORE INTO deadline_assignments (deadline_id, student_id) VALUES (%s,%s)",
#                   (did, st_id))
#             notify("student", st_id, "deadline",
#                    "Submission Deadline Set",
#                    f"Your final thesis submission deadline is {date_str}")
#             messagebox.showinfo("Set", f"Deadline set to {date_str}")
#         self._load_student()

#     def _grade_dialog(self, mid, st_id):
#         dlg = FinalGradeDialog(self.master, mid, st_id)
#         self.wait_window(dlg)
#         self._load_student()


# class FinalGradeDialog(tk.Toplevel):
#     """Dialog for supervisor to give score/100 and grade for final submission."""
#     def __init__(self, master, mid, st_id):
#         super().__init__(master)
#         self.mid   = mid
#         self.st_id = st_id
#         self.title("Grade Final Submission")
#         self.geometry("440x340")
#         self.configure(bg=BG_MAIN)
#         self.resizable(False, False)
#         self.grab_set()
#         row = query("SELECT final_score, grade, supervisor_comment FROM milestones WHERE milestone_id=%s",
#                     (mid,), one=True) or {}
#         self._build(row.get("final_score") or 0,
#                     row.get("grade") or "",
#                     row.get("supervisor_comment") or "")

#     def _build(self, old_score, old_grade, old_comment):
#         f = tk.Frame(self, bg=BG_MAIN, padx=24, pady=20)
#         f.pack(fill="both", expand=True)
#         tk.Label(f, text="Grade Final Submission",
#                  bg=BG_MAIN, fg=DARK,
#                  font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 16))

#         # Score out of 100
#         tk.Label(f, text="Score (0–100)", bg=BG_MAIN, fg=MUTED,
#                  font=("Segoe UI", 9)).pack(anchor="w")
#         self.score_var = tk.IntVar(value=old_score)
#         score_frame = tk.Frame(f, bg=BG_MAIN)
#         score_frame.pack(fill="x", pady=(4, 4))
#         self.score_lbl = tk.Label(score_frame, text=f"{old_score}/100",
#                                    bg=BG_MAIN, fg=BLUE,
#                                    font=("Segoe UI", 16, "bold"))
#         self.score_lbl.pack(side="left", padx=(0, 12))
#         slider = ttk.Scale(score_frame, from_=0, to=100,
#                            variable=self.score_var, orient="horizontal",
#                            command=lambda v: self.score_lbl.config(
#                                text=f"{int(float(v))}/100"))
#         slider.pack(side="left", fill="x", expand=True)

#         # Grade letter
#         tk.Label(f, text="Grade", bg=BG_MAIN, fg=MUTED,
#                  font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))
#         self.grade_var = tk.StringVar(value=old_grade)
#         ttk.Combobox(f, textvariable=self.grade_var,
#                      values=["A+","A","A-","B+","B","B-",
#                              "C+","C","C-","D","F",
#                              "Excellent","Good","Satisfactory","Pass","Fail"],
#                      width=20).pack(anchor="w", pady=(4, 10))

#         # Comment
#         tk.Label(f, text="Feedback comment", bg=BG_MAIN, fg=MUTED,
#                  font=("Segoe UI", 9)).pack(anchor="w")
#         self.comment = tk.Text(f, height=4, bg=BG_WHITE, fg=DARK,
#                                font=("Segoe UI", 10), relief="solid",
#                                padx=8, pady=6,
#                                highlightthickness=1,
#                                highlightbackground=BORDER)
#         self.comment.pack(fill="x", pady=(4, 14))
#         if old_comment:
#             self.comment.insert("1.0", old_comment)

#         bf = tk.Frame(f, bg=BG_MAIN)
#         bf.pack()
#         tk.Button(bf, text="Save Grade", command=self._save,
#                   bg=GREEN, fg=WHITE, relief="flat",
#                   font=("Segoe UI", 10, "bold"),
#                   padx=14, pady=5).pack(side="left", padx=(0, 8))
#         tk.Button(bf, text="Cancel", command=self.destroy,
#                   bg="#95a5a6", fg=WHITE, relief="flat",
#                   font=("Segoe UI", 10),
#                   padx=14, pady=5).pack(side="left")

#     def _save(self):
#         score   = int(self.score_var.get())
#         grade   = self.grade_var.get().strip()
#         comment = self.comment.get("1.0", "end").strip()
#         query("""UPDATE milestones SET final_score=%s, grade=%s, supervisor_comment=%s
#                  WHERE milestone_id=%s""",
#               (score, grade or None, comment or None, self.mid))
#         notify("student", self.st_id, "milestone",
#                "Final Thesis Graded",
#                f"Your thesis received {score}/100 — Grade: {grade}")
#         messagebox.showinfo("Saved", f"Grade saved: {score}/100 — {grade}")
#         self.destroy()



"""
pages/milestones.py
Thesis progress tracker with 6-phase pipeline, improved donut chart,
segmented phase bar, sequential phase locking, final submission upload,
and grading by supervisor (final submission only).
CEN 302 Software Engineering | Group III | Epoka University
"""

import os, shutil, uuid, math
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

PHASES = [
    "Abstract",
    "Introduction",
    "Literature Review",
    "Methodology",
    "Results",
    "Conclusion & Final",
]
PHASE_COLORS = ["#2980b9", "#8e44ad", "#d4ac0d", "#e67e22", "#27ae60", "#1a6b3c"]
PHASE_SHORT  = ["Abstract", "Introduction", "Lit. Review", "Methodology", "Results", "Conclusion"]


def notify(user_role, user_id, ntype, title, message):
    try:
        query("""INSERT INTO notifications (user_role,user_id,type,title,message)
                 VALUES (%s,%s,%s,%s,%s)""",
              (user_role, user_id, ntype, title, message))
    except Exception:
        pass


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
        # deadline_assignments.submitted_at — used by deadlines page to show submission status
        query("ALTER TABLE deadline_assignments ADD COLUMN IF NOT EXISTS submitted_at DATETIME DEFAULT NULL")
    except Exception:
        pass

_ensure_columns()


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


def draw_donut(canvas, pct, color=None, size=180):
    if color is None:
        color = GREEN
    canvas.delete("all")
    cx = cy = size // 2
    r  = size // 2 - 16
    # Background ring
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                       outline="#e8e8e8", width=20, fill="")
    if pct > 0:
        extent = min(359.9, pct / 100 * 359.9)
        canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                          start=90, extent=-extent,
                          style="arc", outline=color, width=20)
    # Inner white fill for clean look
    inner_r = r - 14
    canvas.create_oval(cx-inner_r, cy-inner_r, cx+inner_r, cy+inner_r,
                       fill=BG_WHITE, outline="")
    canvas.create_text(cx, cy - 12, text=f"{pct}%",
                       font=("Segoe UI", 22, "bold"), fill=DARK)
    canvas.create_text(cx, cy + 12, text="Complete",
                       font=("Segoe UI", 10), fill=MUTED)


def draw_phase_bar(parent, phase_list):
    """Draw a single rectangle divided into 6 equal color-coded segments."""
    bar_outer = tk.Frame(parent, bg=BG_WHITE,
                         highlightthickness=1, highlightbackground=BORDER)
    bar_outer.pack(fill="x", pady=(8, 0))
    for i, (color, status) in enumerate(zip(PHASE_COLORS, phase_list)):
        if status == "Done":
            bg = color
            fg = WHITE
        elif status == "In Progress":
            bg = BLUE
            fg = WHITE
        else:
            bg = "#dde1e7"
            fg = "#888"
        seg = tk.Frame(bar_outer, bg=bg, height=38)
        seg.grid(row=0, column=i, sticky="nsew")
        bar_outer.columnconfigure(i, weight=1)
        seg.pack_propagate(False)
        tk.Label(seg, text=PHASE_SHORT[i], bg=bg, fg=fg,
                 font=("Segoe UI", 7, "bold"),
                 wraplength=70, justify="center").pack(expand=True)


# ════════════════════════════════════════════════════════════
#  STUDENT VIEW
# ════════════════════════════════════════════════════════════
class StudentMilestones(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)
        page_header(self, "Thesis Progress", "Track your thesis phases and submit your final work")
        self._build()

    def _build(self):
        try:
            self._build_inner()
        except Exception as e:
            import traceback
            tk.Label(self, text=f"Error loading milestones:\n{e}",
                     bg=BG_MAIN, fg=DANGER,
                     font=("Segoe UI", 10),
                     wraplength=600, justify="left").pack(pady=20, padx=20)
            traceback.print_exc()

    def _build_inner(self):
        sid = SESSION["user_id"]
        stu = query("SELECT supervisor_id FROM students WHERE student_id=%s", (sid,), one=True)
        if not stu or not stu["supervisor_id"]:
            tk.Label(self, text="No supervisor assigned yet. Contact admin.",
                     bg=BG_MAIN, fg=WARNING,
                     font=("Segoe UI", 12)).pack(pady=40)
            return

        sup_id = stu["supervisor_id"]
        row    = get_or_create_milestone(sid, sup_id)
        mid    = row["milestone_id"]

        raw_phases = (row.get("phase_status") or "")
        phase_list = raw_phases.split("|") if raw_phases and "|" in raw_phases else ["Not Started"] * 6
        while len(phase_list) < 6:
            phase_list.append("Not Started")

        done_count = sum(1 for p in phase_list if p == "Done")
        pct = int(done_count / 6 * 100)

        sf = ScrollFrame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        # ── Top row: donut + deadline ──────────────────────────
        top = tk.Frame(inner, bg=BG_MAIN)
        top.pack(fill="x", padx=20, pady=(10, 0))

        donut_card = card_frame(top, padx=20, pady=16)
        donut_card.pack(side="left", padx=(0, 12))
        tk.Label(donut_card, text="Overall Progress",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack()
        ring_color = GREEN if pct == 100 else (BLUE if pct > 0 else "#bdc3c7")
        c = tk.Canvas(donut_card, width=180, height=180, bg=BG_WHITE, highlightthickness=0)
        c.pack(pady=8)
        draw_donut(c, pct, color=ring_color)
        tk.Label(donut_card, text=f"{done_count} of 6 phases complete",
                 bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 9)).pack()

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
            dcol = DANGER if days_left <= 1 else (WARNING if days_left <= 7 else GREEN)
            tk.Label(info_card, text=str(dl["due_date"]),
                     bg=BG_WHITE, fg=dcol,
                     font=("Segoe UI", 22, "bold")).pack(anchor="w", pady=(8, 0))
            if days_left < 0:   msg = "OVERDUE!"
            elif days_left == 0: msg = "Due TODAY!"
            elif days_left == 1: msg = "⚠  Due TOMORROW — Upload your work!"
            else:               msg = f"{days_left} days remaining"
            tk.Label(info_card, text=msg, bg=BG_WHITE, fg=dcol,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w")
        else:
            tk.Label(info_card, text="No deadline set yet",
                     bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 13)).pack(anchor="w", pady=8)

        # ── Thesis Phases card ─────────────────────────────────
        ph_card = card_frame(inner, padx=16, pady=16)
        ph_card.pack(fill="x", padx=20, pady=14)
        tk.Label(ph_card, text="Thesis Phases",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 4))

        # Segmented rectangular progress bar
        draw_phase_bar(ph_card, phase_list)

        # Status labels below bar
        label_row = tk.Frame(ph_card, bg=BG_WHITE)
        label_row.pack(fill="x", pady=(3, 12))
        for i in range(6):
            s = phase_list[i]
            fg = GREEN if s == "Done" else (BLUE if s == "In Progress" else MUTED)
            icon = "✓" if s == "Done" else ("●" if s == "In Progress" else "○")
            lf = tk.Frame(label_row, bg=BG_WHITE)
            lf.grid(row=0, column=i, sticky="nsew")
            label_row.columnconfigure(i, weight=1)
            tk.Label(lf, text=f"{icon} {s}", bg=BG_WHITE, fg=fg,
                     font=("Segoe UI", 8, "bold"),
                     wraplength=80, justify="center").pack(expand=True)

        tk.Frame(ph_card, bg=BORDER, height=1).pack(fill="x", pady=(0, 10))
        tk.Label(ph_card, text="Update Phase Status:",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 6))

        def is_unlocked(idx):
            if idx == 0:
                return True
            return all(phase_list[i] == "Done" for i in range(idx))

        for i, (phase, color) in enumerate(zip(PHASES, PHASE_COLORS)):
            status   = phase_list[i]
            unlocked = is_unlocked(i)

            row_f = tk.Frame(ph_card, bg=BG_WHITE,
                             highlightthickness=1, highlightbackground="#ececec")
            row_f.pack(fill="x", pady=2)

            dot_color = color if status == "Done" else (BLUE if status == "In Progress" else "#bdc3c7")
            dot_f = tk.Frame(row_f, bg=dot_color, width=10, height=10)
            dot_f.pack(side="left", padx=(10, 8), pady=12)

            tk.Label(row_f, text=phase, bg=BG_WHITE, fg=DARK,
                     font=("Segoe UI", 10, "bold"), width=18, anchor="w").pack(side="left")

            if not unlocked:
                tk.Label(row_f, text="🔒  Complete previous phase first",
                         bg=BG_WHITE, fg=MUTED,
                         font=("Segoe UI", 9)).pack(side="left", padx=10)
            elif status == "Done":
                tk.Label(row_f, text="✓  Done",
                         bg=BG_WHITE, fg=GREEN,
                         font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)
            else:
                var = tk.StringVar(value=status)
                cb  = ttk.Combobox(row_f, textvariable=var,
                                   values=["Not Started", "In Progress", "Done"],
                                   state="readonly", width=15)
                cb.pack(side="left", padx=10, pady=6)
                cb.bind("<<ComboboxSelected>>",
                        lambda e, idx=i, v=var, pl=list(phase_list), m=mid, s=sid:
                        self._update_phase(m, s, idx, v.get(), pl))

        # ── Final Submission card ──────────────────────────────
        final_card = card_frame(inner, padx=16, pady=16)
        final_card.pack(fill="x", padx=20, pady=(0, 14))
        tk.Label(final_card, text="Final Submission",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        all_done  = all(p == "Done" for p in phase_list)
        submitted = bool(row.get("final_file_name"))
        graded    = row.get("final_score") is not None

        if not all_done:
            wf = tk.Frame(final_card, bg="#fff8e1",
                          highlightthickness=1, highlightbackground=WARNING)
            wf.pack(fill="x", pady=(0, 8))
            tk.Label(wf, text="⚠  Complete all 6 phases before submitting your final thesis.",
                     bg="#fff8e1", fg=WARNING,
                     font=("Segoe UI", 10), padx=12, pady=10).pack(anchor="w")

        elif not submitted:
            ok_f = tk.Frame(final_card, bg="#f0fdf4",
                            highlightthickness=1, highlightbackground=GREEN)
            ok_f.pack(fill="x", pady=(0, 10))
            tk.Label(ok_f,
                     text="✓  All phases complete! Upload your final thesis document below.",
                     bg="#f0fdf4", fg=GREEN,
                     font=("Segoe UI", 10, "bold"), padx=12, pady=10).pack(anchor="w")

            self._chosen_path  = tk.StringVar(value="")
            file_row = tk.Frame(final_card, bg=BG_WHITE)
            file_row.pack(fill="x", pady=(0, 6))
            self._chosen_label = tk.Label(file_row, text="No file chosen",
                                          bg=BG_WHITE, fg=MUTED,
                                          font=("Segoe UI", 9))
            self._chosen_label.pack(side="left", padx=(0, 10))

            btn_row = tk.Frame(final_card, bg=BG_WHITE)
            btn_row.pack(anchor="w")
            tk.Button(btn_row, text="📁  Choose File (PDF / DOCX)",
                      command=self._choose_file,
                      bg="#ecf0f1", fg=DARK, relief="flat",
                      font=("Segoe UI", 10), padx=12, pady=7).pack(side="left", padx=(0, 10))
            self._submit_btn = tk.Button(btn_row, text="✔  Submit Final Thesis",
                      command=lambda m=mid, s=sup_id: self._submit_final(m, s),
                      bg=GREEN, fg=WHITE, relief="flat",
                      font=("Segoe UI", 10, "bold"), padx=14, pady=7,
                      state="disabled")
            self._submit_btn.pack(side="left")
            tk.Label(final_card, text="⚠  Once submitted you cannot upload again.",
                     bg=BG_WHITE, fg=DANGER,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))

        else:
            lock_f = tk.Frame(final_card, bg="#f0fdf4",
                              highlightthickness=1, highlightbackground=GREEN)
            lock_f.pack(fill="x", pady=(0, 10))
            tk.Label(lock_f, text=f"✓  Submitted: {row['final_file_name']}",
                     bg="#f0fdf4", fg=GREEN,
                     font=("Segoe UI", 11, "bold"), padx=12, pady=8).pack(anchor="w")
            tk.Label(lock_f, text="Submission is closed. Awaiting supervisor grade.",
                     bg="#f0fdf4", fg=MUTED,
                     font=("Segoe UI", 9), padx=12, pady=4).pack(anchor="w", pady=(0, 8))

            if graded:
                grade = row.get("grade") or ""
                gf = tk.Frame(final_card, bg=BG_WHITE)
                gf.pack(anchor="w", pady=(6, 0))
                tk.Label(gf, text=f"  Score: {row['final_score']}/100  ",
                         bg=BLUE, fg=WHITE,
                         font=("Segoe UI", 13, "bold"), padx=12, pady=6).pack(side="left", padx=(0, 8))
                if grade:
                    gc = GREEN if grade in ("A", "A+", "A-", "Excellent") else (
                         DANGER if grade in ("F", "Fail") else GOLD_TILE)
                    tk.Label(gf, text=f"  Grade: {grade}  ",
                             bg=gc, fg=WHITE,
                             font=("Segoe UI", 13, "bold"), padx=12, pady=6).pack(side="left")
                if row.get("supervisor_comment"):
                    tk.Label(final_card,
                             text=f"Supervisor feedback: {row['supervisor_comment']}",
                             bg="#eaf4fb", fg=DARK, font=("Segoe UI", 10),
                             wraplength=540, padx=12, pady=8).pack(fill="x", pady=(8, 0))
            else:
                tk.Label(final_card,
                         text="⏳  Waiting for supervisor to grade your submission...",
                         bg=BG_WHITE, fg=MUTED,
                         font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 0))

    def _update_phase(self, mid, sid, idx, new_status, phase_list):
        phase_list[idx] = new_status
        new_str    = "|".join(phase_list)
        done_count = sum(1 for p in phase_list if p == "Done")
        pct        = int(done_count / 6 * 100)
        status     = "Completed" if pct == 100 else "In Progress"
        query("""UPDATE milestones SET phase_status=%s, progress_pct=%s, status=%s
                 WHERE milestone_id=%s""",
              (new_str, pct, status, mid))
        for w in self.winfo_children():
            w.destroy()
        page_header(self, "Thesis Progress", "Track your thesis phases and submit your final work")
        self._build()

    def _choose_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Documents", "*.pdf *.docx"), ("All files", "*.*")])
        if not path:
            return
        self._chosen_path.set(path)
        self._chosen_label.config(text=f"Selected: {os.path.basename(path)}", fg=BLUE)
        self._submit_btn.config(state="normal")

    def _submit_final(self, mid, sup_id):
        path = self._chosen_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("No File", "Please choose a file first.")
            return
        if not messagebox.askyesno("Confirm Submission",
                "Once submitted you CANNOT upload again.\n\nSubmit your final thesis now?"):
            return
        ext  = path.rsplit(".", 1)[-1].lower()
        safe = f"final_{SESSION['user_id']}_{uuid.uuid4().hex[:8]}.{ext}"
        shutil.copy2(path, os.path.join(UPLOAD_FOLDER, safe))
        fname = os.path.basename(path)
        query("""UPDATE milestones
                 SET final_file_path=%s, final_file_name=%s, status='Completed'
                 WHERE milestone_id=%s""", (safe, fname, mid))
        # Mark submitted_at in deadline_assignments (so deadlines page shows submitted status)
        try:
            query("""UPDATE deadline_assignments da
                     JOIN deadlines d ON da.deadline_id=d.deadline_id
                     SET da.submitted_at=NOW()
                     WHERE da.student_id=%s""",
                  (SESSION["user_id"],))
        except Exception:
            pass  # Column may not exist on older installs; milestone record is the source of truth
        notify("supervisor", sup_id, "submission",
               "Final Thesis Submitted",
               f"{SESSION['name']} submitted their final thesis: {fname}")
        messagebox.showinfo("Submitted",
                            f"'{fname}' submitted successfully!\n\n"
                            "Your submission is now closed. Awaiting supervisor grade.")
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
        page_header(self, "Thesis Progress", "Monitor students, set deadlines and grade submissions")
        self._sel_student_id = None
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
        self._students = students
        self._stu_map  = {s["full_name"]: s["student_id"] for s in students}
        self._sup_id   = sup_id

        sel_card = card_frame(self, padx=16, pady=12)
        sel_card.pack(fill="x", padx=20, pady=(12, 0))
        sf = tk.Frame(sel_card, bg=BG_WHITE)
        sf.pack(fill="x")
        tk.Label(sf, text="Select student:", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
        self._stu_var = tk.StringVar(value=students[0]["full_name"])
        cb = ttk.Combobox(sf, textvariable=self._stu_var,
                          values=[s["full_name"] for s in students],
                          state="readonly", width=28)
        cb.pack(side="left")
        tk.Button(sf, text="Load Student", command=self._load_student,
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=12, pady=4).pack(side="left", padx=8)

        self._content = tk.Frame(self, bg=BG_MAIN)
        self._content.pack(fill="both", expand=True, padx=20, pady=10)
        self._load_student()

    def _load_student(self):
        for w in self._content.winfo_children():
            w.destroy()
        sname  = self._stu_var.get()
        st_id  = self._stu_map.get(sname)
        if not st_id:
            return
        self._sel_student_id = st_id
        sup_id = self._sup_id
        row    = get_or_create_milestone(st_id, sup_id)
        mid    = row["milestone_id"]

        raw    = row.get("phase_status") or ""
        phases = raw.split("|") if "|" in raw else ["Not Started"] * 6
        while len(phases) < 6:
            phases.append("Not Started")
        done   = sum(1 for p in phases if p == "Done")
        pct    = int(done / 6 * 100)
        bar_col = GREEN if pct == 100 else (GOLD_TILE if pct > 0 else "#bdc3c7")

        sf = ScrollFrame(self._content, bg=BG_MAIN)
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        # Progress overview
        pc = card_frame(inner, padx=16, pady=14)
        pc.pack(fill="x", pady=(0, 10))
        hdr = tk.Frame(pc, bg=BG_WHITE)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"👤  {sname}", bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(hdr, text=f"{pct}%  ({done}/6 phases complete)",
                 bg=BG_WHITE, fg=bar_col,
                 font=("Segoe UI", 11, "bold")).pack(side="right")

        draw_phase_bar(pc, phases)

        label_row = tk.Frame(pc, bg=BG_WHITE)
        label_row.pack(fill="x", pady=(3, 4))
        for i in range(6):
            s = phases[i]
            fg = GREEN if s == "Done" else (BLUE if s == "In Progress" else MUTED)
            icon = "✓" if s == "Done" else ("●" if s == "In Progress" else "○")
            lf = tk.Frame(label_row, bg=BG_WHITE)
            lf.grid(row=0, column=i, sticky="nsew")
            label_row.columnconfigure(i, weight=1)
            tk.Label(lf, text=f"{icon} {s}", bg=BG_WHITE, fg=fg,
                     font=("Segoe UI", 7, "bold"),
                     wraplength=75, justify="center").pack(expand=True)

        # Deadline management
        dc = card_frame(inner, padx=16, pady=14)
        dc.pack(fill="x", pady=(0, 10))
        tk.Label(dc, text="Submission Deadline for this Student",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

        dl = query("""SELECT d.deadline_id, d.due_date FROM deadlines d
                      JOIN deadline_assignments da ON d.deadline_id=da.deadline_id
                      WHERE da.student_id=%s ORDER BY d.due_date ASC LIMIT 1""",
                   (st_id,), one=True)

        dl_row = tk.Frame(dc, bg=BG_WHITE)
        dl_row.pack(fill="x")
        if dl:
            days = (dl["due_date"] - date.today()).days
            dcol = DANGER if days <= 1 else (WARNING if days <= 7 else GREEN)
            tk.Label(dl_row, text=f"Current: {dl['due_date']}",
                     bg=BG_WHITE, fg=dcol,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 14))

        tk.Label(dl_row, text="New date:", bg=BG_WHITE, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        self._dl_var = tk.StringVar(value=str(dl["due_date"]) if dl else "")
        dl_e = tk.Entry(dl_row, textvariable=self._dl_var, width=14)
        style_entry(dl_e)
        dl_e.pack(side="left", ipady=5, padx=(0, 8))
        tk.Button(dl_row, text="Set" if not dl else "Update",
                  command=lambda s=st_id, d=dl: self._save_deadline(s, d),
                  bg=BLUE, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=10, pady=4).pack(side="left")

        # Final submission + grading
        rc = card_frame(inner, padx=16, pady=14)
        rc.pack(fill="x", pady=(0, 10))
        tk.Label(rc, text="Final Submission",
                 bg=BG_WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

        if row.get("final_file_name"):
            ff = tk.Frame(rc, bg="#f0fdf4",
                          highlightthickness=1, highlightbackground=GREEN)
            ff.pack(fill="x", pady=(0, 10))
            ff_row = tk.Frame(ff, bg="#f0fdf4")
            ff_row.pack(fill="x", padx=10, pady=6)
            tk.Label(ff_row, text=f"✓  {row['final_file_name']}",
                     bg="#f0fdf4", fg=GREEN,
                     font=("Segoe UI", 10, "bold")).pack(side="left")
            file_path = os.path.join(UPLOAD_FOLDER, row.get("final_file_path", ""))
            tk.Button(ff_row, text="📄 Open Document",
                      command=lambda fp=file_path: self._open_doc(fp),
                      bg=BLUE, fg=WHITE, relief="flat",
                      font=("Segoe UI", 9, "bold"), padx=10, pady=3).pack(side="right")

            if row.get("final_score") is not None:
                gf = tk.Frame(rc, bg=BG_WHITE)
                gf.pack(anchor="w", pady=(0, 8))
                tk.Label(gf, text=f"  Score: {row['final_score']}/100  ",
                         bg=BLUE, fg=WHITE,
                         font=("Segoe UI", 11, "bold"), padx=10, pady=4).pack(side="left", padx=(0, 8))
                if row.get("grade"):
                    gc = GREEN if row["grade"] in ("A", "A+", "A-", "Excellent") else (
                         DANGER if row["grade"] in ("F", "Fail") else GOLD_TILE)
                    tk.Label(gf, text=f"  Grade: {row['grade']}  ",
                             bg=gc, fg=WHITE,
                             font=("Segoe UI", 11, "bold"), padx=10, pady=4).pack(side="left")
                if row.get("supervisor_comment"):
                    tk.Label(rc, text=f"Your feedback: {row['supervisor_comment']}",
                             bg=BG_WHITE, fg=DARK, font=("Segoe UI", 9),
                             wraplength=520).pack(anchor="w", pady=(0, 8))

            tk.Button(rc,
                      text="✎ Grade Final Submission" if row.get("final_score") is None else "✎ Update Grade",
                      command=lambda m=mid, s=st_id: self._grade_dialog(m, s),
                      bg=GOLD_TILE, fg=WHITE, relief="flat",
                      font=("Segoe UI", 10, "bold"), padx=12, pady=6).pack(anchor="w")
        else:
            tk.Label(rc, text="⏳  Student has not submitted yet.",
                     bg=BG_WHITE, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w")

    def _open_doc(self, file_path):
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("File Not Found",
                                 f"Cannot find the file:\n{file_path}")
            return
        try:
            import sys, subprocess
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def _save_deadline(self, st_id, dl):
        date_str = self._dl_var.get().strip()
        if not date_str:
            messagebox.showwarning("Missing", "Please enter a date.")
            return
        sup_id = self._sup_id
        if dl:
            query("UPDATE deadlines SET due_date=%s WHERE deadline_id=%s",
                  (date_str, dl["deadline_id"]))
            notify("student", st_id, "deadline",
                   "Deadline Updated",
                   f"Your final submission deadline was updated to {date_str}")
            messagebox.showinfo("Updated", f"Deadline updated to {date_str}")
        else:
            did = query("""INSERT INTO deadlines (supervisor_id, title, due_date, description)
                           VALUES (%s,'Final Thesis Submission',%s,
                           'Submit your final thesis document')""",
                        (sup_id, date_str))
            query("INSERT IGNORE INTO deadline_assignments (deadline_id, student_id) VALUES (%s,%s)",
                  (did, st_id))
            notify("student", st_id, "deadline",
                   "Submission Deadline Set",
                   f"Your final thesis submission deadline is {date_str}")
            messagebox.showinfo("Set", f"Deadline set to {date_str}")
        self._load_student()

    def _grade_dialog(self, mid, st_id):
        dlg = FinalGradeDialog(self.master, mid, st_id)
        self.wait_window(dlg)
        self._load_student()


class FinalGradeDialog(tk.Toplevel):
    """Dialog for supervisor: score out of 100 + grade for final submission only."""
    def __init__(self, master, mid, st_id):
        super().__init__(master)
        self.mid   = mid
        self.st_id = st_id
        self.title("Grade Final Submission")
        self.geometry("460x380")
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
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 2))
        tk.Label(f,
                 text="Only the final submission is graded. Individual phases are not scored.",
                 bg=BG_MAIN, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 14))

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

        tk.Label(f, text="Grade", bg=BG_MAIN, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))
        self.grade_var = tk.StringVar(value=old_grade)
        ttk.Combobox(f, textvariable=self.grade_var,
                     values=["A+", "A", "A-", "B+", "B", "B-",
                             "C+", "C", "C-", "D", "F",
                             "Excellent", "Good", "Satisfactory", "Pass", "Fail"],
                     width=20).pack(anchor="w", pady=(4, 10))

        tk.Label(f, text="Feedback comment", bg=BG_MAIN, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        self.comment = tk.Text(f, height=4, bg=BG_WHITE, fg=DARK,
                               font=("Segoe UI", 10), relief="solid",
                               padx=8, pady=6,
                               highlightthickness=1, highlightbackground=BORDER)
        self.comment.pack(fill="x", pady=(4, 14))
        if old_comment:
            self.comment.insert("1.0", old_comment)

        bf = tk.Frame(f, bg=BG_MAIN)
        bf.pack()
        tk.Button(bf, text="Save Grade", command=self._save,
                  bg=GREEN, fg=WHITE, relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=14, pady=5).pack(side="left", padx=(0, 8))
        tk.Button(bf, text="Cancel", command=self.destroy,
                  bg="#95a5a6", fg=WHITE, relief="flat",
                  font=("Segoe UI", 10), padx=14, pady=5).pack(side="left")

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
