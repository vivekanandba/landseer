"""Pydantic schemas for the automation / notifications API."""

from typing import List, Optional

from pydantic import BaseModel


class ExpiringDocument(BaseModel):
    document_id: int
    property_id: Optional[int] = None
    filename: str
    expires_on: str
    message: str


class PriceAlert(BaseModel):
    property_id: int
    name: str
    old_price: float
    new_price: float
    change_pct: float
    message: str


class FollowUp(BaseModel):
    property_id: int
    name: str
    idle_days: int
    message: str


class NotificationsResponse(BaseModel):
    expiring_documents: List[ExpiringDocument]
    price_alerts: List[PriceAlert]
    follow_ups: List[FollowUp]
