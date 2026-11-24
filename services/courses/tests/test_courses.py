import pymssql

import app  # importing the app applies the migrations
import course_service
import database


def setup_function():
    # Every test starts from an empty table, so tests do not depend on each other's order
    connection = database.connect()
    connection.cursor().execute("DELETE FROM courses")
    connection.commit()
    connection.close()


def add_one(name="Artificial Intelligence", code="CS301"):
    course_service.add_course(name, code)
    return course_service.get_all_courses()[0]["id"]


def test_add_and_get_course():
    course_service.add_course("Artificial Intelligence", "CS301")

    courses = course_service.get_all_courses()

    assert len(courses) == 1
    assert courses[0]["name"] == "Artificial Intelligence"
    assert courses[0]["code"] == "CS301"


def test_update_course():
    course_id = add_one()

    assert course_service.update_course(course_id, "AI Fundamentals", "CS305") is True

    updated_courses = course_service.get_all_courses()

    assert updated_courses[0]["name"] == "AI Fundamentals"
    assert updated_courses[0]["code"] == "CS305"


def test_update_missing_course_returns_false():
    assert course_service.update_course(999999, "Nothing", "NO") is False


def test_delete_course():
    course_id = add_one()

    course_service.delete_course(course_id)

    assert course_service.get_all_courses() == []


def test_post_and_put_reject_invalid_input():
    client = app.app.test_client()
    course_id = add_one()

    bad_bodies = [
        {},
        {"name": "", "code": "X"},
        {"name": "A", "code": "  "},
        {"name": "x" * 201, "code": "X"},
        {"name": "A", "code": "x" * 51},
        {"name": "\U0001F4DA" * 101, "code": "X"},  # an emoji takes two UTF-16 units in NVARCHAR(200)
        {"name": None, "code": "X"},
        {"name": 123, "code": "X"},
        {"name": "A", "code": ["X"]},
        ["not", "an", "object"],
        "text",
        5,
    ]
    for body in bad_bodies:
        assert client.post("/courses", json=body).status_code == 400, body
        assert client.put(f"/courses/{course_id}", json=body).status_code == 400, body

    assert client.post("/courses", data="not json").status_code == 400
    assert client.post("/courses").status_code == 400
    assert len(course_service.get_all_courses()) == 1
    # A rejected PUT changes nothing
    assert course_service.get_all_courses()[0]["name"] == "Artificial Intelligence"


def test_put_unknown_course_returns_404():
    response = app.app.test_client().put("/courses/999999", json={"name": "A", "code": "B"})

    assert response.status_code == 404
    assert response.get_json() == {"error": "course not found"}


def test_post_and_delete_routes():
    client = app.app.test_client()

    response = client.post("/courses", json={"name": "  DevOps  ", "code": "DEVOPS"})
    assert response.status_code == 201
    assert response.get_json() == {"name": "DevOps", "code": "DEVOPS"}  # spaces around the text are removed

    course_id = course_service.get_all_courses()[0]["id"]
    assert client.delete(f"/courses/{course_id}").status_code == 204
    assert client.delete(f"/courses/{course_id}").status_code == 204  # deleting twice is not an error
    assert course_service.get_all_courses() == []


def test_database_down_gives_a_json_503(monkeypatch):
    def no_database():
        raise pymssql.OperationalError("database unavailable")

    monkeypatch.setattr(course_service, "get_connection", no_database)

    response = app.app.test_client().get("/courses")

    assert response.status_code == 503
    assert response.get_json() == {"error": "the database is unavailable, try again in a moment"}
