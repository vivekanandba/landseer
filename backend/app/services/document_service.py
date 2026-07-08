"""Document domain operations: categorization, OCR, verification and history.

Like the other services this layer is free of HTTP concerns so it can be driven
from BDD steps, unit tests and the API alike. "OCR" here is simulated: callers
supply the extracted fields (real OCR would run out of process).
"""
import re
from collections import Counter
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentType, VerificationStatus
from app.models.property import Neighbor, Property, Subdivision

IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"}

# Standard checklist for a clear-title purchase in Tamil Nadu.
REQUIRED_TYPES = (DocumentType.PATTA, DocumentType.FMB, DocumentType.EC)

# An Encumbrance Certificate is treated as valid for 30 years from issue.
EC_VALIDITY_YEARS = 30


# ---------------------------------------------------------------------------
# Filename intelligence
# ---------------------------------------------------------------------------
def _tokens(text: str) -> set:
    return set(t for t in re.split(r"[^a-z0-9]+", text.lower()) if t)


def categorize(filename: str) -> DocumentType:
    """Infer a document type from its filename."""
    stem, _, ext = filename.rpartition(".")
    stem = stem or filename
    ext = ext.lower()
    name = stem.lower()
    tokens = _tokens(stem)

    if ext in IMAGE_EXTS:
        return DocumentType.PHOTO
    if "onenote" in tokens or "notes" in tokens:
        return DocumentType.NOTES
    if "patta" in tokens:
        return DocumentType.PATTA
    if "fmb" in tokens:
        return DocumentType.FMB
    if "deed" in tokens:
        return DocumentType.DEED
    if ("record" in name or "records" in name) and (
        "land" in tokens or "integrated" in tokens
    ):
        return DocumentType.LAND_RECORD
    if "ec" in tokens:
        return DocumentType.EC
    return DocumentType.DOCUMENT


def extract_survey_number(filename: str) -> Optional[str]:
    """Pull a Vellore-style survey number (e.g. ``171-4``, ``171-4D``) from a name."""
    stem = filename.rsplit(".", 1)[0]
    match = re.search(r"\b\d{1,3}-\d+[A-Za-z]?\d*", stem)
    if match:
        return match.group(0).upper()
    match = re.search(r"\b\d{1,3}[A-Za-z]?\b", stem)
    if match:
        return match.group(0).upper()
    return None


# ---------------------------------------------------------------------------
# Upload & OCR
# ---------------------------------------------------------------------------
def needs_ocr(doc: Document) -> bool:
    """Photos are indexed as-is; everything else is queued for text extraction."""
    return doc.doc_type != DocumentType.PHOTO


def upload_document(
    session: Session,
    prop: Property,
    filename: str,
    *,
    subdivision: Optional[Subdivision] = None,
    neighbor: Optional[Neighbor] = None,
    doc_type: Optional[DocumentType] = None,
    issue_date: Optional[date] = None,
    extracted_survey_number: Optional[str] = None,
) -> Document:
    resolved_type = doc_type or categorize(filename)
    survey = extracted_survey_number or extract_survey_number(filename)

    version = 1 + _count_of_type(session, prop, resolved_type)
    doc = Document(
        property_id=prop.id,
        subdivision_id=subdivision.id if subdivision else None,
        neighbor_id=neighbor.id if neighbor else None,
        filename=filename,
        doc_type=resolved_type,
        extracted_survey_number=survey,
        version=version,
        status=VerificationStatus.UPLOADED,
    )
    if issue_date is not None:
        doc.issue_date = issue_date
    doc.ocr_status = "queued" if needs_ocr(doc) else "not_required"
    session.add(doc)
    session.flush()
    return doc


def simulate_ocr(session: Session, doc: Document, fields: Dict[str, str]) -> Document:
    """Apply extracted OCR fields to a document and mark OCR complete."""
    if "survey_number" in fields:
        doc.extracted_survey_number = fields["survey_number"]
    if "owner_name" in fields:
        doc.extracted_owner_name = fields["owner_name"]
    if "extent" in fields:
        doc.extracted_extent = fields["extent"]
    if "village" in fields:
        doc.extracted_village = fields["village"]
    doc.ocr_text = " ".join(str(v) for v in fields.values())
    doc.ocr_status = "complete"
    session.flush()
    return doc


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
def documents_for_property(session: Session, prop: Property) -> List[Document]:
    return list(
        session.scalars(
            select(Document)
            .where(Document.property_id == prop.id)
            .order_by(Document.version)
        )
    )


def documents_of_type(
    session: Session, prop: Property, doc_type: DocumentType
) -> List[Document]:
    return [d for d in documents_for_property(session, prop) if d.doc_type == doc_type]


def documents_for_subdivision(session: Session, subdivision: Subdivision) -> List[Document]:
    return list(
        session.scalars(
            select(Document).where(Document.subdivision_id == subdivision.id)
        )
    )


def documents_for_neighbor(session: Session, neighbor: Neighbor) -> List[Document]:
    return list(
        session.scalars(select(Document).where(Document.neighbor_id == neighbor.id))
    )


def _count_of_type(session: Session, prop: Property, doc_type: DocumentType) -> int:
    return len(documents_of_type(session, prop, doc_type))


def latest_version(
    session: Session, prop: Property, doc_type: DocumentType
) -> Optional[Document]:
    docs = documents_of_type(session, prop, doc_type)
    return max(docs, key=lambda d: d.version) if docs else None


def search_by_ocr(session: Session, query: str) -> List[Document]:
    needle = query.lower()
    return [
        d
        for d in session.scalars(select(Document))
        if d.ocr_text and needle in d.ocr_text.lower()
    ]


def highlight(text: str, query: str) -> str:
    """Wrap matches of ``query`` in ``[[...]]`` markers for result display."""
    return re.sub(f"({re.escape(query)})", r"[[\1]]", text, flags=re.IGNORECASE)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def checklist(
    session: Session,
    prop: Property,
    required=REQUIRED_TYPES,
    as_of: Optional[date] = None,
) -> Dict[str, str]:
    """Return the verification status for each required document type.

    Expiry is evaluated against ``as_of`` (default today) so a document whose
    validity has lapsed reports ``expired`` even if its stored status was not
    updated.
    """
    as_of = as_of or date.today()
    result = {}
    for doc_type in required:
        found = documents_of_type(session, prop, doc_type)
        if not found:
            result[doc_type.value] = VerificationStatus.MISSING.value
        elif any(d.status == VerificationStatus.ISSUES_FOUND for d in found):
            result[doc_type.value] = VerificationStatus.ISSUES_FOUND.value
        elif any(d.status == VerificationStatus.EXPIRED or is_expired(d, as_of) for d in found):
            result[doc_type.value] = VerificationStatus.EXPIRED.value
        else:
            result[doc_type.value] = VerificationStatus.VERIFIED.value
    return result


def expiry_date(doc: Document) -> Optional[date]:
    if doc.doc_type != DocumentType.EC or doc.issue_date is None:
        return None
    issued = doc.issue_date
    try:
        return issued.replace(year=issued.year + EC_VALIDITY_YEARS)
    except ValueError:  # Feb 29 -> Feb 28
        return issued.replace(year=issued.year + EC_VALIDITY_YEARS, day=28)


def is_expired(doc: Document, as_of: date) -> bool:
    expires = expiry_date(doc)
    return expires is not None and as_of > expires


def cross_verify(session: Session, prop: Property) -> dict:
    """Compare survey numbers across a property's documents.

    The majority survey number is taken as authoritative; any document that
    disagrees is flagged ``issues_found`` and reported as a mismatch.
    """
    docs = [d for d in documents_for_property(session, prop) if d.extracted_survey_number]
    counts = Counter(d.extracted_survey_number for d in docs)
    if not counts:
        return {"expected": None, "mismatches": []}
    expected = counts.most_common(1)[0][0]
    mismatches = []
    for doc in docs:
        if doc.extracted_survey_number != expected:
            doc.status = VerificationStatus.ISSUES_FOUND
            mismatches.append(doc.filename)
    session.flush()
    return {"expected": expected, "mismatches": mismatches}
