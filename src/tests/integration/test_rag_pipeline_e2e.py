from __future__ import annotations

from uuid import UUID

import pytest
from arq.constants import default_queue_name
from sqlalchemy import func, select

from src.modules.knowledge.models import DocumentChunk
from src.workers.indexing_worker import index_document_job


@pytest.mark.asyncio
async def test_upload_index_search_happy_path(client, redis_client, async_session):
    """Upload → enqueue ARQ → handler do worker → chunks → busca semântica."""
    payload = {'title': 'Doc E2E', 'type': 'GENERAL', 'content_hash': '9' * 64}
    body = b'conteudo semantico teste pipeline rag odontologia ' * 5
    files = {'file': ('e2e.txt', body, 'text/plain')}
    res = await client.post('/knowledge/documents', data=payload, files=files)
    assert res.status_code == 202
    doc_id = res.json()['id']

    pending = await redis_client.zcard(default_queue_name)
    assert pending >= 1, 'esperado pelo menos um job pendente na fila ARQ (sorted set)'

    await index_document_job({'redis': redis_client}, doc_id)

    chunk_count = await async_session.scalar(
        select(func.count())
        .select_from(DocumentChunk)
        .where(DocumentChunk.document_id == UUID(doc_id)),
    )
    assert chunk_count is not None and chunk_count >= 1

    search = await client.post(
        '/knowledge/search',
        json={'query': 'odontologia pipeline', 'top_k': 5, 'threshold': 0.1},
    )
    assert search.status_code == 200
    data = search.json()
    assert isinstance(data, list)
    assert len(data) >= 1
