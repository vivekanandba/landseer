"""Property REST endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
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
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if location is not None:
        return svc.search_by_location(db, location, limit=limit, offset=offset)
    if min_price is not None and max_price is not None:
        return svc.filter_by_price(db, min_price, max_price, limit=limit, offset=offset)
    return svc.list_properties(db, limit=limit, offset=offset)


@router.post("", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_property(db, **payload.model_dump())
    except svc.DuplicateProperty as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: int, db: Session = Depends(get_db)):
    try:
        return svc.get_property(db, property_id)
    except svc.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{property_id}", response_model=PropertyRead)
def update_property(property_id: int, payload: PropertyUpdate, db: Session = Depends(get_db)):
    try:
        prop = svc.get_property(db, property_id)
    except svc.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    try:
        return svc.update_property(db, prop, payload.model_dump(exclude_unset=True))
    except svc.DuplicateProperty as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: int, db: Session = Depends(get_db)):
    try:
        prop = svc.get_property(db, property_id)
    except svc.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    svc.delete_property(db, prop)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{property_id}/subdivisions",
    response_model=SubdivisionRead,
    status_code=status.HTTP_201_CREATED,
)
def add_subdivision(property_id: int, payload: SubdivisionCreate, db: Session = Depends(get_db)):
    try:
        prop = svc.get_property(db, property_id)
    except svc.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return svc.add_neighbor(db, prop, **payload.model_dump())
