"""Integration tests for the import endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_import_property(session):
    resp = client.post(
        "/api/v1/imports/property",
        json={
            "name": "Thuthikadu",
            "files": [
                {"path": "1392-171-4-Patta.pdf"},
                {"path": "171-4A/171-4A-FMB.pdf"},
                {"path": "Neighbors/171-3A8/171-3A8-Patta.pdf"},
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    report = resp.json()
    assert report["properties_created"] == 1
    assert report["subdivisions_created"] == 1
    assert report["neighbors_tracked"] == 1
    assert report["documents_imported"] == 3


def test_batch_import(session):
    resp = client.post(
        "/api/v1/imports/batch",
        json={
            "folders": [
                {"name": "Moothakkal", "files": [{"path": f"m-{i}.pdf"} for i in range(3)]},
                {"name": "Irumbli", "files": [{"path": f"i-{i}.pdf"} for i in range(4)]},
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["properties_created"] == 2 and body["documents_imported"] == 7
    assert "Imported 2 properties" in body["summary"]
