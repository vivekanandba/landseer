"""Survey boundary + map export endpoints."""

import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.survey import BoundaryCreate, BoundaryRead
from app.services import kml_service, survey_service
from app.services import property_service as props

router = APIRouter(prefix="/api/v1/properties", tags=["surveys"])


def _property(db: Session, property_id: int):
    try:
        return props.get_property(db, property_id)
    except props.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{property_id}/boundary",
    response_model=BoundaryRead,
    status_code=status.HTTP_201_CREATED,
)
def add_boundary(property_id: int, payload: BoundaryCreate, db: Session = Depends(get_db)):
    prop = _property(db, property_id)
    neighbor = None
    if payload.neighbor_survey_number:
        neighbor = next(
            (n for n in prop.neighbors if n.survey_number == payload.neighbor_survey_number),
            None,
        )
        if neighbor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Neighbor {payload.neighbor_survey_number!r} not found",
            )
    try:
        return survey_service.add_boundary(
            db,
            prop,
            [(v.lat, v.lng) for v in payload.vertices],
            label=payload.label,
            neighbor=neighbor,
        )
    except survey_service.InvalidBoundary as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/{property_id}/map.geojson")
def map_geojson(property_id: int, db: Session = Depends(get_db)):
    prop = _property(db, property_id)
    return kml_service.geojson(survey_service.boundaries_for_map(db, prop))


@router.get("/{property_id}/map.kml")
def map_kml(property_id: int, db: Session = Depends(get_db)):
    prop = _property(db, property_id)
    boundaries = survey_service.boundaries_for_map(db, prop)
    # Render to a temp file so a GET has no persistent side effect and works on a
    # read-only application filesystem.
    fd, path = tempfile.mkstemp(suffix=".kml", prefix=f"property-{property_id}-")
    os.close(fd)
    kml_service.generate_kml(boundaries, path)
    return FileResponse(
        path,
        media_type=kml_service.KML_MEDIA_TYPE,
        filename=f"property-{property_id}.kml",
    )
