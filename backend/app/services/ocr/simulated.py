"""Simulated OCR provider — returns injected fields, no engine required."""
import os
from typing import Dict, Optional


class SimulatedOcrProvider:
    """Return canned fields keyed by filename (falling back to ``default``).

    Used by tests and any environment without a real OCR engine configured.
    """

    def __init__(self, by_filename: Optional[Dict[str, dict]] = None, default: Optional[dict] = None):
        self._by_filename = by_filename or {}
        self._default = default or {}

    def extract(self, source: str) -> Dict[str, str]:
        return dict(self._by_filename.get(os.path.basename(source), self._default))
