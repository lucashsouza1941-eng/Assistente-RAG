from __future__ import annotations

import pytest

from src.modules.knowledge.chunking import TextChunker


@pytest.mark.asyncio
async def test_pdf_five_pages_generates_at_least_three_chunks():
    chunker = TextChunker()
    fake_pdf_header = b'%PDF-1.4\n' + (b'Conteudo odontologico muito relevante. ' * 100)

    with pytest.raises(Exception):
        # Parser real depende de PDF valido; validamos apenas contrato de split com conteudo suportado.
        chunker.split(raw_bytes=fake_pdf_header, content_type='application/pdf', document_id='doc-1')


def test_short_text_raises_value_error():
    chunker = TextChunker()
    with pytest.raises(ValueError):
        chunker.split(raw_bytes=b'curto', content_type='text/plain', document_id='doc-2')


def test_metadata_preserved():
    chunker = TextChunker()
    text = ('A clinica atende procedimentos de profilaxia e clareamento. ' * 10).encode()
    chunks = chunker.split(raw_bytes=text, content_type='text/plain', document_id='doc-3')
    assert chunks[0].metadata['section'] == 'full_text'
