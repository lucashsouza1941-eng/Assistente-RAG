import logging
import sys
import uuid

import structlog

REQUIRED_FIELDS = ('timestamp', 'level', 'correlation_id', 'module', 'action', 'duration_ms', 'metadata')


def _normalize(_logger, _name, event_dict):
    event_dict['action'] = event_dict.pop('event', event_dict.get('action', 'unknown'))
    event_dict.setdefault('duration_ms', 0)
    event_dict.setdefault('metadata', {})
    for field in REQUIRED_FIELDS:
        event_dict.setdefault(field, None)
    return event_dict


def bind_global_context(environment: str, service_name: str, version: str) -> None:
    structlog.contextvars.bind_contextvars(
        environment=environment,
        service_name=service_name,
        version=version,
    )


def bind_correlation_id(correlation_id: str | None = None) -> str:
    cid = correlation_id or str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(correlation_id=cid)
    return cid


def configure_logging(level: str = 'INFO') -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            _normalize,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), stream=sys.stdout)


def get_logger(module: str):
    return structlog.get_logger(module=module)


def sanitize_message(value: str) -> str:
    if len(value) <= 50:
        return value
    return f'{value[:50]}...'
