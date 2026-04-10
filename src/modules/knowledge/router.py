from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.knowledge.indexer import IndexingService
from src.modules.knowledge.schemas import DocumentCreateRequest, DocumentPage, DocumentResponse, ReindexResponse, SearchRequest, SearchResult
from src.modules.knowledge.service import DocumentService

COMMON_AUTH_RESPONSES = {
    401: {'description': 'API key ausente'},
    403: {'description': 'API key invalida'},
    422: {'description': 'Validacao falhou'},
}

router = APIRouter(prefix='/knowledge', tags=['knowledge'], dependencies=[Depends(require_api_key)])


@router.post('/documents', response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED, responses={**COMMON_AUTH_RESPONSES, 409: {'description': 'Conflito: documento duplicado'}})
async def create_document(background_tasks: BackgroundTasks, title: str = Form(...), type: str = Form(...), content_hash: str = Form(...), file: UploadFile = File(...), db: AsyncSession = Depends(get_db_session), settings=Depends(get_settings)) -> DocumentResponse:
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail='Arquivo excede 10MB')
    if (file.content_type or '') not in {'application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}:
        raise HTTPException(status_code=422, detail='Tipo de arquivo nao suportado')

    document_id = uuid4()
    original_filename = file.filename or 'upload'
    tmp_dir = Path('/tmp') / str(document_id)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    (tmp_dir / original_filename).write_bytes(content)
    (tmp_dir / 'meta.json').write_text(json.dumps({'content_type': file.content_type, 'original_filename': original_filename}), encoding='utf-8')

    service = DocumentService(db)
    try:
        doc = await service.create(DocumentCreateRequest(title=title, type=type, original_filename=original_filename, content_hash=content_hash), document_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    background_tasks.add_task(IndexingService().index_document, doc.id, settings)
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


@router.post('/documents/{document_id}/reindex', response_model=ReindexResponse, status_code=status.HTTP_202_ACCEPTED, responses={**COMMON_AUTH_RESPONSES, 404: {'description': 'Recurso nao encontrado'}})
async def reindex(document_id: UUID, db: AsyncSession = Depends(get_db_session), settings=Depends(get_settings)) -> ReindexResponse:
    try:
        status_value = await DocumentService(db).index(document_id, settings)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReindexResponse(document_id=str(document_id), status=status_value)


@router.post('/search', response_model=list[SearchResult], status_code=status.HTTP_200_OK, responses=COMMON_AUTH_RESPONSES)
async def search(payload: SearchRequest, db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> list[SearchResult]:
    chunks = await DocumentService(db).search(payload.query, payload.top_k, payload.threshold, redis, settings)
    return [SearchResult(chunk_id=c.chunk_id, content=c.content, score=c.score, document_title=c.document_title, metadata=c.metadata) for c in chunks]
