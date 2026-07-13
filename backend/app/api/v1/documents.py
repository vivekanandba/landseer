"""Document + OCR endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import DocumentType
from app.schemas.document import DocumentRead, DocumentUpload, OcrFields, OcrParseRequest
from app.services import document_service as docs
from app.services import property_service as props
from app.services.ocr import extract_fields

router = APIRouter(prefix="/api/v1", tags=["documents"])


def _property(db: Session, property_id: int):
    try:
        return props.get_property(db, property_id)
    except props.PropertyNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/properties/{property_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(property_id: int, payload: DocumentUpload, db: Session = Depends(get_db)):
    prop = _property(db, property_id)
    doc_type = None
    if payload.doc_type:
        try:
            doc_type = DocumentType(payload.doc_type)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown doc_type {payload.doc_type!r}",
            ) from exc
    return docs.upload_document(
        db, prop, payload.filename, doc_type=doc_type, issue_date=payload.issue_date
    )


@router.get("/properties/{property_id}/documents", response_model=List[DocumentRead])
def list_documents(property_id: int, db: Session = Depends(get_db)):
    return docs.documents_for_property(db, _property(db, property_id))


@router.post("/ocr/parse", response_model=OcrFields)
def parse_ocr(payload: OcrParseRequest):
    """Parse survey number / owner / extent / village out of OCR text."""
    fields = extract_fields(payload.text)
    fields.pop("text", None)
    return fields
