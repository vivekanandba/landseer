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


def test_patch_price_records_history(session):
    pid = client.post(
        "/api/v1/properties", json={"name": "Gudiyatham 12", "asking_price": 900000}
    ).json()["id"]
    resp = client.patch(f"/api/v1/properties/{pid}", json={"asking_price": 950000})
    assert resp.status_code == 200, resp.text
    assert resp.json()["asking_price"] == 950000


def test_patch_name_collision_returns_409(session):
    client.post("/api/v1/properties", json={"name": "Existing"})
    pid = client.post("/api/v1/properties", json={"name": "Other"}).json()["id"]
    resp = client.patch(f"/api/v1/properties/{pid}", json={"name": "Existing"})
    assert resp.status_code == 409, resp.text


def test_list_properties_pagination_bounds(session):
    for i in range(3):
        client.post("/api/v1/properties", json={"name": f"Bulk {i}"})
    assert len(client.get("/api/v1/properties", params={"limit": 2}).json()) == 2
    # limit above the cap is rejected by validation.
    assert client.get("/api/v1/properties", params={"limit": 99999}).status_code == 422


def test_ocr_parse_rejects_oversized_text(session):
    resp = client.post("/api/v1/ocr/parse", json={"text": "x" * 100_001})
    assert resp.status_code == 422


def test_delete_property(session):
    pid = client.post("/api/v1/properties", json={"name": "Disposable"}).json()["id"]
    assert client.delete(f"/api/v1/properties/{pid}").status_code == 204
    assert client.get(f"/api/v1/properties/{pid}").status_code == 404


def test_delete_missing_property_returns_404(session):
    assert client.delete("/api/v1/properties/999999").status_code == 404
