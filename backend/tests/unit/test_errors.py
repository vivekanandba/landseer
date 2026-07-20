"""Unit tests for the global exception handlers / error envelope."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import register_exception_handlers
from app.services.property_service import DuplicateProperty, PropertyNotFound
from app.services.survey_service import InvalidBoundary


def _app_that_raises(exc: Exception) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise exc

    # raise_server_exceptions=False so the catch-all handler produces a response
    # instead of the test client re-raising.
    return TestClient(app, raise_server_exceptions=False)


def test_domain_not_found_maps_to_404_envelope():
    client = _app_that_raises(PropertyNotFound("no such property"))
    resp = client.get("/boom")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["type"] == "PropertyNotFound"
    assert body["error"]["message"] == "no such property"
    assert "request_id" in body["error"]


def test_domain_duplicate_maps_to_409():
    resp = _app_that_raises(DuplicateProperty("dup")).get("/boom")
    assert resp.status_code == 409
    assert resp.json()["error"]["type"] == "DuplicateProperty"


def test_domain_invalid_maps_to_422():
    resp = _app_that_raises(InvalidBoundary("bad")).get("/boom")
    assert resp.status_code == 422
    assert resp.json()["error"]["type"] == "InvalidBoundary"


def test_unhandled_exception_is_generic_500_without_leaking_details():
    resp = _app_that_raises(RuntimeError("secret internal detail")).get("/boom")
    assert resp.status_code == 500
    assert "secret internal detail" not in resp.text
    body = resp.json()
    assert body["error"]["type"] == "InternalServerError"
    assert body["error"]["message"] == "An internal error occurred."
