from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.knowledge.models import DocumentStatus
from src.modules.knowledge.schemas import DocumentCreateRequest, DocumentResponse, SearchRequest, SearchResult
from src.modules.knowledge.service import DocumentService

router = APIRouter(prefix='/knowledge', tags=['knowledge'], dependencies=[Depends(require_api_key)])


@router.post('/documents', response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_document(title: str = Form(...), type: str = Form(...), content_hash: str = Form(...), file: UploadFile = File(...), db: AsyncSession = Depends(get_db_session)) -> DocumentResponse:
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='max 10MB')
    if (file.content_type or '') not in {'application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}:
        raise HTTPException(status_code=400, detail='unsupported type')
    service = DocumentService(db)
    try:
        doc = await service.create(DocumentCreateRequest(title=title, type=type, original_filename=file.filename or 'upload', content_hash=content_hash))
    except ValueError:
        raise HTTPException(status_code=409, detail='duplicate content_hash')
    return DocumentResponse(id=str(doc.id), title=doc.title, type=doc.type, status=doc.status, chunks_count=doc.chunks_count, created_at=doc.created_at)


@router.post('/documents/{document_id}/reindex', status_code=status.HTTP_202_ACCEPTED)
async def reindex(document_id: UUID, db: AsyncSession = Depends(get_db_session), settings=Depends(get_settings)) -> dict:
    status_value = await DocumentService(db).index(document_id, settings)
    return {'document_id': str(document_id), 'status': status_value}


@router.post('/search', response_model=list[SearchResult], status_code=status.HTTP_200_OK)
async def search(payload: SearchRequest, db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> list[SearchResult]:
    chunks = await DocumentService(db).search(payload.query, payload.top_k, payload.threshold, redis, settings)
    return [SearchResult(chunk_id=c.chunk_id, content=c.content, score=c.score, document_title=c.document_title, metadata=c.metadata) for c in chunks]


@router.get('/documents', response_model=list[DocumentResponse], status_code=status.HTTP_200_OK)
async def list_documents(page: int = Query(default=1, ge=1), size: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db_session)) -> list[DocumentResponse]:
    from sqlalchemy import select
    from src.modules.knowledge.models import Document
    docs = (await db.execute(select(Document).offset((page - 1) * size).limit(size))).scalars().all()
    return [DocumentResponse(id=str(d.id), title=d.title, type=d.type, status=d.status, chunks_count=d.chunks_count, created_at=d.created_at) for d in docs]


@router.delete('/documents/{document_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete(document_id: UUID, db: AsyncSession = Depends(get_db_session)) -> None:
    from pathlib import Path
    from src.modules.knowledge.models import Document
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail='not found')
    await db.delete(doc)
    await db.commit()
    p = Path('/tmp') / str(document_id)
    if p.exists():
        p.unlink()
