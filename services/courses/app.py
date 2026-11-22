import os
import time

from flask import Flask, g, jsonify, request

from course_service import add_course, delete_course, get_all_courses, update_course
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


def read_course_fields():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    code = str(data.get("code", "")).strip()
    return name, code


@app.get("/courses")
def list_courses():
    return jsonify([dict(course) for course in get_all_courses()])


@app.post("/courses")
def create_course():
    name, code = read_course_fields()
    if not name or not code:
        return jsonify({"error": "name and code are required"}), 400

    add_course(name, code)
    return jsonify({"name": name, "code": code}), 201


@app.put("/courses/<int:course_id>")
def edit_course(course_id):
    name, code = read_course_fields()
    if not name or not code:
        return jsonify({"error": "name and code are required"}), 400

    update_course(course_id, name, code)
    return jsonify({"id": course_id, "name": name, "code": code})


@app.delete("/courses/<int:course_id>")
def remove_course(course_id):
    delete_course(course_id)
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
