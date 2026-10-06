from database import get_connection


def get_all_courses():
    connection = get_connection()

    courses = connection.execute(
        "SELECT id, name, code FROM courses ORDER BY name"
    ).fetchall()

    connection.close()

    return courses


def add_course(name, code):
    connection = get_connection()

    connection.execute(
        "INSERT INTO courses (name, code) VALUES (?, ?)",
        (name, code),
    )

    connection.commit()
    connection.close()


def delete_course(course_id):
    connection = get_connection()

    connection.execute(
        "DELETE FROM courses WHERE id = ?",
        (course_id,),
    )

    connection.commit()
    connection.close()