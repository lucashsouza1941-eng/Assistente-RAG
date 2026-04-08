from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.modules.knowledge.models import DocumentStatus, DocumentType


class DocumentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    type: DocumentType
    original_filename: str = Field(min_length=1, max_length=255)
    content_hash: str = Field(min_length=64, max_length=64)


class DocumentCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: DocumentStatus


class IndexDocumentResponse(BaseModel):
    document_id: str
    status: DocumentStatus
