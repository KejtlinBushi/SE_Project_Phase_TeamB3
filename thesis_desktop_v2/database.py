"""
database.py
Handles MySQL connection to XAMPP database.
CEN 302 Software Engineering | Group III | Epoka University
"""

import pymysql
import pymysql.cursors

DB_CONFIG = {
    "host":        "localhost",
    "port":        3306,
    "user":        "root",
    "password":    "",           # XAMPP default = no password
    "database":    "thesis_tracker",
    "charset":     "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit":  True,
}


def get_db():
    """Open and return a new database connection."""
    return pymysql.connect(**DB_CONFIG)


def query(sql, args=(), one=False):
    """
    Run any SQL query.
    - SELECT  → returns one row (dict) or list of rows
    - INSERT  → returns the new row's ID
    - UPDATE/DELETE → returns number of rows affected
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, args)
        if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            conn.commit()
            if sql.strip().upper().startswith("INSERT"):
                return cur.lastrowid
            return cur.rowcount
        return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()


def test_connection():
    """
    Test the database connection on startup.
    Returns True if connected, raises Exception if not.
    """
    conn = pymysql.connect(**DB_CONFIG)
    conn.close()
    return True
