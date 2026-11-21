"""GET /assignments adds course names from the courses service, and copes when it is down."""
import app as app_module
import assignment_service
import database
from courses_client import CoursesUnavailable


def setup_function():
    connection = database.connect()
    connection.cursor().execute("DELETE FROM assignments")
    connection.commit()
    connection.close()

    assignment_service.add_assignment("AI Report", "2026-12-01", "High", 1)
    assignment_service.add_assignment("Old Essay", "2026-12-02", "Low", 99)


def get_assignments():
    return app_module.app.test_client().get("/assignments")


def test_course_names_are_added(monkeypatch):
    monkeypatch.setattr(app_module, "fetch_course_names", lambda: {1: "Software Development"})

    names = [a["course_name"] for a in get_assignments().get_json()]

    assert names == ["Software Development", "Unknown course"]


def test_assignments_still_listed_when_courses_is_down(monkeypatch):
    def courses_down():
        raise CoursesUnavailable("connection refused")

    monkeypatch.setattr(app_module, "fetch_course_names", courses_down)

    response = get_assignments()

    assert response.status_code == 200
    assert [a["title"] for a in response.get_json()] == ["AI Report", "Old Essay"]
    assert all(a["course_name"] is None for a in response.get_json())
