"""Integration test for the notifications endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.services import property_service as props

client = TestClient(app)


def test_notifications_reports_price_alert(session):
    # Seed a property with a >5% price jump, then commit so the request sees it.
    prop = props.create_property(session, name="Alert Plot", asking_price=1000000)
    props.record_price(session, prop, 1000000)
    props.record_price(session, prop, 1300000)  # +30%
    session.commit()

    resp = client.get("/api/v1/notifications", params={"price_threshold_pct": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert {"expiring_documents", "price_alerts", "follow_ups"} <= set(body)
    assert any(a["name"] == "Alert Plot" for a in body["price_alerts"])


def test_notifications_empty_by_default(session):
    resp = client.get("/api/v1/notifications")
    assert resp.status_code == 200
    assert resp.json() == {"expiring_documents": [], "price_alerts": [], "follow_ups": []}
