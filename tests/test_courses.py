import os
import tempfile

import database
import course_service


def setup_module():
    temp_dir = tempfile.mkdtemp()

    database.DATA_DIR = temp_dir
    database.DATABASE_PATH = os.path.join(temp_dir, "test.db")

    database.init_db()


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