"""Pydantic schemas for documents and OCR."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

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
    # Cap the payload so a pathological blob can't tie up parsing; real OCR text
    # for a land document is far under this.
    text: str = Field(max_length=100_000)


class OcrFields(BaseModel):
    survey_number: Optional[str] = None
    owner_name: Optional[str] = None
    extent: Optional[str] = None
    village: Optional[str] = None
