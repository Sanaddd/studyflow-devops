import app as app_module
import database


def client():
    return app_module.app.test_client()


def test_health_ok():
    response = client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "db": "ok", "version": app_module.VERSION}


def test_health_returns_503_when_database_fails(monkeypatch):
    monkeypatch.setattr(app_module, "check_db", lambda: False)

    response = client().get("/health")

    assert response.status_code == 503
    assert response.get_json()["db"] == "error"


def test_check_db_false_when_database_unreachable(monkeypatch):
    def broken_connection():
        raise OSError("database unavailable")

    monkeypatch.setattr(database, "connect", broken_connection)

    assert database.check_db() is False


def test_each_request_is_logged(capsys):
    client().get("/assignments")

    line = capsys.readouterr().out.strip().splitlines()[-1]
    method, path, status, duration = line.split()
    assert (method, path, status) == ("GET", "/assignments", "200")
    assert duration.endswith("ms")
