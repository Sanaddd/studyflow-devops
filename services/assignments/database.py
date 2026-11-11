import os
import sqlite3


DATA_DIR = os.environ.get("DATA_DIR", "data")
DATABASE_PATH = os.path.join(DATA_DIR, "assignments.db")


def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    connection = get_connection()

    # course_id refers to a course owned by the courses service.
    # There is no FOREIGN KEY because that table lives in another database.
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            course_id INTEGER NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()
