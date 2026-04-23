from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.health_checks import check_db_redis_vector
from src.core.security import require_api_key
from src.dependencies import get_db_session, get_redis
from src.modules.settings.health_schemas import HealthResponse

router = APIRouter(
    prefix='/internal',
    tags=['health-internal'],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    '/health',
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={401: {'description': 'Unauthorized'}, 403: {'description': 'Forbidden'}, 503: {'description': 'Service unavailable'}},
)
async def health_check(db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis)) -> HealthResponse:
    db_ok, redis_ok, vector_ok = await check_db_redis_vector(db, redis)
    if not (db_ok and redis_ok and vector_ok):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=HealthResponse(
                status='unhealthy',
                db='ok' if db_ok else 'down',
                redis='ok' if redis_ok else 'down',
                vector_store='ok' if vector_ok else 'down',
            ).model_dump(),
        )
    return HealthResponse(status='ok', db='ok', redis='ok', vector_store='ok')
