from functools import lru_cache
from typing import AsyncGenerator

from arq.connections import ArqRedis, RedisSettings, create_pool
from fastapi import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
engine: AsyncEngine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis_client


async def get_arq_redis() -> AsyncGenerator[ArqRedis, None]:
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        yield pool
    finally:
        await pool.close()
