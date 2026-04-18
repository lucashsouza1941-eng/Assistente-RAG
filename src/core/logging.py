import logging
import sys
import uuid
from collections.abc import MutableMapping
from typing import Any, cast

import structlog

REQUIRED_FIELDS = ('timestamp', 'level', 'correlation_id', 'module', 'action', 'duration_ms', 'metadata')

_SENSITIVE_NAME_SUBSTRINGS = ('api_key', 'token', 'secret', 'password', 'authorization', 'x-api-key')
_REDACTED = '***REDACTED***'


def _field_name_is_sensitive(name: str) -> bool:
    lower = str(name).lower()
    return any(sub in lower for sub in _SENSITIVE_NAME_SUBSTRINGS)


def _sanitize_nested(obj: object) -> object:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if _field_name_is_sensitive(str(k)):
                out[k] = _REDACTED
            elif isinstance(v, dict):
                out[k] = _sanitize_nested(v)
            elif isinstance(v, list):
                out[k] = [_sanitize_nested(i) for i in v]
            else:
                out[k] = v
        return out
    if isinstance(obj, list):
        return [_sanitize_nested(i) for i in obj]
    return obj


def sanitize_sensitive_fields(
    _logger: Any, _name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    out = _sanitize_nested(event_dict)
    if isinstance(out, MutableMapping):
        return out
    return event_dict


def _normalize(
    _logger: Any, _name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
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
            sanitize_sensitive_fields,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), stream=sys.stdout)


def get_logger(module: str) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(module=module))


def sanitize_message(value: str) -> str:
    if len(value) <= 50:
        return value
    return f'{value[:50]}...'
