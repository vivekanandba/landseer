"""Pydantic schemas for documents and OCR."""
from datetime import date
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentType, VerificationStatus


class DocumentUpload(BaseModel):
    filename: str
    doc_type: Optional[str] = None
    issue_date: Optional[date] = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: Optional[int] = None
    subdivision_id: Optional[int] = None
    neighbor_id: Optional[int] = None
    filename: str
    doc_type: DocumentType
    status: VerificationStatus
    ocr_status: str
    version: int
    extracted_survey_number: Optional[str] = None
    extracted_owner_name: Optional[str] = None
    extracted_extent: Optional[str] = None
    extracted_village: Optional[str] = None


class OcrParseRequest(BaseModel):
    text: str


class OcrFields(BaseModel):
    survey_number: Optional[str] = None
    owner_name: Optional[str] = None
    extent: Optional[str] = None
    village: Optional[str] = None
