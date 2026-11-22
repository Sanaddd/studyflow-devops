"""Integration test across the seam, against the real system started by docker compose.

Run from the repository root after `docker compose up --build -d`:
    python -m pytest tests/integration -v

It checks the one flow that crosses the services: the assignments service asks the
courses service for course names. Then it stops the courses service to check that
assignments still answer, quickly and without course names.
"""
import json
import os
import subprocess
import time
import urllib.request
import uuid

COURSES = os.environ.get("COURSES_BASE", "http://localhost:8001")
ASSIGNMENTS = os.environ.get("ASSIGNMENTS_BASE", "http://localhost:8002")


def request(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        text = response.read()
        return response.status, json.loads(text) if text else None


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

    # 2. Create an assignment for it in the assignments service (it only stores the id)
    request("POST", f"{ASSIGNMENTS}/assignments",
            {"title": title, "due_date": "2030-01-01", "priority": "Low", "course_id": course["id"]})

    # 3. The assignments service fetched the name from the courses service over HTTP
    _, assignments = request("GET", f"{ASSIGNMENTS}/assignments")
    mine = next(a for a in assignments if a["title"] == title)
    assert mine["course_name"] == "Integration Course"

    # 4. With the courses service stopped, assignments still answer quickly, without names
    compose("stop", "courses")
    try:
        started = time.perf_counter()
        status, assignments = request("GET", f"{ASSIGNMENTS}/assignments")
        elapsed = time.perf_counter() - started

        mine = next(a for a in assignments if a["title"] == title)
        assert status == 200
        assert mine["course_name"] is None
        assert elapsed < 5  # bounded by the 2 s timeout, never a hung request

        # The assignments service's own health does not depend on the courses service
        assert request("GET", f"{ASSIGNMENTS}/health")[0] == 200
    finally:
        compose("start", "courses")
