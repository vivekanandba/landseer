"""Integration tests for document upload/list and OCR parse endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _property(name="Thuthikadu 171-4"):
    return client.post("/api/v1/properties", json={"name": name}).json()["id"]


def test_upload_and_list_documents(session):
    pid = _property()
    created = client.post(
        f"/api/v1/properties/{pid}/documents", json={"filename": "171-4-Patta.pdf"}
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["doc_type"] == "patta" and body["ocr_status"] == "queued"

    listed = client.get(f"/api/v1/properties/{pid}/documents").json()
    assert [d["filename"] for d in listed] == ["171-4-Patta.pdf"]


def test_unknown_doc_type_returns_422(session):
    pid = _property("P2")
    resp = client.post(
        f"/api/v1/properties/{pid}/documents",
        json={"filename": "x.pdf", "doc_type": "nonsense"},
    )
    assert resp.status_code == 422


def test_ocr_parse_endpoint(session):
    resp = client.post(
        "/api/v1/ocr/parse",
        json={"text": "Survey Number: 171-4\nOwner Name: Ramesh Kumar\nVillage: Thuthikadu"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["survey_number"] == "171-4"
    assert body["owner_name"] == "Ramesh Kumar"
