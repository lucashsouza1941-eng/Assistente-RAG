from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_chat_with_existing_conversation_and_sources(client):
    first = await client.post('/chat/message', json={'message': 'Oi'})
    assert first.status_code == 200
    conv_id = first.json()['conversation_id']

    second = await client.post('/chat/message', json={'message': 'Quero agendar', 'conversation_id': conv_id})
    assert second.status_code == 200
    assert 'sources' in second.json()


@pytest.mark.asyncio
async def test_conversation_pagination_and_message_order(client):
    _ = await client.post('/chat/message', json={'message': 'Pergunta 1'})
    page = await client.get('/chat/conversations?page=1&size=10')
    assert page.status_code == 200

    conv = page.json()['items'][0]['id']
    messages = await client.get(f'/chat/conversations/{conv}/messages')
    assert messages.status_code == 200
