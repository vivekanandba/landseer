"""Document model: files attached to a property, subdivision or neighbor."""
from __future__ import annotations

import enum
from datetime import date
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class DocumentType(str, enum.Enum):
    PATTA = "patta"
    FMB = "fmb"
    EC = "ec"
    DEED = "deed"
    LAND_RECORD = "land_record"
    NOTES = "notes"
    PHOTO = "photo"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class VerificationStatus(str, enum.Enum):
    MISSING = "missing"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    ISSUES_FOUND = "issues_found"
    EXPIRED = "expired"


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # A document is attached to exactly one of these; parent property is always set.
    property_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    subdivision_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subdivisions.id", ondelete="CASCADE"), index=True
    )
    neighbor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("neighbors.id", ondelete="CASCADE"), index=True
    )

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, values_callable=lambda e: [m.value for m in e]),
        default=DocumentType.UNKNOWN,
        nullable=False,
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, values_callable=lambda e: [m.value for m in e]),
        default=VerificationStatus.UPLOADED,
        nullable=False,
    )

    issue_date: Mapped[Optional[date]] = mapped_column(Date)

    # Fields populated by OCR extraction.
    extracted_survey_number: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    extracted_owner_name: Mapped[Optional[str]] = mapped_column(String(255))
    extracted_extent: Mapped[Optional[str]] = mapped_column(String(64))
    extracted_village: Mapped[Optional[str]] = mapped_column(String(128))
    ocr_text: Mapped[Optional[str]] = mapped_column(Text)
    ocr_status: Mapped[str] = mapped_column(String(32), default="pending")

    version: Mapped[int] = mapped_column(Integer, default=1)
