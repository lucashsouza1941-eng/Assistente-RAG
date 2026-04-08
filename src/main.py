from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.logging import configure_logging, get_logger
from src.core.middleware import CorrelationIDMiddleware, TimingMiddleware
from src.modules.analytics.router import router as analytics_router
from src.modules.chat.router import router as chat_router
from src.modules.knowledge.router import router as knowledge_router
from src.modules.settings.health_router import router as health_router
from src.modules.settings.router import router as settings_router
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
    app.include_router(analytics_router)
    app.include_router(settings_router)
    app.include_router(health_router)
    app.include_router(whatsapp_router)

    return app


app = create_app()
