"""Integration tests for the Smart Matching endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_recommend_flow(session):
    # Seed a couple of properties directly through the property API.
    client.post("/api/v1/properties", json={
        "name": "Cheap Plot", "location": "Thuthikadu",
        "total_area_sqft": 100000, "asking_price": 3000000, "price_per_sqft": 30,
    })
    client.post("/api/v1/properties", json={
        "name": "Pricey Plot", "location": "Thuthikadu",
        "total_area_sqft": 10000, "asking_price": 9000000, "price_per_sqft": 400,
    })

    created = client.post("/api/v1/preferences", json={
        "name": "Value Seeker", "budget_max": 4000000, "locations": ["Thuthikadu"],
    })
    assert created.status_code == 201, created.text

    recs = client.get("/api/v1/preferences/Value Seeker/recommendations")
    assert recs.status_code == 200
    body = recs.json()
    names = [r["name"] for r in body]
    assert names[0] == "Cheap Plot"                      # best fit first
    pricey = next(r for r in body if r["name"] == "Pricey Plot")
    assert pricey["disqualified"] and pricey["reasons"]  # over budget


def test_unknown_preference_returns_404(session):
    assert client.get("/api/v1/preferences/nope/recommendations").status_code == 404
