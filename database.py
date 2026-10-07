import os
import sqlite3


DATA_DIR = os.environ.get("DATA_DIR", "data")
DATABASE_PATH = os.path.join(DATA_DIR, "studyflow.db")


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

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            course_id INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
        """
    )
    
    connection.commit()
    connection.close()