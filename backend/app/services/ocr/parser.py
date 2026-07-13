"""Parse key fields out of OCR text from a Tamil Nadu Patta / land document.

Pure and engine-independent so it can be unit-tested in isolation. Reuses the
filename survey-number extractor as a fallback when the text has no explicit
"Survey Number:" label.
"""

import re
from typing import Dict, Optional

# Survey-number shapes, matched against the full OCR text (not a filename).
_SURVEY_RE = re.compile(r"\b\d{1,3}-\d+[A-Za-z]?\d*")
_SURVEY_FALLBACK_RE = re.compile(r"\b\d{1,3}[A-Za-z]?\b")


def _labelled(text: str, label: str) -> Optional[str]:
    match = re.search(label + r"\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _survey_from_text(text: str) -> Optional[str]:
    match = _SURVEY_RE.search(text) or _SURVEY_FALLBACK_RE.search(text)
    return match.group(0).upper() if match else None


def extract_fields(text: str) -> Dict[str, str]:
    """Extract survey_number/owner_name/extent/village (+ raw text) from OCR text."""
    fields: Dict[str, str] = {}

    survey_match = re.search(
        r"survey\s*(?:number|no\.?)?\s*[:\-]\s*([0-9A-Za-z\-]+)", text, re.IGNORECASE
    )
    survey = survey_match.group(1) if survey_match else _survey_from_text(text)
    if survey:
        fields["survey_number"] = survey

    owner = _labelled(text, r"owner(?:\s*name)?")
    if owner:
        fields["owner_name"] = owner
    extent = _labelled(text, r"extent")
    if extent:
        fields["extent"] = extent
    village = _labelled(text, r"village")
    if village:
        fields["village"] = village

    fields["text"] = text
    return fields
