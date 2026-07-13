"""OCR provider interface."""
from typing import Dict

try:  # Protocol is stdlib on 3.8+
    from typing import Protocol
except ImportError:  # pragma: no cover
    from typing_extensions import Protocol


class OcrProvider(Protocol):
    """Extract fields (survey_number/owner_name/extent/village/text) from a
    document identified by ``source`` (a filename or path)."""

    def extract(self, source: str) -> Dict[str, str]:
        ...
