"""HTTP client for the courses service: the only way this service learns about courses.

Assignments store only a course_id. Course names live in the courses service's own
database, so they are fetched over HTTP instead of with a JOIN.
"""
import json
import os
import urllib.request

# Where the courses service is, and how long to wait for it. Set by compose / the pipeline.
COURSES_URL = os.environ.get("COURSES_URL", "http://courses:8000")
COURSES_TIMEOUT_S = float(os.environ.get("COURSES_TIMEOUT_S", "2"))


class CoursesUnavailable(Exception):
    """The courses service did not answer in time, or answered with an error."""


def fetch_course_names():
    """Return {course_id: course_name} from GET /courses on the courses service.

    Raises CoursesUnavailable instead of hanging or crashing when the courses
    service is stopped, slow (longer than COURSES_TIMEOUT_S) or returns an error.
    """
    try:
        with urllib.request.urlopen(f"{COURSES_URL}/courses", timeout=COURSES_TIMEOUT_S) as response:
            courses = json.load(response)
    except (OSError, ValueError) as error:
        # OSError covers connection refused, DNS failure, timeouts and HTTP error statuses;
        # ValueError covers a body that is not valid JSON
        raise CoursesUnavailable(str(error)) from error

    return {course["id"]: course["name"] for course in courses}
