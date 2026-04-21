from __future__ import annotations

from uuid import uuid4
from typing import Any, cast

import pytest

from src.modules.chat.rag_chain import RAGChain
from src.modules.knowledge.retriever import RetrievedChunk


class _DB:
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        class _S:
            def scalars(self) -> "_S":
                return self

            def all(self) -> list[Any]:
                return []

        return _S()


@pytest.mark.asyncio
async def test_no_chunks_default_response():
    class _R:
        async def search(self, q: str) -> list[RetrievedChunk]:
            return []
    s = cast(Any, type('S', (), {'openai_api_key': 'x', 'clinic_name': 'Clinica', 'escalation_threshold': 0.7})())
    chain = RAGChain(
        cast(Any, _DB()),
        cast(Any, _R()),
        s,
        model="gpt-4o-mini",
        temperature=0.0,
        max_tokens=200,
        escalation_threshold=0.7,
        clinic_name="Clinica",
    )
    r = await chain.generate('duvida', uuid4())
    assert r.escalated is True


@pytest.mark.asyncio
async def test_low_confidence_escalates(monkeypatch):
    class _R:
        async def search(self, q: str) -> list[RetrievedChunk]:
            return [RetrievedChunk('1', 'ctx', 0.6, 'Doc', {})]
    s = cast(Any, type('S', (), {'openai_api_key': 'x', 'clinic_name': 'Clinica', 'escalation_threshold': 0.9})())
    chain = RAGChain(
        cast(Any, _DB()),
        cast(Any, _R()),
        s,
        model="gpt-4o-mini",
        temperature=0.0,
        max_tokens=200,
        escalation_threshold=0.9,
        clinic_name="Clinica",
    )
    class _L:
        async def ainvoke(self, p: Any) -> Any:
            return type('M', (), {'content': 'talvez'})()
    monkeypatch.setattr(chain, 'llm', _L())
    monkeypatch.setattr('src.modules.chat.rag_chain.get_rag_prompt', lambda _: type('P', (), {'__or__': lambda self, other: other})())
    r = await chain.generate('duvida', uuid4())
    assert r.escalated is True
