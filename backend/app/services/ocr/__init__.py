"""OCR providers and field parsing.

The default provider is simulated so the test path never imports a real OCR
engine. Real extraction (Tesseract / cloud) lives behind the same ``extract``
interface and imports its heavy dependencies lazily.
"""
from app.services.ocr.parser import extract_fields
from app.services.ocr.provider import OcrProvider
from app.services.ocr.simulated import SimulatedOcrProvider

__all__ = ["OcrProvider", "SimulatedOcrProvider", "extract_fields"]
