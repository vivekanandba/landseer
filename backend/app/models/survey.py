"""Survey boundaries: ordered vertices describing a plot's outline.

Geometry is stored as portable lat/long floats (works identically on SQLite and
PostgreSQL) rather than a PostGIS geometry type, so the in-memory test path needs
no spatial extension. A neighbor's boundary is attached to the same parent
property (via ``neighbor_id``) so it can be layered on one map.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SurveyBoundary(Base, TimestampMixin):
    __tablename__ = "survey_boundaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    # Set when this boundary outlines a neighbor of the property (else None = subject).
    neighbor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("neighbors.id", ondelete="CASCADE")
    )
    label: Mapped[Optional[str]] = mapped_column(String(255))
    srid: Mapped[int] = mapped_column(Integer, default=4326)

    vertices: Mapped[List["SurveyVertex"]] = relationship(
        back_populates="boundary",
        cascade="all, delete-orphan",
        order_by="SurveyVertex.seq",
    )

    @property
    def is_neighbor(self) -> bool:
        return self.neighbor_id is not None


class SurveyVertex(Base):
    __tablename__ = "survey_vertices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    boundary_id: Mapped[int] = mapped_column(
        ForeignKey("survey_boundaries.id", ondelete="CASCADE")
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)

    boundary: Mapped["SurveyBoundary"] = relationship(back_populates="vertices")
