import logging
import sys
import uuid

import structlog


def bind_correlation_id(correlation_id: str | None = None) -> str:
    value = correlation_id or str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(correlation_id=value)
    return value


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt='iso')
    processors = [structlog.contextvars.merge_contextvars, structlog.stdlib.add_log_level, timestamper, structlog.processors.JSONRenderer()]
    structlog.configure(processors=processors, logger_factory=structlog.stdlib.LoggerFactory(), wrapper_class=structlog.stdlib.BoundLogger, cache_logger_on_first_use=True)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def get_logger(name: str):
    return structlog.get_logger(name)

