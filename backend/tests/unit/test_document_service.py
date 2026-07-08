"""Unit tests for document_service: categorization, OCR, verification, history."""
from datetime import date

import pytest

from app.models.document import DocumentType, VerificationStatus
from app.services import document_service as docs
from app.services import property_service as props


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("171-4-Patta.pdf", DocumentType.PATTA),
        ("FMB-171-4A.pdf", DocumentType.FMB),
        ("EC.pdf", DocumentType.EC),
        ("Mother-Deed.pdf", DocumentType.DEED),
        ("171-4D-Integrated-Land-Record.pdf", DocumentType.LAND_RECORD),
        ("Thuthikadu-OneNote.pdf", DocumentType.NOTES),
        ("Cultivated-Crops.png", DocumentType.PHOTO),
        ("Soil-Health-Card.pdf", DocumentType.DOCUMENT),
    ],
)
def test_categorize(filename, expected):
    assert docs.categorize(filename) == expected


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("1392-171-4-Patta.pdf", "171-4"),
        ("FMB-171-4D.pdf", "171-4D"),
        ("171-4-EC-Kaniayambadi.pdf", "171-4"),
        ("Patta-184.pdf", "184"),
        ("119-4.pdf", "119-4"),
    ],
)
def test_extract_survey_number(filename, expected):
    assert docs.extract_survey_number(filename) == expected


def test_land_record_is_not_misread_as_ec():
    # "record" contains the substring "ec"; token matching must not misfire.
    assert docs.categorize("Integrated-Land-Record.pdf") == DocumentType.LAND_RECORD


def test_upload_queues_ocr_for_non_photo(session):
    prop = props.create_property(session, name="P")
    doc = docs.upload_document(session, prop, "Patta.pdf")
    assert doc.doc_type == DocumentType.PATTA
    assert docs.needs_ocr(doc) and doc.ocr_status == "queued"


def test_ec_expiry_after_thirty_years(session):
    prop = props.create_property(session, name="P")
    doc = docs.upload_document(
        session, prop, "EC.pdf", doc_type=DocumentType.EC, issue_date=date(2020, 1, 15)
    )
    assert not docs.is_expired(doc, date(2030, 1, 1))
    assert docs.is_expired(doc, date(2051, 1, 20))


def test_cross_verify_flags_minority(session):
    prop = props.create_property(session, name="P")
    for filename, survey in [("Patta.pdf", "171-4"), ("FMB.pdf", "171-4"), ("EC.pdf", "171-5")]:
        docs.upload_document(session, prop, filename, extracted_survey_number=survey)
    result = docs.cross_verify(session, prop)
    assert result["expected"] == "171-4"
    assert result["mismatches"] == ["EC.pdf"]
    ec = docs.documents_of_type(session, prop, DocumentType.EC)[0]
    assert ec.status == VerificationStatus.ISSUES_FOUND


def test_versioning_tracks_latest(session):
    prop = props.create_property(session, name="P")
    docs.upload_document(session, prop, "Patta-v1.pdf")
    latest = docs.upload_document(session, prop, "Patta-v2.pdf")
    assert latest.version == 2
    assert docs.latest_version(session, prop, DocumentType.PATTA).filename == "Patta-v2.pdf"
