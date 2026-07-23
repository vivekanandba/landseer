"""Comparison REST endpoints."""

import os
import tempfile
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.database import get_db
from app.schemas.comparison import (
    ComparisonCreate,
    ComparisonNotes,
    ComparisonRead,
    ComparisonTable,
    FeatureCell,
    InvestmentEntry,
)
from app.services import comparison_service as cmp
from app.services import property_service as props

router = APIRouter(prefix="/api/v1/comparisons", tags=["comparisons"])


def _require(db: Session, name: str):
    comparison = cmp.get_comparison(db, name)
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Comparison {name!r} not found"
        )
    return comparison


def _property(db: Session, property_id: int):
    try:
        return props.get_property(db, property_id)
    except props.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=ComparisonRead, status_code=status.HTTP_201_CREATED)
def create_comparison(payload: ComparisonCreate, db: Session = Depends(get_db)):
    properties = [_property(db, pid) for pid in payload.property_ids]
    try:
        return cmp.create_comparison(db, payload.name, properties, notes=payload.notes)
    except cmp.DuplicateComparison as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{name}", response_model=ComparisonRead)
def get_comparison(name: str, db: Session = Depends(get_db)):
    return _require(db, name)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comparison(name: str, db: Session = Depends(get_db)):
    cmp.delete_comparison(db, _require(db, name))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{name}/properties/{property_id}", response_model=ComparisonRead)
def add_property(name: str, property_id: int, db: Session = Depends(get_db)):
    comparison = _require(db, name)
    cmp.add_property(db, comparison, _property(db, property_id))
    return comparison


@router.patch("/{name}", response_model=ComparisonRead)
def update_notes(name: str, payload: ComparisonNotes, db: Session = Depends(get_db)):
    return cmp.add_notes(db, _require(db, name), payload.notes)


@router.get("/{name}/table", response_model=ComparisonTable)
def table(name: str, db: Session = Depends(get_db)):
    comparison = _require(db, name)
    return cmp.build_table(db, cmp.properties_in(db, comparison))


@router.get("/{name}/features", response_model=Dict[str, Dict[str, FeatureCell]])
def features(name: str, db: Session = Depends(get_db)):
    comparison = _require(db, name)
    return cmp.feature_comparison(db, cmp.properties_in(db, comparison))


@router.get("/{name}/investment", response_model=Dict[str, InvestmentEntry])
def investment(name: str, db: Session = Depends(get_db)):
    comparison = _require(db, name)
    return cmp.investment_comparison(db, cmp.properties_in(db, comparison))


@router.get("/{name}/export.pdf")
def export_pdf(name: str, db: Session = Depends(get_db)):
    comparison = _require(db, name)
    fd, path = tempfile.mkstemp(suffix=".pdf", prefix=f"comparison-{comparison.id}-")
    os.close(fd)
    cmp.export_pdf(db, comparison, path)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{name}.pdf",
        background=BackgroundTask(os.remove, path),
    )
