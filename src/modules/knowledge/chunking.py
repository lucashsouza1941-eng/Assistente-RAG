from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

from src.core.logging import get_logger

log = get_logger(module='knowledge.chunking')


@dataclass(slots=True)
class ChunkData:
    content: str
    chunk_index: int
    metadata: dict
    token_count: int


class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def split(self, raw_bytes: bytes, content_type: str, document_id: str) -> list[ChunkData]:
        parts = self._extract(raw_bytes, content_type)
        chunks: list[ChunkData] = []
        for part in parts:
            for fragment in self.splitter.split_text(part['text']):
                text = fragment.strip()
                if len(text) < 50:
                    continue
                chunks.append(ChunkData(content=text, chunk_index=len(chunks), metadata={'page': part.get('page'), 'section': part.get('section')}, token_count=max(1, len(text) // 4)))
        if not chunks:
            raise ValueError('No valid chunks generated')
        avg = sum(c.token_count for c in chunks) / len(chunks)
        log.info('chunking.completed', metadata={'document_id': document_id, 'total_chunks': len(chunks), 'avg_token_count': round(avg, 2)})
        return chunks

    def _extract(self, raw_bytes: bytes, content_type: str) -> list[dict]:
        ct = content_type.lower().split(';')[0].strip()
        if ct == 'application/pdf':
            reader = PdfReader(BytesIO(raw_bytes))
            return [{'text': p.extract_text() or '', 'page': i, 'section': None} for i, p in enumerate(reader.pages, start=1)]
        if ct in {'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'}:
            doc = DocxDocument(BytesIO(raw_bytes))
            return [{'text': p.text, 'page': None, 'section': f'paragraph_{i}'} for i, p in enumerate(doc.paragraphs, start=1) if p.text.strip()]
        if ct == 'text/plain':
            return [{'text': raw_bytes.decode('utf-8', errors='ignore'), 'page': None, 'section': 'full_text'}]
        raise ValueError(f'Unsupported content_type: {content_type}')
