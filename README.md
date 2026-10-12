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

## Testing

The project uses pytest and pytest-cov for automated testing.

To run the tests:

    python -m pytest -v

To run the tests with coverage:

    python -m pytest --cov=course_service --cov=assignment_service --cov=database --cov-report=term-missing

Current result:

- 7 tests passed
- 100% coverage across course_service.py, assignment_service.py, and database.py

## Running the project

Create a virtual environment:

    python3 -m venv venv

Activate it on macOS/Linux:

    source venv/bin/activate

Install the dependencies:

    pip install -r requirements.txt

Start the application:

    python app.py

The application uses port 5000 by default.

A different port can be supplied using the PORT environment variable:

    PORT=5001 python app.py

StudyFlow binds to 0.0.0.0 so it can later run correctly inside a container.

## Database

StudyFlow uses SQLite for both courses and assignments.

By default, the database is stored at:

    data/studyflow.db

The database directory can be changed using the DATA_DIR environment variable.

For example:

    DATA_DIR=my_data python app.py

The database and required tables are created automatically when the application starts.

## Configuration

The application uses these environment variables:

- PORT - port used by the Flask server. Default: 5000
- DATA_DIR - directory used to store the SQLite database. Default: data

The app does not require an external database or any interactive setup before starting.