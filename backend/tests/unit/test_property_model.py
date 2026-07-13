"""Unit tests for the Property model and service (TDD)."""

import pytest

from app.models.property import PropertyStatus
from app.services import property_service as svc


def test_create_property_defaults_to_evaluating(session):
    prop = svc.create_property(session, name="Thuthikadu 171-4", survey_number="171-4")
    assert prop.id is not None
    assert prop.status == PropertyStatus.EVALUATING
    assert prop.district == "Vellore"


def test_duplicate_name_raises(session):
    svc.create_property(session, name="Moothakkal")
    with pytest.raises(svc.DuplicateProperty):
        svc.create_property(session, name="Moothakkal")


def test_subdivision_area_totals(session):
    prop = svc.create_property(session, name="Thuthikadu 171-4")
    svc.add_subdivision(session, prop, name="4A", survey_number_full="171-4A", area_sqft=4200)
    svc.add_subdivision(session, prop, name="4C", survey_number_full="171-4C", area_sqft=4100)
    svc.add_subdivision(session, prop, name="4D", survey_number_full="171-4D", area_sqft=4200)
    session.refresh(prop)
    assert len(prop.subdivisions) == 3
    assert prop.subdivision_area_sqft == 12500


def test_add_neighbor_with_direction(session):
    prop = svc.create_property(session, name="Thuthikadu 171-4")
    svc.add_neighbor(session, prop, survey_number="171-3A8", direction="north")
    session.refresh(prop)
    assert prop.neighbors[0].direction.value == "north"


def test_status_update_is_logged(session):
    prop = svc.create_property(session, name="Moothakkal")
    svc.update_status(session, prop, "shortlisted")
    assert prop.status == PropertyStatus.SHORTLISTED
    actions = [log.action for log in prop.activity_logs]
    assert "status_changed" in actions


def test_search_by_location(session):
    svc.create_property(session, name="Thuthikadu 171-4", location="Thuthikadu")
    svc.create_property(session, name="Moothakkal Plot", location="Moothakkal")
    results = svc.search_by_location(session, "Thuthikadu")
    assert [p.name for p in results] == ["Thuthikadu 171-4"]


def test_filter_by_price(session):
    svc.create_property(session, name="A", asking_price=1850000)
    svc.create_property(session, name="B", asking_price=1600000)
    svc.create_property(session, name="C", asking_price=3500000)
    results = svc.filter_by_price(session, 1500000, 2000000)
    assert {p.name for p in results} == {"A", "B"}
