"""Broker domain operations."""

from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker import Broker, BrokerProperty
from app.models.property import Property, PropertyStatus


class BrokerNotFound(Exception):
    pass


def create_broker(session: Session, **fields) -> Broker:
    broker = Broker(**fields)
    session.add(broker)
    session.flush()
    return broker


def get_broker_by_name(session: Session, name: str) -> Optional[Broker]:
    return session.scalar(select(Broker).where(Broker.name == name))


def get_broker(session: Session, broker_id: int) -> Broker:
    broker = session.get(Broker, broker_id)
    if broker is None:
        raise BrokerNotFound(f"Broker id={broker_id} not found")
    return broker


def list_brokers(session: Session) -> List[Broker]:
    return list(session.scalars(select(Broker).order_by(Broker.name)))


def link_to_property(
    session: Session,
    broker: Broker,
    prop: Property,
    shown_date: Optional[date] = None,
    asking_price: Optional[float] = None,
    broker_notes: Optional[str] = None,
) -> BrokerProperty:
    link = BrokerProperty(
        broker_id=broker.id,
        property_id=prop.id,
        shown_date=shown_date,
        asking_price=asking_price,
        broker_notes=broker_notes,
    )
    session.add(link)
    session.flush()
    return link


def brokers_for_property(session: Session, prop: Property) -> List[BrokerProperty]:
    stmt = (
        select(BrokerProperty)
        .where(BrokerProperty.property_id == prop.id)
        .order_by(BrokerProperty.shown_date)
    )
    return list(session.scalars(stmt))


def search_by_area(session: Session, area: str) -> List[Broker]:
    needle = area.strip().lower()
    return [b for b in session.scalars(select(Broker)) if needle in [a.lower() for a in b.areas]]


def performance(session: Session, broker: Broker) -> dict:
    """Conversion metrics across the properties this broker has shown."""
    links = session.scalars(
        select(BrokerProperty).where(BrokerProperty.broker_id == broker.id)
    ).all()
    shown = len(links)
    statuses = []
    for link in links:
        prop = session.get(Property, link.property_id)
        if prop is not None:
            statuses.append(prop.status)
    shortlisted = sum(1 for s in statuses if s == PropertyStatus.SHORTLISTED)
    purchased = sum(1 for s in statuses if s == PropertyStatus.PURCHASED)
    return {
        "broker_id": broker.id,
        "shown_count": shown,
        "shortlisted_count": shortlisted,
        "purchased_count": purchased,
        "shortlist_rate": round(shortlisted / shown * 100, 2) if shown else 0.0,
        "conversion_rate": round(purchased / shown * 100, 2) if shown else 0.0,
    }
