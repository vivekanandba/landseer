"""Integration tests for the survey boundary / map endpoints."""

import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SQUARE = [
    {"lat": 12.9001, "lng": 79.1001},
    {"lat": 12.9005, "lng": 79.1001},
    {"lat": 12.9005, "lng": 79.1010},
    {"lat": 12.9001, "lng": 79.1010},
]


def _create_property(name="Thuthikadu 171-4"):
    return client.post("/api/v1/properties", json={"name": name}).json()["id"]


def test_add_boundary_and_geojson(session):
    pid = _create_property()
    created = client.post(f"/api/v1/properties/{pid}/boundary", json={"vertices": SQUARE})
    assert created.status_code == 201, created.text
    assert len(created.json()["vertices"]) == 4

    fc = client.get(f"/api/v1/properties/{pid}/map.geojson").json()
    assert fc["type"] == "FeatureCollection"
    assert fc["features"][0]["properties"]["role"] == "subject"
    # GeoJSON coordinates are lng,lat.
    assert fc["features"][0]["geometry"]["coordinates"][0][0][0] > 79


def test_boundary_requires_three_vertices(session):
    pid = _create_property("P2")
    resp = client.post(f"/api/v1/properties/{pid}/boundary", json={"vertices": SQUARE[:2]})
    assert resp.status_code == 422  # pydantic min_length


def test_boundary_on_missing_property_404(session):
    assert (
        client.post("/api/v1/properties/999999/boundary", json={"vertices": SQUARE}).status_code
        == 404
    )


def test_map_kml_streams_without_persisting(session):
    pid = _create_property("KmlProp")
    client.post(f"/api/v1/properties/{pid}/boundary", json={"vertices": SQUARE})
    resp = client.get(f"/api/v1/properties/{pid}/map.kml")
    assert resp.status_code == 200
    assert resp.text.startswith("<?xml") and "coordinates" in resp.text
    # No artifact left under the repo data dir.
    assert not os.path.exists(os.path.join("data", "kml", f"property-{pid}.kml"))
