from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session, get_settings
from src.modules.knowledge.schemas import (
    DocumentCreateRequest,
    DocumentCreateResponse,
    IndexDocumentResponse,
)
from src.modules.knowledge.service import DocumentService

router = APIRouter(prefix='/knowledge', tags=['knowledge'])


@router.post('/documents', response_model=DocumentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    title: str = Form(...),
    type: str = Form(...),
    content_hash: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings),
) -> DocumentCreateResponse:
    service = DocumentService(db)

    payload = DocumentCreateRequest(
        title=title,
        type=type,
        original_filename=file.filename or 'upload.bin',
        content_hash=content_hash,
    )
    document = await service.create_document(payload)

    content = await file.read()
    await service.save_temp_upload(document.id, content, file.content_type or 'application/octet-stream')

    return DocumentCreateResponse(id=str(document.id), status=document.status)


@router.post('/documents/{document_id}/index', response_model=IndexDocumentResponse)
async def index_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    settings=Depends(get_settings),
) -> IndexDocumentResponse:
    service = DocumentService(db)
    try:
        result = await service.index_document(document_id, settings)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return IndexDocumentResponse(document_id=str(document_id), status=result)
