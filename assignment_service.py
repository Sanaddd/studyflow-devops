from database import get_connection


def get_all_assignments():
    connection = get_connection()

    assignments = connection.execute(
        """
        SELECT assignments.id,
               assignments.title,
               assignments.due_date,
               assignments.priority,
               assignments.completed,
               assignments.course_id,
               courses.name AS course_name
        FROM assignments
        JOIN courses ON assignments.course_id = courses.id
        ORDER BY assignments.due_date
        """
    ).fetchall()

    connection.close()

    return assignments


def add_assignment(title, due_date, priority, course_id):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO assignments (title, due_date, priority, course_id)
        VALUES (?, ?, ?, ?)
        """,
        (title, due_date, priority, course_id),
    )

    connection.commit()
    connection.close()