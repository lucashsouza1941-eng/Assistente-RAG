import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from src.core.logging import bind_correlation_id, get_logger

log = get_logger(module='core.middleware')


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        bind_correlation_id(correlation_id)
        response = await call_next(request)
        response.headers['X-Correlation-ID'] = correlation_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
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


def _normalized_path(path: str) -> str:
    p = path.rstrip('/') or '/'
    return p if p.startswith('/') else f'/{p}'


def _is_rate_limit_excluded(path: str) -> bool:
    p = _normalized_path(path)
    return p in ('/health', '/whatsapp/webhook', '/metrics')


def get_client_ip(request: Request) -> str:
    # Confiar no X-Forwarded-For somente em ambiente atras de proxy confiavel.
    forwarded_for = request.headers.get('X-Forwarded-For')
    app_settings = getattr(request.app.state, 'settings', None)
    trust_proxy = bool(getattr(app_settings, 'trust_proxy', False))
    if forwarded_for and trust_proxy:
        return forwarded_for.split(',')[0].strip()
    client = request.client
    return client.host if client else 'unknown'


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limite global: 100 req/min por IP (Redis). Exclui /health e /whatsapp/webhook."""

    LIMIT = 100
    WINDOW_SEC = 60
    KEY_PREFIX = 'rate_limit'

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if _is_rate_limit_excluded(request.url.path):
            return await call_next(request)

        redis = getattr(request.app.state, 'redis_client', None)
        if redis is None:
            log.warning('rate_limit_skipped', metadata={'reason': 'redis_client_missing'})
            return await call_next(request)

        ip = get_client_ip(request)
        minute_window = int(time.time() // self.WINDOW_SEC)
        key = f'{self.KEY_PREFIX}:{ip}:{minute_window}'

        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, self.WINDOW_SEC * 2)
        except Exception as exc:
            log.warning(
                'rate_limit_redis_error',
                metadata={'error_type': type(exc).__name__, 'error_message': str(exc)[:200]},
            )
            return await call_next(request)

        if count > self.LIMIT:
            retry_after = max(1, self.WINDOW_SEC - int(time.time()) % self.WINDOW_SEC)
            return JSONResponse(
                status_code=429,
                content={'detail': 'Too many requests'},
                headers={'Retry-After': str(retry_after)},
            )

        return await call_next(request)
