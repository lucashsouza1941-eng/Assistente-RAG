from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_duplicate_409(client):
    payload = {'title': 'Doc', 'type': 'GENERAL', 'content_hash': 'a' * 64}
    files = {'file': ('a.txt', b'conteudo ' * 20, 'text/plain')}
    assert (await client.post('/knowledge/documents', data=payload, files=files)).status_code == 202
    assert (await client.post('/knowledge/documents', data=payload, files=files)).status_code == 409
