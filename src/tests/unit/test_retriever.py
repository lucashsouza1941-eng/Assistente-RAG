from __future__ import annotations

import pytest
from typing import Any, cast

from src.modules.knowledge.retriever import RetrieverService


class _Redis:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        return self.store.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> None:
        self.store[key] = value


class _DB:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        class _R:
            def __init__(self, rows: list[dict[str, Any]]) -> None:
                self._rows = rows

            def mappings(self) -> "_R":
                return self

            def all(self) -> list[dict[str, Any]]:
                return self._rows

        return _R(self.rows)


@pytest.mark.asyncio
async def test_score_correct():
    rows = [{'id': '1', 'content': 'c', 'score': 0.9, 'document_title': 'd', 'metadata': {}}]
    svc = RetrieverService(cast(Any, _DB(rows)), cast(Any, _Redis()), cast(Any, type('S', (), {'openai_api_key': 'x'})()))
    async def _fake_query_embedding(self: RetrieverService, q: str) -> list[float]:
        return [0.1] * 1536
    svc._query_embedding = _fake_query_embedding.__get__(svc, RetrieverService)  # type: ignore[method-assign]  # bind explícito de método async só para teste.
    res = await svc.search('q')
    assert res[0].score == 0.9


@pytest.mark.asyncio
async def test_threshold_one_empty():
    svc = RetrieverService(cast(Any, _DB([])), cast(Any, _Redis()), cast(Any, type('S', (), {'openai_api_key': 'x'})()))
    async def _fake_query_embedding(self: RetrieverService, q: str) -> list[float]:
        return [0.1] * 1536
    svc._query_embedding = _fake_query_embedding.__get__(svc, RetrieverService)  # type: ignore[method-assign]  # bind explícito de método async só para teste.
    res = await svc.search('q', threshold=1.0)
    assert res == []
