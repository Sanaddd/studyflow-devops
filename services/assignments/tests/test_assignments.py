import app  # noqa: F401  (importing the app applies the migrations)
import assignment_service
import database


def setup_function():
    connection = database.connect()
    connection.cursor().execute("DELETE FROM assignments")
    connection.commit()
    connection.close()


# The course lives in the courses service now; assignments only store its id.
COURSE_ID = 1


def test_add_and_get_assignment():
    course_id = COURSE_ID

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
    assert assignments[0]["course_id"] == COURSE_ID


def test_toggle_assignment_complete():
    course_id = COURSE_ID

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

    assert updated_assignments[0]["completed"] is True


def test_delete_assignment():
    course_id = COURSE_ID

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
    course_id = COURSE_ID

    assignment_service.add_assignment(
        "Old Assignment",
        "2020-01-01",
        "Medium",
        course_id,
    )

    assignments = assignment_service.get_all_assignments()

    assert assignments[0]["overdue"] is True


def test_description_defaults_to_empty():
    assignment_service.add_assignment("No description", "2026-10-20", "Low", COURSE_ID)

    assert assignment_service.get_all_assignments()[0]["description"] == ""


def test_post_assignment_with_description():
    client = app.app.test_client()

    response = client.post(
        "/assignments",
        json={"title": "Report", "description": "ADRs and diagrams", "due_date": "2026-12-01",
              "priority": "High", "course_id": COURSE_ID},
    )

    assert response.status_code == 201
    assert response.get_json()["description"] == "ADRs and diagrams"
    assert assignment_service.get_all_assignments()[0]["description"] == "ADRs and diagrams"
