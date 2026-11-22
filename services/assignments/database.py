import os
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import pymssql

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Azure SQL serverless returns this error while a paused database is resuming.
DATABASE_RESUMING = 40613


def connect():
    """Open one connection using DATABASE_URL: mssql://user:password@host:port/database"""
    url = urlparse(os.environ["DATABASE_URL"])
    return pymssql.connect(
        server=url.hostname,
        port=url.port or 1433,
        user=unquote(url.username),
        password=unquote(url.password),
        database=url.path.lstrip("/"),
        login_timeout=5,
        timeout=10,
    )


def connect_with_retry(attempts=8, first_delay=1.0, max_delay=15.0):
    """Connect, retrying with exponential backoff.

    SQL Server needs ~20 s after its container starts, and a paused Azure SQL
    serverless database needs up to a minute to resume (error 40613).
    8 attempts with delays 1, 2, 4, 8, 15, 15, 15 s wait about a minute in total.
    """
    delay = first_delay
    for attempt in range(1, attempts + 1):
        try:
            return connect()
        except (pymssql.OperationalError, pymssql.InterfaceError) as error:
            if attempt == attempts:
                raise
            resuming = str(DATABASE_RESUMING) in str(error)
            reason = "database resuming" if resuming else "database not reachable"
            print(f"{reason} (attempt {attempt}/{attempts}), retrying in {delay:.0f}s", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, max_delay)


def get_connection():
    return connect_with_retry()


def split_batches(sql):
    """Split a migration file into batches on lines that contain only GO, like sqlcmd does."""
    batches, current = [], []
    for line in sql.splitlines():
        if line.strip().upper() == "GO":
            batches.append("\n".join(current))
            current = []
        else:
            current.append(line)
    batches.append("\n".join(current))
    return [batch for batch in batches if batch.strip()]


def run_migrations():
    """Apply every migrations/NNN_*.sql file not yet recorded in schema_migrations, in order.

    Each migration runs exactly once. All pending migrations run inside one transaction
    that first takes an exclusive application lock, so two processes starting at the
    same time (e.g. two gunicorn workers) never apply the same migration twice.
    Returns the names of the migrations applied by this call.
    """
    files = sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))
    applied_now = []

    connection = connect_with_retry()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "EXEC sp_getapplock @Resource = 'schema_migrations', @LockMode = 'Exclusive', "
            "@LockOwner = 'Transaction', @LockTimeout = 60000"
        )
        cursor.execute(
            """
            IF OBJECT_ID('schema_migrations') IS NULL
                CREATE TABLE schema_migrations (
                    version NVARCHAR(100) NOT NULL PRIMARY KEY,
                    applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
                )
            """
        )
        cursor.execute("SELECT version FROM schema_migrations")
        already_applied = {row[0] for row in cursor.fetchall()}

        for path in files:
            if path.name in already_applied:
                continue
            print(f"applying migration {path.name}", flush=True)
            for batch in split_batches(path.read_text()):
                cursor.execute(batch)
            cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
            applied_now.append(path.name)

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    if not applied_now:
        print("migrations: database is up to date", flush=True)
    return applied_now


def check_db():
    """Return True if this service can read from and write to its own database.

    Used by GET /health. One connection attempt only, so /health answers quickly
    when the database is down. The write is rolled back and leaves no data behind.
    """
    try:
        connection = connect()
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO health_check (checked_at) VALUES (SYSUTCDATETIME())")
            cursor.execute("SELECT COUNT(*) FROM health_check")
            cursor.fetchone()
            connection.rollback()
        finally:
            connection.close()
        return True
    except Exception:
        return False
