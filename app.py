import os

from flask import Flask, redirect, render_template, request, url_for

from assignment_service import add_assignment, get_all_assignments

from course_service import (
    add_course,
    delete_course,
    get_all_courses,
    update_course,
)

from database import init_db


app = Flask(__name__)

init_db()


@app.route("/")
def home():
    courses = get_all_courses()
    assignments = get_all_assignments()

    return render_template(
        "index.html",
        courses=courses,
        assignments=assignments,
    )


@app.route("/courses", methods=["POST"])
def create_course():
    name = request.form["name"].strip()
    code = request.form["code"].strip()

    if name and code:
        add_course(name, code)

    return redirect(url_for("home"))

@app.route("/assignments", methods=["POST"])
def create_assignment():
    title = request.form["title"].strip()
    due_date = request.form["due_date"]
    priority = request.form["priority"]
    course_id = request.form["course_id"]

    if title and due_date and priority and course_id:
        add_assignment(title, due_date, priority, course_id)

    return redirect(url_for("home"))

@app.route("/courses/<int:course_id>/edit", methods=["POST"])
def edit_course(course_id):
    name = request.form["name"].strip()
    code = request.form["code"].strip()

    if name and code:
        update_course(course_id, name, code)

    return redirect(url_for("home"))   

@app.route("/courses/<int:course_id>/delete", methods=["POST"])
def remove_course(course_id):
    delete_course(course_id)
    return redirect(url_for("home"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)