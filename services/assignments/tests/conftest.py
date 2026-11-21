"""Test database setup.

Tests run against a real SQL Server, never Azure SQL. TEST_SQLSERVER_URL points at a
throwaway server with an admin login, e.g. mssql://sa:<password>@localhost:1433/master.
A fresh database is created for this test run, DATABASE_URL points the service at it,
and it is dropped at the end. This runs before app.py is imported, because app.py
applies the migrations at import time.
"""
import os
import uuid
from urllib.parse import urlparse

import pymssql

ADMIN_URL = urlparse(os.environ["TEST_SQLSERVER_URL"])
TEST_DB = f"test_{uuid.uuid4().hex[:12]}"


def admin_connection():
    return pymssql.connect(
        server=ADMIN_URL.hostname,
        port=ADMIN_URL.port or 1433,
        user=ADMIN_URL.username,
        password=ADMIN_URL.password,
        autocommit=True,  # CREATE/DROP DATABASE cannot run inside a transaction
    )


_connection = admin_connection()
_connection.cursor().execute(f"CREATE DATABASE {TEST_DB}")
_connection.close()

os.environ["DATABASE_URL"] = ADMIN_URL._replace(path=f"/{TEST_DB}").geturl()

# No courses service in unit tests: point at a closed local port so calls fail fast.
# Tests that need course names replace fetch_course_names with a stub.
os.environ.setdefault("COURSES_URL", "http://127.0.0.1:9")


def pytest_sessionfinish(session, exitstatus):
    connection = admin_connection()
    connection.cursor().execute(
        f"ALTER DATABASE {TEST_DB} SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE {TEST_DB}"
    )
    connection.close()
