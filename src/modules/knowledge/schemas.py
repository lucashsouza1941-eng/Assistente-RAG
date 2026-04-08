from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.knowledge.models import DocumentStatus, DocumentType
from src.modules.knowledge.retriever import RetrievedChunk


class DocumentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    type: DocumentType
    original_filename: str = Field(min_length=1, max_length=255)
    content_hash: str = Field(min_length=64, max_length=64)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    type: DocumentType
    original_filename: str
    content_hash: str
    status: DocumentStatus
    chunks_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentCreateResponse(BaseModel):
    id: str
    status: DocumentStatus


class DocumentPage(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    size: int


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.7


class SearchResult(BaseModel):
    chunk_id: str
    content: str
    score: float
    document_title: str
    metadata: dict

    @classmethod
    def from_retrieved(cls, chunk: RetrievedChunk) -> 'SearchResult':
        return cls(chunk_id=chunk.chunk_id, content=chunk.content, score=chunk.score, document_title=chunk.document_title, metadata=chunk.metadata)


class IndexDocumentResponse(BaseModel):
    document_id: str
    status: DocumentStatus
