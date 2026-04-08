from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.knowledge.indexer import IndexingService
from src.modules.knowledge.models import Document, DocumentStatus
from src.modules.knowledge.schemas import DocumentCreateRequest


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_document(self, payload: DocumentCreateRequest) -> Document:
        document = Document(
            id=uuid4(),
            title=payload.title,
            type=payload.type,
            original_filename=payload.original_filename,
            content_hash=payload.content_hash,
            status=DocumentStatus.PENDING,
            chunks_count=0,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def save_temp_upload(self, document_id: UUID, content: bytes, content_type: str) -> None:
        tmp_path = Path('/tmp')
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / str(document_id)).write_bytes(content)
        (tmp_path / f'{document_id}.content_type').write_text(content_type, encoding='utf-8')

    async def index_document(self, document_id: UUID, settings) -> DocumentStatus:
        indexer = IndexingService(self.db, settings)
        return await indexer.index_document(document_id)
