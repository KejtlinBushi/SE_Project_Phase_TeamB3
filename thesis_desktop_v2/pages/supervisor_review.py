
import os
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import fitz
    from PIL import Image, ImageTk
except Exception:
    fitz = None
    Image = None
    ImageTk = None

from database import query
from auth import SESSION
from ui import WHITE, BLUE, GREEN, DANGER, MUTED, DARK, open_file


UPLOAD_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "uploads")
)


class SupervisorReviewWindow(tk.Toplevel):
    def __init__(self, parent, submission, refresh_callback=None):
        super().__init__(parent)

        self.parent = parent
        #ruajtja e submission 
        self.submission = submission
        self._ensure_description_loaded()
        self.refresh_callback = refresh_callback
        self.file_path = self._resolve_file_path()
        self.preview_images = []

        self.title(
            f"Thesis Submission Review - v{submission['version_number']} - {submission['full_name']}"
        )
        self.geometry("1250x780")
        self.configure(bg="#eef3f8")

        self._build()

    def _ensure_description_loaded(self):
        """Make sure the optional student description is available in this window."""
        if self.submission.get("description") is not None:
            return

        try:
            row = query(
                "SELECT description FROM submissions WHERE submission_id=%s",
                (self.submission["submission_id"],),
                one=True
            )

            if row:
                self.submission["description"] = row.get("description")
        except Exception:
            self.submission["description"] = ""

    def _resolve_file_path(self):
        stored_path = self.submission.get("file_path")

        if not stored_path:
            return None

        stored_path = stored_path.replace("\\", os.sep).replace("/", os.sep)

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

    def _build(self):
        header = tk.Frame(self, bg="#1a5276", height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="📄 THESIS SUBMISSION REVIEW",
            bg="#1a5276",
            fg=WHITE,
            font=("Segoe UI", 20, "bold")
        ).pack(side="left", padx=25)

        tk.Button(
            header,
            text="Open in Default App",
            command=self._open_document_external,
            bg="#2980b9",
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=8
        ).pack(side="right", padx=(0, 25))

        tk.Button(
            header,
            text="Back to Submissions",
            command=self.destroy,
            bg="#7f8c8d",
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=8
        ).pack(side="right", padx=(0, 10))

        main = tk.Frame(self, bg="#eef3f8")
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

        self._build_document_preview(left)
        self._build_feedback_panel(right)

   
    # LEFT: DOCUMENT PREVIEW
    
    def _build_document_preview(self, parent):
        tk.Label(
            parent,
            text="📘 THESIS DOCUMENT",
            bg=WHITE,
            fg="#003B7A",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=18, pady=(15, 10))

        tk.Frame(parent, bg="#d5dde8", height=1).pack(fill="x", padx=18)

        doc_frame = tk.Frame(parent, bg="#454545")
        doc_frame.pack(fill="both", expand=True, padx=18, pady=15)

        self.doc_canvas = tk.Canvas(
            doc_frame,
            bg="#454545",
            highlightthickness=0,
            width=580,
            height=520
        )

        doc_scroll = ttk.Scrollbar(
            doc_frame,
            orient="vertical",
            command=self.doc_canvas.yview
        )

        self.doc_canvas.configure(yscrollcommand=doc_scroll.set)

        self.doc_canvas.grid(row=0, column=0, sticky="nsew")
        doc_scroll.grid(row=0, column=1, sticky="ns")

        doc_frame.rowconfigure(0, weight=1)
        doc_frame.columnconfigure(0, weight=1)

        self.doc_canvas.images = []

        #presim 300 ms para se te behet load preview
        self.after(300, self._load_pdf_preview)

        bottom_doc = tk.Frame(parent, bg=WHITE)
        bottom_doc.pack(fill="x", padx=18, pady=(0, 15))

        tk.Label(
            bottom_doc,
            text=f"📎 {self.submission['file_name']}",
            bg=WHITE,
            fg=DARK,
            font=("Segoe UI", 10)
        ).pack(side="left")

        tk.Label(
            bottom_doc,
            text=f"Type: {self.submission['file_type']}   Size: {self.submission['file_size_kb']} KB",
            bg=WHITE,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(side="right")

    def _load_pdf_preview(self):
        self.doc_canvas.delete("all")
        self.doc_canvas.images = []

        try:
            if not self.file_path or not os.path.exists(self.file_path):
                self.doc_canvas.create_text(
                    300,
                    250,
                    text="File was not found in the uploads folder.\nPlease upload the thesis again.",
                    fill=WHITE,
                    font=("Segoe UI", 13),
                    justify="center"
                )
                self.doc_canvas.configure(scrollregion=(0, 0, 600, 520))
                return

            if fitz is None or Image is None or ImageTk is None:
                self.doc_canvas.create_text(
                    300,
                    250,
                    text="PDF preview libraries are not installed.\nClick 'Open in Default App' to view the document.",
                    fill=WHITE,
                    font=("Segoe UI", 13),
                    justify="center"
                )
                self.doc_canvas.configure(scrollregion=(0, 0, 600, 520))
                return

            if str(self.submission["file_type"]).lower() == "pdf":
                pdf = fitz.open(self.file_path)

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
                    self.doc_canvas.images.append(photo)

                    self.doc_canvas.create_text(
                        margin_left,
                        y_position,
                        anchor="nw",
                        text=f"Page {page_number + 1}",
                        fill=WHITE,
                        font=("Segoe UI", 10, "bold")
                    )

                    y_position += 25

                    self.doc_canvas.create_image(
                        margin_left,
                        y_position,
                        anchor="nw",
                        image=photo
                    )

                    y_position += pix.height + 35

                pdf.close()

                self.doc_canvas.configure(
                    scrollregion=(0, 0, canvas_width + 50, y_position)
                )

            else:
                self.doc_canvas.create_text(
                    300,
                    250,
                    text="Only PDF preview is supported.\nPlease ask the student to upload a PDF file.",
                    fill=WHITE,
                    font=("Segoe UI", 13),
                    justify="center"
                )
                self.doc_canvas.configure(scrollregion=(0, 0, 600, 520))

        except Exception as e:
            self.doc_canvas.create_text(
                300,
                250,
                text=f"Preview could not be loaded.\n{e}\n\nClick 'Open in Default App' to view the document.",
                fill=WHITE,
                font=("Segoe UI", 11),
                justify="center"
            )
            self.doc_canvas.configure(scrollregion=(0, 0, 600, 520))

        self.doc_canvas.bind("<MouseWheel>", self._scroll_document)

    def _scroll_document(self, event):
        self.doc_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    
    # RIGHT: FEEDBACK PANEL
   
    def _build_feedback_panel(self, parent):
        top_feedback = tk.Frame(parent, bg=WHITE)
        top_feedback.pack(fill="x", padx=22, pady=(18, 10))

        tk.Label(
            top_feedback,
            text="💬 SUPERVISOR'S FEEDBACK",
            bg=WHITE,
            fg="#003B7A",
            font=("Segoe UI", 13, "bold")
        ).pack(side="left")

        status = self.submission["status"]

        if status == "Approved":
            status_color = GREEN
        elif status == "Rejected":
            status_color = DANGER
        else:
            status_color = "#d99a00"

        self.status_label = tk.Label(
            top_feedback,
            text=status,
            bg=status_color,
            fg=WHITE,
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=4
        )
        self.status_label.pack(side="right")

        tk.Frame(parent, bg="#d5dde8", height=1).pack(
            fill="x",
            padx=22,
            pady=(0, 15)
        )

        details = tk.Frame(
            parent,
            bg="#f8fbff",
            highlightbackground="#d5dde8",
            highlightthickness=1
        )
        details.pack(fill="x", padx=22, pady=(0, 10))

        tk.Label(
            details,
            text="Submission Details",
            bg="#f8fbff",
            fg="#003B7A",
            font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(12, 8))

        description_text = (self.submission.get("description") or "No description provided.").strip()

        info_items = [
            ("Student", self.submission["full_name"]),
            ("Version", f"v{self.submission['version_number']}"),
            ("File Name", self.submission["file_name"]),
            ("Submitted", str(self.submission["submitted_at"])[:16]),
            ("Status", self.submission["status"]),
            ("Description", description_text)
        ]
         #kryhet nje loop per te vendosur info ne dz kolona ne panalin djathtas
        for i, (label_text, value_text) in enumerate(info_items):
            row_number = (i // 2) + 1
            column_number = i % 2

            box = tk.Frame(details, bg="#f8fbff")
            box.grid(row=row_number, column=column_number, sticky="ew", padx=15, pady=4)

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
            parent,
            text="Write Feedback for Student",
            bg=WHITE,
            fg="#003B7A",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=22, pady=(0, 8))

        feedback_frame = tk.Frame(
            parent,
            bg=WHITE,
            highlightbackground="#b7d7c2",
            highlightthickness=1
        )
        feedback_frame.pack(fill="x", padx=22, pady=(0, 8))

        self.feedback_box = tk.Text(
            feedback_frame,
            height=4,
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
            command=self.feedback_box.yview
        )

        self.feedback_box.configure(yscrollcommand=feedback_scroll.set)

        existing_feedback = self.submission.get("feedback") or ""
        self.feedback_box.insert("1.0", existing_feedback)

        self.feedback_box.pack(side="left", fill="both", expand=True)
        feedback_scroll.pack(side="right", fill="y")

      
        button_frame = tk.Frame(parent, bg=WHITE)
        button_frame.pack(fill="x", padx=22, pady=(0, 8))
        button_frame.lift()

        tk.Button(
            button_frame,
            text="Submit Feedback",
            command=self._post_feedback_to_student,
            bg=BLUE,
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            button_frame,
            text="Approve",
            command=lambda: self._submit_review("Approved"),
            bg=GREEN,
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            button_frame,
            text="Reject",
            command=lambda: self._submit_review("Rejected"),
            bg=DANGER,
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            button_frame,
            text="Close",
            command=self.destroy,
            bg="#7f8c8d",
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 10),
            padx=12,
            pady=6
        ).pack(side="right")

    def _open_document_external(self):
        if not self.file_path or not os.path.exists(self.file_path):
            messagebox.showerror(
                "File Not Found",
                "The thesis file could not be found."
            )
            return

        open_file(self.file_path)

    def _get_feedback(self):
        #merr tekstin nga fillimi deri ne fund 
        return self.feedback_box.get("1.0", "end").strip()

    def _insert_or_update_feedback(self, comment):
        existing = query(
            "SELECT feedback_id FROM feedback WHERE submission_id=%s",
            (self.submission["submission_id"],),
            one=True
        )

        if existing:
            query("""
                UPDATE feedback
                SET comment=%s, supervisor_id=%s
                WHERE submission_id=%s
            """, (
                comment,
                SESSION["user_id"],
                self.submission["submission_id"]
            ))
        else:
            query("""
                INSERT INTO feedback
                (submission_id, supervisor_id, comment)
                VALUES (%s, %s, %s)
            """, (
                self.submission["submission_id"],
                SESSION["user_id"],
                comment
            ))

    def _post_feedback_to_student(self):
        comment = self._get_feedback()

        if not comment:
            messagebox.showwarning(
                "Empty Feedback",
                "Please write feedback before submitting it."
            )
            return

        self._insert_or_update_feedback(comment)

        query("""
            INSERT INTO notifications
            (user_role, user_id, type, title, message, ref_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            "student",
            self.submission["student_id"],
            "submission",
            "New Supervisor Feedback",
            f"Your supervisor submitted feedback for '{self.submission['file_name']}'.",
            self.submission["submission_id"]
        ))

        messagebox.showinfo(
            "Submitted",
            "Feedback was submitted successfully. The student can now see it."
        )

        if self.refresh_callback:
            self.refresh_callback()

    def _submit_review(self, status):
        comment = self._get_feedback()

        if status == "Rejected" and not comment:
            messagebox.showwarning(
                "Feedback Required",
                "Please write feedback before rejecting the submission."
            )
            return

        query(
            "UPDATE submissions SET status=%s WHERE submission_id=%s",
            (status, self.submission["submission_id"])
        )

        if comment:
            self._insert_or_update_feedback(comment)

        query("""
            INSERT INTO notifications
            (user_role, user_id, type, title, message, ref_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            "student",
            self.submission["student_id"],
            "submission",
            f"Submission {status}",
            f"Your file '{self.submission['file_name']}' was {status.lower()}.",
            self.submission["submission_id"]
        ))

        messagebox.showinfo(
            "Done",
            f"Submission {status.lower()} successfully."
        )

        if self.refresh_callback:
            self.refresh_callback()

        self.destroy()


