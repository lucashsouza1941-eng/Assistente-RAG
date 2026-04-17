from __future__ import annotations

from redis.asyncio import Redis

from src.core.logging import get_logger

log = get_logger(module='core.metrics')

PREFIX = 'metrics:v1:'
KEY_INDEXING_FAILED = PREFIX + 'indexing_job_failed'
KEY_WHATSAPP_HANDLER_FAILED = PREFIX + 'whatsapp_handler_failed'
KEY_WEBHOOK_SIGNATURE_FAIL = PREFIX + 'webhook_signature_failed'

KEY_ARQ_JOBS_ENQUEUED = PREFIX + 'arq_jobs_enqueued_total'
KEY_ARQ_JOBS_COMPLETED = PREFIX + 'arq_jobs_completed_total'
KEY_ARQ_JOBS_FAILED = PREFIX + 'arq_jobs_failed_total'
# Soma dos tempos (ms) enqueue → conclusão com sucesso; média = soma / completed
KEY_ARQ_JOB_DURATION_MS_SUM = PREFIX + 'arq_job_duration_ms_sum'


async def incr(redis: Redis | None, key: str, amount: int = 1) -> None:
    if redis is None:
        return
    try:
        await redis.incrby(key, amount)
    except Exception:
        pass


async def incrby(redis: Redis | None, key: str, amount: int) -> None:
    if redis is None or amount <= 0:
        return
    try:
        await redis.incrby(key, amount)
    except Exception:
        pass


def log_metric_event(metric: str, **metadata: object) -> None:
    log.info('metrics.event', metadata={'metric': metric, **metadata})
