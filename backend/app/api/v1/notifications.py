"""Automation / notifications endpoint."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.notification import NotificationsResponse
from app.services import notification_service as notify

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationsResponse)
def notifications(
    as_of: Optional[date] = None,
    within_days: int = 30,
    idle_days: int = 30,
    price_threshold_pct: float = 5.0,
    db: Session = Depends(get_db),
):
    """Documents nearing expiry, notable price changes, and stale follow-ups.

    ``as_of`` (ISO date) lets you preview what would fire on a given day.
    """
    return notify.collect(
        db,
        as_of=as_of,
        within_days=within_days,
        idle_days=idle_days,
        price_threshold_pct=price_threshold_pct,
    )
