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


class _DB:
    def __init__(self, rows):
        self.rows = rows

    async def execute(self, *args, **kwargs):
        class _R:
            def __init__(self, rows):
                self._rows = rows

            def mappings(self):
                return self

            def all(self):
                return self._rows

        return _R(self.rows)


@pytest.mark.asyncio
async def test_score_correct():
    rows = [{'id': '1', 'content': 'c', 'score': 0.9, 'document_title': 'd', 'metadata': {}}]
    svc = RetrieverService(_DB(rows), _Redis(), type('S', (), {'openai_api_key': 'x'})())
    svc._query_embedding = lambda q: [0.1] * 1536
    res = await svc.search('q')
    assert res[0].score == 0.9


@pytest.mark.asyncio
async def test_threshold_one_empty():
    svc = RetrieverService(_DB([]), _Redis(), type('S', (), {'openai_api_key': 'x'})())
    svc._query_embedding = lambda q: [0.1] * 1536
    res = await svc.search('q', threshold=1.0)
    assert res == []
