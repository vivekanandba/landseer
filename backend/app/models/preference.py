"""Buyer preference / requirements used by the Smart Matching engine."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Preference(Base, TimestampMixin):
    """A named set of land-buying requirements to score properties against.

    List/dict fields use the portable ``JSON`` column type (supported on both
    SQLite and PostgreSQL) so no extra dependency or migration machinery is
    needed for the in-memory test path.
    """

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    size_min_sqft: Mapped[Optional[float]] = mapped_column(Float)
    size_max_sqft: Mapped[Optional[float]] = mapped_column(Float)
    budget_max: Mapped[Optional[float]] = mapped_column(Float)

    # Acceptable locations (empty = any).
    locations: Mapped[List[str]] = mapped_column(JSON, default=list)
    # Feature attributes that must be present, e.g. ["water_source", "corner_plot"].
    required_features: Mapped[List[str]] = mapped_column(JSON, default=list)
    # Optional per-criterion weight override; falls back to DEFAULT_WEIGHTS when null.
    weights: Mapped[Optional[dict]] = mapped_column(JSON)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Preference {self.name!r}>"
