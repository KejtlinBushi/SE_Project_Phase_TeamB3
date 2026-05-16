import os
import tkinter as tk
from tkinter import messagebox
import vlc

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

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self.is_playing = False
        self.slider_is_updating = False

        self.build_ui()

    def build_ui(self):
        main = tk.Frame(self, bg=BG_MAIN)
        main.pack(fill="both", expand=True, padx=35, pady=15)

        controls = tk.Frame(main, bg="#0f172a", height=75)
        controls.pack(fill="x", side="bottom")
        controls.pack_propagate(False)

        self.play_btn = tk.Button(
            controls, text="▶ Play", command=self.toggle_play,
            bg="#0f172a", fg=WHITE, relief="flat",
            font=("Segoe UI", 12, "bold"), cursor="hand2"
        )
        self.play_btn.pack(side="left", padx=18, pady=18)

        self.stop_btn = tk.Button(
            controls, text="■ Stop", command=self.stop_video,
            bg="#0f172a", fg=WHITE, relief="flat",
            font=("Segoe UI", 12, "bold"), cursor="hand2"
        )
        self.stop_btn.pack(side="left", padx=8, pady=18)

        self.time_label = tk.Label(
            controls, text="00:00 / 00:00",
            bg="#0f172a", fg=WHITE,
            font=("Segoe UI", 12, "bold")
        )
        self.time_label.pack(side="left", padx=15)

        tk.Button(
            controls, text="↶ 10s", command=lambda: self.skip_seconds(-10),
            bg="#0f172a", fg=WHITE, relief="flat",
            font=("Segoe UI", 12, "bold"), cursor="hand2"
        ).pack(side="left", padx=10, pady=18)

        tk.Button(
            controls, text="↷ 10s", command=lambda: self.skip_seconds(10),
            bg="#0f172a", fg=WHITE, relief="flat",
            font=("Segoe UI", 12, "bold"), cursor="hand2"
        ).pack(side="left", padx=10, pady=18)

        self.volume = tk.Scale(
            controls, from_=0, to=100, orient="horizontal",
            showvalue=False, command=self.change_volume,
            bg="#0f172a", troughcolor="#475569",
            activebackground=BLUE, highlightthickness=0,
            length=140
        )
        self.volume.set(80)
        self.volume.pack(side="right", padx=20, pady=15)

        self.progress = tk.Scale(
            main, from_=0, to=1000, orient="horizontal",
            showvalue=False, command=self.seek_video,
            bg="#0f172a", troughcolor="#475569",
            activebackground=BLUE, highlightthickness=0
        )
        self.progress.pack(fill="x", side="bottom")

        self.video_panel = tk.Frame(main, bg="black")
        self.video_panel.pack(fill="both", expand=True, side="top")

        self.after(1000, self.load_video)

    def load_video(self):
        if not os.path.exists(self.video_path):
            messagebox.showerror(
                "Video Not Found",
                "Please save the video as:\nassets/student_tutorial.mp4"
            )
            return

        media = self.instance.media_new(self.video_path)
        self.player.set_media(media)

        self.update_idletasks()

        if os.name == "nt":
            self.player.set_hwnd(self.video_panel.winfo_id())
        else:
            self.player.set_xwindow(self.video_panel.winfo_id())

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

    def seek_video(self, value):
        if self.slider_is_updating:
            return

        length = self.player.get_length()

        if length > 0:
            self.player.set_time(int((int(value) / 1000) * length))

    def update_progress(self):
        length = self.player.get_length()
        current = self.player.get_time()

        if length > 0 and current >= 0:
            self.slider_is_updating = True
            self.progress.set(int((current / length) * 1000))
            self.slider_is_updating = False
            self.time_label.config(
                text=f"{self.format_time(current)} / {self.format_time(length)}"
            )

        self.after(700, self.update_progress)

    def change_volume(self, value):
        self.player.audio_set_volume(int(float(value)))

    def format_time(self, milliseconds):
        total_seconds = int(milliseconds / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"