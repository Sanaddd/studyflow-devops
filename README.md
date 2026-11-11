# StudyFlow

StudyFlow is a small student planner app I am building for my DevOps assignment.

The idea is to have one simple place where a student can keep track of their courses and the assignments linked to them.

The project has two main parts:

1. Courses
2. Assignments

Both parts will store their data in SQLite.

## What I plan to build

For courses, I want the user to be able to add, view, edit, and delete courses.

For assignments, the user should be able to add an assignment, link it to a course, give it a due date and priority, and mark it as completed.

## Tech used

- Python
- Flask
- SQLite
- HTML/CSS
- pytest
- pytest-cov

## Current progress

The basic Flask app is set up and running locally.

## Project structure (Assignment 2)

StudyFlow is being split into two services along the seam from ADR-2:

    services/
      courses/        Courses domain: own Flask app, own database, own Dockerfile
      assignments/    Assignments domain: own Flask app, own database, own Dockerfile
    ui/               Front end (being converted to a static site)

Each service has its own `requirements.txt` (runtime, pinned) and
`requirements-dev.txt` (tests). Assignments store only a `course_id`; course
details belong to the courses service.

## Running a single service

    cd services/courses            # or services/assignments
    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements-dev.txt
    python app.py                  # listens on PORT, default 8000

## Running a service in Docker

    docker build -t studyflow-courses services/courses
    docker run --rm -p 8001:8000 studyflow-courses

## Testing

From inside a service folder:

    python -m pytest -v
    python -m pytest --cov=. --cov-report=term-missing

## Configuration

Each service reads:

- PORT - port the service listens on. Default: 8000
- DATA_DIR - directory for the service's database file. Default: data
