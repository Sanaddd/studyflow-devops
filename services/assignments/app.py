import os

from flask import Flask, jsonify, request

from assignment_service import (
    add_assignment,
    delete_assignment,
    get_all_assignments,
    toggle_assignment_complete,
)
from database import init_db


app = Flask(__name__)

init_db()


@app.get("/assignments")
def list_assignments():
    return jsonify(get_all_assignments())


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
    return jsonify({"title": title, "due_date": due_date, "priority": priority, "course_id": int(course_id)}), 201


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
