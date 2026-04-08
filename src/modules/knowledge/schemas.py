from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from src.modules.knowledge.models import DocumentStatus, DocumentType


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
