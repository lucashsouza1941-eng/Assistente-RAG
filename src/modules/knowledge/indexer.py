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

logger = get_logger(__name__)


class IndexingService:
    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.chunker = TextChunker()
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)

    async def index_document(self, document_id: UUID) -> DocumentStatus:
        started = time.perf_counter()
        logger.info('indexing.start', document_id=str(document_id))

        document = await self.db.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            raise ValueError(f'Document {document_id} not found')

        try:
            document.status = DocumentStatus.PROCESSING
            await self.db.flush()

            tmp_path = Path('/tmp') / f'{document.id}'
            if not tmp_path.exists():
                raise FileNotFoundError(f'File not found in storage temp path: {tmp_path}')

            raw = tmp_path.read_bytes()
            content_type = self._resolve_content_type(document.id, raw)
            chunks = self.chunker.split(raw_bytes=raw, content_type=content_type, document_id=str(document.id))
            logger.info('indexing.chunks_created', document_id=str(document.id), chunks_created=len(chunks))

            embeddings = await self._embed_in_batches([c.content for c in chunks])
            logger.info('indexing.embeddings_generated', document_id=str(document.id), embeddings_generated=len(embeddings))

            chunk_rows = [
                DocumentChunk(
                    document_id=document.id,
                    content=chunk.content,
                    embedding=embedding,
                    chunk_index=chunk.chunk_index,
                    metadata_=chunk.metadata,
                    token_count=chunk.token_count,
                )
                for chunk, embedding in zip(chunks, embeddings, strict=True)
            ]
            self.db.add_all(chunk_rows)

            document.status = DocumentStatus.INDEXED
            document.chunks_count = len(chunk_rows)
            document.error_message = None
            await self.db.commit()

            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.info('indexing.completed', document_id=str(document.id), indexed_at=time.time(), duration_ms=duration_ms)
            return DocumentStatus.INDEXED
        except Exception as exc:
            await self.db.rollback()
            managed_doc = await self.db.scalar(select(Document).where(Document.id == document_id))
            if managed_doc is not None:
                managed_doc.status = DocumentStatus.ERROR
                managed_doc.error_message = str(exc)
                await self.db.commit()
            logger.exception('indexing.failed', document_id=str(document_id), error=str(exc))
            raise

    async def _embed_in_batches(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        batches = [texts[idx : idx + batch_size] for idx in range(0, len(texts), batch_size)]

        async def create_embedding_batch(batch: list[str]) -> list[list[float]]:
            result = await self.openai.embeddings.create(model='text-embedding-3-small', input=batch)
            return [item.embedding for item in result.data]

        responses = await asyncio.gather(*(create_embedding_batch(batch) for batch in batches))
        return [vector for response in responses for vector in response]

    def _resolve_content_type(self, document_id: UUID, raw: bytes) -> str:
        sidecar = Path('/tmp') / f'{document_id}.content_type'
        if sidecar.exists():
            value = sidecar.read_text(encoding='utf-8').strip()
            if value:
                return value
        return self._detect_content_type(raw)

    @staticmethod
    def _detect_content_type(raw: bytes) -> str:
        if raw.startswith(b'%PDF-'):
            return 'application/pdf'
        if raw.startswith(b'PK'):
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        return 'text/plain'
