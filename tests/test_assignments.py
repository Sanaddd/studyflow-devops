import os
import tempfile

import assignment_service
import course_service
import database


def setup_module():
    temp_dir = tempfile.mkdtemp()

    database.DATA_DIR = temp_dir
    database.DATABASE_PATH = os.path.join(temp_dir, "test.db")

    database.init_db()


def setup_function():
    connection = database.get_connection()
    connection.execute("DELETE FROM assignments")
    connection.execute("DELETE FROM courses")
    connection.commit()
    connection.close()

    course_service.add_course("Artificial Intelligence", "CS301")


def test_add_and_get_assignment():
    courses = course_service.get_all_courses()
    course_id = courses[0]["id"]

    assignment_service.add_assignment(
        "AI Report",
        "2026-10-20",
        "High",
        course_id,
    )

    assignments = assignment_service.get_all_assignments()

    assert len(assignments) == 1
    assert assignments[0]["title"] == "AI Report"
    assert assignments[0]["priority"] == "High"
    assert assignments[0]["course_name"] == "Artificial Intelligence"


def test_toggle_assignment_complete():
    courses = course_service.get_all_courses()
    course_id = courses[0]["id"]

    assignment_service.add_assignment(
        "AI Report",
        "2026-10-20",
        "High",
        course_id,
    )

    assignments = assignment_service.get_all_assignments()
    assignment_id = assignments[0]["id"]

    assignment_service.toggle_assignment_complete(assignment_id)

    updated_assignments = assignment_service.get_all_assignments()

    assert updated_assignments[0]["completed"] == 1


def test_delete_assignment():
    courses = course_service.get_all_courses()
    course_id = courses[0]["id"]

    assignment_service.add_assignment(
        "AI Report",
        "2026-10-20",
        "High",
        course_id,
    )

    assignments = assignment_service.get_all_assignments()
    assignment_id = assignments[0]["id"]

    assignment_service.delete_assignment(assignment_id)

    remaining_assignments = assignment_service.get_all_assignments()

    assert len(remaining_assignments) == 0


def test_overdue_assignment():
    courses = course_service.get_all_courses()
    course_id = courses[0]["id"]

    assignment_service.add_assignment(
        "Old Assignment",
        "2020-01-01",
        "Medium",
        course_id,
    )

    assignments = assignment_service.get_all_assignments()

    assert assignments[0]["overdue"] is True