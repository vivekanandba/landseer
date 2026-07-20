"""Integration tests for comparison endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _seed_two(session):
    a = client.post(
        "/api/v1/properties",
        json={
            "name": "Thuthikadu 171-4",
            "location": "Thuthikadu",
            "total_area_sqft": 12500,
            "asking_price": 1850000,
            "price_per_sqft": 148,
        },
    ).json()["id"]
    b = client.post(
        "/api/v1/properties",
        json={
            "name": "Kotikal Forest",
            "location": "Kathalampattu",
            "total_area_sqft": 112000,
            "asking_price": 3500000,
            "price_per_sqft": 31,
        },
    ).json()["id"]
    return a, b


def test_create_view_and_export(session):
    a, b = _seed_two(session)
    created = client.post("/api/v1/comparisons", json={"name": "Top 2", "property_ids": [a, b]})
    assert created.status_code == 201, created.text

    table = client.get("/api/v1/comparisons/Top 2/table").json()
    assert table["columns"][0] == "Location" and len(table["rows"]) == 2

    pdf = client.get("/api/v1/comparisons/Top 2/export.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_add_property_and_notes(session):
    a, b = _seed_two(session)
    client.post("/api/v1/comparisons", json={"name": "C", "property_ids": [a]})
    client.post(f"/api/v1/comparisons/C/properties/{b}")
    patched = client.patch("/api/v1/comparisons/C", json={"notes": "weekend review"})
    assert patched.json()["notes"] == "weekend review"
    assert len(client.get("/api/v1/comparisons/C/table").json()["rows"]) == 2


def test_features_and_investment_typed_responses(session):
    a, b = _seed_two(session)
    client.post("/api/v1/comparisons", json={"name": "Views", "property_ids": [a, b]})

    features = client.get("/api/v1/comparisons/Views/features")
    assert features.status_code == 200, features.text
    # Keyed by property name; each feature cell has value + color.
    cell = features.json()["Thuthikadu 171-4"]["water_source"]
    assert set(cell) == {"value", "color"}

    investment = client.get("/api/v1/comparisons/Views/investment")
    assert investment.status_code == 200, investment.text
    entry = investment.json()["Thuthikadu 171-4"]
    assert {"projected_value_3y", "registration_cost", "total_investment"} <= set(entry)


def test_unknown_comparison_404(session):
    assert client.get("/api/v1/comparisons/nope/table").status_code == 404


def test_duplicate_comparison_409(session):
    client.post("/api/v1/comparisons", json={"name": "Dup"})
    again = client.post("/api/v1/comparisons", json={"name": "Dup"})
    assert again.status_code == 409
