from __future__ import annotations

import asyncio
import json
import shutil
import time
from pathlib import Path
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import delete, select

from src.config import Settings
from src.core.logging import get_logger
from src.dependencies import AsyncSessionLocal
from src.modules.knowledge.chunking import TextChunker
from src.modules.knowledge.models import Document, DocumentChunk, DocumentStatus
from src.modules.knowledge.storage import MinioStorage

log = get_logger(module='knowledge.indexer')


class IndexingService:
    def __init__(self) -> None:
        self.chunker = TextChunker()

    async def index_document(self, document_id: UUID, settings: Settings) -> DocumentStatus:
        started = time.perf_counter()
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        # Origem da verdade: MinIO (bucket configurável). /tmp aqui é só scratch local após download.
        tmp_dir = Path('/tmp') / str(document_id)
        storage = MinioStorage(settings)
        try:
            await storage.ensure_bucket()
            await self._download_document_assets(storage, document_id, tmp_dir)
            meta_path = tmp_dir / 'meta.json'
            async with AsyncSessionLocal() as db:
                async with db.begin():
                    doc = await db.scalar(select(Document).where(Document.id == document_id))
                    if doc is None:
                        raise ValueError('Document not found')
                    doc.status = DocumentStatus.PROCESSING
                    await db.flush()

                    meta = json.loads(meta_path.read_text(encoding='utf-8'))
                    content_type = str(meta['content_type'])
                    original_filename = str(meta['original_filename'])
                    file_path = tmp_dir / original_filename

                    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
                    await db.flush()

                    chunks = self.chunker.split(file_path=file_path, content_type=content_type, document_id=str(document_id))
                    vectors = await self._embed_batches(client, [c.content for c in chunks])

                    for c, v in zip(chunks, vectors, strict=True):
                        db.add(
                            DocumentChunk(
                                document_id=doc.id,
                                content=c.content,
                                embedding=v,
                                chunk_index=c.chunk_index,
                                metadata_=c.metadata,
                                token_count=c.token_count,
                            )
                        )

                    doc.status = DocumentStatus.INDEXED
                    doc.chunks_count = len(chunks)
                    doc.error_message = None

            shutil.rmtree(tmp_dir, ignore_errors=True)

            log.info(
                'indexing.completed',
                duration_ms=int((time.perf_counter() - started) * 1000),
                metadata={
                    'document_id': str(document_id),
                    'chunks_created': len(chunks),
                    'embeddings_generated': len(vectors),
                    'indexed_at': time.time(),
                },
            )
            return DocumentStatus.INDEXED
        except Exception as exc:
            async with AsyncSessionLocal() as db:
                async with db.begin():
                    managed = await db.scalar(select(Document).where(Document.id == document_id))
                    if managed is not None:
                        managed.status = DocumentStatus.ERROR
                        managed.error_message = str(exc)
            log.error(
                'indexing_failed',
                error_type=type(exc).__name__,
                error_message=str(exc)[:200],
                document_id=str(document_id),
            )
            raise

    async def _embed_batches(self, client: AsyncOpenAI, texts: list[str]) -> list[list[float]]:
        batches = [texts[i : i + 100] for i in range(0, len(texts), 100)]

        async def _one(batch: list[str]) -> list[list[float]]:
            r = await client.embeddings.create(model='text-embedding-3-small', input=batch)
            return [x.embedding for x in r.data]

        nested = await asyncio.gather(*(_one(b) for b in batches))
        return [v for part in nested for v in part]

    async def _download_document_assets(self, storage: MinioStorage, document_id: UUID, tmp_dir: Path) -> None:
        tmp_dir.mkdir(parents=True, exist_ok=True)
        meta_bytes = await storage.download_bytes(f'{document_id}/meta.json')
        (tmp_dir / 'meta.json').write_bytes(meta_bytes)
        meta = json.loads(meta_bytes.decode('utf-8'))
        original_filename = str(meta['original_filename'])
        file_bytes = await storage.download_bytes(f'{document_id}/file')
        (tmp_dir / original_filename).write_bytes(file_bytes)
