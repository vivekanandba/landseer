"""Property REST endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.property import (
    NeighborCreate,
    NeighborRead,
    PropertyCreate,
    PropertyRead,
    PropertyUpdate,
    SubdivisionCreate,
    SubdivisionRead,
)
from app.services import property_service as svc

router = APIRouter(prefix="/api/v1/properties", tags=["properties"])


@router.get("", response_model=List[PropertyRead])
def list_properties(
    location: Optional[str] = Query(default=None),
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    db: Session = Depends(get_db),
):
    if location is not None:
        return svc.search_by_location(db, location)
    if min_price is not None and max_price is not None:
        return svc.filter_by_price(db, min_price, max_price)
    return svc.list_properties(db)


@router.post("", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_property(db, **payload.model_dump())
    except svc.DuplicateProperty as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: int, db: Session = Depends(get_db)):
    try:
        return svc.get_property(db, property_id)
    except svc.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{property_id}", response_model=PropertyRead)
def update_property(property_id: int, payload: PropertyUpdate, db: Session = Depends(get_db)):
    try:
        prop = svc.get_property(db, property_id)
    except svc.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        svc.update_status(db, prop, data.pop("status"))
    for field, value in data.items():
        setattr(prop, field, value)
    return prop


@router.post(
    "/{property_id}/subdivisions",
    response_model=SubdivisionRead,
    status_code=status.HTTP_201_CREATED,
)
def add_subdivision(property_id: int, payload: SubdivisionCreate, db: Session = Depends(get_db)):
    try:
        prop = svc.get_property(db, property_id)
    except svc.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return svc.add_subdivision(db, prop, **payload.model_dump())


@router.post(
    "/{property_id}/neighbors",
    response_model=NeighborRead,
    status_code=status.HTTP_201_CREATED,
)
def add_neighbor(property_id: int, payload: NeighborCreate, db: Session = Depends(get_db)):
    try:
        prop = svc.get_property(db, property_id)
    except svc.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return svc.add_neighbor(db, prop, **payload.model_dump())
