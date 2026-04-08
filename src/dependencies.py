from functools import lru_cache
from typing import AsyncGenerator

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
engine: AsyncEngine = create_async_engine(settings.database_url, echo=settings.debug)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_redis() -> AsyncGenerator[Redis, None]:
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
