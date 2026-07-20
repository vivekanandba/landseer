"""Integration tests for broker endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_list_and_get_broker(session):
    created = client.post(
        "/api/v1/brokers",
        json={"name": "Rajesh Kumar", "areas_covered": "Vellore,Katpadi", "commission_rate": 2.0},
    )
    assert created.status_code == 201, created.text
    bid = created.json()["id"]

    assert client.get(f"/api/v1/brokers/{bid}").json()["name"] == "Rajesh Kumar"
    assert any(b["id"] == bid for b in client.get("/api/v1/brokers").json())
    by_area = client.get("/api/v1/brokers", params={"area": "Katpadi"}).json()
    assert [b["id"] for b in by_area] == [bid]


def test_link_broker_to_property_and_performance(session):
    bid = client.post("/api/v1/brokers", json={"name": "Suresh"}).json()["id"]
    pid = client.post("/api/v1/properties", json={"name": "Kotikal Forest"}).json()["id"]
    link = client.post(f"/api/v1/brokers/{bid}/properties/{pid}", json={"asking_price": 2500000})
    assert link.status_code == 201, link.text

    perf = client.get(f"/api/v1/brokers/{bid}/performance").json()
    assert perf["shown_count"] == 1 and perf["conversion_rate"] == 0.0


def test_unknown_broker_404(session):
    assert client.get("/api/v1/brokers/999999").status_code == 404


def test_relinking_broker_is_idempotent(session):
    bid = client.post("/api/v1/brokers", json={"name": "Meena"}).json()["id"]
    pid = client.post("/api/v1/properties", json={"name": "Ambur Plot"}).json()["id"]
    first = client.post(f"/api/v1/brokers/{bid}/properties/{pid}", json={"asking_price": 2000000})
    second = client.post(f"/api/v1/brokers/{bid}/properties/{pid}", json={"asking_price": 2200000})
    assert first.status_code == 201 and second.status_code == 201, second.text
    # Re-linking updates terms rather than creating a duplicate row.
    perf = client.get(f"/api/v1/brokers/{bid}/performance").json()
    assert perf["shown_count"] == 1
