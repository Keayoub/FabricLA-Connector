"""
Structured logging and telemetry for ingestion events.
"""
import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Generator

_logger = logging.getLogger("fabricla_connector.telemetry")


def log_event(event_type: str, **kwargs: Any) -> None:
    """Emit a structured JSON log line for a telemetry event."""
    payload = {"event": event_type, **kwargs}
    _logger.info(json.dumps(payload, default=str))


@contextmanager
def timed_event(event_type: str, **kwargs: Any) -> Generator[None, None, None]:
    """Context manager that logs an event with elapsed_ms on exit."""
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        log_event(event_type, elapsed_ms=elapsed_ms, **kwargs)
