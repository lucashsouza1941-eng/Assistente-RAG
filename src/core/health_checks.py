"""Verificacoes compartilhadas entre GET /health (publico) e GET /internal/health (API key)."""

from __future__ import annotations

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_db_redis_vector(db: AsyncSession, redis: Redis) -> tuple[bool, bool, bool]:
    db_ok = redis_ok = vector_ok = False
    try:
        await db.execute(text('SELECT 1'))
        db_ok = True
    except Exception:
        pass
    try:
        redis_ok = bool(await redis.ping())
    except Exception:
        pass
    try:
        result = await db.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
        vector_ok = bool(result.scalar())
    except Exception:
        pass
    return db_ok, redis_ok, vector_ok
