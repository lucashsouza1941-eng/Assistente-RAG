from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, cast

from openai import AsyncOpenAI
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.logging import get_logger

log = get_logger(module='knowledge.retriever')


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    document_title: str
    metadata: dict[str, Any]


class RetrieverService:
    def __init__(self, db: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.db = db
        self.redis = redis
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def search(self, query: str, top_k: int = 5, threshold: float = 0.7) -> list[RetrievedChunk]:
        emb = await self._query_embedding(query)
        query_vec = '[' + ','.join(f'{x:.8f}' for x in emb) + ']'
        stmt = text('SELECT dc.id, dc.content, dc.metadata, d.title AS document_title, 1-(dc.embedding <=> CAST(:query_vec AS vector)) AS score FROM document_chunks dc JOIN documents d ON d.id = dc.document_id WHERE 1-(dc.embedding <=> CAST(:query_vec AS vector)) > :threshold ORDER BY score DESC LIMIT :top_k')
        rows = (await self.db.execute(stmt, {'query_vec': query_vec, 'threshold': threshold, 'top_k': top_k})).mappings().all()
        out = [RetrievedChunk(chunk_id=str(r['id']), content=r['content'], score=float(r['score']), document_title=r['document_title'], metadata=r['metadata'] or {}) for r in rows]
        log.info('retriever.search', metadata={'query_preview': query[:50] + ('...' if len(query) > 50 else ''), 'chunks_found': len(out), 'top_score': max([c.score for c in out], default=0.0), 'threshold_used': threshold})
        return out

    async def _query_embedding(self, query: str) -> list[float]:
        key = f"emb:{hashlib.sha256(query.encode()).hexdigest()}"
        cached = await self.redis.get(key)
        if cached:
            return cast(list[float], json.loads(cached))
        resp = await self.client.embeddings.create(model='text-embedding-3-small', input=[query])
        emb = resp.data[0].embedding
        await self.redis.set(key, json.dumps(emb), ex=3600)
        return emb
