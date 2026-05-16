
import os
import uuid
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime, date, timedelta

from database import query
from auth import SESSION
from ui import (
    BG_MAIN,
    BG_WHITE,
    BLUE,
    WHITE,
    MUTED,
    DARK,
    BORDER,
    card_frame,
    page_header,
    open_file
)


UPLOAD_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "uploads")
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


class ChatMessagesBase(tk.Frame):
    def __init__(self, parent, current_role):
        super().__init__(parent, bg=BG_MAIN)

        self.current_role = current_role
        self.current_user_id = SESSION["user_id"]

        self.other_role = None
        self.other_user_id = None
        self.other_user_name = None

        self.conversation_options = {}
        self.selected_conversation = tk.StringVar()
        self.msg_var = tk.StringVar()

        self.active_tab = "chat"
        self.reply_to_message = None
        self.messages_by_id = {}

        # UI attributes created later in _build_input_bar().
        # Defining them here also prevents VS Code/Pylance yellow warnings.
        self.reply_preview = None
        self.reply_title = None
        self.reply_text = None
        self.input_outer = None
        self.message_entry = None

        self._setup_scrollbar_style()
        self._ensure_optional_message_columns()

        page_header(
            self,
            "Messages",
            "Chat with your supervisor" if current_role == "student"
            else "Chat with your students"
        )

        self._build()

    # =========================
    # DATABASE SAFE UPGRADE
    # =========================
    def _ensure_optional_message_columns(self):
        """
        These columns are needed for reply/edit/delete.
        If they already exist, the errors are ignored.
        """
        optional_columns = [
            "ALTER TABLE messages ADD COLUMN reply_to_message_id INT NULL",
            "ALTER TABLE messages ADD COLUMN is_deleted TINYINT DEFAULT 0",
            "ALTER TABLE messages ADD COLUMN edited_at DATETIME NULL"
        ]

        for sql in optional_columns:
            try:
                query(sql)
            except Exception:
                pass

    # =========================
    # STYLE
    # =========================
    def _setup_scrollbar_style(self):
        try:
            style = ttk.Style()
            style.theme_use("clam")

            style.configure(
                "Modern.Vertical.TScrollbar",
                gripcount=0,
                background="#cfd8e3",
                darkcolor="#cfd8e3",
                lightcolor="#cfd8e3",
                troughcolor="#f7f9fc",
                bordercolor="#f7f9fc",
                arrowcolor="#7f8c8d",
                relief="flat",
                width=10
            )

            style.map(
                "Modern.Vertical.TScrollbar",
                background=[("active", "#b8c4d1")]
            )
        except Exception:
            pass

    # =========================
    # MAIN UI
    # =========================
    def _build(self):
        self.main = tk.Frame(self, bg=BG_MAIN)
        self.main.pack(fill="both", expand=True, padx=20, pady=(12, 16))

        if self.current_role == "supervisor":
            self._build_student_selector()

        self._build_chat_container()

        self._load_default_conversation()

    def _build_student_selector(self):
        selector = card_frame(self.main, padx=16, pady=12)
        selector.pack(fill="x", pady=(0, 12))

        tk.Label(
            selector,
            text="Select Student Conversation",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        self.student_combo = ttk.Combobox(
            selector,
            textvariable=self.selected_conversation,
            state="readonly",
            width=40
        )
        self.student_combo.pack(side="right")
        self.student_combo.bind("<<ComboboxSelected>>", self._on_conversation_change)

    def _build_chat_container(self):
        self.chat_card = tk.Frame(
            self.main,
            bg=BG_WHITE,
            highlightbackground="#dce3ea",
            highlightthickness=1
        )
        self.chat_card.pack(fill="both", expand=True)

        # Use grid inside chat_card so the input bar keeps a fixed height.
        self.chat_card.grid_rowconfigure(0, weight=0)  # header
        self.chat_card.grid_rowconfigure(1, weight=0)  # tabs
        self.chat_card.grid_rowconfigure(2, weight=1)  # messages
        self.chat_card.grid_rowconfigure(3, weight=0)  # input
        self.chat_card.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_tabs()
        self._build_body()
        self._build_input_bar()

    def _build_header(self):
        header = tk.Frame(self.chat_card, bg=BG_WHITE, height=72)
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)

        self.avatar_label = tk.Label(
            header,
            text="AD",
            bg="#e8eef7",
            fg=BLUE,
            font=("Segoe UI", 11, "bold"),
            width=4,
            height=2
        )
        self.avatar_label.pack(side="left", padx=(18, 12), pady=14)

        title_area = tk.Frame(header, bg=BG_WHITE)
        title_area.pack(side="left", fill="x", expand=True, pady=14)

        self.chat_title = tk.Label(
            title_area,
            text="Conversation",
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 13, "bold")
        )
        self.chat_title.pack(anchor="w")

        self.chat_status = tk.Label(
            title_area,
            text="● Available for thesis communication",
            bg=BG_WHITE,
            fg="#2e8b57",
            font=("Segoe UI", 9)
        )
        self.chat_status.pack(anchor="w", pady=(2, 0))

        refresh = tk.Button(
            header,
            text="Refresh",
            command=self._refresh_messages,
            bg="#f1f5f9",
            fg=DARK,
            relief="flat",
            font=("Segoe UI", 9),
            padx=14,
            pady=6,
            cursor="hand2"
        )
        refresh.pack(side="right", padx=(0, 18))

    def _build_tabs(self):
        tab_bar = tk.Frame(self.chat_card, bg=BG_WHITE)
        tab_bar.grid(row=1, column=0, sticky="ew")

        tk.Frame(tab_bar, bg="#e8edf3", height=1).pack(fill="x", side="bottom")

        right_tabs = tk.Frame(tab_bar, bg=BG_WHITE)
        right_tabs.pack(side="right", padx=18)

        self.chat_tab_btn = tk.Button(
            right_tabs,
            text="Chat",
            command=lambda: self._switch_tab("chat"),
            bg=BG_WHITE,
            fg=BLUE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=22,
            pady=10,
            cursor="hand2"
        )
        self.chat_tab_btn.pack(side="left")

        self.files_tab_btn = tk.Button(
            right_tabs,
            text="Files",
            command=lambda: self._switch_tab("files"),
            bg=BG_WHITE,
            fg=MUTED,
            relief="flat",
            font=("Segoe UI", 10),
            padx=22,
            pady=10,
            cursor="hand2"
        )
        self.files_tab_btn.pack(side="left")

    def _build_body(self):
        self.body = tk.Frame(self.chat_card, bg="#f7f9fc")
        self.body.grid(row=2, column=0, sticky="nsew")

        self.canvas = tk.Canvas(
            self.body,
            bg="#f7f9fc",
            highlightthickness=0
        )

        self.scrollbar = ttk.Scrollbar(
            self.body,
            orient="vertical",
            command=self.canvas.yview,
            style="Modern.Vertical.TScrollbar"
        )

        self.msg_frame = tk.Frame(self.canvas, bg="#f7f9fc")
        self.msg_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.msg_frame,
            anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._resize_message_frame)
        self.canvas.bind("<MouseWheel>", self._scroll_messages)

    def _build_input_bar(self):
        self.input_outer = tk.Frame(
            self.chat_card,
            bg=BG_WHITE,
            highlightbackground="#dce3ea",
            highlightthickness=1,
            height=76
        )
        self.input_outer.grid(row=3, column=0, sticky="ew")
        self.input_outer.grid_propagate(False)

        # Reply preview is placed OVER the message area, not packed into the input bar.
        # This prevents the typing area from shrinking when replying.
        self.reply_preview = tk.Frame(
            self.body,
            bg="#f8fafc",
            highlightbackground="#dce3ea",
            highlightthickness=1,
            height=54
        )
        self.reply_preview.pack_propagate(False)

        reply_left = tk.Frame(
            self.reply_preview,
            bg="#f8fafc"
        )
        reply_left.pack(
            side="left",
            fill="x",
            expand=True,
            padx=12,
            pady=6
        )

        self.reply_title = tk.Label(
            reply_left,
            text="Replying to message",
            bg="#f8fafc",
            fg=BLUE,
            font=("Segoe UI", 9, "bold")
        )
        self.reply_title.pack(anchor="w")

        self.reply_text = tk.Label(
            reply_left,
            text="",
            bg="#f8fafc",
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=760,
            justify="left"
        )
        self.reply_text.pack(anchor="w")

        close_reply = tk.Button(
            self.reply_preview,
            text="✕",
            command=self._cancel_reply,
            bg="#f8fafc",
            fg=MUTED,
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            cursor="hand2"
        )
        close_reply.pack(side="right", padx=10)

        self.input_row = tk.Frame(
            self.input_outer,
            bg=BG_WHITE,
            height=58
        )
        self.input_row.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=8
        )
        self.input_row.pack_propagate(False)

        attach = tk.Button(
            self.input_row,
            text="📎",
            command=self._send_attachment,
            bg="#f1f5f9",
            fg=DARK,
            relief="flat",
            font=("Segoe UI", 13),
            width=4,
            cursor="hand2"
        )
        attach.pack(
            side="left",
            padx=(0, 8),
            fill="y"
        )

        entry_holder = tk.Frame(
            self.input_row,
            bg="#f8fafc",
            highlightbackground="#d5dde8",
            highlightthickness=1
        )
        entry_holder.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.message_entry = tk.Entry(
            entry_holder,
            textvariable=self.msg_var,
            bg="#f8fafc",
            fg=DARK,
            relief="flat",
            font=("Segoe UI", 10)
        )
        self.message_entry.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=8
        )
        self.message_entry.bind(
            "<Return>",
            lambda event: self._send_message()
        )

        send = tk.Button(
            self.input_row,
            text="➤",
            command=self._send_message,
            bg="#2e8b57",
            fg=WHITE,
            relief="flat",
            font=("Segoe UI", 13, "bold"),
            width=4,
            cursor="hand2"
        )
        send.pack(
            side="right",
            padx=(8, 0),
            fill="y"
        )

    # =========================
    # CONVERSATION LOADING
    # =========================
    def _load_default_conversation(self):
        if self.current_role == "student":
            self._load_student_supervisor()
        else:
            self._load_supervisor_students()

    def _load_student_supervisor(self):
        sid = self.current_user_id

        supervisor = query("""
            SELECT s.supervisor_id, sup.full_name
            FROM students s
            JOIN supervisors sup ON s.supervisor_id = sup.supervisor_id
            WHERE s.student_id = %s
        """, (sid,), one=True)

        if not supervisor:
            self._show_empty_state("No supervisor has been assigned yet.")
            return

        self.other_role = "supervisor"
        self.other_user_id = supervisor["supervisor_id"]
        self.other_user_name = supervisor["full_name"]

        self.chat_title.config(text=self.other_user_name)
        self._set_avatar_text(self.other_user_name)

        self._load_content()

    def _load_supervisor_students(self):
        supervisor_id = self.current_user_id

        students = query("""
            SELECT student_id, full_name
            FROM students
            WHERE supervisor_id = %s
            ORDER BY full_name ASC
        """, (supervisor_id,)) or []

        if not students:
            self._show_empty_state("No students are assigned to you yet.")
            return

        self.conversation_options = {
            student["full_name"]: student["student_id"]
            for student in students
        }

        self.student_combo.config(values=list(self.conversation_options.keys()))

        first_student = list(self.conversation_options.keys())[0]
        self.selected_conversation.set(first_student)

        self.other_role = "student"
        self.other_user_id = self.conversation_options[first_student]
        self.other_user_name = first_student

        self.chat_title.config(text=self.other_user_name)
        self._set_avatar_text(self.other_user_name)

        self._load_content()

    def _on_conversation_change(self, event=None):
        selected = self.selected_conversation.get()

        if not selected:
            return

        self.other_role = "student"
        self.other_user_id = self.conversation_options.get(selected)
        self.other_user_name = selected

        self.chat_title.config(text=self.other_user_name)
        self._set_avatar_text(self.other_user_name)
        self._cancel_reply()
        self._load_content()

    # =========================
    # TABS
    # =========================
    def _switch_tab(self, tab):
        self.active_tab = tab

        if tab == "chat":
            self.chat_tab_btn.config(fg=BLUE, font=("Segoe UI", 10, "bold"))
            self.files_tab_btn.config(fg=MUTED, font=("Segoe UI", 10))
            self.input_outer.grid(row=3, column=0, sticky="ew")
        else:
            self.chat_tab_btn.config(fg=MUTED, font=("Segoe UI", 10))
            self.files_tab_btn.config(fg=BLUE, font=("Segoe UI", 10, "bold"))
            self._cancel_reply()
            self.input_outer.grid_remove()

        self._load_content()

    def _load_content(self):
        if self.active_tab == "chat":
            self._load_messages()
        else:
            self._load_files()

    # =========================
    # DATA
    # =========================
    def _get_message_id(self, row):
        for key in ("message_id", "id"):
            if key in row:
                return row[key]
        return None

    def _get_conversation_rows(self):
        if not self.other_user_id:
            return []

        return query("""
            SELECT *
            FROM messages
            WHERE
                (
                    sender_role = %s
                    AND sender_id = %s
                    AND receiver_role = %s
                    AND receiver_id = %s
                )
                OR
                (
                    sender_role = %s
                    AND sender_id = %s
                    AND receiver_role = %s
                    AND receiver_id = %s
                )
            ORDER BY sent_at ASC
        """, (
            self.current_role,
            self.current_user_id,
            self.other_role,
            self.other_user_id,
            self.other_role,
            self.other_user_id,
            self.current_role,
            self.current_user_id
        )) or []

    def _load_messages(self):
        self._clear_messages()

        rows = self._get_conversation_rows()

        self.messages_by_id = {}
        for row in rows:
            message_id = self._get_message_id(row)
            if message_id is not None:
                self.messages_by_id[message_id] = row

        if not rows:
            self._show_empty_state("No messages yet.\\nStart the conversation below.")
            return

        last_date_label = None

        for row in rows:
            current_label = self._format_date_separator(row.get("sent_at"))

            if current_label != last_date_label:
                self._add_day_separator(current_label)
                last_date_label = current_label

            self._add_message_bubble(row)

        self.after_idle(self._scroll_to_bottom)

    def _load_files(self):
        self._clear_messages()

        rows = [
            row for row in self._get_conversation_rows()
            if row.get("attachment_path") and not self._is_deleted(row)
        ]

        if not rows:
            self._show_empty_state("No files have been shared in this conversation yet.")
            return

        container = tk.Frame(self.msg_frame, bg="#f7f9fc")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(
            container,
            text="Shared Files",
            bg="#f7f9fc",
            fg=DARK,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", pady=(0, 12))

        for row in rows:
            self._add_file_list_item(container, row)

    # =========================
    # UI HELPERS
    # =========================
    def _clear_messages(self):
        for widget in self.msg_frame.winfo_children():
            widget.destroy()

    def _add_day_separator(self, text):
        wrap = tk.Frame(self.msg_frame, bg="#f7f9fc")
        wrap.pack(fill="x", pady=(16, 10))

        tk.Label(
            wrap,
            text=text,
            bg="#e6ebf1",
            fg=MUTED,
            font=("Segoe UI", 8, "bold"),
            padx=12,
            pady=4
        ).pack()

    def _add_message_bubble(self, row):
        is_me = row["sender_role"] == self.current_role
        deleted = self._is_deleted(row)

        outer = tk.Frame(self.msg_frame, bg="#f7f9fc")
        outer.pack(fill="x", padx=24, pady=7)

        if is_me:
            outer.columnconfigure(0, weight=1)
            bubble_col = 1
            sticky = "e"
        else:
            outer.columnconfigure(1, weight=1)
            bubble_col = 0
            sticky = "w"

        bubble_bg = "#dff5e7" if is_me else "#ffffff"
        bubble_border = "#cdebd8" if is_me else "#dfe6ee"

        bubble = tk.Frame(
            outer,
            bg=bubble_bg,
            highlightbackground=bubble_border,
            highlightthickness=1,
            padx=13,
            pady=9
        )
        bubble.grid(row=0, column=bubble_col, sticky=sticky)

        reply_id = row.get("reply_to_message_id")
        if reply_id:
            replied_row = self.messages_by_id.get(reply_id)
            if replied_row:
                self._add_replied_preview_inside_bubble(bubble, replied_row)

        body = row.get("body") or ""

        if deleted:
            tk.Label(
                bubble,
                text="This message was deleted",
                bg=bubble_bg,
                fg=MUTED,
                font=("Segoe UI", 10, "italic"),
                wraplength=430,
                justify="left"
            ).pack(anchor="w")
        else:
            if body and not body.startswith("[Attachment:"):
                tk.Label(
                    bubble,
                    text=body,
                    bg=bubble_bg,
                    fg=DARK,
                    font=("Segoe UI", 10),
                    wraplength=430,
                    justify="left"
                ).pack(anchor="w")

            if row.get("attachment_path"):
                self._add_attachment_bubble_content(bubble, row)

        footer = tk.Frame(bubble, bg=bubble_bg)
        footer.pack(fill="x", pady=(5, 0))

        if row.get("edited_at") and not deleted:
            tk.Label(
                footer,
                text="edited",
                bg=bubble_bg,
                fg=MUTED,
                font=("Segoe UI", 8, "italic")
            ).pack(side="left")

        tk.Label(
            footer,
            text=self._format_time(row.get("sent_at")),
            bg=bubble_bg,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(side="right")

        if not deleted:
            more_btn = tk.Button(
                bubble,
                text="More",
                command=lambda r=row, b=bubble: self._open_message_menu(r, b),
                bg=bubble_bg,
                fg=BLUE,
                relief="flat",
                font=("Segoe UI", 8),
                cursor="hand2",
                padx=0,
                pady=0
            )
            more_btn.pack(anchor="e", pady=(5, 0))

    def _open_message_menu(self, row, widget):
        is_me = row["sender_role"] == self.current_role
        is_attachment = bool(row.get("attachment_path"))

        menu = tk.Menu(self, tearoff=0)

        menu.add_command(
            label="Reply",
            command=lambda: self._start_reply(row)
        )

        if is_me and not is_attachment:
            menu.add_command(
                label="Edit",
                command=lambda: self._edit_message(row)
            )

        if is_me:
            menu.add_command(
                label="Delete",
                command=lambda: self._delete_message(row)
            )

        try:
            menu.tk_popup(
                widget.winfo_rootx() + widget.winfo_width() - 20,
                widget.winfo_rooty() + widget.winfo_height() - 10
            )
        finally:
            menu.grab_release()

    def _add_replied_preview_inside_bubble(self, parent, replied_row):
        replied_sender = "You" if replied_row["sender_role"] == self.current_role else self.other_user_name
        replied_text = self._message_summary(replied_row)

        preview = tk.Frame(
            parent,
            bg="#f1f5f9",
            highlightbackground="#d0d7de",
            highlightthickness=1,
            padx=8,
            pady=5
        )
        preview.pack(fill="x", pady=(0, 7))

        tk.Label(
            preview,
            text=replied_sender,
            bg="#f1f5f9",
            fg=BLUE,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        tk.Label(
            preview,
            text=replied_text,
            bg="#f1f5f9",
            fg=MUTED,
            font=("Segoe UI", 8),
            wraplength=360,
            justify="left"
        ).pack(anchor="w")

    def _add_attachment_bubble_content(self, parent, row):
        attachment_name = row.get("attachment_name") or "Attachment"
        attachment_path = row.get("attachment_path")
        full_path = os.path.join(UPLOAD_FOLDER, attachment_path)

        file_card = tk.Frame(
            parent,
            bg="#ffffff",
            highlightbackground="#dce3ea",
            highlightthickness=1,
            padx=10,
            pady=8
        )
        file_card.pack(anchor="w", fill="x")

        icon_text = "PDF" if attachment_name.lower().endswith(".pdf") else "DOC"

        icon = tk.Label(
            file_card,
            text=icon_text,
            bg="#d93025" if icon_text == "PDF" else "#2b579a",
            fg=WHITE,
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=5
        )
        icon.pack(side="left", padx=(0, 10))

        info = tk.Frame(file_card, bg="#ffffff")
        info.pack(side="left", fill="x", expand=True)

        tk.Button(
            info,
            text=attachment_name,
            command=lambda p=full_path: self._open_attachment(p),
            bg="#ffffff",
            fg=DARK,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=0
        ).pack(anchor="w", fill="x")

        tk.Label(
            info,
            text="Click to open file",
            bg="#ffffff",
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w")

    def _add_file_list_item(self, parent, row):
        attachment_name = row.get("attachment_name") or "Attachment"
        attachment_path = row.get("attachment_path")
        full_path = os.path.join(UPLOAD_FOLDER, attachment_path)

        item = tk.Frame(
            parent,
            bg=BG_WHITE,
            highlightbackground="#dce3ea",
            highlightthickness=1,
            padx=12,
            pady=10
        )
        item.pack(fill="x", pady=(0, 8))

        tk.Label(
            item,
            text="📄",
            bg=BG_WHITE,
            fg=BLUE,
            font=("Segoe UI", 16)
        ).pack(side="left", padx=(0, 10))

        info = tk.Frame(item, bg=BG_WHITE)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(
            info,
            text=attachment_name,
            bg=BG_WHITE,
            fg=DARK,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        sender = "You" if row["sender_role"] == self.current_role else self.other_user_name

        tk.Label(
            info,
            text=f"Shared by {sender} • {str(row['sent_at'])[:16]}",
            bg=BG_WHITE,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(2, 0))

        tk.Button(
            item,
            text="Open",
            command=lambda p=full_path: self._open_attachment(p),
            bg="#f1f5f9",
            fg=BLUE,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=5,
            cursor="hand2"
        ).pack(side="right")

    def _show_empty_state(self, text):
        self._clear_messages()

        empty = tk.Frame(self.msg_frame, bg="#f7f9fc")
        empty.pack(fill="both", expand=True, padx=20, pady=90)

        tk.Label(
            empty,
            text="💬",
            bg="#f7f9fc",
            fg=MUTED,
            font=("Segoe UI", 30)
        ).pack()

        tk.Label(
            empty,
            text=text,
            bg="#f7f9fc",
            fg=MUTED,
            font=("Segoe UI", 11),
            justify="center"
        ).pack(pady=(8, 0))

    # =========================
    # REPLY / EDIT / DELETE
    # =========================
    def _start_reply(self, row):
        self.reply_to_message = row

        sender_name = (
            "You"
            if row["sender_role"] == self.current_role
            else self.other_user_name
        )

        self.reply_title.config(text=f"Replying to {sender_name}")
        self.reply_text.config(text=self._message_summary(row))

        if not self.reply_preview.winfo_ismapped():
            self.reply_preview.place(
                relx=0,
                rely=1,
                relwidth=1,
                height=60,
                anchor="sw"
            )
            self.reply_preview.lift()

        self.message_entry.focus_set()

    def _cancel_reply(self):
        self.reply_to_message = None

        if self.reply_preview is not None:
            self.reply_preview.place_forget()

    def _edit_message(self, row):
        message_id = self._get_message_id(row)

        if not message_id:
            messagebox.showerror("Error", "Message ID was not found.")
            return

        old_body = row.get("body") or ""

        new_body = simpledialog.askstring(
            "Edit Message",
            "Update your message:",
            initialvalue=old_body,
            parent=self
        )

        if new_body is None:
            return

        new_body = new_body.strip()

        if not new_body:
            messagebox.showwarning("Empty Message", "Message cannot be empty.")
            return

        query("""
            UPDATE messages
            SET body = %s, edited_at = NOW()
            WHERE message_id = %s
            AND sender_role = %s
            AND sender_id = %s
        """, (
            new_body,
            message_id,
            self.current_role,
            self.current_user_id
        ))

        self._load_messages()

    def _delete_message(self, row):
        message_id = self._get_message_id(row)

        if not message_id:
            messagebox.showerror("Error", "Message ID was not found.")
            return

        confirm = messagebox.askyesno(
            "Delete Message",
            "Are you sure you want to delete this message?"
        )

        if not confirm:
            return

        query("""
            UPDATE messages
            SET body = 'This message was deleted',
                attachment_path = NULL,
                attachment_name = NULL,
                is_deleted = 1
            WHERE message_id = %s
            AND sender_role = %s
            AND sender_id = %s
        """, (
            message_id,
            self.current_role,
            self.current_user_id
        ))

        self._load_messages()

    # =========================
    # SEND
    # =========================
    def _send_message(self):
        body = self.msg_var.get().strip()

        if not body:
            return

        if not self.other_user_id:
            messagebox.showwarning("No Conversation", "Please select a conversation first.")
            return

        reply_id = None
        if self.reply_to_message:
            reply_id = self._get_message_id(self.reply_to_message)

        try:
            query("""
                INSERT INTO messages
                (
                    sender_role,
                    sender_id,
                    receiver_role,
                    receiver_id,
                    body,
                    reply_to_message_id
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                self.current_role,
                self.current_user_id,
                self.other_role,
                self.other_user_id,
                body,
                reply_id
            ))
        except Exception:
            query("""
                INSERT INTO messages
                (sender_role, sender_id, receiver_role, receiver_id, body)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.current_role,
                self.current_user_id,
                self.other_role,
                self.other_user_id,
                body
            ))

        create_notification(
            self.other_role,
            self.other_user_id,
            "message",
            "New Message",
            f"{SESSION['name']}: {body[:60]}"
        )

        self.msg_var.set("")
        self._cancel_reply()
        self.active_tab = "chat"
        self._update_tab_styles()
        self._load_messages()

    def _send_attachment(self):
        if not self.other_user_id:
            messagebox.showwarning("No Conversation", "Please select a conversation first.")
            return

        path = filedialog.askopenfilename(
            filetypes=[
                ("Documents", "*.pdf *.docx"),
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        ext = path.rsplit(".", 1)[-1].lower()

        if ext not in ("pdf", "docx"):
            messagebox.showerror("Invalid File", "Only PDF and DOCX files are allowed.")
            return

        size_kb = os.path.getsize(path) // 1024

        if size_kb > 10240:
            messagebox.showerror("Too Large", "Attachment must not exceed 10 MB.")
            return

        safe_name = (
            f"msg_{self.current_role}_"
            f"{self.current_user_id}_"
            f"{uuid.uuid4().hex[:10]}.{ext}"
        )

        destination = os.path.join(UPLOAD_FOLDER, safe_name)

        try:
            shutil.copy2(path, destination)
        except Exception as e:
            messagebox.showerror("Attachment Error", f"Could not attach file: {e}")
            return

        original_name = os.path.basename(path)

        reply_id = None
        if self.reply_to_message:
            reply_id = self._get_message_id(self.reply_to_message)

        try:
            query("""
                INSERT INTO messages
                (
                    sender_role,
                    sender_id,
                    receiver_role,
                    receiver_id,
                    body,
                    attachment_path,
                    attachment_name,
                    reply_to_message_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.current_role,
                self.current_user_id,
                self.other_role,
                self.other_user_id,
                f"[Attachment: {original_name}]",
                safe_name,
                original_name,
                reply_id
            ))
        except Exception:
            query("""
                INSERT INTO messages
                (
                    sender_role,
                    sender_id,
                    receiver_role,
                    receiver_id,
                    body,
                    attachment_path,
                    attachment_name
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                self.current_role,
                self.current_user_id,
                self.other_role,
                self.other_user_id,
                f"[Attachment: {original_name}]",
                safe_name,
                original_name
            ))

        create_notification(
            self.other_role,
            self.other_user_id,
            "message",
            "New Attachment",
            f"{SESSION['name']} sent a file: {original_name}"
        )

        self._cancel_reply()
        self.active_tab = "chat"
        self._update_tab_styles()
        self._load_messages()

    # =========================
    # FORMATTERS / HELPERS
    # =========================
    def _update_tab_styles(self):
        if self.active_tab == "chat":
            self.chat_tab_btn.config(fg=BLUE, font=("Segoe UI", 10, "bold"))
            self.files_tab_btn.config(fg=MUTED, font=("Segoe UI", 10))
            if not self.input_outer.winfo_ismapped():
                self.input_outer.grid(row=3, column=0, sticky="ew")
        else:
            self.chat_tab_btn.config(fg=MUTED, font=("Segoe UI", 10))
            self.files_tab_btn.config(fg=BLUE, font=("Segoe UI", 10, "bold"))
            self.input_outer.grid_remove()

    def _is_deleted(self, row):
        value = row.get("is_deleted")
        return value in (1, "1", True)

    def _message_summary(self, row):
        if self._is_deleted(row):
            return "This message was deleted"

        if row.get("attachment_name"):
            return f"📄 {row.get('attachment_name')}"

        body = row.get("body") or ""
        if len(body) > 90:
            return body[:90] + "..."
        return body

    def _format_time(self, value):
        dt = self._parse_datetime(value)
        if not dt:
            return str(value)[11:16] if value else ""
        return dt.strftime("%H:%M")

    def _format_date_separator(self, value):
        dt = self._parse_datetime(value)

        if not dt:
            return str(value)[:10] if value else ""

        message_date = dt.date()
        today = date.today()
        yesterday = today - timedelta(days=1)

        if message_date == today:
            return "Today"

        if message_date == yesterday:
            return "Yesterday"

        if today - message_date < timedelta(days=7):
            return dt.strftime("%A")

        return dt.strftime("%Y-%m-%d")

    def _parse_datetime(self, value):
        if isinstance(value, datetime):
            return value

        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())

        if not value:
            return None

        text = str(value)

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(text[:19], fmt)
            except Exception:
                pass

        return None

    def _refresh_messages(self):
        self._load_content()

    def _open_attachment(self, path):
        if not path or not os.path.exists(path):
            messagebox.showerror("File Not Found", "The attachment could not be found.")
            return

        open_file(path)

    def _scroll_to_bottom(self):
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(1.0)

    def _resize_message_frame(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _scroll_messages(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _set_avatar_text(self, name):
        if not name:
            self.avatar_label.config(text="U")
            return

        parts = name.split()

        if len(parts) >= 2:
            initials = parts[0][0] + parts[1][0]
        else:
            initials = name[:2]

        self.avatar_label.config(text=initials.upper())


class StudentMessages(ChatMessagesBase):
    def __init__(self, parent):
        super().__init__(parent, current_role="student")


class SupervisorMessages(ChatMessagesBase):
    def __init__(self, parent):
        super().__init__(parent, current_role="supervisor")

