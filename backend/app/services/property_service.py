"""Property domain operations.

The service layer is intentionally free of FastAPI/HTTP concerns so it can be
driven directly from BDD step definitions and unit tests, and reused by the API.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price_history import PriceHistory
from app.models.property import (
    ActivityLog,
    Direction,
    Neighbor,
    Property,
    PropertyStatus,
    Subdivision,
)


class PropertyNotFound(Exception):
    pass


class DuplicateProperty(Exception):
    pass


# Some callers (e.g. the comparison feature) speak in spreadsheet column names;
# map those to the canonical model attributes.
FIELD_ALIASES = {
    "area_sqft": "total_area_sqft",
    "price_total": "asking_price",
}
NUMERIC_FIELDS = {"total_area_sqft", "asking_price", "price_per_sqft"}


def _coerce_status(status) -> PropertyStatus:
    if isinstance(status, PropertyStatus):
        return status
    return PropertyStatus(str(status))


def _normalize_fields(fields: dict) -> dict:
    normalized = {}
    for key, value in fields.items():
        key = FIELD_ALIASES.get(key, key)
        if key in NUMERIC_FIELDS and value is not None and not isinstance(value, (int, float)):
            value = float(value)
        normalized[key] = value
    return normalized


def create_property(session: Session, **fields) -> Property:
    fields = _normalize_fields(fields)
    name = fields.get("name")
    if name and get_property_by_name(session, name) is not None:
        raise DuplicateProperty(f"Property {name!r} already exists")

    if "status" in fields and fields["status"] is not None:
        fields["status"] = _coerce_status(fields["status"])

    prop = Property(**fields)
    session.add(prop)
    session.flush()
    _log(session, prop, "created", f"Property {prop.name!r} created")
    return prop


def get_property(session: Session, property_id: int) -> Property:
    prop = session.get(Property, property_id)
    if prop is None:
        raise PropertyNotFound(f"Property id={property_id} not found")
    return prop


def get_property_by_name(session: Session, name: str) -> Optional[Property]:
    return session.scalar(select(Property).where(Property.name == name))


def get_or_create_property(session: Session, name: str, **fields) -> Property:
    existing = get_property_by_name(session, name)
    if existing is not None:
        return existing
    return create_property(session, name=name, **fields)


def update_status(session: Session, prop: Property, status) -> Property:
    new_status = _coerce_status(status)
    old_status = prop.status
    prop.status = new_status
    session.flush()
    _log(
        session,
        prop,
        "status_changed",
        f"Status changed from {old_status.value} to {new_status.value}",
    )
    return prop


def add_subdivision(
    session: Session,
    prop: Property,
    name: str,
    survey_number_full: Optional[str] = None,
    area_sqft: Optional[float] = None,
) -> Subdivision:
    sub = Subdivision(
        property_id=prop.id,
        name=name,
        survey_number_full=survey_number_full,
        area_sqft=area_sqft,
    )
    session.add(sub)
    session.flush()
    return sub


def add_neighbor(
    session: Session,
    prop: Property,
    survey_number: str,
    direction=None,
    notes: Optional[str] = None,
    shared_boundary: bool = False,
) -> Neighbor:
    if isinstance(direction, str) and direction:
        direction = Direction(direction)
    neighbor = Neighbor(
        property_id=prop.id,
        survey_number=survey_number,
        direction=direction,
        notes=notes,
        shared_boundary=shared_boundary,
    )
    session.add(neighbor)
    session.flush()
    return neighbor


def search_by_location(session: Session, location: str) -> List[Property]:
    stmt = select(Property).where(Property.location == location)
    return list(session.scalars(stmt))


def filter_by_price(session: Session, low: float, high: float) -> List[Property]:
    stmt = (
        select(Property)
        .where(Property.asking_price >= low, Property.asking_price <= high)
        .order_by(Property.asking_price)
    )
    return list(session.scalars(stmt))


def list_properties(session: Session) -> List[Property]:
    return list(session.scalars(select(Property).order_by(Property.name)))


def record_price(
    session: Session, prop: Property, price: float, source: str = "manual"
) -> PriceHistory:
    """Record a new asking price: update the property and append price history
    (which drives price-change alerts) and the activity timeline."""
    price = float(price)
    old = prop.asking_price
    prop.asking_price = price
    entry = PriceHistory(property_id=prop.id, price=price, source=source)
    session.add(entry)
    session.flush()
    _log(session, prop, "price_changed", f"Price {old} -> {price} ({source})")
    return entry


def _log(session: Session, prop: Property, action: str, detail: str) -> ActivityLog:
    entry = ActivityLog(property_id=prop.id, action=action, detail=detail)
    session.add(entry)
    session.flush()
    return entry
