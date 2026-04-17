from __future__ import annotations

from uuid import UUID

import pytest

from src.dependencies import get_settings
from src.modules.knowledge.indexer import IndexingService


@pytest.mark.asyncio
async def test_upload_index_search_happy_path(client):
    """Upload → indexação (mesmo fluxo do worker) → busca semântica (MinIO mock em conftest)."""
    settings = get_settings()
    payload = {'title': 'Doc E2E', 'type': 'GENERAL', 'content_hash': '9' * 64}
    files = {'file': ('e2e.txt', b'conteudo semantico teste pipeline rag odontologia ' * 5, 'text/plain')}
    res = await client.post('/knowledge/documents', data=payload, files=files)
    assert res.status_code == 202
    doc_id = res.json()['id']

    await IndexingService().index_document(UUID(doc_id), settings)

    search = await client.post(
        '/knowledge/search',
        json={'query': 'odontologia pipeline', 'top_k': 5, 'threshold': 0.1},
    )
    assert search.status_code == 200
    data = search.json()
    assert isinstance(data, list)
    assert len(data) >= 1
