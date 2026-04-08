from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_upload_index_search_delete_flow(client):
    resp = await client.post('/knowledge/documents', data={'title': 'Doc', 'type': 'GENERAL', 'content_hash': 'b' * 64}, files={'file': ('a.txt', b'Texto odontologico muito longo ' * 20, 'text/plain')})
    assert resp.status_code == 202

    doc_id = resp.json()['id']
    _ = await client.post(f'/knowledge/documents/{doc_id}/reindex')

    search = await client.post('/knowledge/search', json={'query': 'limpeza', 'top_k': 3, 'threshold': 0.1})
    assert search.status_code == 200

    first_delete = await client.delete(f'/knowledge/documents/{doc_id}')
    assert first_delete.status_code == 204

    second_delete = await client.delete(f'/knowledge/documents/{doc_id}')
    assert second_delete.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_hash_returns_409(client):
    payload = {'title': 'Doc', 'type': 'GENERAL', 'content_hash': 'c' * 64}
    files = {'file': ('a.txt', b'Texto odontologico muito longo ' * 20, 'text/plain')}
    assert (await client.post('/knowledge/documents', data=payload, files=files)).status_code == 202
    assert (await client.post('/knowledge/documents', data=payload, files=files)).status_code == 409
