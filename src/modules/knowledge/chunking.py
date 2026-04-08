from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ChunkData:
    content: str
    chunk_index: int
    metadata: dict
    token_count: int


class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def split(self, *, raw_bytes: bytes, content_type: str, document_id: str) -> list[ChunkData]:
        source_parts = self._extract_by_content_type(raw_bytes, content_type)
        chunks: list[ChunkData] = []

        for part in source_parts:
            page = part.get('page')
            section = part.get('section')
            text = (part.get('text') or '').strip()
            if not text:
                continue

            for fragment in self.splitter.split_text(text):
                clean = fragment.strip()
                if not clean or len(clean) < 50:
                    continue
                chunks.append(
                    ChunkData(
                        content=clean,
                        chunk_index=len(chunks),
                        metadata={'page': page, 'section': section},
                        token_count=self._estimate_tokens(clean),
                    )
                )

        avg_token_count = 0.0
        if chunks:
            avg_token_count = sum(c.token_count for c in chunks) / len(chunks)

        logger.info(
            'chunking.completed',
            document_id=document_id,
            total_chunks=len(chunks),
            avg_token_count=round(avg_token_count, 2),
        )
        return chunks

    def _extract_by_content_type(self, raw_bytes: bytes, content_type: str) -> list[dict]:
        normalized = content_type.lower().split(';')[0].strip()

        if normalized == 'application/pdf':
            return self._extract_pdf(raw_bytes)
        if normalized in {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
        }:
            return self._extract_docx(raw_bytes)
        if normalized == 'text/plain':
            text = raw_bytes.decode('utf-8', errors='ignore')
            return [{'text': text, 'page': None, 'section': 'full_text'}]

        raise ValueError(f'Unsupported content_type: {content_type}')

    def _extract_pdf(self, raw_bytes: bytes) -> list[dict]:
        reader = PdfReader(BytesIO(raw_bytes))
        parts: list[dict] = []
        for idx, page in enumerate(reader.pages, start=1):
            parts.append({'text': page.extract_text() or '', 'page': idx, 'section': None})
        return parts

    def _extract_docx(self, raw_bytes: bytes) -> list[dict]:
        doc = DocxDocument(BytesIO(raw_bytes))
        parts: list[dict] = []
        for idx, paragraph in enumerate(doc.paragraphs, start=1):
            text = (paragraph.text or '').strip()
            if not text:
                continue
            parts.append({'text': text, 'page': None, 'section': f'paragraph_{idx}'})
        return parts

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)
