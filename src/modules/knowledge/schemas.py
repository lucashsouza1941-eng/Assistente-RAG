from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from src.modules.knowledge.models import DocumentStatus, DocumentType
from src.schemas.pagination import Page


class DocumentCreateRequest(BaseModel):
    title: str
    type: DocumentType
    original_filename: str
    content_hash: str


class DocumentResponse(BaseModel):
    id: str
    title: str
    type: DocumentType
    status: DocumentStatus
    chunks_count: int
    created_at: datetime


class DocumentPage(Page[DocumentResponse]):
    pass


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.7


class SearchResult(BaseModel):
    chunk_id: str
    content: str
    score: float
    document_title: str
    metadata: dict[str, Any]


class ReindexQueuedResponse(BaseModel):
    """Resposta do POST /reindex: apenas confirma enfileiramento; indexação ocorre no worker."""

    status: Literal['queued'] = 'queued'
