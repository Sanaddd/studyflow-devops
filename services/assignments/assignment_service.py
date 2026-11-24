from datetime import date

from database import get_connection


def get_all_assignments():
    connection = get_connection()
    try:
        cursor = connection.cursor(as_dict=True)
        cursor.execute(
            """
            SELECT id, title, description, due_date, priority, completed, course_id
            FROM assignments
            ORDER BY due_date
            """
        )
        rows = cursor.fetchall()
    finally:
        connection.close()

    today = date.today()

    assignment_list = []

    for row in rows:
        assignment_data = dict(row)

        # SQL Server returns DATE as a date and BIT as a bool
        assignment_data["overdue"] = row["due_date"] < today and not row["completed"]
        assignment_data["due_date"] = row["due_date"].isoformat()
        assignment_data["completed"] = bool(row["completed"])

        assignment_list.append(assignment_data)

    return assignment_list


def add_assignment(title, due_date, priority, course_id, description=""):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO assignments (title, description, due_date, priority, course_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (title, description, due_date, priority, course_id),
        )
        connection.commit()
    finally:
        connection.close()


def toggle_assignment_complete(assignment_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE assignments
            SET completed = CASE WHEN completed = 0 THEN 1 ELSE 0 END
            WHERE id = %s
            """,
            (assignment_id,),
        )
        connection.commit()
    finally:
        connection.close()


def delete_assignment(assignment_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM assignments WHERE id = %s", (assignment_id,))
        connection.commit()
    finally:
        connection.close()
