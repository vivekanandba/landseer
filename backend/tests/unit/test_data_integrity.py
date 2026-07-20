"""Data-integrity tests: composite uniqueness constraints, NOT NULL on
Document.property_id, and SQLite cascade deletes (which only fire once
foreign-key enforcement is enabled)."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.broker import Broker, BrokerProperty
from app.models.comparison import Comparison, ComparisonItem
from app.models.document import Document
from app.models.price_history import PriceHistory
from app.models.property import Neighbor, Property, Subdivision


def _property(session, name="Subject") -> Property:
    prop = Property(name=name)
    session.add(prop)
    session.flush()
    return prop


def test_duplicate_subdivision_rejected(session):
    prop = _property(session)
    session.add(Subdivision(property_id=prop.id, name="Plot A"))
    session.flush()
    session.add(Subdivision(property_id=prop.id, name="Plot A"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_duplicate_neighbor_rejected(session):
    prop = _property(session)
    session.add(Neighbor(property_id=prop.id, survey_number="171-4"))
    session.flush()
    session.add(Neighbor(property_id=prop.id, survey_number="171-4"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_duplicate_broker_property_link_rejected(session):
    prop = _property(session)
    broker = Broker(name="Ravi")
    session.add(broker)
    session.flush()
    session.add(BrokerProperty(broker_id=broker.id, property_id=prop.id))
    session.flush()
    session.add(BrokerProperty(broker_id=broker.id, property_id=prop.id))
    with pytest.raises(IntegrityError):
        session.flush()


def test_duplicate_comparison_item_rejected(session):
    prop = _property(session)
    cmp = Comparison(name="Shortlist")
    session.add(cmp)
    session.flush()
    session.add(ComparisonItem(comparison_id=cmp.id, property_id=prop.id))
    session.flush()
    session.add(ComparisonItem(comparison_id=cmp.id, property_id=prop.id))
    with pytest.raises(IntegrityError):
        session.flush()


def test_document_requires_a_parent_property(session):
    session.add(Document(filename="patta.pdf", property_id=None))
    with pytest.raises(IntegrityError):
        session.flush()


def test_deleting_property_cascades_to_price_history(session):
    """price_history has no ORM relationship on Property, so removal relies on
    the DB-level ON DELETE CASCADE — which only works with FK enforcement on."""
    prop = _property(session)
    session.add(PriceHistory(property_id=prop.id, price=1_000_000))
    session.flush()
    assert session.execute(select(PriceHistory)).scalars().all()

    session.delete(prop)
    session.flush()
    assert session.execute(select(PriceHistory)).scalars().all() == []
