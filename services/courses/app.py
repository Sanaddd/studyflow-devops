import os

from flask import Flask, jsonify, request

from course_service import add_course, delete_course, get_all_courses, update_course
from database import init_db


app = Flask(__name__)

init_db()


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
