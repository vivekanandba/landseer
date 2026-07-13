"""Automation: surface documents nearing expiry, price changes and stale
follow-ups, and dispatch them through a pluggable notifier.

All scan functions are pure and take an ``as_of`` date so they are deterministic
and testable in-memory. Delivery is abstracted behind ``Notifier`` — the default
``LogNotifier`` just captures messages; SMTP/email is a later, credential-gated
notifier.
"""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.price_history import PriceHistory
from app.models.property import ActivityLog, Property, PropertyStatus
from app.services import document_service as docs


class Notifier:
    """Delivery interface. Implementations send a single message string."""

    def send(self, message: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class LogNotifier(Notifier):
    """Default notifier: collects messages (and logs them) instead of sending."""

    def __init__(self):
        self.messages: List[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


def expiring_documents(
    session: Session, within_days: int = 30, as_of: Optional[date] = None
) -> List[dict]:
    """Documents whose expiry falls on/before ``as_of + within_days`` (includes
    already-expired). Reuses document_service.expiry_date."""
    as_of = as_of or date.today()
    horizon = as_of + timedelta(days=within_days)
    alerts = []
    for doc in session.scalars(select(Document)):
        expires = docs.expiry_date(doc)
        if expires is None or expires > horizon:
            continue
        state = "expired" if expires < as_of else "expiring soon"
        message = f"{doc.filename} ({doc.doc_type.value}) {state} on {expires.isoformat()}"
        alerts.append(
            {
                "document_id": doc.id,
                "property_id": doc.property_id,
                "filename": doc.filename,
                "expires_on": expires.isoformat(),
                "message": message,
            }
        )
    return alerts


def price_change_alerts(session: Session, threshold_pct: float = 5.0) -> List[dict]:
    """Properties whose two most recent recorded prices differ by >= threshold."""
    alerts = []
    for prop in session.scalars(select(Property)):
        history = list(
            session.scalars(
                select(PriceHistory)
                .where(PriceHistory.property_id == prop.id)
                .order_by(PriceHistory.id.desc())
            )
        )
        if len(history) < 2:
            continue
        new_price, old_price = history[0].price, history[1].price
        if not old_price:
            continue
        change_pct = (new_price - old_price) / old_price * 100
        if abs(change_pct) < threshold_pct:
            continue
        direction = "increased" if change_pct > 0 else "dropped"
        alerts.append(
            {
                "property_id": prop.id,
                "name": prop.name,
                "old_price": old_price,
                "new_price": new_price,
                "change_pct": round(change_pct, 1),
                "message": f"{prop.name}: price {direction} {abs(round(change_pct, 1))}% "
                f"({old_price:.0f} -> {new_price:.0f})",
            }
        )
    return alerts


def follow_ups(session: Session, as_of: Optional[date] = None, idle_days: int = 30) -> List[dict]:
    """Properties still being evaluated with no activity in ``idle_days``."""
    as_of = as_of or date.today()
    alerts = []
    for prop in session.scalars(
        select(Property).where(Property.status == PropertyStatus.EVALUATING)
    ):
        last = session.scalar(
            select(ActivityLog.created_at)
            .where(ActivityLog.property_id == prop.id)
            .order_by(ActivityLog.created_at.desc())
        )
        if last is None:
            continue
        idle = (as_of - last.date()).days
        if idle < idle_days:
            continue
        alerts.append(
            {
                "property_id": prop.id,
                "name": prop.name,
                "idle_days": idle,
                "message": f"{prop.name}: no activity in {idle} days — follow up?",
            }
        )
    return alerts


def collect(
    session: Session,
    as_of: Optional[date] = None,
    within_days: int = 30,
    idle_days: int = 30,
    price_threshold_pct: float = 5.0,
) -> dict:
    """Run every scan and return the categorized results."""
    return {
        "expiring_documents": expiring_documents(session, within_days, as_of),
        "price_alerts": price_change_alerts(session, price_threshold_pct),
        "follow_ups": follow_ups(session, as_of, idle_days),
    }


def run_due(session: Session, notifier: Notifier, **kwargs) -> dict:
    """Collect all due notifications and dispatch each via ``notifier``."""
    result = collect(session, **kwargs)
    for items in result.values():
        for item in items:
            notifier.send(item["message"])
    return result
