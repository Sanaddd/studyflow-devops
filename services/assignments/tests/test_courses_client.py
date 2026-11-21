"""The courses client against a small fake courses service running on a local port."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import courses_client


class FakeCourses(BaseHTTPRequestHandler):
    mode = "ok"  # "ok", "slow" or "error"

    def do_GET(self):
        if self.mode == "slow":
            time.sleep(1)
        if self.mode == "error":
            self.send_response(500)
            self.end_headers()
            return
        body = json.dumps([{"id": 1, "name": "Software Development", "code": "SDD"}]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # keep test output quiet


@pytest.fixture
def fake_courses(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), FakeCourses)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(courses_client, "COURSES_URL", f"http://127.0.0.1:{server.server_port}")
    yield FakeCourses
    FakeCourses.mode = "ok"
    server.shutdown()
    server.server_close()


def test_returns_names_by_id(fake_courses):
    assert courses_client.fetch_course_names() == {1: "Software Development"}


def test_slow_service_times_out(fake_courses, monkeypatch):
    fake_courses.mode = "slow"
    monkeypatch.setattr(courses_client, "COURSES_TIMEOUT_S", 0.2)

    started = time.perf_counter()
    with pytest.raises(courses_client.CoursesUnavailable):
        courses_client.fetch_course_names()

    assert time.perf_counter() - started < 0.9  # gave up at the timeout, did not wait for the answer


def test_error_status_is_unavailable(fake_courses):
    fake_courses.mode = "error"

    with pytest.raises(courses_client.CoursesUnavailable):
        courses_client.fetch_course_names()


def test_stopped_service_is_unavailable(monkeypatch):
    # Nothing listens on port 9 (discard), so the connection is refused
    monkeypatch.setattr(courses_client, "COURSES_URL", "http://127.0.0.1:9")

    with pytest.raises(courses_client.CoursesUnavailable):
        courses_client.fetch_course_names()
