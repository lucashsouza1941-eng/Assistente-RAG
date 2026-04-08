from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.chat.rag_chain import RAGChain
from src.modules.knowledge.retriever import RetrievedChunk


class _DB:
    async def execute(self, *args, **kwargs):
        class _S:
            def scalars(self):
                return self

            def all(self):
                return []

        return _S()


@pytest.mark.asyncio
async def test_no_chunks_default_response():
    class _R:
        async def search(self, q):
            return []
    s = type('S', (), {'openai_api_key': 'x', 'clinic_name': 'Clinica', 'escalation_threshold': 0.7})()
    r = await RAGChain(_DB(), _R(), s).generate('duvida', uuid4())
    assert r.escalated is True


@pytest.mark.asyncio
async def test_low_confidence_escalates(monkeypatch):
    class _R:
        async def search(self, q):
            return [RetrievedChunk('1', 'ctx', 0.6, 'Doc', {})]
    s = type('S', (), {'openai_api_key': 'x', 'clinic_name': 'Clinica', 'escalation_threshold': 0.9})()
    chain = RAGChain(_DB(), _R(), s)
    monkeypatch.setattr(chain, 'llm', type('L', (), {'ainvoke': lambda self, p: type('M', (), {'content': 'talvez'})()})())
    monkeypatch.setattr('src.modules.chat.rag_chain.get_rag_prompt', lambda _: type('P', (), {'__or__': lambda self, other: other})())
    r = await chain.generate('duvida', uuid4())
    assert r.escalated is True
