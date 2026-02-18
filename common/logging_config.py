import logging
import sys
from datetime import datetime
from typing import Any, Dict

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat()

        # Add log level
        log_record["level"] = record.levelname

        # Add logger name
        log_record["logger"] = record.name

        # Add correlation_id if present
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id


def setup_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """Configure structured logging"""

    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(logger)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records"""

    def __init__(self, correlation_id: str):
        super().__init__()
        self.correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self.correlation_id
        return True
