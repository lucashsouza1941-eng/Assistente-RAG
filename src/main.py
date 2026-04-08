from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.logging import configure_logging, get_logger
from src.core.middleware import CorrelationIDMiddleware, TimingMiddleware
from src.modules.chat.router import router as chat_router
from src.modules.knowledge.router import router as knowledge_router
from src.modules.whatsapp.router import router as whatsapp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger = get_logger(__name__)
    logger.info('app.starting')
    yield
    logger.info('app.stopping')


def create_app() -> FastAPI:
    app = FastAPI(title='Assistente RAG API', lifespan=lifespan)

    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(TimingMiddleware)

    app.include_router(knowledge_router)
    app.include_router(chat_router)
    app.include_router(whatsapp_router)

    return app


app = create_app()
