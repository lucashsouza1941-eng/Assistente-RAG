from __future__ import annotations

from arq import func
from arq.connections import RedisSettings

from src.core.logging import get_logger
from src.dependencies import get_settings

log = get_logger(module='workers.indexing')
settings = get_settings()


async def index_document_job(ctx: dict, document_id: str) -> dict:
    """Job de indexacao com retry automatico."""
    from uuid import UUID

    from src.modules.knowledge.indexer import IndexingService

    service = IndexingService()
    result = await service.index_document(UUID(document_id), settings)
    return {"document_id": document_id, "status": result.value}


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
