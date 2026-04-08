from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.modules.knowledge.indexer import IndexingService
from src.modules.knowledge.models import Document, DocumentStatus
from src.modules.knowledge.retriever import RetrieverService
from src.modules.knowledge.schemas import DocumentCreateRequest


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: DocumentCreateRequest) -> Document:
        if await self.db.scalar(select(Document).where(Document.content_hash == payload.content_hash)):
            raise ValueError('duplicate content_hash')
        doc = Document(title=payload.title, type=payload.type, original_filename=payload.original_filename, content_hash=payload.content_hash)
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def index(self, document_id: UUID, settings: Settings) -> DocumentStatus:
        return await IndexingService(self.db, settings).index_document(document_id)

    async def search(self, query: str, top_k: int, threshold: float, redis: Redis, settings: Settings):
        return await RetrieverService(self.db, redis, settings).search(query, top_k, threshold)
