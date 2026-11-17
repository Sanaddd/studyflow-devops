import os
import sqlite3


DATA_DIR = os.environ.get("DATA_DIR", "data")
DATABASE_PATH = os.path.join(DATA_DIR, "courses.db")


def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def check_db():
    """Return True if this service can read from and write to its own database.

    Used by GET /health. The write is rolled back, so the check leaves no data behind.
    """
    try:
        connection = get_connection()
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS health_check (id INTEGER PRIMARY KEY, checked_at TEXT)"
            )
            connection.execute("INSERT INTO health_check (checked_at) VALUES (datetime('now'))")
            connection.execute("SELECT COUNT(*) FROM health_check").fetchone()
            connection.rollback()
        finally:
            connection.close()
        return True
    except Exception:
        return False
