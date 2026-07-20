"""Tests for property partial-update semantics and list pagination."""

import pytest
from sqlalchemy import select

from app.models.price_history import PriceHistory
from app.models.property import ActivityLog, PropertyStatus
from app.services import property_service as svc


def _prop(session, name="Subject", **fields):
    return svc.create_property(session, name=name, **fields)


def test_update_price_records_history_and_activity(session):
    prop = _prop(session, asking_price=1_000_000)  # seeds a baseline history row
    svc.update_property(session, prop, {"asking_price": 1_250_000})

    assert prop.asking_price == 1_250_000
    history = (
        session.execute(
            select(PriceHistory.price)
            .where(PriceHistory.property_id == prop.id)
            .order_by(PriceHistory.id)
        )
        .scalars()
        .all()
    )
    assert history == [1_000_000, 1_250_000]
    actions = (
        session.execute(select(ActivityLog.action).where(ActivityLog.property_id == prop.id))
        .scalars()
        .all()
    )
    assert "price_changed" in actions


def test_update_price_no_new_history_when_unchanged(session):
    prop = _prop(session, asking_price=1_000_000)  # baseline only
    svc.update_property(session, prop, {"asking_price": 1_000_000})
    history = (
        session.execute(select(PriceHistory.price).where(PriceHistory.property_id == prop.id))
        .scalars()
        .all()
    )
    assert history == [1_000_000]


def test_update_name_collision_raises(session):
    _prop(session, name="Alpha")
    beta = _prop(session, name="Beta")
    with pytest.raises(svc.DuplicateProperty):
        svc.update_property(session, beta, {"name": "Alpha"})


def test_update_status_and_plain_field(session):
    prop = _prop(session)
    svc.update_property(session, prop, {"status": PropertyStatus.SHORTLISTED, "notes": "nice"})
    assert prop.status == PropertyStatus.SHORTLISTED
    assert prop.notes == "nice"


def test_first_price_change_fires_alert_end_to_end(session):
    from app.services import notification_service as notify

    prop = _prop(session, asking_price=1_000_000)
    svc.update_property(session, prop, {"asking_price": 1_300_000})  # +30%
    alerts = notify.price_change_alerts(session, threshold_pct=5.0)
    assert any(a["property_id"] == prop.id and a["change_pct"] == 30.0 for a in alerts)


def test_list_properties_pagination(session):
    for i in range(5):
        _prop(session, name=f"P{i}")
    page = svc.list_properties(session, limit=2, offset=2)
    assert [p.name for p in page] == ["P2", "P3"]


def test_filtered_list_paths_honor_pagination(session):
    for i in range(4):
        _prop(session, name=f"Loc{i}", location="Ambur")
    by_loc = svc.search_by_location(session, "Ambur", limit=2, offset=1)
    assert [p.name for p in by_loc] == ["Loc1", "Loc2"]
