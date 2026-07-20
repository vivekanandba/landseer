"""Pydantic schemas for brokers."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BrokerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    areas_covered: Optional[str] = None
    commission_rate: float = 0.0


class BrokerRead(BrokerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class BrokerPropertyLink(BaseModel):
    shown_date: Optional[date] = None
    asking_price: Optional[float] = None
    broker_notes: Optional[str] = None


class BrokerPerformance(BaseModel):
    broker_id: int
    shown_count: int
    shortlisted_count: int
    purchased_count: int
    shortlist_rate: float
    conversion_rate: float


class BrokerPropertyLinkResult(BaseModel):
    broker_id: int
    property_id: int
