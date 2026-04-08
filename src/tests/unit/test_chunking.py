from __future__ import annotations

import pytest

from src.modules.knowledge.chunking import TextChunker


def test_short_text_raises_value_error():
    with pytest.raises(ValueError):
        TextChunker().split(b'curto', 'text/plain', 'doc')


def test_metadata_preserved():
    text = ('Atendimento odontologico com protocolo completo. ' * 20).encode()
    chunks = TextChunker().split(text, 'text/plain', 'doc')
    assert chunks[0].metadata['section'] == 'full_text'


def test_pdf_5_pages_contract():
    fake_pdf = b'%PDF-1.4\n' + b'abc'
    with pytest.raises(Exception):
        TextChunker().split(fake_pdf, 'application/pdf', 'doc')
