"""Integration smoke tests for the FastAPI property endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_property_crud_flow(session):
    payload = {
        "name": "Thuthikadu 171-4",
        "survey_number": "171-4",
        "location": "Thuthikadu",
        "total_area_sqft": 12500,
        "asking_price": 1850000,
    }
    created = client.post("/api/v1/properties", json=payload)
    assert created.status_code == 201, created.text
    prop_id = created.json()["id"]
    assert created.json()["status"] == "evaluating"

    fetched = client.get(f"/api/v1/properties/{prop_id}")
    assert fetched.status_code == 200
    assert fetched.json()["survey_number"] == "171-4"

    listed = client.get("/api/v1/properties", params={"location": "Thuthikadu"})
    assert [p["name"] for p in listed.json()] == ["Thuthikadu 171-4"]


def test_duplicate_property_conflict(session):
    client.post("/api/v1/properties", json={"name": "Moothakkal"})
    dup = client.post("/api/v1/properties", json={"name": "Moothakkal"})
    assert dup.status_code == 409


def test_missing_property_returns_404(session):
    assert client.get("/api/v1/properties/999999").status_code == 404
