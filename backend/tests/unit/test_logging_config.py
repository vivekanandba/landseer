"""Unit tests for logging configuration and the request-ID filter."""

import logging

from app.logging_config import _RequestIdFilter, configure_logging, get_logger
from app.request_context import get_request_id, set_request_id


def test_configure_logging_is_idempotent():
    configure_logging()
    configure_logging()
    logger = logging.getLogger("landseer")
    # Exactly one handler even after repeated configuration.
    assert len(logger.handlers) == 1
    assert logger.propagate is False


def test_get_logger_is_namespaced_child():
    assert get_logger("widget").name == "landseer.widget"


def test_request_id_filter_stamps_current_request_id():
    set_request_id("abc123")
    record = logging.LogRecord("landseer.test", logging.INFO, __file__, 1, "hi", None, None)
    assert _RequestIdFilter().filter(record) is True
    assert record.request_id == "abc123"


def test_request_id_filter_defaults_when_unset():
    set_request_id("")
    record = logging.LogRecord("landseer.test", logging.INFO, __file__, 1, "hi", None, None)
    _RequestIdFilter().filter(record)
    assert record.request_id == "-"
    # sanity: context var is empty
    assert get_request_id() == ""
