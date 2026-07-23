"""Broker REST endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.broker import (
    BrokerCreate,
    BrokerPerformance,
    BrokerPropertyLink,
    BrokerPropertyLinkResult,
    BrokerRead,
)
from app.services import broker_service as brokers
from app.services import property_service as props

router = APIRouter(prefix="/api/v1/brokers", tags=["brokers"])


def _broker(db: Session, broker_id: int):
    try:
        return brokers.get_broker(db, broker_id)
    except brokers.BrokerNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=BrokerRead, status_code=status.HTTP_201_CREATED)
def create_broker(payload: BrokerCreate, db: Session = Depends(get_db)):
    return brokers.create_broker(db, **payload.model_dump())


@router.get("", response_model=List[BrokerRead])
def list_brokers(
    area: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if area:
        return brokers.search_by_area(db, area, limit=limit, offset=offset)
    return brokers.list_brokers(db, limit=limit, offset=offset)


@router.get("/{broker_id}", response_model=BrokerRead)
def get_broker(broker_id: int, db: Session = Depends(get_db)):
    return _broker(db, broker_id)


@router.delete("/{broker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_broker(broker_id: int, db: Session = Depends(get_db)):
    brokers.delete_broker(db, _broker(db, broker_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{broker_id}/properties/{property_id}",
    response_model=BrokerPropertyLinkResult,
    status_code=status.HTTP_201_CREATED,
)
def link_property(
    broker_id: int, property_id: int, payload: BrokerPropertyLink, db: Session = Depends(get_db)
):
    broker = _broker(db, broker_id)
    try:
        prop = props.get_property(db, property_id)
    except props.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    brokers.link_to_property(db, broker, prop, **payload.model_dump())
    return {"broker_id": broker.id, "property_id": prop.id}


@router.get("/{broker_id}/performance", response_model=BrokerPerformance)
def performance(broker_id: int, db: Session = Depends(get_db)):
    return brokers.performance(db, _broker(db, broker_id))
