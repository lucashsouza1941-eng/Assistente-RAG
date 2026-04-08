from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_message_endpoint(client):
    res = await client.post('/chat/message', json={'message': 'oi'})
    assert res.status_code == 200
