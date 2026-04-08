import logging
import os
import sys
import uuid

import structlog


REQUIRED_FIELDS = (
    'timestamp',
    'level',
    'correlation_id',
    'module',
    'action',
    'duration_ms',
    'metadata',
)


def _ensure_required_fields(_logger, _method_name, event_dict):
    event_dict['action'] = event_dict.pop('event', event_dict.get('action', 'unknown'))
    event_dict.setdefault('duration_ms', 0)
    event_dict.setdefault('metadata', {})
    for key in REQUIRED_FIELDS:
        event_dict.setdefault(key, None)
    return event_dict


def bind_global_context(environment: str, service_name: str, version: str) -> None:
    structlog.contextvars.bind_contextvars(
        environment=environment,
        service_name=service_name,
        version=version,
    )


def bind_correlation_id(correlation_id: str | None = None) -> str:
    value = correlation_id or str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(correlation_id=value)
    return value


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt='iso')
    processors = [
        structlog.contextvars.merge_contextvars,
        timestamper,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        _ensure_required_fields,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bind_global_context(
        environment=os.getenv('ENVIRONMENT', 'development'),
        service_name=os.getenv('SERVICE_NAME', 'assistente-rag-api'),
        version=os.getenv('SERVICE_VERSION', '0.1.0'),
    )


def get_logger(module: str):
    return structlog.get_logger(module=module)


def sanitize_text_preview(value: str, size: int = 50) -> str:
    if len(value) <= size:
        return value
    return f'{value[:size]}...'
