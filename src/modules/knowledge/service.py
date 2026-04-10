from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.knowledge.indexer import IndexingService
from src.modules.knowledge.models import Document, DocumentStatus
from src.modules.knowledge.retriever import RetrieverService
from src.modules.knowledge.schemas import DocumentCreateRequest


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: DocumentCreateRequest, document_id: UUID) -> Document:
        if await self.db.scalar(select(Document).where(Document.content_hash == payload.content_hash)):
            raise ValueError('A document with this content_hash already exists')
        doc = Document(id=document_id, title=payload.title, type=payload.type, original_filename=payload.original_filename, content_hash=payload.content_hash, status=DocumentStatus.PENDING)
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list_paginated(self, page: int, size: int) -> tuple[list[Document], int]:
        items = (await self.db.execute(select(Document).order_by(Document.created_at.desc()).offset((page - 1) * size).limit(size))).scalars().all()
        total = int(await self.db.scalar(select(func.count(Document.id))) or 0)
        return list(items), total

    async def delete(self, document_id: UUID) -> None:
        doc = await self.db.get(Document, document_id)
        if doc is None:
            raise ValueError('Document not found')
        await self.db.delete(doc)
        await self.db.commit()

    async def index(self, document_id: UUID, settings: Settings) -> DocumentStatus:
        return await IndexingService().index_document(document_id, settings)

    async def search(self, query: str, top_k: int, threshold: float, redis: Redis, settings: Settings):
        return await RetrieverService(self.db, redis, settings).search(query, top_k, threshold)
