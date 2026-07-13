"""Broker aggregate and the broker<->property association."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Broker(Base, TimestampMixin):
    __tablename__ = "brokers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    # Stored as a comma-separated list of areas (e.g. "Vellore,Katpadi").
    areas_covered: Mapped[Optional[str]] = mapped_column(String(512))
    commission_rate: Mapped[float] = mapped_column(Float, default=0.0)

    listings: Mapped[List[BrokerProperty]] = relationship(
        back_populates="broker", cascade="all, delete-orphan"
    )

    @property
    def areas(self) -> List[str]:
        if not self.areas_covered:
            return []
        return [a.strip() for a in self.areas_covered.split(",") if a.strip()]

    def commission_on(self, negotiated_price: float) -> float:
        return round(negotiated_price * self.commission_rate / 100.0, 2)


class BrokerProperty(Base, TimestampMixin):
    """A broker showing a specific property, with the terms on that day."""

    __tablename__ = "broker_properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    broker_id: Mapped[int] = mapped_column(ForeignKey("brokers.id", ondelete="CASCADE"))
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    shown_date: Mapped[Optional[date]] = mapped_column(Date)
    asking_price: Mapped[Optional[float]] = mapped_column(Float)
    broker_notes: Mapped[Optional[str]] = mapped_column(Text)

    broker: Mapped[Broker] = relationship(back_populates="listings")
