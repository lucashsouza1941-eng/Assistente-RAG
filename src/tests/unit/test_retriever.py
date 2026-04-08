from __future__ import annotations

import pytest

from src.modules.knowledge.retriever import RetrieverService


class _Redis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value


class _Result:
    def mappings(self):
        return self

    def all(self):
        return [
            {
                'id': 'chunk-1',
                'content': 'conteudo',
                'score': 0.9,
                'document_title': 'Doc A',
                'metadata': {'page': 1},
            }
        ]


class _DB:
    async def execute(self, *args, **kwargs):
        return _Result()


@pytest.mark.asyncio
async def test_score_and_threshold():
    service = RetrieverService(db=_DB(), redis=_Redis(), settings=type('S', (), {'openai_api_key': 'x'})())
    service._get_query_embedding = lambda q: [0.1] * 1536
    result = await service.search('duvida', top_k=5, threshold=0.7)
    assert result[0].score == 0.9


@pytest.mark.asyncio
async def test_threshold_one_returns_empty(monkeypatch):
    class _EmptyDB:
        async def execute(self, *args, **kwargs):
            class E:
                def mappings(self):
                    return self

                def all(self):
                    return []

            return E()

    service = RetrieverService(db=_EmptyDB(), redis=_Redis(), settings=type('S', (), {'openai_api_key': 'x'})())
    service._get_query_embedding = lambda q: [0.1] * 1536
    result = await service.search('duvida', top_k=5, threshold=1.0)
    assert result == []


@pytest.mark.asyncio
async def test_cache_hit_does_not_call_openai(monkeypatch):
    redis = _Redis()
    service = RetrieverService(db=_DB(), redis=redis, settings=type('S', (), {'openai_api_key': 'x'})())

    called = {'value': False}

    async def _bad(*args, **kwargs):
        called['value'] = True
        raise AssertionError('Should not call OpenAI')

    await redis.set('rag:query_embedding:' + __import__('hashlib').sha256('q'.encode()).hexdigest(), '[0.1,0.1]')
    service.openai.embeddings.create = _bad
    _ = await service._get_query_embedding('q')
    assert called['value'] is False
