import pymssql
import pytest

import app  # importing the app applies the migrations
import assignment_service
import database
from courses_client import CoursesUnavailable


def setup_function():
    connection = database.connect()
    connection.cursor().execute("DELETE FROM assignments")
    connection.commit()
    connection.close()


# The course lives in the courses service now; assignments only store its id.
COURSE_ID = 1

VALID = {"title": "Report", "due_date": "2026-12-01", "priority": "High", "course_id": COURSE_ID}


@pytest.fixture(autouse=True)
def courses_stub(monkeypatch):
    # The courses service is replaced by a stub that knows exactly one course
    monkeypatch.setattr(app, "fetch_course_names", lambda: {COURSE_ID: "Software Development"})


def post(body):
    return app.app.test_client().post("/assignments", json=body)


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
    response = post({**VALID, "description": "ADRs and diagrams"})

    assert response.status_code == 201
    assert response.get_json()["description"] == "ADRs and diagrams"
    assert assignment_service.get_all_assignments()[0]["description"] == "ADRs and diagrams"


def test_post_rejects_invalid_values():
    bad_values = [
        {"due_date": "notadate"},
        {"due_date": "tomorrow"},
        {"due_date": 20261201},
        {"priority": "Whatever"},
        {"priority": ["High"]},
        {"course_id": "abc"},
        {"course_id": True},
        {"course_id": 1.5},
        {"course_id": [COURSE_ID]},
        {"course_id": 0},
        {"course_id": -1},
        {"title": "x" * 201},
        {"title": None},
        {"title": 123},
        {"description": "x" * 501},
        {"description": 5},
    ]

    for bad in bad_values:
        response = post({**VALID, **bad})
        assert response.status_code == 400, bad
        assert "error" in response.get_json()

    assert assignment_service.get_all_assignments() == []


def test_post_rejects_a_missing_field():
    for field in ("title", "due_date", "priority", "course_id"):
        body = {key: value for key, value in VALID.items() if key != field}
        assert post(body).status_code == 400, field

    assert assignment_service.get_all_assignments() == []


def test_post_rejects_a_body_that_is_not_a_json_object():
    client = app.app.test_client()

    for body in (["not", "an", "object"], "text", 5):
        assert client.post("/assignments", json=body).status_code == 400
    assert client.post("/assignments", data="not json").status_code == 400
    assert client.post("/assignments").status_code == 400


def test_post_rejects_a_course_that_does_not_exist():
    response = post({**VALID, "course_id": 999})

    assert response.status_code == 400
    assert response.get_json() == {"error": "course_id does not match an existing course"}
    assert assignment_service.get_all_assignments() == []


def test_post_is_refused_when_the_courses_service_is_down(monkeypatch):
    def courses_down():
        raise CoursesUnavailable("connection refused")

    monkeypatch.setattr(app, "fetch_course_names", courses_down)

    response = post(VALID)

    assert response.status_code == 503
    assert "courses service is unavailable" in response.get_json()["error"]
    assert assignment_service.get_all_assignments() == []  # nothing is saved without the check


def test_due_date_is_always_stored_as_yyyy_mm_dd():
    response = post({**VALID, "due_date": "20261201"})  # ISO basic format: also a valid date

    assert response.status_code == 201
    assert response.get_json()["due_date"] == "2026-12-01"
    assert assignment_service.get_all_assignments()[0]["due_date"] == "2026-12-01"


def test_length_limits_count_the_way_sql_server_does():
    # NVARCHAR(200) holds 200 UTF-16 units, and an emoji takes two of them
    assert post({**VALID, "title": "\U0001F4DA" * 100}).status_code == 201
    assert post({**VALID, "title": "\U0001F4DA" * 101}).status_code == 400
    assert len(assignment_service.get_all_assignments()) == 1


def test_null_description_is_saved_as_empty():
    assert post({**VALID, "description": None}).status_code == 201
    assert assignment_service.get_all_assignments()[0]["description"] == ""


def test_toggle_route():
    client = app.app.test_client()
    assignment_service.add_assignment("AI Report", "2026-10-20", "High", COURSE_ID)
    assignment_id = assignment_service.get_all_assignments()[0]["id"]

    assert client.post(f"/assignments/{assignment_id}/toggle").status_code == 204
    assert assignment_service.get_all_assignments()[0]["completed"] is True


def test_toggle_unknown_assignment_returns_404():
    response = app.app.test_client().post("/assignments/999999/toggle")

    assert response.status_code == 404
    assert response.get_json() == {"error": "assignment not found"}


def test_delete_route_can_be_repeated():
    client = app.app.test_client()
    assignment_service.add_assignment("AI Report", "2026-10-20", "High", COURSE_ID)
    assignment_id = assignment_service.get_all_assignments()[0]["id"]

    assert client.delete(f"/assignments/{assignment_id}").status_code == 204
    assert client.delete(f"/assignments/{assignment_id}").status_code == 204
    assert assignment_service.get_all_assignments() == []


def test_database_down_gives_a_json_503(monkeypatch):
    def no_database():
        raise pymssql.OperationalError("database unavailable")

    monkeypatch.setattr(assignment_service, "get_connection", no_database)

    response = app.app.test_client().get("/assignments")

    assert response.status_code == 503
    assert response.get_json() == {"error": "the database is unavailable, try again in a moment"}
