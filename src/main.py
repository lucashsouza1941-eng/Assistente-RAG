from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException
from redis.asyncio import Redis
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware

from src.config import Settings
from src.core.logging import bind_global_context, configure_logging
from src.core.middleware import CorrelationIDMiddleware, TimingMiddleware
from src.dependencies import engine, get_db_session, get_redis
from src.modules.analytics.router import router as analytics_router
from src.modules.chat.router import router as chat_router
from src.modules.knowledge.router import router as knowledge_router
from src.modules.settings.router import router as settings_router
from src.modules.whatsapp.client import MetaAPIClient
from src.modules.whatsapp.router import router as whatsapp_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    configure_logging(settings.log_level)
    bind_global_context(settings.environment, settings.service_name, settings.service_version)

    app.state.redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.meta_api_client = MetaAPIClient(settings)
    try:
        yield
    finally:
        await app.state.redis_client.aclose()
        await app.state.meta_api_client.client.aclose()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title='OdontoBot API', lifespan=lifespan)
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['*'],
    )

    app.include_router(knowledge_router)
    app.include_router(chat_router)
    app.include_router(whatsapp_router)
    app.include_router(analytics_router)
    app.include_router(settings_router)

    @app.get('/health', status_code=200, responses={503: {'description': 'Dependencia indisponivel'}})
    async def health(db=Depends(get_db_session), redis=Depends(get_redis)) -> dict[str, str]:
        db_ok = redis_ok = vector_ok = False
        try:
            await db.execute(text('SELECT 1'))
            db_ok = True
        except Exception:
            db_ok = False
        try:
            redis_ok = bool(await redis.ping())
        except Exception:
            redis_ok = False
        try:
            result = await db.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
            vector_ok = bool(result.scalar())
        except Exception:
            vector_ok = False

        if not (db_ok and redis_ok and vector_ok):
            raise HTTPException(status_code=503, detail='Uma ou mais dependencias estao indisponiveis: db/redis/vector_store')

        return {'status': 'ok', 'db': 'ok', 'redis': 'ok', 'vector_store': 'ok'}

    return app


app = create_app()
