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


def _rate_limit_scope(path: str) -> str | None:
    p = _normalized_path(path)
    if p == '/health' or p == '/internal/health':
        return None
    if p == '/whatsapp/webhook':
        return 'webhook'
    if p.startswith('/settings') or p.startswith('/metrics') or p.startswith('/whatsapp/admin'):
        return 'admin'
    return 'global'


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
    """Rate limit por escopo (global/admin/webhook) com contadores isolados."""

    WINDOW_SEC = 60
    KEY_PREFIX = 'rate_limit'

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        scope = _rate_limit_scope(request.url.path)
        if scope is None:
            return await call_next(request)

        redis = getattr(request.app.state, 'redis_client', None)
        if redis is None:
            # Fail-open: sem Redis no app.state nao ha contadores de rate limit — a requisicao segue.
            # Trade-off: disponibilidade acima de protecao ate o cliente Redis voltar (ver RUNBOOK).
            client = request.client
            ip = client.host if client else 'unknown'
            log.critical(
                'rate_limit_skipped',
                reason='redis_client_missing',
                ip=ip,
                path=request.url.path,
            )
            return await call_next(request)

        ip = get_client_ip(request)
        minute_window = int(time.time() // self.WINDOW_SEC)
        key = f'{self.KEY_PREFIX}:{scope}:{ip}:{minute_window}'
        app_settings = getattr(request.app.state, 'settings', None)
        global_limit = int(getattr(app_settings, 'rate_limit_global_per_minute', 100))
        admin_limit = int(getattr(app_settings, 'rate_limit_admin_per_minute', 30))
        webhook_limit = int(getattr(app_settings, 'rate_limit_webhook_per_minute', 120))
        if scope == 'admin':
            limit = admin_limit
        elif scope == 'webhook':
            limit = webhook_limit
        else:
            limit = global_limit

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

        if count > limit:
            retry_after = max(1, self.WINDOW_SEC - int(time.time()) % self.WINDOW_SEC)
            return JSONResponse(
                status_code=429,
                content={'detail': f'Too many requests ({scope})'},
                headers={'Retry-After': str(retry_after)},
            )

        return await call_next(request)
