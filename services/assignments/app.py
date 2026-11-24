import os
import time
from datetime import date

import pymssql
from flask import Flask, g, jsonify, request

from assignment_service import (
    add_assignment,
    delete_assignment,
    get_all_assignments,
    toggle_assignment_complete,
)
from courses_client import CoursesUnavailable, fetch_course_names
from database import check_db, run_migrations

app = Flask(__name__)

# Bring the schema up to date before serving any request
run_migrations()


PRIORITIES = ("Low", "Medium", "High")


# Version of the running code: the commit SHA, set by the pipeline. "dev" when run locally.
VERSION = os.environ.get("GIT_SHA", "dev")


# Browser origins allowed to call this API (the UI's origin), comma-separated.
# Unset means no cross-origin access at all.
CORS_ORIGINS = {
    origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()
}


@app.before_request
def start_timer():
    g.start_time = time.perf_counter()


@app.after_request
def log_request(response):
    # One line per request on stdout: method, path, status, duration
    duration_ms = (time.perf_counter() - g.get("start_time", time.perf_counter())) * 1000
    print(f"{request.method} {request.path} {response.status_code} {duration_ms:.1f}ms", flush=True)
    return response


@app.after_request
def add_cors_headers(response):
    # Only the UI's origin gets the CORS headers, so other sites' pages cannot read the API.
    # Flask answers the browser's OPTIONS preflight itself; these headers make it pass.
    origin = request.headers.get("Origin")
    if origin in CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Vary"] = "Origin"
    return response


@app.get("/health")
def health():
    # Reports only this service's own state, never the other service's
    db_ok = check_db()
    body = {"status": "ok" if db_ok else "error", "db": "ok" if db_ok else "error", "version": VERSION}
    return jsonify(body), 200 if db_ok else 503


@app.get("/assignments")
def list_assignments():
    assignments = get_all_assignments()

    # Cross-service flow: course names come from the courses service over HTTP.
    # If it is down or slow, assignments are still returned, with course_name null,
    # so this service keeps working on its own data.
    try:
        names = fetch_course_names()
    except CoursesUnavailable as error:
        print(f"courses service unavailable: {error}", flush=True)
        names = None

    for assignment in assignments:
        if names is None:
            assignment["course_name"] = None
        else:
            # The course may have been deleted: the database cannot stop that across services
            assignment["course_name"] = names.get(assignment["course_id"], "Unknown course")

    return jsonify(assignments)


@app.errorhandler(pymssql.OperationalError)
@app.errorhandler(pymssql.InterfaceError)
def database_unavailable(error):
    # The database stayed unreachable through every retry: a clear JSON error, not an HTML page
    print(f"database unavailable: {error}", flush=True)
    return jsonify({"error": "the database is unavailable, try again in a moment"}), 503


def read_text(data, field):
    """The field as a stripped string. Empty when it is missing, null or not text."""
    value = data.get(field)
    return value.strip() if isinstance(value, str) else ""


def too_long(text, limit):
    """True if the text does not fit an NVARCHAR(limit) column.

    SQL Server counts UTF-16 units and an emoji takes two of them, so len() is not enough.
    """
    return len(text.encode("utf-16-le", "surrogatepass")) // 2 > limit


def read_course_id(value):
    """course_id as a positive whole number, or None. true, 1.5 and lists are not accepted."""
    if isinstance(value, bool):
        return None
    if isinstance(value, str) and value.strip().isdecimal():
        value = int(value)
    return value if isinstance(value, int) and value > 0 else None


def bad_request(message):
    return jsonify({"error": message}), 400


@app.post("/assignments")
def create_assignment():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):  # no body, invalid JSON, or JSON that is not an object
        data = {}
    title = read_text(data, "title")
    description = read_text(data, "description")  # optional, added by migration 002
    due_date = data.get("due_date")
    priority = data.get("priority")
    course_id = read_course_id(data.get("course_id"))

    # Reject bad input with a clear 400 instead of letting SQL Server fail with a 500
    if not title or not due_date or not priority or data.get("course_id") is None:
        return bad_request("title, due_date, priority and course_id are required")
    if too_long(title, 200) or too_long(description, 500):
        return bad_request("title must be at most 200 characters and description at most 500")
    if not isinstance(data.get("description") or "", str):
        return bad_request("description must be text")
    if priority not in PRIORITIES:
        return bad_request("priority must be Low, Medium or High")
    try:
        due_date = date.fromisoformat(due_date).isoformat()  # always stored as YYYY-MM-DD
    except (TypeError, ValueError):
        return bad_request("due_date must be a date like 2026-12-01")
    if course_id is None:
        return bad_request("course_id must be a positive whole number")

    # Second call across the seam: the course must exist in the courses service.
    # The database cannot check this, because there is no foreign key across two databases.
    try:
        course_names = fetch_course_names()
    except CoursesUnavailable as error:
        print(f"courses service unavailable: {error}", flush=True)
        message = "the courses service is unavailable, so the course cannot be checked; try again in a moment"
        return jsonify({"error": message}), 503
    if course_id not in course_names:
        return bad_request("course_id does not match an existing course")

    add_assignment(title, due_date, priority, course_id, description)
    created = {
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "course_id": course_id,
    }
    return jsonify(created), 201


@app.post("/assignments/<int:assignment_id>/toggle")
def complete_assignment(assignment_id):
    if not toggle_assignment_complete(assignment_id):
        return jsonify({"error": "assignment not found"}), 404
    return "", 204


@app.delete("/assignments/<int:assignment_id>")
def remove_assignment(assignment_id):
    delete_assignment(assignment_id)
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
