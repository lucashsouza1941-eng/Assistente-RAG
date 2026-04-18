from __future__ import annotations

import json
import time
from typing import Any
from uuid import UUID, uuid4

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.metrics import KEY_ARQ_JOBS_ENQUEUED, incr
from src.core.security import require_api_key
from src.dependencies import get_arq_redis, get_db_session, get_redis, get_settings
from src.modules.knowledge.models import Document, DocumentType
from src.modules.knowledge.schemas import (
    DocumentCreateRequest,
    DocumentPage,
    DocumentResponse,
    ReindexQueuedResponse,
    SearchRequest,
    SearchResult,
)
from src.modules.knowledge.service import DocumentService
from src.modules.knowledge.storage import MinioStorage

COMMON_AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {'description': 'API key ausente'},
    403: {'description': 'API key invalida'},
    422: {'description': 'Validacao falhou'},
}

router = APIRouter(prefix='/knowledge', tags=['knowledge'], dependencies=[Depends(require_api_key)])


@router.post('/documents', response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED, responses={**COMMON_AUTH_RESPONSES, 409: {'description': 'Conflito: documento duplicado'}})
async def create_document(
    title: str = Form(...),
    type: DocumentType = Form(...),
    content_hash: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    arq_redis: ArqRedis = Depends(get_arq_redis),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> DocumentResponse:
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail='Arquivo excede 10MB')
    if (file.content_type or '') not in {'application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}:
        raise HTTPException(status_code=422, detail='Tipo de arquivo nao suportado')

    document_id = uuid4()
    original_filename = file.filename or 'upload'
    # Persistência compartilhada (MinIO): o worker roda noutro container e lê os mesmos objetos.
    storage = MinioStorage(settings)
    await storage.ensure_bucket()
    await storage.upload_bytes(f'{document_id}/file', content, file.content_type)
    await storage.upload_bytes(
        f'{document_id}/meta.json',
        json.dumps({'content_type': file.content_type, 'original_filename': original_filename}).encode('utf-8'),
        'application/json',
    )

    service = DocumentService(db)
    try:
        doc = await service.create(DocumentCreateRequest(title=title, type=type, original_filename=original_filename, content_hash=content_hash), document_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    enqueued_at_ms = int(time.time() * 1000)
    await arq_redis.enqueue_job('index_document', str(doc.id), enqueued_at_ms)
    await incr(redis, KEY_ARQ_JOBS_ENQUEUED)
    return DocumentResponse(id=str(doc.id), title=doc.title, type=doc.type, status=doc.status, chunks_count=doc.chunks_count, created_at=doc.created_at)


@router.get('/documents', response_model=DocumentPage, status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def list_documents(page: int = Query(default=1, ge=1), size: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db_session)) -> DocumentPage:
    items, total = await DocumentService(db).list_paginated(page, size)
    pages = (total + size - 1) // size if total else 0
    return DocumentPage(items=[DocumentResponse(id=str(d.id), title=d.title, type=d.type, status=d.status, chunks_count=d.chunks_count, created_at=d.created_at) for d in items], total=total, page=page, size=size, pages=pages)


@router.delete('/documents/{document_id}', status_code=status.HTTP_204_NO_CONTENT, responses={**COMMON_AUTH_RESPONSES, 404: {'description': 'Recurso nao encontrado'}})
async def delete(document_id: UUID, db: AsyncSession = Depends(get_db_session)) -> None:
    try:
        await DocumentService(db).delete(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    '/documents/{document_id}/reindex',
    response_model=ReindexQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        **COMMON_AUTH_RESPONSES,
        404: {'description': 'Documento nao encontrado'},
        422: {'description': 'Arquivo de origem ausente no storage'},
    },
)
async def reindex(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    arq_redis: ArqRedis = Depends(get_arq_redis),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> ReindexQueuedResponse:
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail='Document not found')
    storage = MinioStorage(settings)
    await storage.ensure_bucket()
    prefix = f'{document_id}/'
    if not await storage.exists(f'{prefix}file') or not await storage.exists(f'{prefix}meta.json'):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Arquivo de origem nao encontrado no storage; nao e possivel reindexar.',
        )
    enqueued_at_ms = int(time.time() * 1000)
    await arq_redis.enqueue_job('index_document', str(document_id), enqueued_at_ms)
    await incr(redis, KEY_ARQ_JOBS_ENQUEUED)
    return ReindexQueuedResponse()


@router.post('/search', response_model=list[SearchResult], status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> list[SearchResult]:
    chunks = await DocumentService(db).search(payload.query, payload.top_k, payload.threshold, redis, settings)
    return [SearchResult(chunk_id=c.chunk_id, content=c.content, score=c.score, document_title=c.document_title, metadata=c.metadata) for c in chunks]
