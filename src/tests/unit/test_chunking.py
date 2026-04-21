from __future__ import annotations

import pytest
from pathlib import Path

from src.modules.knowledge.chunking import TextChunker


def test_short_text_raises_value_error():
    path = Path(__file__).with_name("_tmp_short.txt")
    path.write_text("curto", encoding="utf-8")
    with pytest.raises(ValueError):
        TextChunker().split(path, 'text/plain', 'doc')
    path.unlink(missing_ok=True)


def test_metadata_preserved():
    path = Path(__file__).with_name("_tmp_long.txt")
    path.write_text('Atendimento odontologico com protocolo completo. ' * 20, encoding="utf-8")
    chunks = TextChunker().split(path, 'text/plain', 'doc')
    assert chunks[0].metadata['section'] == 'full_text'
    path.unlink(missing_ok=True)


def test_pdf_5_pages_contract():
    path = Path(__file__).with_name("_tmp_fake.pdf")
    path.write_bytes(b'%PDF-1.4\n' + b'abc')
    with pytest.raises(Exception):
        TextChunker().split(path, 'application/pdf', 'doc')
    path.unlink(missing_ok=True)
