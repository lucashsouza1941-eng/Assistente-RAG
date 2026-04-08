from __future__ import annotations

import asyncio
import time
from pathlib import Path
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.logging import get_logger
from src.modules.knowledge.chunking import TextChunker
from src.modules.knowledge.models import Document, DocumentChunk, DocumentStatus

log = get_logger(module='knowledge.indexer')


class IndexingService:
    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.chunker = TextChunker()

    async def index_document(self, document_id: UUID) -> DocumentStatus:
        started = time.perf_counter()
        doc = await self.db.scalar(select(Document).where(Document.id == document_id))
        if doc is None:
            raise ValueError('Document not found')
        try:
            doc.status = DocumentStatus.PROCESSING
            await self.db.flush()
            raw = (Path('/tmp') / str(document_id)).read_bytes()
            content_type = (Path('/tmp') / f'{document_id}.content_type').read_text(encoding='utf-8').strip()
            chunks = self.chunker.split(raw, content_type, str(document_id))
            vectors = await self._embed_batches([c.content for c in chunks])
            for c, v in zip(chunks, vectors, strict=True):
                self.db.add(DocumentChunk(document_id=doc.id, content=c.content, embedding=v, chunk_index=c.chunk_index, metadata_=c.metadata, token_count=c.token_count))
            doc.status = DocumentStatus.INDEXED
            doc.chunks_count = len(chunks)
            doc.error_message = None
            await self.db.commit()
            log.info('indexing.completed', duration_ms=int((time.perf_counter() - started) * 1000), metadata={'document_id': str(document_id), 'chunks_created': len(chunks), 'embeddings_generated': len(vectors), 'indexed_at': time.time()})
            return doc.status
        except Exception as exc:
            await self.db.rollback()
            doc = await self.db.scalar(select(Document).where(Document.id == document_id))
            if doc is not None:
                doc.status = DocumentStatus.ERROR
                doc.error_message = str(exc)
                await self.db.commit()
            raise

    async def _embed_batches(self, texts: list[str]) -> list[list[float]]:
        batches = [texts[i:i + 100] for i in range(0, len(texts), 100)]
        async def _one(batch: list[str]) -> list[list[float]]:
            r = await self.client.embeddings.create(model='text-embedding-3-small', input=batch)
            return [x.embedding for x in r.data]
        nested = await asyncio.gather(*(_one(b) for b in batches))
        return [v for part in nested for v in part]
