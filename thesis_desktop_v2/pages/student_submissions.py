import os
import shutil
import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import fitz
    from PIL import Image, ImageTk
except Exception:
    fitz = None
    Image = None
    ImageTk = None

from database import query
from auth import SESSION

from ui import (
    BG_MAIN,
    BG_WHITE,
    BLUE,
    BLUE2,
    GREEN,
    GOLD_TILE,
    WHITE,
    MUTED,
    DARK,
    BORDER,
    DANGER,
    style_btn,
    style_entry,
    card_frame,
    page_header,
    style_treeview,
    open_file
)


UPLOAD_FOLDER = os.path.join(
    os.path.dirname(__file__),
    "..",
    "uploads"
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def create_notification(user_role, user_id, notif_type, title, message, ref_id=None):
    try:
        query("""
            INSERT INTO notifications
            (user_role, user_id, type, title, message, ref_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_role,
            user_id,
            notif_type,
            title,
            message,
            ref_id
        ))
    except Exception:
        pass


class StudentSubmissions(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)

        page_header(
            self,
            "My Submissions",
            "Upload, delete, and view thesis feedback"
        )

        self.file_path = None
        self.submissions_data = {}

        self._build()

    def _build(self):
        sid = SESSION["user_id"]

        upload_card = card_frame(self, padx=16, pady=14)
        upload_card.pack(fill="x", padx=20, pady=(12, 0))

        tk.Label(
            upload_card,
            text="Upload Thesis Version",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            upload_card,
            text="Description (optional)",
            bg=BG_WHITE,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w")

        self.desc_var = tk.StringVar()

        desc_entry = tk.Entry(upload_card, textvariable=self.desc_var)
        style_entry(desc_entry)
        desc_entry.pack(fill="x", ipady=5, pady=(4, 10))

        self.file_lbl = tk.Label(
            upload_card,
            text="No file selected",
            bg=BG_WHITE,
            fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.file_lbl.pack(anchor="w", pady=(0, 6))

        btn_frame = tk.Frame(upload_card, bg=BG_WHITE)
        btn_frame.pack(anchor="w")

        tk.Button(
            btn_frame,
            text="Choose File (PDF/DOCX)",
            command=self._pick_file,
            bg="#ecf0f1",
            fg=DARK,
            relief="flat",
            font=("Segoe UI", 10),
            padx=10,
            pady=5
        ).pack(side="left", padx=(0, 8))

        upload_btn = tk.Button(
            btn_frame,
            text="Upload",
            command=self._upload
        )
        style_btn(upload_btn)
        upload_btn.pack(side="left")

        history_card = card_frame(self, padx=0, pady=0)
        history_card.pack(fill="both", expand=True, padx=20, pady=12)

        tk.Label(
            history_card,
            text="Submission History",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=14, pady=(10, 6))

        tk.Frame(history_card, bg=BORDER, height=1).pack(fill="x")

        table_frame = tk.Frame(history_card, bg=BG_WHITE)
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        cols = (
            "Version",
            "File Name",
            "Type",
            "Size KB",
            "Status",
            "Submitted"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            height=10
        )

        style_treeview(
            self.tree,
            cols,
            [70, 240, 70, 80, 100, 150]
        )

        y_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._open_selected_feedback)

        action_frame = tk.Frame(history_card, bg=BG_WHITE)
        action_frame.pack(fill="x", padx=8, pady=(0, 10))

        tk.Button(
            action_frame,
            text="View Full Feedback",
            command=self._open_selected_feedback,
            bg=BLUE,
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10),
            padx=12,
            pady=6
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            action_frame,
            text="Open Thesis File",
            command=self._open_selected_file,
            bg=BLUE2,
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10),
            padx=12,
            pady=6
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            action_frame,
            text="Delete Submission",
            command=self._delete_selected_submission,
            bg=DANGER,
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10),
            padx=12,
            pady=6
        ).pack(side="left")

        self._load(sid)

    def _load(self, sid):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.submissions_data = {}

        rows = query("""
            SELECT 
                s.submission_id,
                s.version_number,
                s.file_name,
                s.file_path,
                s.file_type,
                s.file_size_kb,
                s.status,
                s.submitted_at,
                s.description,
                f.comment AS feedback
            FROM submissions s
            LEFT JOIN feedback f 
                ON s.submission_id = f.submission_id
            WHERE s.student_id = %s
            ORDER BY s.submitted_at DESC
        """, (sid,)) or []

        for row in rows:
            submission_id = str(row["submission_id"])
            self.submissions_data[submission_id] = row

            self.tree.insert(
                "",
                "end",
                iid=submission_id,
                values=(
                    f"v{row['version_number']}",
                    row["file_name"],
                    row["file_type"],
                    row["file_size_kb"],
                    row["status"],
                    str(row["submitted_at"])[:16]
                )
            )

    def _resolve_submission_file_path(self, submission):
        stored_path = submission.get("file_path")

        if not stored_path:
            return None

        if os.path.isabs(stored_path) and os.path.exists(stored_path):
            return stored_path

        path_in_uploads = os.path.join(UPLOAD_FOLDER, stored_path)

        if os.path.exists(path_in_uploads):
            return path_in_uploads

        path_by_name = os.path.join(
            UPLOAD_FOLDER,
            os.path.basename(stored_path)
        )

        if os.path.exists(path_by_name):
            return path_by_name

        return path_in_uploads

    def _pick_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Documents", "*.pdf *.docx"),
                ("All files", "*.*")
            ]
        )

        if path:
            self.file_path = path
            self.file_lbl.config(
                text=os.path.basename(path),
                fg=BLUE
            )

    def _upload(self):
        if not self.file_path:
            messagebox.showwarning(
                "No File",
                "Please choose a thesis file first."
            )
            return

        sid = SESSION["user_id"]

        ext = self.file_path.rsplit(".", 1)[-1].lower()

        if ext not in ("pdf", "docx"):
            messagebox.showerror(
                "Invalid File",
                "Only PDF and DOCX files are allowed."
            )
            return

        size_kb = os.path.getsize(self.file_path) // 1024

        if size_kb > 10240:
            messagebox.showerror(
                "Too Large",
                "File must not exceed 10 MB."
            )
            return

        ver_row = query("""
            SELECT COALESCE(MAX(version_number), 0) + 1 AS nv
            FROM submissions
            WHERE student_id = %s
        """, (sid,), one=True)

        version = ver_row["nv"]

        safe_name = f"{sid}_v{version}_{uuid.uuid4().hex[:8]}.{ext}"
        destination = os.path.join(UPLOAD_FOLDER, safe_name)

        try:
            shutil.copy2(self.file_path, destination)
        except Exception as e:
            messagebox.showerror(
                "Upload Error",
                f"Could not upload file: {e}"
            )
            return

        query("""
            INSERT INTO submissions
            (
                student_id,
                version_number,
                file_path,
                file_name,
                file_type,
                file_size_kb,
                description,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
        """, (
            sid,
            version,
            safe_name,
            os.path.basename(self.file_path),
            ext.upper(),
            size_kb,
            self.desc_var.get()
        ))

        sup = query("""
            SELECT supervisor_id
            FROM students
            WHERE student_id = %s
        """, (sid,), one=True)

        if sup and sup["supervisor_id"]:
            create_notification(
                "supervisor",
                sup["supervisor_id"],
                "submission",
                "New Thesis Submission",
                f"{SESSION['name']} uploaded thesis version {version}"
            )

        messagebox.showinfo(
            "Uploaded",
            f"Thesis version {version} uploaded successfully."
        )

        self.file_path = None
        self.file_lbl.config(
            text="No file selected",
            fg=MUTED
        )
        self.desc_var.set("")

        self._load(sid)

    def _get_selected_submission(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Selection",
                "Please select a submission first."
            )
            return None

        return self.submissions_data.get(selected[0])

    def _open_selected_file(self):
        submission = self._get_selected_submission()

        if not submission:
            return

        file_path = self._resolve_submission_file_path(submission)

        if not file_path or not os.path.exists(file_path):
            messagebox.showerror(
                "File Not Found",
                "The thesis file could not be found."
            )
            return

        open_file(file_path)

    def _delete_selected_submission(self):
        submission = self._get_selected_submission()

        if not submission:
            return

        if submission["status"] in ("Approved", "Rejected"):
            messagebox.showwarning(
                "Cannot Delete",
                "This thesis version cannot be deleted because it has already been approved or rejected."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this thesis version?"
        )

        if not confirm:
            return

        try:
            file_path = self._resolve_submission_file_path(submission)

            if file_path and os.path.exists(file_path):
                os.remove(file_path)

            query("""
                DELETE FROM submissions
                WHERE submission_id = %s
                AND student_id = %s
            """, (
                submission["submission_id"],
                SESSION["user_id"]
            ))

            messagebox.showinfo(
                "Deleted",
                "Submission deleted successfully."
            )

            self._load(SESSION["user_id"])

        except Exception as e:
            messagebox.showerror(
                "Delete Error",
                f"Could not delete submission: {e}"
            )
    def _open_selected_feedback(self, event=None):
        submission = self._get_selected_submission()

        if not submission:
            return

        win = tk.Toplevel(self)
        win.title(
            f"Thesis Submission Feedback - "
            f"v{submission['version_number']} - {SESSION['name']}"
        )
        win.geometry("1250x720")
        win.configure(bg="#eef3f8")

        file_path = self._resolve_submission_file_path(submission)
        feedback_text = submission.get("feedback") or "No feedback has been provided yet."

        header = tk.Frame(win, bg="#1a5276", height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="📄 THESIS SUBMISSION FEEDBACK",
            bg="#1a5276",
            fg=WHITE,
            font=("Segoe UI", 20, "bold")
        ).pack(side="left", padx=25)

        tk.Button(
            header,
            text="Open in Default App",
            command=lambda: open_file(file_path)
            if file_path and os.path.exists(file_path)
            else messagebox.showerror("File Not Found", "The thesis file could not be found."),
            bg="#2980b9",
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=8
        ).pack(side="right", padx=(0, 25))

        main = tk.Frame(win, bg="#eef3f8")
        main.pack(fill="both", expand=True, padx=18, pady=18)

        left = tk.Frame(
            main,
            bg=WHITE,
            highlightbackground="#d5dde8",
            highlightthickness=1
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = tk.Frame(
            main,
            bg=WHITE,
            highlightbackground="#d5dde8",
            highlightthickness=1
        )
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Button(
            header,
            text="Back to Submissions",
            command=win.destroy,
            bg="#7f8c8d",
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=8
        ).pack(side="right", padx=(0, 10))
        

        # =========================
        # LEFT: DOCUMENT PREVIEW
        # =========================
        tk.Label(
            left,
            text="📘 THESIS DOCUMENT",
            bg=WHITE,
            fg="#003B7A",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=18, pady=(15, 10))

        tk.Frame(left, bg="#d5dde8", height=1).pack(fill="x", padx=18)

        doc_frame = tk.Frame(left, bg="#454545")
        doc_frame.pack(fill="both", expand=True, padx=18, pady=15)

        doc_canvas = tk.Canvas(
            doc_frame,
            bg="#454545",
            highlightthickness=0,
            width=580,
            height=520
        )

        doc_scroll = ttk.Scrollbar(
            doc_frame,
            orient="vertical",
            command=doc_canvas.yview
        )

        doc_canvas.configure(yscrollcommand=doc_scroll.set)

        doc_canvas.grid(row=0, column=0, sticky="nsew")
        doc_scroll.grid(row=0, column=1, sticky="ns")

        doc_frame.rowconfigure(0, weight=1)
        doc_frame.columnconfigure(0, weight=1)

        doc_canvas.images = []

        try:
            if not file_path or not os.path.exists(file_path):
                doc_canvas.create_text(
                    300,
                    250,
                    text="File was not found in the uploads folder.\nPlease upload the thesis again.",
                    fill=WHITE,
                    font=("Segoe UI", 13),
                    justify="center"
                )
                doc_canvas.configure(scrollregion=(0, 0, 600, 520))

            elif fitz is None or Image is None or ImageTk is None:
                doc_canvas.create_text(
                    300,
                    250,
                    text="PDF preview libraries are not installed.\nClick 'Open in Default App' to view the document.",
                    fill=WHITE,
                    font=("Segoe UI", 13),
                    justify="center"
                )
                doc_canvas.configure(scrollregion=(0, 0, 600, 520))

            elif submission["file_type"].lower() == "pdf":
                pdf = fitz.open(file_path)

                canvas_width = 540
                margin_left = 20
                y_position = 20

                for page_number in range(len(pdf)):
                    page = pdf.load_page(page_number)
                    rect = page.rect

                    zoom = canvas_width / rect.width
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(zoom, zoom),
                        alpha=False
                    )

                    img = Image.frombytes(
                        "RGB",
                        (pix.width, pix.height),
                        pix.samples
                    )

                    photo = ImageTk.PhotoImage(img)
                    doc_canvas.images.append(photo)

                    doc_canvas.create_text(
                        margin_left,
                        y_position,
                        anchor="nw",
                        text=f"Page {page_number + 1}",
                        fill=WHITE,
                        font=("Segoe UI", 10, "bold")
                    )

                    y_position += 25

                    doc_canvas.create_image(
                        margin_left,
                        y_position,
                        anchor="nw",
                        image=photo
                    )

                    y_position += pix.height + 35

                pdf.close()

                doc_canvas.configure(
                    scrollregion=(0, 0, canvas_width + 50, y_position)
                )

            else:
                doc_canvas.create_text(
                    300,
                    250,
                    text="DOCX preview is not available.\nClick 'Open in Default App' to view the document.",
                    fill=WHITE,
                    font=("Segoe UI", 13),
                    justify="center"
                )
                doc_canvas.configure(scrollregion=(0, 0, 600, 520))

        except Exception as e:
            doc_canvas.create_text(
                300,
                250,
                text=f"Preview could not be loaded.\n{e}\n\nClick 'Open in Default App' to view the document.",
                fill=WHITE,
                font=("Segoe UI", 11),
                justify="center"
            )
            doc_canvas.configure(scrollregion=(0, 0, 600, 520))

        def _scroll_document(event):
            doc_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        doc_canvas.bind("<MouseWheel>", _scroll_document)

        bottom_doc = tk.Frame(left, bg=WHITE)
        bottom_doc.pack(fill="x", padx=18, pady=(0, 15))

        tk.Label(
            bottom_doc,
            text=f"📎 {submission['file_name']}",
            bg=WHITE,
            fg=DARK,
            font=("Segoe UI", 10)
        ).pack(side="left")

        tk.Label(
            bottom_doc,
            text=f"Type: {submission['file_type']}   Size: {submission['file_size_kb']} KB",
            bg=WHITE,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(side="right")

        # =========================
        # RIGHT: FEEDBACK
        # =========================
        top_feedback = tk.Frame(right, bg=WHITE)
        top_feedback.pack(fill="x", padx=22, pady=(18, 10))

        tk.Label(
            top_feedback,
            text="💬 SUPERVISOR'S FEEDBACK",
            bg=WHITE,
            fg="#003B7A",
            font=("Segoe UI", 13, "bold")
        ).pack(side="left")

        status = submission["status"]

        if status == "Approved":
            status_color = GREEN
        elif status == "Rejected":
            status_color = DANGER
        else:
            status_color = GOLD_TILE

        tk.Label(
            top_feedback,
            text=status,
            bg=status_color,
            fg=WHITE,
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=4
        ).pack(side="right")

        tk.Frame(right, bg="#d5dde8", height=1).pack(fill="x", padx=22, pady=(0, 15))

        details = tk.Frame(
            right,
            bg="#f8fbff",
            highlightbackground="#d5dde8",
            highlightthickness=1
        )
        details.pack(fill="x", padx=22, pady=(0, 18))

        tk.Label(
            details,
            text="Submission Details",
            bg="#f8fbff",
            fg="#003B7A",
            font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(12, 8))

        info_items = [
            ("Student", SESSION["name"]),
            ("Version", f"v{submission['version_number']}"),
            ("File Name", submission["file_name"]),
            ("Submitted", str(submission["submitted_at"])[:16]),
            ("Status", submission["status"]),
            ("File Size", f"{submission['file_size_kb']} KB")
        ]

        for i, (label_text, value_text) in enumerate(info_items):
            row_number = (i // 2) + 1
            column_number = i % 2

            box = tk.Frame(details, bg="#f8fbff")
            box.grid(row=row_number, column=column_number, sticky="ew", padx=15, pady=7)

            tk.Label(
                box,
                text=label_text,
                bg="#f8fbff",
                fg=MUTED,
                font=("Segoe UI", 9)
            ).pack(anchor="w")

            tk.Label(
                box,
                text=value_text,
                bg="#f8fbff",
                fg=DARK,
                font=("Segoe UI", 10, "bold"),
                wraplength=230,
                justify="left"
            ).pack(anchor="w")

        details.columnconfigure(0, weight=1)
        details.columnconfigure(1, weight=1)

        tk.Label(
            right,
            text="Detailed Feedback",
            bg=WHITE,
            fg="#003B7A",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=22, pady=(0, 8))

        feedback_frame = tk.Frame(
            right,
            bg=WHITE,
            highlightbackground="#b7d7c2",
            highlightthickness=1
        )
        feedback_frame.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        feedback_box = tk.Text(
            feedback_frame,
            wrap="word",
            bg="#fbfffd",
            fg=DARK,
            font=("Segoe UI", 11),
            bd=0,
            padx=15,
            pady=15
        )

        feedback_scroll = ttk.Scrollbar(
            feedback_frame,
            orient="vertical",
            command=feedback_box.yview
        )

        feedback_box.configure(yscrollcommand=feedback_scroll.set)

        feedback_box.insert("1.0", feedback_text)
        feedback_box.config(state="disabled")

        feedback_box.pack(side="left", fill="both", expand=True)
        feedback_scroll.pack(side="right", fill="y")

        # =========================
        # STUDENT REPLY
        # =========================
        tk.Label(
            right,
            text="Reply to Supervisor",
            bg=WHITE,
            fg="#003B7A",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=22, pady=(0, 8))

        reply_frame = tk.Frame(
            right,
            bg=WHITE,
            highlightbackground="#d5dde8",
            highlightthickness=1
        )
        reply_frame.pack(fill="x", padx=22, pady=(0, 18))

        reply_box = tk.Text(
            reply_frame,
            height=4,
            wrap="word",
            bg="#ffffff",
            fg=DARK,
            font=("Segoe UI", 10),
            padx=10,
            pady=8
        )
        reply_box.pack(fill="x", padx=8, pady=8)

        tk.Button(
            reply_frame,
            text="Send Reply",
            command=lambda: self._send_feedback_reply(submission, reply_box),
            bg=BLUE,
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6
        ).pack(anchor="e", padx=8, pady=(0, 8))

        # =========================
        # BOTTOM BUTTONS
        # =========================
        bottom = tk.Frame(right, bg=WHITE)
        bottom.pack(fill="x", padx=22, pady=(0, 18))

        tk.Button(
            bottom,
            text="Open Thesis File",
            command=lambda: open_file(file_path)
            if file_path and os.path.exists(file_path)
            else messagebox.showerror("File Not Found", "The thesis file could not be found."),
            bg=BLUE,
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10),
            padx=14,
            pady=7
        ).pack(side="left")

        tk.Button(
            bottom,
            text="Close",
            command=win.destroy,
            bg="#7f8c8d",
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10),
            padx=14,
            pady=7
        ).pack(side="right")
    # def _open_selected_feedback(self, event=None):
    #     submission = self._get_selected_submission()

    #     if not submission:
    #         return

    #     win = tk.Toplevel(self)
    #     win.title(
    #         f"Thesis Submission Feedback - "
    #         f"v{submission['version_number']} - {SESSION['name']}"
    #     )
    #     win.geometry("1250x720")
    #     win.configure(bg="#eef3f8")

    #     file_path = self._resolve_submission_file_path(submission)
    #     feedback_text = submission.get("feedback") or "No feedback has been provided yet."

    #     header = tk.Frame(win, bg="#003B7A", height=90)
    #     header.pack(fill="x")
    #     header.pack_propagate(False)

    #     tk.Label(
    #         header,
    #         text="📄  THESIS SUBMISSION FEEDBACK",
    #         bg="#003B7A",
    #         fg=WHITE,
    #         font=("Segoe UI", 20, "bold")
    #     ).pack(side="left", padx=25)

    #     tk.Button(
    #         header,
    #         text="Open in Default App",
    #         command=lambda: open_file(file_path)
    #         if file_path and os.path.exists(file_path)
    #         else messagebox.showerror(
    #             "File Not Found",
    #             "The thesis file could not be found."
    #         ),
    #         bg="#2F80ED",
    #         fg=WHITE,
    #         relief="flat",
    #         font=("Segoe UI", 10, "bold"),
    #         padx=18,
    #         pady=8
    #     ).pack(side="right", padx=(0, 25))

    #     main = tk.Frame(win, bg="#eef3f8")
    #     main.pack(fill="both", expand=True, padx=18, pady=18)

    #     left = tk.Frame(
    #         main,
    #         bg=WHITE,
    #         highlightbackground="#d5dde8",
    #         highlightthickness=1
    #     )
    #     left.pack(side="left", fill="both", expand=True, padx=(0, 10))

    #     right = tk.Frame(
    #         main,
    #         bg=WHITE,
    #         highlightbackground="#d5dde8",
    #         highlightthickness=1
    #     )
    #     right.pack(side="right", fill="both", expand=True, padx=(10, 0))

    #     tk.Label(
    #         left,
    #         text="📘 THESIS DOCUMENT",
    #         bg=WHITE,
    #         fg="#003B7A",
    #         font=("Segoe UI", 13, "bold")
    #     ).pack(anchor="w", padx=18, pady=(15, 10))

    #     tk.Frame(left, bg="#d5dde8", height=1).pack(fill="x", padx=18)

    #     doc_canvas = tk.Canvas(left, bg="#454545", highlightthickness=0)
    #     doc_canvas.pack(fill="both", expand=True, padx=18, pady=15)

    #     try:
    #         if not file_path or not os.path.exists(file_path):
    #             doc_canvas.create_text(
    #                 300,
    #                 250,
    #                 text=(
    #                     "File was not found in the uploads folder.\n"
    #                     "Please upload the thesis again."
    #                 ),
    #                 fill=WHITE,
    #                 font=("Segoe UI", 13),
    #                 justify="center"
    #             )

    #         elif fitz is None or Image is None or ImageTk is None:
    #             doc_canvas.create_text(
    #                 300,
    #                 250,
    #                 text=(
    #                     "PDF preview libraries are not installed.\n"
    #                     "Click 'Open in Default App' to view the document."
    #                 ),
    #                 fill=WHITE,
    #                 font=("Segoe UI", 13),
    #                 justify="center"
    #             )

    #         elif submission["file_type"].lower() == "pdf":
    #             pdf = fitz.open(file_path)
    #             page = pdf.load_page(0)

    #             pix = page.get_pixmap(
    #                 matrix=fitz.Matrix(1.5, 1.5),
    #                 alpha=False
    #             )

    #             img = Image.frombytes(
    #                 "RGB",
    #                 (pix.width, pix.height),
    #                 pix.samples
    #             )

    #             img.thumbnail((560, 680))

    #             photo = ImageTk.PhotoImage(img)

    #             doc_canvas.image = photo
    #             doc_canvas.create_image(20, 20, anchor="nw", image=photo)

    #             pdf.close()

    #         else:
    #             doc_canvas.create_text(
    #                 300,
    #                 250,
    #                 text=(
    #                     "DOCX preview is not available.\n"
    #                     "Click 'Open in Default App' to view the document."
    #                 ),
    #                 fill=WHITE,
    #                 font=("Segoe UI", 13),
    #                 justify="center"
    #             )

    #     except Exception as e:
    #         doc_canvas.create_text(
    #             300,
    #             250,
    #             text=(
    #                 f"Preview could not be loaded.\n{e}\n\n"
    #                 "Click 'Open in Default App' to view the document."
    #             ),
    #             fill=WHITE,
    #             font=("Segoe UI", 11),
    #             justify="center"
    #         )

    #     bottom_doc = tk.Frame(left, bg=WHITE)
    #     bottom_doc.pack(fill="x", padx=18, pady=(0, 15))

    #     tk.Label(
    #         bottom_doc,
    #         text=f"📎 {submission['file_name']}",
    #         bg=WHITE,
    #         fg=DARK,
    #         font=("Segoe UI", 10)
    #     ).pack(side="left")

    #     tk.Label(
    #         bottom_doc,
    #         text=(
    #             f"Type: {submission['file_type']}   "
    #             f"Size: {submission['file_size_kb']} KB"
    #         ),
    #         bg=WHITE,
    #         fg=MUTED,
    #         font=("Segoe UI", 10)
    #     ).pack(side="right")

    #     top_feedback = tk.Frame(right, bg=WHITE)
    #     top_feedback.pack(fill="x", padx=22, pady=(18, 10))

    #     tk.Label(
    #         top_feedback,
    #         text="💬 SUPERVISOR'S FEEDBACK",
    #         bg=WHITE,
    #         fg="#003B7A",
    #         font=("Segoe UI", 13, "bold")
    #     ).pack(side="left")

    #     status = submission["status"]

    #     if status == "Approved":
    #         status_color = GREEN
    #     elif status == "Rejected":
    #         status_color = DANGER
    #     else:
    #         status_color = GOLD_TILE

    #     tk.Label(
    #         top_feedback,
    #         text=status,
    #         bg=status_color,
    #         fg=WHITE,
    #         font=("Segoe UI", 10, "bold"),
    #         padx=14,
    #         pady=4
    #     ).pack(side="right")

    #     tk.Frame(right, bg="#d5dde8", height=1).pack(
    #         fill="x",
    #         padx=22,
    #         pady=(0, 15)
    #     )

    #     details = tk.Frame(
    #         right,
    #         bg="#f8fbff",
    #         highlightbackground="#d5dde8",
    #         highlightthickness=1
    #     )
    #     details.pack(fill="x", padx=22, pady=(0, 18))

    #     tk.Label(
    #         details,
    #         text="Submission Details",
    #         bg="#f8fbff",
    #         fg="#003B7A",
    #         font=("Segoe UI", 11, "bold")
    #     ).grid(
    #         row=0,
    #         column=0,
    #         columnspan=2,
    #         sticky="w",
    #         padx=15,
    #         pady=(12, 8)
    #     )

    #     info_items = [
    #         ("Student", SESSION["name"]),
    #         ("Version", f"v{submission['version_number']}"),
    #         ("File Name", submission["file_name"]),
    #         ("Submitted", str(submission["submitted_at"])[:16]),
    #         ("Status", submission["status"]),
    #         ("File Size", f"{submission['file_size_kb']} KB")
    #     ]

    #     for i, (label_text, value_text) in enumerate(info_items):
    #         row_number = (i // 2) + 1
    #         column_number = i % 2

    #         box = tk.Frame(details, bg="#f8fbff")
    #         box.grid(
    #             row=row_number,
    #             column=column_number,
    #             sticky="ew",
    #             padx=15,
    #             pady=7
    #         )

    #         tk.Label(
    #             box,
    #             text=label_text,
    #             bg="#f8fbff",
    #             fg=MUTED,
    #             font=("Segoe UI", 9)
    #         ).pack(anchor="w")

    #         tk.Label(
    #             box,
    #             text=value_text,
    #             bg="#f8fbff",
    #             fg=DARK,
    #             font=("Segoe UI", 10, "bold"),
    #             wraplength=230,
    #             justify="left"
    #         ).pack(anchor="w")

    #     details.columnconfigure(0, weight=1)
    #     details.columnconfigure(1, weight=1)

    #     tk.Label(
    #         right,
    #         text="Detailed Feedback",
    #         bg=WHITE,
    #         fg="#003B7A",
    #         font=("Segoe UI", 12, "bold")
    #     ).pack(anchor="w", padx=22, pady=(0, 8))

    #     feedback_frame = tk.Frame(
    #         right,
    #         bg=WHITE,
    #         highlightbackground="#b7d7c2",
    #         highlightthickness=1
    #     )
    #     feedback_frame.pack(
    #         fill="both",
    #         expand=True,
    #         padx=22,
    #         pady=(0, 18)
    #     )

    #     feedback_box = tk.Text(
    #         feedback_frame,
    #         wrap="word",
    #         bg="#fbfffd",
    #         fg=DARK,
    #         font=("Segoe UI", 11),
    #         bd=0,
    #         padx=15,
    #         pady=15
    #     )

    #     scroll = ttk.Scrollbar(
    #         feedback_frame,
    #         orient="vertical",
    #         command=feedback_box.yview
    #     )

    #     feedback_box.configure(yscrollcommand=scroll.set)

    #     feedback_box.insert("1.0", feedback_text)
    #     feedback_box.config(state="disabled")

    #     feedback_box.pack(side="left", fill="both", expand=True)
    #     scroll.pack(side="right", fill="y")

    #     bottom = tk.Frame(right, bg=WHITE)
    #     bottom.pack(fill="x", padx=22, pady=(0, 18))

    #     tk.Button(
    #         bottom,
    #         text="Open Thesis File",
    #         command=lambda: open_file(file_path)
    #         if file_path and os.path.exists(file_path)
    #         else messagebox.showerror(
    #             "File Not Found",
    #             "The thesis file could not be found."
    #         ),
    #         bg=BLUE,
    #         fg=WHITE,
    #         relief="flat",
    #         font=("Segoe UI", 10),
    #         padx=14,
    #         pady=7
    #     ).pack(side="left")

    #     tk.Button(
    #         bottom,
    #         text="Close",
    #         command=win.destroy,
    #         bg="#7f8c8d",
    #         fg=WHITE,
    #         relief="flat",
    #         font=("Segoe UI", 10),
    #         padx=14,
    #         pady=7
    #     ).pack(side="right")





