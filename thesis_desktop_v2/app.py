"""
app.py — Entry point for Thesis Progress Tracker Desktop App
CEN 302 Software Engineering | Group III | Epoka University
Run: python app.py
"""

import tkinter as tk
from tkinter import messagebox

from database import test_connection
from auth import SESSION, logout_user
from pages.login import LoginPage


from pages.student import (StudentDashboard, StudentSubmissions,
                            StudentDeadlines, StudentMilestones,
                            StudentMessages,  StudentMeetings,
                            StudentNotifications, StudentProfile)
from pages.supervisor import (SupervisorDashboard, SupervisorReviews,
                               SupervisorDeadlines, SupervisorMilestones,
                               SupervisorMeetings,  SupervisorMessages,
                               SupervisorNotifications, SupervisorProfile)
from pages.admin import (AdminDashboard, AdminUsers, AdminAssignments,
                         AdminActivityLog, AdminNotifications, AdminProfile)
from base_app import BaseApp


class StudentApp(BaseApp):
    NAV_ITEMS = [
        ("dashboard",      "🏠", "Home"),
        ("submissions",    "📄", "Submissions"),
        ("deadlines",      "📅", "Deadlines"),
        ("milestones",     "🎯", "Milestones"),
        ("messages",       "✉",  "Messages"),
        ("meetings",       "📆", "Meetings"),
        ("notifications",  "🔔", "Notifications"),
        ("profile",        "👤", "My Profile"),
    ]
    PAGES = {
        "dashboard":     StudentDashboard,
        "submissions":   StudentSubmissions,
        "deadlines":     StudentDeadlines,
        "milestones":    StudentMilestones,
        "messages":      StudentMessages,
        "meetings":      StudentMeetings,
        "notifications": StudentNotifications,
        "profile":       StudentProfile,
    }


class SupervisorApp(BaseApp):
    NAV_ITEMS = [
        ("dashboard",     "🏠", "Home"),
        ("reviews",       "✓",  "Reviews"),
        ("deadlines",     "📅", "Deadlines"),
        ("milestones",    "🎯", "Milestones"),
        ("meetings",      "📆", "Meetings"),
        ("messages",      "✉",  "Messages"),
        ("notifications", "🔔", "Notifications"),
        ("profile",       "👤", "My Profile"),
    ]
    PAGES = {
        "dashboard":     SupervisorDashboard,
        "reviews":       SupervisorReviews,
        "deadlines":     SupervisorDeadlines,
        "milestones":    SupervisorMilestones,
        "meetings":      SupervisorMeetings,
        "messages":      SupervisorMessages,
        "notifications": SupervisorNotifications,
        "profile":       SupervisorProfile,
    }


class AdminApp(BaseApp):
    NAV_ITEMS = [
        ("dashboard",     "🏠", "Home"),
        ("users",         "👥", "Users"),
        ("assignments",   "🔗", "Assignments"),
        ("activity",      "📋", "Activity Log"),
        ("notifications", "🔔", "Notifications"),
        ("profile",       "👤", "My Profile"),
    ]
    PAGES = {
        "dashboard":     AdminDashboard,
        "users":         AdminUsers,
        "assignments":   AdminAssignments,
        "activity":      AdminActivityLog,
        "notifications": AdminNotifications,
        "profile":       AdminProfile,
    }


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Thesis Progress Tracker — Epoka University")
        self.geometry("1150x700")
        self.minsize(950, 620)
        self.configure(bg="#1a5276")
        self.resizable(True, True)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1150) // 2
        y = (self.winfo_screenheight() - 700)  // 2
        self.geometry(f"+{x}+{y}")
        self.current_frame = None
        self.show_login()

    def clear(self):
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None

    def show_login(self):
        self.clear()
        self.current_frame = LoginPage(self)
        self.current_frame.pack(fill="both", expand=True)

    def show_main(self):
        self.clear()
        role = SESSION["role"]
        if role == "student":
            self.current_frame = StudentApp(self)
        elif role == "supervisor":
            self.current_frame = SupervisorApp(self)
        elif role == "admin":
            self.current_frame = AdminApp(self)
        if self.current_frame:
            self.current_frame.pack(fill="both", expand=True)

    def logout(self):
        logout_user()
        self.show_login()


if __name__ == "__main__":
    try:
        test_connection()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Database Error",
            f"Cannot connect to MySQL.\n\n"
            f"Make sure XAMPP MySQL is running and\n"
            f"database 'thesis_tracker' exists.\n\nError: {e}")
        root.destroy()
        raise SystemExit(1)
    App().mainloop()
