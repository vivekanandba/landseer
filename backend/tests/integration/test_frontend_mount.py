"""The static SPA is served at /app and the root redirects to it, without
shadowing the API or meta routes."""

from app.main import app


def test_root_redirects_to_app(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (307, 308)
    assert resp.headers["location"] == "/app/"


def test_spa_index_served(client):
    resp = client.get("/app/")
    assert resp.status_code == 200
    assert "Landseer" in resp.text
    assert "text/html" in resp.headers["content-type"]


def test_api_and_meta_routes_not_shadowed_by_mount(client, session):
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/properties").status_code == 200
    # OpenAPI docs still resolve.
    assert app.openapi_url == "/openapi.json"
    assert client.get("/openapi.json").status_code == 200
