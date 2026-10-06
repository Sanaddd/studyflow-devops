import os

from flask import Flask, redirect, render_template, request, url_for

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
    return render_template("index.html", courses=courses)


@app.route("/courses", methods=["POST"])
def create_course():
    name = request.form["name"].strip()
    code = request.form["code"].strip()

    if name and code:
        add_course(name, code)

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