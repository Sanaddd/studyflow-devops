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

def toggle_assignment_complete(assignment_id):
    connection = get_connection()

    connection.execute(
        """
        UPDATE assignments
        SET completed = CASE
            WHEN completed = 0 THEN 1
            ELSE 0
        END
        WHERE id = ?
        """,
        (assignment_id,),
    )

    connection.commit()
    connection.close()


def delete_assignment(assignment_id):
    connection = get_connection()

    connection.execute(
        "DELETE FROM assignments WHERE id = ?",
        (assignment_id,),
    )

    connection.commit()
    connection.close()