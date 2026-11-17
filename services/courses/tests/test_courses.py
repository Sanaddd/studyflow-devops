import app  # noqa: F401  (importing the app applies the migrations)
import course_service
import database


def setup_module():
    connection = database.connect()
    connection.cursor().execute("DELETE FROM courses")
    connection.commit()
    connection.close()


def test_add_and_get_course():
    course_service.add_course("Artificial Intelligence", "CS301")

    courses = course_service.get_all_courses()

    assert len(courses) == 1
    assert courses[0]["name"] == "Artificial Intelligence"
    assert courses[0]["code"] == "CS301"


def test_update_course():
    courses = course_service.get_all_courses()
    course_id = courses[0]["id"]

    course_service.update_course(
        course_id,
        "AI Fundamentals",
        "CS305",
    )

    updated_courses = course_service.get_all_courses()

    assert updated_courses[0]["name"] == "AI Fundamentals"
    assert updated_courses[0]["code"] == "CS305"


def test_delete_course():
    courses = course_service.get_all_courses()
    course_id = courses[0]["id"]

    course_service.delete_course(course_id)

    remaining_courses = course_service.get_all_courses()

    assert len(remaining_courses) == 0
