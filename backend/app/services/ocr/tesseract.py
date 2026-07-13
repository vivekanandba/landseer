"""Real OCR via Tesseract. Heavy dependencies are imported lazily so importing
this module never fails in environments (like the test suite) without them."""

import os
from typing import Dict

from app.services.ocr.parser import extract_fields


class TesseractOcrProvider:
    """Extract text from a PDF/image on disk with Tesseract, then parse fields.

    Requires ``pytesseract``, ``pdf2image`` and the Tesseract binary. These are
    imported inside ``extract`` so absence only fails when actually used.
    """

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir

    def extract(self, source: str) -> Dict[str, str]:  # pragma: no cover - needs engine
        import pytesseract  # noqa: WPS433 (lazy import by design)
        from PIL import Image

        path = source if os.path.isabs(source) else os.path.join(self.base_dir, source)
        if path.lower().endswith(".pdf"):
            from pdf2image import convert_from_path

            pages = convert_from_path(path)
            text = "\n".join(pytesseract.image_to_string(p) for p in pages)
        else:
            text = pytesseract.image_to_string(Image.open(path))

        fields = extract_fields(text)
        fields["text"] = text
        return fields
