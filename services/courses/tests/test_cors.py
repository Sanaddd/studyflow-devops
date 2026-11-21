import app as app_module

UI_ORIGIN = "http://localhost:8080"


def client(monkeypatch):
    monkeypatch.setattr(app_module, "CORS_ORIGINS", {UI_ORIGIN})
    return app_module.app.test_client()


def test_ui_origin_is_allowed(monkeypatch):
    response = client(monkeypatch).get("/courses", headers={"Origin": UI_ORIGIN})

    assert response.headers["Access-Control-Allow-Origin"] == UI_ORIGIN


def test_other_origin_gets_no_cors_headers(monkeypatch):
    response = client(monkeypatch).get("/courses", headers={"Origin": "https://evil.example"})

    assert "Access-Control-Allow-Origin" not in response.headers


def test_preflight_from_ui_origin_passes(monkeypatch):
    response = client(monkeypatch).options(
        "/courses",
        headers={
            "Origin": UI_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 200
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert response.headers["Access-Control-Allow-Headers"] == "Content-Type"
