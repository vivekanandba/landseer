"""Comparison aggregate: a saved side-by-side of several properties."""

from __future__ import annotations

from typing import List

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Comparison(Base, TimestampMixin):
    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")

    items: Mapped[List[ComparisonItem]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
        order_by="ComparisonItem.id",
    )


class ComparisonItem(Base):
    __tablename__ = "comparison_items"
    __table_args__ = (
        UniqueConstraint("comparison_id", "property_id", name="uq_comparison_property"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comparison_id: Mapped[int] = mapped_column(ForeignKey("comparisons.id", ondelete="CASCADE"))
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )

    comparison: Mapped[Comparison] = relationship(back_populates="items")
