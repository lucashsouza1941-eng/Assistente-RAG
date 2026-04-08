import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging import bind_correlation_id, get_logger

logger = get_logger(__name__)


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
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info('http.request', path=request.url.path, method=request.method, elapsed_ms=elapsed_ms)
        response.headers['X-Process-Time-Ms'] = f'{elapsed_ms:.2f}'
        return response

