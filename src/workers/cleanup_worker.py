from src.core.logging import get_logger

log = get_logger(module='workers.cleanup')


async def run_cleanup_worker() -> None:
    log.info('worker.cleanup.started')
