from __future__ import annotations

from arq import func
from arq.connections import RedisSettings

from time import perf_counter

from src.core.logging import get_logger
from src.core.metrics import KEY_INDEXING_FAILED, incr, log_metric_event
from src.dependencies import get_settings

log = get_logger(module='workers.indexing')
settings = get_settings()


async def index_document_job(ctx: dict, document_id: str) -> dict:
    """Indexação assíncrona: lê bytes do object storage (MinIO) em `IndexingService`, não do FS da API."""
    from uuid import UUID

    from src.modules.knowledge.indexer import IndexingService

    t0 = perf_counter()
    try:
        service = IndexingService()
        result = await service.index_document(UUID(document_id), settings)
        log.info(
            'indexing.job_ok',
            metadata={'document_id': document_id, 'duration_ms': int((perf_counter() - t0) * 1000)},
        )
        return {"document_id": document_id, "status": result.value}
    except Exception as exc:
        r = ctx.get('redis')
        await incr(r, KEY_INDEXING_FAILED)
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
