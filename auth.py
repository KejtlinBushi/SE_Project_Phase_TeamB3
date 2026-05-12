"""
auth.py
Password hashing and user session management.
CEN 302 Software Engineering | Group III | Epoka University
"""

import bcrypt

# ─────────────────────────────────────────────────────────────
# SESSION  — stores the currently logged-in user
# ─────────────────────────────────────────────────────────────
SESSION = {"user_id": None, "role": None, "name": None}


def login_user(user_id, role, name):
    """Set the current session after successful login."""
    SESSION["user_id"] = user_id
    SESSION["role"]    = role
    SESSION["name"]    = name


def logout_user():
    """Clear the session on logout."""
    SESSION["user_id"] = None
    SESSION["role"]    = None
    SESSION["name"]    = None


def is_logged_in():
    return SESSION["user_id"] is not None


# ─────────────────────────────────────────────────────────────
# PASSWORD HELPERS
# ─────────────────────────────────────────────────────────────
def hash_password(plain_text):
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(plain_text.encode(), bcrypt.gensalt(rounds=12)).decode()


def check_password(plain_text, hashed):
    """Check a plain-text password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_text.encode(), hashed.encode())
    except Exception:
        return False
