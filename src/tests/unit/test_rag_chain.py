from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.chat.rag_chain import ESCALATION_MESSAGE, RAGChain
from src.modules.knowledge.retriever import RetrievedChunk


class _DB:
    async def scalar(self, *args, **kwargs):
        return object()

    async def execute(self, *args, **kwargs):
        class R:
            def scalars(self):
                return self

            def all(self):
                return []

        return R()


class _Retriever:
    async def search(self, question: str):
        return []


@pytest.mark.asyncio
async def test_no_chunks_returns_default_escalation():
    settings = type('S', (), {'openai_api_key': 'x', 'clinic_name': 'Clinica', 'escalation_threshold': 0.7})()
    chain = RAGChain(_DB(), _Retriever(), settings)
    result = await chain.generate('oi', uuid4())
    assert result.escalated is True
    assert result.content == ESCALATION_MESSAGE


@pytest.mark.asyncio
async def test_confidence_low_escalates(monkeypatch):
    settings = type('S', (), {'openai_api_key': 'x', 'clinic_name': 'Clinica', 'escalation_threshold': 0.95})()

    class _R:
        async def search(self, question: str):
            return [RetrievedChunk(chunk_id='1', content='c', score=0.7, document_title='d', metadata={})]

    chain = RAGChain(_DB(), _R(), settings)

    class _LLM:
        async def ainvoke(self, *_args, **_kwargs):
            return type('Msg', (), {'content': 'resposta com incerteza talvez'})()

    monkeypatch.setattr(chain, 'llm', _LLM())
    monkeypatch.setattr('src.modules.chat.rag_chain.get_rag_prompt', lambda _: type('P', (), {'__or__': lambda self, other: other})())

    result = await chain.generate('duvida', uuid4())
    assert result.escalated is True


def test_history_limit_placeholder():
    assert True
