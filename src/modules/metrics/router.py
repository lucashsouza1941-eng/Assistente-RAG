from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from redis.asyncio import Redis

from src.core.metrics import (
    KEY_ARQ_JOB_DURATION_MS_SUM,
    KEY_ARQ_JOBS_COMPLETED,
    KEY_ARQ_JOBS_ENQUEUED,
    KEY_ARQ_JOBS_FAILED,
    KEY_INDEXING_FAILED,
    KEY_WEBHOOK_SIGNATURE_FAIL,
    KEY_WHATSAPP_HANDLER_FAILED,
)
from src.core.security import require_api_key
from src.dependencies import get_redis

router = APIRouter(prefix='/metrics', tags=['metrics'], dependencies=[Depends(require_api_key)])


class MetricsSnapshotResponse(BaseModel):
    """Valores agregados em Redis (`metrics:v1:*`); atualizados pela API, workers e validadores."""

    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {
                    'indexing_job_failed': 0,
                    'whatsapp_handler_failed': 0,
                    'webhook_signature_failed': 0,
                    'arq_jobs_enqueued_total': 12,
                    'arq_jobs_completed_total': 10,
                    'arq_jobs_failed_total': 1,
                    'arq_job_duration_seconds': 2.5,
                }
            ]
        }
    )

    indexing_job_failed: int = Field(
        description='Falhas na execução do job de indexação (exceção antes de concluir).',
    )
    whatsapp_handler_failed: int = Field(
        description='Falhas ao processar mensagem no handler WhatsApp.',
    )
    webhook_signature_failed: int = Field(
        description='Requisições POST ao webhook com assinatura HMAC inválida ou ausente.',
    )
    arq_jobs_enqueued_total: int = Field(
        description='Total de jobs `index_document` enfileirados via API (upload e reindex).',
    )
    arq_jobs_completed_total: int = Field(
        description='Total de execuções do job de indexação concluídas com sucesso no worker.',
    )
    arq_jobs_failed_total: int = Field(
        description=(
            'Execuções do job que falharam com exceção '
            '(cada tentativa; antes de eventual sucesso em retry).'
        ),
    )
    arq_job_duration_seconds: float = Field(
        description=(
            'Média em segundos entre enqueue (timestamp no payload) e conclusão com sucesso; '
            '0 se não houve conclusão.'
        ),
    )


async def _int_redis(redis: Redis, key: str) -> int:
    try:
        raw = await redis.get(key)
        return int(raw) if raw is not None else 0
    except Exception:
        return -1


@router.get(
    '',
    response_model=MetricsSnapshotResponse,
    summary='Métricas operacionais',
    description=(
        'Contadores em Redis: falhas (indexação, WhatsApp, webhook) e fila ARQ `index_document` '
        '(enfileiramentos, conclusões, falhas por tentativa, média enqueue→sucesso).'
    ),
)
async def metrics_snapshot(redis: Redis = Depends(get_redis)) -> MetricsSnapshotResponse:
    indexing_failed = await _int_redis(redis, KEY_INDEXING_FAILED)
    wa_failed = await _int_redis(redis, KEY_WHATSAPP_HANDLER_FAILED)
    sig_failed = await _int_redis(redis, KEY_WEBHOOK_SIGNATURE_FAIL)
    arq_enq = await _int_redis(redis, KEY_ARQ_JOBS_ENQUEUED)
    arq_done = await _int_redis(redis, KEY_ARQ_JOBS_COMPLETED)
    arq_fail = await _int_redis(redis, KEY_ARQ_JOBS_FAILED)
    sum_ms = await _int_redis(redis, KEY_ARQ_JOB_DURATION_MS_SUM)

    if arq_done > 0 and sum_ms >= 0:
        arq_avg_sec = (sum_ms / 1000.0) / arq_done
    else:
        arq_avg_sec = 0.0

    return MetricsSnapshotResponse(
        indexing_job_failed=indexing_failed,
        whatsapp_handler_failed=wa_failed,
        webhook_signature_failed=sig_failed,
        arq_jobs_enqueued_total=arq_enq,
        arq_jobs_completed_total=arq_done,
        arq_jobs_failed_total=arq_fail,
        arq_job_duration_seconds=round(arq_avg_sec, 6),
    )
