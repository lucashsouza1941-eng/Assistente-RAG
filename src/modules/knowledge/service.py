from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.knowledge.indexer import IndexingService
from src.modules.knowledge.models import Document, DocumentChunk, DocumentStatus, DocumentType
from src.modules.knowledge.retriever import RetrieverService
from src.modules.knowledge.schemas import DocumentCreateRequest


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_documents(self, *, page: int, size: int, doc_type: DocumentType | None, status: DocumentStatus | None) -> tuple[list[Document], int]:
        filters: list[Any] = []
        if doc_type is not None:
            filters.append(Document.type == doc_type)
        if status is not None:
            filters.append(Document.status == status)

        stmt = select(Document).order_by(Document.created_at.desc())
        count_stmt = select(func.count(Document.id))
        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        result = await self.db.execute(stmt.offset((page - 1) * size).limit(size))
        total = await self.db.scalar(count_stmt)
        return list(result.scalars().all()), int(total or 0)

    async def create_document(self, payload: DocumentCreateRequest) -> Document:
        existing = await self.db.scalar(select(Document).where(Document.content_hash == payload.content_hash))
        if existing is not None:
            raise ValueError('Document with same content_hash already exists')
        document = Document(id=uuid4(), title=payload.title, type=payload.type, original_filename=payload.original_filename, content_hash=payload.content_hash, status=DocumentStatus.PENDING, chunks_count=0)
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete_document(self, document_id: UUID) -> bool:
        document = await self.db.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            return False
        await self.db.delete(document)
        await self.db.commit()
        tmp_path = Path('/tmp') / str(document_id)
        sidecar = Path('/tmp') / f'{document_id}.content_type'
        if tmp_path.exists():
            tmp_path.unlink()
        if sidecar.exists():
            sidecar.unlink()
        return True

    async def save_temp_upload(self, document_id: UUID, content: bytes, content_type: str) -> None:
        tmp_path = Path('/tmp')
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / str(document_id)).write_bytes(content)
        (tmp_path / f'{document_id}.content_type').write_text(content_type, encoding='utf-8')

    async def index_document(self, document_id: UUID, settings: Settings) -> DocumentStatus:
        indexer = IndexingService(self.db, settings)
        return await indexer.index_document(document_id)

    async def reindex_document(self, document_id: UUID, settings: Settings) -> DocumentStatus:
        document = await self.db.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            raise ValueError(f'Document {document_id} not found')
        await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        document.status = DocumentStatus.PENDING
        document.chunks_count = 0
        await self.db.commit()
        return await self.index_document(document_id, settings)

    async def search(self, query: str, top_k: int, threshold: float, redis: Redis, settings: Settings):
        retriever = RetrieverService(self.db, redis, settings)
        return await retriever.search(query=query, top_k=top_k, threshold=threshold)
