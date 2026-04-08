from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import require_api_key
from src.dependencies import get_db_session, get_redis, get_settings
from src.modules.knowledge.models import DocumentStatus, DocumentType
from src.modules.knowledge.schemas import DocumentCreateRequest, DocumentCreateResponse, DocumentPage, DocumentResponse, IndexDocumentResponse, SearchRequest, SearchResult
from src.modules.knowledge.service import DocumentService

ALLOWED_CONTENT_TYPES = {'application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

router = APIRouter(prefix='/knowledge', tags=['knowledge'], dependencies=[Depends(require_api_key)])


@router.get('/documents', response_model=DocumentPage, status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def list_documents(page: int = Query(default=1, ge=1), size: int = Query(default=20, ge=1, le=100), type: DocumentType | None = Query(default=None), status_filter: DocumentStatus | None = Query(default=None, alias='status'), db: AsyncSession = Depends(get_db_session)) -> DocumentPage:
    service = DocumentService(db)
    items, total = await service.list_documents(page=page, size=size, doc_type=type, status=status_filter)
    return DocumentPage(items=[DocumentResponse.model_validate(item, from_attributes=True) for item in items], total=total, page=page, size=size)


@router.post('/documents', response_model=DocumentCreateResponse, status_code=status.HTTP_202_ACCEPTED, responses={400: {'description': 'Invalid file type or size'}, 401: {'description': 'Unauthorized'}, 409: {'description': 'Duplicate content_hash'}})
async def create_document(title: str = Form(...), type: DocumentType = Form(...), content_hash: str = Form(...), file: UploadFile = File(...), db: AsyncSession = Depends(get_db_session)) -> DocumentCreateResponse:
    if (file.content_type or '') not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unsupported file content_type')
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='File exceeds 10MB limit')

    service = DocumentService(db)
    payload = DocumentCreateRequest(title=title, type=type, original_filename=file.filename or 'upload.bin', content_hash=content_hash)
    try:
        document = await service.create_document(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    await service.save_temp_upload(document.id, content, file.content_type or 'application/octet-stream')
    return DocumentCreateResponse(id=str(document.id), status=document.status)


@router.delete('/documents/{document_id}', status_code=status.HTTP_204_NO_CONTENT, responses={401: {'description': 'Unauthorized'}, 404: {'description': 'Document not found'}})
async def delete_document(document_id: UUID, db: AsyncSession = Depends(get_db_session)) -> None:
    service = DocumentService(db)
    deleted = await service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Document not found')


@router.post('/documents/{document_id}/reindex', response_model=IndexDocumentResponse, status_code=status.HTTP_202_ACCEPTED, responses={401: {'description': 'Unauthorized'}, 404: {'description': 'Document not found'}})
async def reindex_document(document_id: UUID, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db_session), settings=Depends(get_settings)) -> IndexDocumentResponse:
    service = DocumentService(db)

    async def _run() -> None:
        await service.reindex_document(document_id, settings)

    background_tasks.add_task(_run)
    return IndexDocumentResponse(document_id=str(document_id), status=DocumentStatus.PROCESSING)


@router.post('/search', response_model=list[SearchResult], status_code=status.HTTP_200_OK, responses={401: {'description': 'Unauthorized'}})
async def search_documents(payload: SearchRequest, db: AsyncSession = Depends(get_db_session), redis: Redis = Depends(get_redis), settings=Depends(get_settings)) -> list[SearchResult]:
    service = DocumentService(db)
    result = await service.search(payload.query, payload.top_k, payload.threshold, redis, settings)
    return [SearchResult.from_retrieved(chunk) for chunk in result]
