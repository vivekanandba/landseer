"""Property aggregate: Property, Subdivision, Neighbor and the activity timeline."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PropertyStatus(str, enum.Enum):
    EVALUATING = "evaluating"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    PURCHASED = "purchased"


class Direction(str, enum.Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class Property(Base, TimestampMixin):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    survey_number: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    taluk: Mapped[Optional[str]] = mapped_column(String(128))
    district: Mapped[str] = mapped_column(String(128), default="Vellore")

    total_area_sqft: Mapped[Optional[float]] = mapped_column(Float)
    asking_price: Mapped[Optional[float]] = mapped_column(Float, index=True)
    price_per_sqft: Mapped[Optional[float]] = mapped_column(Float)

    status: Mapped[PropertyStatus] = mapped_column(
        Enum(PropertyStatus, values_callable=lambda e: [m.value for m in e]),
        default=PropertyStatus.EVALUATING,
        nullable=False,
        index=True,
    )

    # Infrastructure / feature flags used by comparison.
    water_source: Mapped[Optional[str]] = mapped_column(String(64))
    electricity: Mapped[Optional[str]] = mapped_column(String(64))
    road_access: Mapped[Optional[str]] = mapped_column(String(64))
    corner_plot: Mapped[Optional[bool]] = mapped_column()

    # Investment / scoring fields used by comparison.
    estimated_appreciation_pct: Mapped[Optional[float]] = mapped_column(Float)
    rental_yield: Mapped[Optional[str]] = mapped_column(String(32))
    match_score: Mapped[Optional[float]] = mapped_column(Float)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    subdivisions: Mapped[List[Subdivision]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
    neighbors: Mapped[List[Neighbor]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List[ActivityLog]] = relationship(
        back_populates="property", cascade="all, delete-orphan", order_by="ActivityLog.created_at"
    )

    @property
    def subdivision_area_sqft(self) -> float:
        return sum(s.area_sqft or 0 for s in self.subdivisions)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Property {self.name!r} ({self.status.value})>"


class Subdivision(Base, TimestampMixin):
    __tablename__ = "subdivisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    survey_number_full: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    area_sqft: Mapped[Optional[float]] = mapped_column(Float)

    property: Mapped[Property] = relationship(back_populates="subdivisions")


class Neighbor(Base, TimestampMixin):
    __tablename__ = "neighbors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    survey_number: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    direction: Mapped[Optional[Direction]] = mapped_column(
        Enum(Direction, values_callable=lambda e: [m.value for m in e])
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)
    shared_boundary: Mapped[bool] = mapped_column(default=False)

    property: Mapped[Property] = relationship(back_populates="neighbors")


class ActivityLog(Base):
    """Append-only timeline of changes for a property."""

    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    property: Mapped[Property] = relationship(back_populates="activity_logs")
