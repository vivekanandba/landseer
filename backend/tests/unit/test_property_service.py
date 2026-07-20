"""Focused unit tests for property_service functions not covered elsewhere."""

import pytest

from app.models.property import Direction, PropertyStatus
from app.services import property_service as svc


def test_create_normalizes_aliases_and_string_numerics(make_property):
    # "area_sqft" aliases to total_area_sqft; a string numeric is coerced.
    prop = make_property("Aliased", area_sqft="12500", price_total="1850000")
    assert prop.total_area_sqft == 12500.0
    assert prop.asking_price == 1850000.0


def test_duplicate_create_raises(make_property):
    make_property("Dup")
    with pytest.raises(svc.DuplicateProperty):
        make_property("Dup")


def test_get_missing_raises(session):
    with pytest.raises(svc.PropertyNotFound):
        svc.get_property(session, 999999)


def test_get_or_create_is_idempotent(session, make_property):
    first = make_property("OnceOnly", location="Katpadi")
    again = svc.get_or_create_property(session, "OnceOnly")
    assert again.id == first.id
    fresh = svc.get_or_create_property(session, "Brand New")
    assert fresh.id != first.id


def test_update_status_logs_transition(session, make_property):
    prop = make_property("Movable")
    svc.update_status(session, prop, "shortlisted")
    assert prop.status == PropertyStatus.SHORTLISTED
    actions = [log.action for log in prop.activity_logs]
    assert "status_changed" in actions


def test_add_subdivision_and_neighbor(session, make_property):
    prop = make_property("Parcel")
    sub = svc.add_subdivision(session, prop, name="Plot A", area_sqft=5000)
    neighbor = svc.add_neighbor(session, prop, survey_number="12-3", direction="north")
    assert sub.property_id == prop.id
    assert neighbor.direction is Direction.NORTH
    assert prop.subdivision_area_sqft == 5000
