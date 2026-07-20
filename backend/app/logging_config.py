"""Application logging configuration.

Configures a single stdout handler on the ``landseer`` logger namespace (not the
root logger, so uvicorn's own access/error logging is left untouched). Every
record is stamped with the current request-ID via :class:`_RequestIdFilter`.

``configure_logging`` is idempotent — safe to call at import time and again from
the app lifespan.
"""

import logging
import sys

from app.request_context import get_request_id

_LOGGER_NAME = "landseer"
_configured = False


class _RequestIdFilter(logging.Filter):
    """Attach the active request-ID to each record (``-`` when outside a request)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id() or "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    global _configured
    if _configured:
        return
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RequestIdFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s")
    )
    logger.handlers = [handler]
    # Keep our namespace self-contained; don't double-log through the root logger.
    logger.propagate = False
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the configured ``landseer`` namespace."""
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")
