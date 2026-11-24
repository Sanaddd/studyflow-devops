"""Integration test across the seam, against the real system started by docker compose.

Run from the repository root after `docker compose up --build -d`:
    python -m pytest tests/integration -v

It checks the calls that cross the services: the assignments service asks the courses
service for course names, and checks that a course exists before saving an assignment.
Then it stops the courses service to check that assignments still list, quickly and
without course names, and that creating one is refused with a clear error.
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid

COURSES = os.environ.get("COURSES_BASE", "http://localhost:8001")
ASSIGNMENTS = os.environ.get("ASSIGNMENTS_BASE", "http://localhost:8002")


def request(method, url, body=None):
    """Return (status, JSON body). An HTTP error status is returned, not raised."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status, text = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, text = error.code, error.read()
    try:
        return status, json.loads(text) if text else None
    except ValueError:
        return status, None


def compose(*args):
    subprocess.run(["docker", "compose", *args], check=True, capture_output=True)


def wait_healthy(base, seconds=90):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            if request("GET", f"{base}/health")[0] == 200:
                return
        except OSError:
            pass
        time.sleep(2)
    raise AssertionError(f"{base} did not become healthy")


def test_assignment_shows_course_name_and_survives_courses_outage():
    wait_healthy(COURSES)
    wait_healthy(ASSIGNMENTS)

    # Unique values, so the test also works on a database that already has data
    code = f"IT{uuid.uuid4().hex[:6]}"
    title = f"Integration {code}"

    # 1. Create a course in the courses service and find its id
    request("POST", f"{COURSES}/courses", {"name": "Integration Course", "code": code})
    course = next(c for c in request("GET", f"{COURSES}/courses")[1] if c["code"] == code)

    # 2. Create an assignment for it in the assignments service (it only stores the id).
    #    The assignments service first asks the courses service whether the course exists.
    new_assignment = {"title": title, "due_date": "2030-01-01", "priority": "Low", "course_id": course["id"]}
    assert request("POST", f"{ASSIGNMENTS}/assignments", new_assignment)[0] == 201

    # 3. The assignments service fetched the name from the courses service over HTTP
    _, assignments = request("GET", f"{ASSIGNMENTS}/assignments")
    mine = next(a for a in assignments if a["title"] == title)
    assert mine["course_name"] == "Integration Course"

    # 4. A course id that the courses service does not know is refused
    status, body = request("POST", f"{ASSIGNMENTS}/assignments", {**new_assignment, "course_id": 2000000000})
    assert status == 400
    assert body == {"error": "course_id does not match an existing course"}

    # 5. With the courses service stopped, assignments still answer quickly, without names
    compose("stop", "courses")
    try:
        started = time.perf_counter()
        status, assignments = request("GET", f"{ASSIGNMENTS}/assignments")
        elapsed = time.perf_counter() - started

        mine = next(a for a in assignments if a["title"] == title)
        assert status == 200
        assert mine["course_name"] is None
        assert elapsed < 5  # bounded by the 2 s timeout, never a hung request

        # Creating an assignment needs the course check: refused quickly, with a clear error
        started = time.perf_counter()
        second = {**new_assignment, "title": f"{title} second"}
        status, body = request("POST", f"{ASSIGNMENTS}/assignments", second)
        assert status == 503
        assert "courses service is unavailable" in body["error"]
        assert time.perf_counter() - started < 5
        assert all(a["title"] != second["title"] for a in request("GET", f"{ASSIGNMENTS}/assignments")[1])

        # The assignments service's own health does not depend on the courses service
        assert request("GET", f"{ASSIGNMENTS}/health")[0] == 200
    finally:
        compose("start", "courses")
