import os
import sys
import tkinter as tk
from tkinter import messagebox
import vlc

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ui import BG_MAIN, BLUE, WHITE, page_header


class StudentHelp(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_MAIN)

        page_header(
            self,
            "Need Help?",
            "Watch the tutorial video to learn how to use the student dashboard"
        )

        self.video_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "student_tutorial.mp4")
        )

        self.instance = vlc.Instance(
            "--avcodec-hw=none",
            "--vout=directdraw",
            "--no-video-title-show",
            "--quiet"
        )

        self.player = self.instance.media_player_new()
        self.is_playing = False

        self.build_ui()

    def build_ui(self):
        main = tk.Frame(self, bg=BG_MAIN)
        main.pack(fill="both", expand=True, padx=35, pady=(10, 20))

        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=0)
        main.grid_rowconfigure(2, weight=0)
        main.grid_columnconfigure(0, weight=1)

        self.video_panel = tk.Frame(main, bg="black")
        self.video_panel.grid(row=0, column=0, sticky="nsew")

        self.progress = tk.Scale(
            main,
            from_=0,
            to=1000,
            orient="horizontal",
            showvalue=False,
            bg="#0f172a",
            troughcolor="#475569",
            activebackground=BLUE,
            highlightthickness=0
        )
        self.progress.grid(row=1, column=0, sticky="ew")
        self.progress.bind("<ButtonRelease-1>", self.seek_video)

        controls = tk.Frame(main, bg="#0f172a", height=80)
        controls.grid(row=2, column=0, sticky="ew")
        controls.grid_propagate(False)

        self.play_btn = tk.Button(
            controls,
            text="▶ Play",
            command=self.toggle_play,
            bg="#0f172a",
            fg=WHITE,
            activebackground="#0f172a",
            activeforeground=WHITE,
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        )
        self.play_btn.pack(side="left", padx=(20, 10), pady=20)

        self.stop_btn = tk.Button(
            controls,
            text="■ Stop",
            command=self.stop_video,
            bg="#0f172a",
            fg=WHITE,
            activebackground="#0f172a",
            activeforeground=WHITE,
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        )
        self.stop_btn.pack(side="left", padx=10, pady=20)

        self.time_label = tk.Label(
            controls,
            text="00:00 / 00:00",
            bg="#0f172a",
            fg=WHITE,
            font=("Segoe UI", 12, "bold")
        )
        self.time_label.pack(side="left", padx=15)

        spacer = tk.Frame(controls, bg="#0f172a")
        spacer.pack(side="left", fill="x", expand=True)

        tk.Button(
            controls,
            text="↶ 10s",
            command=lambda: self.skip_seconds(-10),
            bg="#0f172a",
            fg=WHITE,
            activebackground="#0f172a",
            activeforeground=WHITE,
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        ).pack(side="left", padx=10, pady=20)

        tk.Button(
            controls,
            text="↷ 10s",
            command=lambda: self.skip_seconds(10),
            bg="#0f172a",
            fg=WHITE,
            activebackground="#0f172a",
            activeforeground=WHITE,
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2"
        ).pack(side="left", padx=10, pady=20)

        self.volume = tk.Scale(
            controls,
            from_=0,
            to=100,
            orient="horizontal",
            showvalue=False,
            command=self.change_volume,
            bg="#0f172a",
            troughcolor="#475569",
            activebackground=BLUE,
            highlightthickness=0,
            length=140
        )
        self.volume.set(80)
        self.volume.pack(side="left", padx=(10, 20), pady=15)

        self.after(1000, self.load_video)

    def load_video(self):
        if not os.path.exists(self.video_path):
            messagebox.showerror(
                "Video Not Found",
                "Please save the video as:\nassets/student_tutorial.mp4"
            )
            return

        media = self.instance.media_new(self.video_path)
        media.add_option(":avcodec-hw=none")
        media.add_option(":no-drop-late-frames")
        media.add_option(":no-skip-frames")

        self.player.set_media(media)
        self.update_idletasks()
        self.player.set_hwnd(self.video_panel.winfo_id())
        self.player.audio_set_volume(80)

        self.player.play()
        self.is_playing = True
        self.play_btn.config(text="⏸ Pause")

        self.after(1000, self.update_progress)

    def toggle_play(self):
        if self.is_playing:
            self.player.pause()
            self.play_btn.config(text="▶ Play")
            self.is_playing = False
        else:
            self.player.play()
            self.play_btn.config(text="⏸ Pause")
            self.is_playing = True

    def stop_video(self):
        self.player.stop()
        self.is_playing = False
        self.play_btn.config(text="▶ Play")
        self.progress.set(0)
        self.time_label.config(text="00:00 / 00:00")

    def skip_seconds(self, seconds):
        current = self.player.get_time()
        length = self.player.get_length()

        if current < 0:
            return

        new_time = max(0, current + seconds * 1000)

        if length > 0:
            new_time = min(new_time, length)

        self.player.set_time(new_time)

    def seek_video(self, event=None):
        length = self.player.get_length()

        if length > 0:
            value = self.progress.get()
            self.player.set_time(int((value / 1000) * length))

    def update_progress(self):
        length = self.player.get_length()
        current = self.player.get_time()

        if length > 0 and current >= 0:
            self.progress.set(int((current / length) * 1000))
            self.time_label.config(
                text=f"{self.format_time(current)} / {self.format_time(length)}"
            )

        self.after(1000, self.update_progress)

    def change_volume(self, value):
        self.player.audio_set_volume(int(float(value)))

    def format_time(self, milliseconds):
        total_seconds = int(milliseconds / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"