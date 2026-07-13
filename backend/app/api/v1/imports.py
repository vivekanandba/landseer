"""OneDrive import REST endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.import_ import (
    BatchImportRequest,
    BatchImportResponse,
    ImportPropertyRequest,
    ImportReport,
)
from app.services import import_service as importer

router = APIRouter(prefix="/api/v1/imports", tags=["imports"])


@router.post("/property", response_model=ImportReport)
def import_property(payload: ImportPropertyRequest, db: Session = Depends(get_db)):
    files = [entry.model_dump(exclude_none=True) for entry in payload.files]
    return importer.import_property(db, payload.name, files).report()


@router.post("/batch", response_model=BatchImportResponse)
def batch_import(payload: BatchImportRequest, db: Session = Depends(get_db)):
    folders = [
        {"name": folder.name, "files": [e.model_dump(exclude_none=True) for e in folder.files]}
        for folder in payload.folders
    ]
    return importer.batch_import(db, folders)
