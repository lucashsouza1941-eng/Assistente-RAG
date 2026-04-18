from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class DocumentType(enum.StrEnum):
    PROCEDURE = 'PROCEDURE'
    FAQ = 'FAQ'
    PROTOCOL = 'PROTOCOL'
    GENERAL = 'GENERAL'


class DocumentStatus(enum.StrEnum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    INDEXED = 'INDEXED'
    ERROR = 'ERROR'


class Document(Base):
    __tablename__ = 'documents'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(500))
    type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, name='document_type'))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus, name='document_status'), default=DocumentStatus.PENDING)
    chunks_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates='document', cascade='all, delete-orphan')


class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    __table_args__ = (
        Index('ix_document_chunks_embedding_ivfflat', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    chunk_index: Mapped[int]
    metadata_: Mapped[dict[str, Any]] = mapped_column(JSONB, name='metadata')
    token_count: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    document: Mapped[Document] = relationship(back_populates='chunks')
