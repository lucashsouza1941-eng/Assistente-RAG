import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import bind_correlation_id, get_logger

log = get_logger(module='core.middleware')


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        bind_correlation_id(correlation_id)
        response = await call_next(request)
        response.headers['X-Correlation-ID'] = correlation_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        log.info(
            'http.request',
            action='http.request',
            duration_ms=duration_ms,
            metadata={'path': request.url.path, 'status_code': response.status_code, 'method': request.method},
        )
        return response
