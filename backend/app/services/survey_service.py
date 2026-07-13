"""Survey boundary operations: store vertices and gather them for mapping."""
from typing import List, Optional, Sequence, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.property import Neighbor, Property
from app.models.survey import SurveyBoundary, SurveyVertex

Vertex = Tuple[float, float]  # (lat, lng)


class InvalidBoundary(Exception):
    pass


def add_boundary(
    session: Session,
    prop: Property,
    vertices: Sequence[Vertex],
    label: Optional[str] = None,
    neighbor: Optional[Neighbor] = None,
) -> SurveyBoundary:
    """Store an ordered polygon of (lat, lng) vertices for a property or one of
    its neighbors. At least 3 vertices are required to form a polygon."""
    if len(vertices) < 3:
        raise InvalidBoundary("A boundary needs at least 3 vertices")

    boundary = SurveyBoundary(
        property_id=prop.id,
        neighbor_id=neighbor.id if neighbor else None,
        label=label or (neighbor.survey_number if neighbor else prop.name),
    )
    session.add(boundary)
    session.flush()
    for i, (lat, lng) in enumerate(vertices):
        session.add(SurveyVertex(boundary_id=boundary.id, seq=i, lat=lat, lng=lng))
    session.flush()
    session.refresh(boundary)
    return boundary


def boundary_for(session: Session, prop: Property) -> Optional[SurveyBoundary]:
    """The subject property's own boundary (neighbor boundaries excluded)."""
    return session.scalar(
        select(SurveyBoundary).where(
            SurveyBoundary.property_id == prop.id, SurveyBoundary.neighbor_id.is_(None)
        )
    )


def neighbor_boundaries(session: Session, prop: Property) -> List[SurveyBoundary]:
    return list(
        session.scalars(
            select(SurveyBoundary).where(
                SurveyBoundary.property_id == prop.id,
                SurveyBoundary.neighbor_id.is_not(None),
            )
        )
    )


def boundaries_for_map(session: Session, prop: Property) -> List[SurveyBoundary]:
    """Subject boundary first (if any), then neighbor boundaries — the set a map
    or KML export should render together."""
    subject = boundary_for(session, prop)
    result = [subject] if subject else []
    result.extend(neighbor_boundaries(session, prop))
    return result
