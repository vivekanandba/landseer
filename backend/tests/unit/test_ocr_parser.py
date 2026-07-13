"""Unit tests for the OCR field parser (engine-independent)."""
from app.services.ocr import extract_fields

PATTA_TEXT = """
Government of Tamil Nadu
Patta No: 1234
Survey Number: 171-4
Owner Name: Ramesh Kumar
Extent: 12500 sqft
Village: Thuthikadu
"""


def test_extract_labelled_fields():
    fields = extract_fields(PATTA_TEXT)
    assert fields["survey_number"] == "171-4"
    assert fields["owner_name"] == "Ramesh Kumar"
    assert fields["extent"] == "12500 sqft"
    assert fields["village"] == "Thuthikadu"


def test_survey_number_falls_back_to_pattern():
    # No explicit "Survey Number:" label -> reuse the filename-style extractor.
    fields = extract_fields("Document for plot 171-4D in Kaniyambadi")
    assert fields["survey_number"] == "171-4D"


def test_missing_fields_are_omitted():
    fields = extract_fields("no useful labels here")
    assert "owner_name" not in fields and "village" not in fields
