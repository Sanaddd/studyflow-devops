from database import get_connection


def get_all_courses():
    connection = get_connection()
    try:
        cursor = connection.cursor(as_dict=True)
        cursor.execute("SELECT id, name, code FROM courses ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def add_course(name, code):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO courses (name, code) VALUES (%s, %s)",
            (name, code),
        )
        connection.commit()
    finally:
        connection.close()


def update_course(course_id, name, code):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE courses SET name = %s, code = %s WHERE id = %s",
            (name, code, course_id),
        )
        connection.commit()
    finally:
        connection.close()


def delete_course(course_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        connection.commit()
    finally:
        connection.close()
