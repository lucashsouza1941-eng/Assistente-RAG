from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger = get_logger(__name__)
    logger.info('app.starting')
    yield
    logger.info('app.stopping')


def create_app() -> FastAPI:
    app = FastAPI(title='Assistente RAG API', lifespan=lifespan)
    return app


app = create_app()

