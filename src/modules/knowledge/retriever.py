from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from openai import AsyncOpenAI
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    document_title: str
    metadata: dict


class RetrieverService:
    def __init__(self, db: AsyncSession, redis: Redis, settings: Settings) -> None:
        self.db = db
        self.redis = redis
        self.settings = settings
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)

    async def search(self, query: str, top_k: int = 5, threshold: float = 0.7) -> list[RetrievedChunk]:
        query_embedding = await self._get_query_embedding(query)
        sql = text(
            """
            SELECT
                dc.id,
                dc.content,
                dc.metadata,
                d.title AS document_title,
                1 - (dc.embedding <=> CAST(:query_vec AS vector)) AS score
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE 1 - (dc.embedding <=> CAST(:query_vec AS vector)) > :threshold
            ORDER BY score DESC
            LIMIT :top_k
            """
        )

        query_vec = '[' + ','.join(f'{value:.8f}' for value in query_embedding) + ']'
        result = await self.db.execute(
            sql,
            {'query_vec': query_vec, 'threshold': threshold, 'top_k': top_k},
        )
        rows = result.mappings().all()

        chunks = [
            RetrievedChunk(
                chunk_id=str(row['id']),
                content=row['content'],
                score=float(row['score']),
                document_title=row['document_title'],
                metadata=row['metadata'] or {},
            )
            for row in rows
        ]

        top_score = max((chunk.score for chunk in chunks), default=0.0)
        logger.info(
            'retriever.search',
            query_preview=query[:50],
            chunks_found=len(chunks),
            top_score=round(top_score, 4),
            threshold_used=threshold,
        )
        return chunks

    async def _get_query_embedding(self, query: str) -> list[float]:
        key = f'rag:query_embedding:{hashlib.sha256(query.encode("utf-8")).hexdigest()}'
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        response = await self.openai.embeddings.create(
            model='text-embedding-3-small',
            input=[query],
        )
        embedding = response.data[0].embedding
        await self.redis.set(key, json.dumps(embedding), ex=3600)
        return embedding
