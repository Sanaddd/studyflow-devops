import os
import time

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


@app.post("/assignments")
def create_assignment():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    due_date = data.get("due_date")
    priority = data.get("priority")
    course_id = data.get("course_id")

    if not (title and due_date and priority and course_id):
        return jsonify({"error": "title, due_date, priority and course_id are required"}), 400

    add_assignment(title, due_date, priority, int(course_id))
    created = {"title": title, "due_date": due_date, "priority": priority, "course_id": int(course_id)}
    return jsonify(created), 201


@app.post("/assignments/<int:assignment_id>/toggle")
def complete_assignment(assignment_id):
    toggle_assignment_complete(assignment_id)
    return "", 204


@app.delete("/assignments/<int:assignment_id>")
def remove_assignment(assignment_id):
    delete_assignment(assignment_id)
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
