import pymssql
import pytest

import app  # noqa: F401  (importing the app applies the migrations)
import database


def test_migrations_are_recorded():
    connection = database.connect()
    cursor = connection.cursor()
    cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
    versions = [row[0] for row in cursor.fetchall()]
    connection.close()

    assert versions[0] == "001_init.sql"


def test_second_run_applies_nothing():
    assert database.run_migrations() == []


def test_split_batches_on_go_lines():
    sql = "CREATE TABLE a (id INT);\nGO\n  go  \nCREATE TABLE b (id INT);\n"

    assert database.split_batches(sql) == ["CREATE TABLE a (id INT);", "CREATE TABLE b (id INT);"]


def test_connect_retries_then_succeeds(monkeypatch):
    calls = []

    def flaky_connect():
        calls.append(1)
        if len(calls) < 3:
            raise pymssql.OperationalError("40613 database is resuming")
        return "connection"

    monkeypatch.setattr(database, "connect", flaky_connect)
    monkeypatch.setattr(database.time, "sleep", lambda seconds: None)

    assert database.connect_with_retry() == "connection"
    assert len(calls) == 3


def test_connect_gives_up_after_last_attempt(monkeypatch):
    def broken_connect():
        raise pymssql.OperationalError("unreachable")

    monkeypatch.setattr(database, "connect", broken_connect)
    monkeypatch.setattr(database.time, "sleep", lambda seconds: None)

    with pytest.raises(pymssql.OperationalError):
        database.connect_with_retry(attempts=3)
