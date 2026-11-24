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

    assert versions == ["001_init.sql", "002_add_description.sql"]


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


def test_migration_002_keeps_existing_rows():
    # Recreate the state before 002 on a scratch table: a row inserted without a description,
    # then the same ALTER as 002. The old row must survive with the default ''.
    connection = database.connect()
    cursor = connection.cursor()
    cursor.execute("IF OBJECT_ID('m002_check') IS NOT NULL DROP TABLE m002_check")
    cursor.execute("CREATE TABLE m002_check (id INT IDENTITY(1,1) PRIMARY KEY, title NVARCHAR(200) NOT NULL)")
    cursor.execute("INSERT INTO m002_check (title) VALUES ('Old row')")
    alter = (database.MIGRATIONS_DIR / "002_add_description.sql").read_text()
    cursor.execute(alter.replace("assignments", "m002_check"))
    cursor.execute("SELECT title, description FROM m002_check")
    rows = cursor.fetchall()
    cursor.execute("DROP TABLE m002_check")
    connection.commit()
    connection.close()

    assert rows == [("Old row", "")]


def test_failed_migration_is_rolled_back(monkeypatch, tmp_path):
    # A migration that fails half way leaves nothing behind and is not recorded,
    # so the service refuses to start instead of running on a half-changed schema
    (tmp_path / "999_broken.sql").write_text(
        "CREATE TABLE half_done (id INT);\nGO\nALTER TABLE table_that_does_not_exist ADD x INT;\n"
    )
    monkeypatch.setattr(database, "MIGRATIONS_DIR", tmp_path)

    with pytest.raises(pymssql.Error):
        database.run_migrations()

    connection = database.connect()
    cursor = connection.cursor()
    cursor.execute("SELECT OBJECT_ID('half_done')")
    half_done_table = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM schema_migrations WHERE version = '999_broken.sql'")
    times_recorded = cursor.fetchone()[0]
    connection.close()

    assert half_done_table is None
    assert times_recorded == 0

