from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.metrics import (
    KEY_INDEXING_FAILED,
    KEY_WEBHOOK_SIGNATURE_FAIL,
    KEY_WHATSAPP_HANDLER_FAILED,
)
from src.core.security import require_api_key
from src.dependencies import get_redis
from redis.asyncio import Redis

router = APIRouter(prefix='/metrics', tags=['metrics'], dependencies=[Depends(require_api_key)])


@router.get('')
async def metrics_snapshot(redis: Redis = Depends(get_redis)) -> dict[str, int | str]:
    keys = {
        'indexing_job_failed': KEY_INDEXING_FAILED,
        'whatsapp_handler_failed': KEY_WHATSAPP_HANDLER_FAILED,
        'webhook_signature_failed': KEY_WEBHOOK_SIGNATURE_FAIL,
    }
    out: dict[str, int | str] = {}
    for name, key in keys.items():
        try:
            raw = await redis.get(key)
            out[name] = int(raw) if raw is not None else 0
        except Exception:
            out[name] = -1
    return out
