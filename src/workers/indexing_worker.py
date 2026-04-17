from __future__ import annotations

from time import perf_counter, time

from arq import func
from arq.connections import RedisSettings

from src.core.logging import get_logger
from src.core.metrics import (
    KEY_ARQ_JOB_DURATION_MS_SUM,
    KEY_ARQ_JOBS_COMPLETED,
    KEY_ARQ_JOBS_FAILED,
    KEY_INDEXING_FAILED,
    incr,
    incrby,
    log_metric_event,
)
from src.dependencies import get_settings

log = get_logger(module='workers.indexing')
settings = get_settings()


async def index_document_job(ctx: dict, document_id: str, enqueued_at_ms: int = 0) -> dict:
    """Indexação via MinIO. `enqueued_at_ms`: epoch ms na API para métrica enqueue→sucesso."""
    from uuid import UUID

    from src.modules.knowledge.indexer import IndexingService

    t0 = perf_counter()
    r = ctx.get('redis')
    try:
        service = IndexingService()
        result = await service.index_document(UUID(document_id), settings)
        wall_ms = int((perf_counter() - t0) * 1000)
        log.info(
            'indexing.job_ok',
            metadata={'document_id': document_id, 'duration_ms': wall_ms},
        )
        await incr(r, KEY_ARQ_JOBS_COMPLETED)
        if enqueued_at_ms > 0:
            queue_to_done_ms = max(0, int(time() * 1000) - enqueued_at_ms)
            await incrby(r, KEY_ARQ_JOB_DURATION_MS_SUM, queue_to_done_ms)
        return {"document_id": document_id, "status": result.value}
    except Exception as exc:
        await incr(r, KEY_INDEXING_FAILED)
        await incr(r, KEY_ARQ_JOBS_FAILED)
        log_metric_event(
            'indexing_job_failed',
            document_id=document_id,
            duration_ms=int((perf_counter() - t0) * 1000),
            error=str(exc)[:200],
        )
        raise


async def startup(ctx: dict) -> None:
    log.info("indexing_worker_started")


async def shutdown(ctx: dict) -> None:
    log.info("indexing_worker_stopped")


class WorkerSettings:
    functions = [func(index_document_job, name="index_document")]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_tries = 3
    retry_delay = 60
    job_timeout = 300
    on_startup = startup
    on_shutdown = shutdown
