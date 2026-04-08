from src.core.logging import get_logger

log = get_logger(module='workers.indexing')


async def run_indexing_worker() -> None:
    log.info('worker.indexing.started')
