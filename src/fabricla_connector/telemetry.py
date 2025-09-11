"""
Structured logging and telemetry for ingestion events.
"""
import logging

from typing import Any

def log_event(event_type: str, **kwargs: Any) -> None:
    logging.info(f"{event_type}: {kwargs}")
