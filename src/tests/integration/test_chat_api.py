from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select

from src.dependencies import get_db_session, get_redis
from src.main import create_app
from src.modules.chat.models import Conversation, ConversationStatus, Message


@pytest.mark.asyncio
async def test_message_endpoint(client):
    res = await client.post('/chat/message', json={'message': 'oi'})
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_unread_count_requires_api_key(async_session, redis_client):
    app = create_app()
    app.state.redis_client = redis_client

    async def _db_override():
        yield async_session

    async def _redis_override():
        return redis_client

    app.dependency_overrides[get_db_session] = _db_override
    app.dependency_overrides[get_redis] = _redis_override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            res = await ac.get('/conversations/unread-count')
        assert res.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unread_count_returns_total_unread(client, async_session):
    await async_session.execute(delete(Message))
    await async_session.execute(delete(Conversation))
    await async_session.commit()

    async_session.add_all(
        [
            Conversation(whatsapp_number_hash='a' * 64, status=ConversationStatus.ACTIVE, is_read=False),
            Conversation(whatsapp_number_hash='b' * 64, status=ConversationStatus.ACTIVE, is_read=False),
            Conversation(whatsapp_number_hash='c' * 64, status=ConversationStatus.ACTIVE, is_read=True),
        ]
    )
    await async_session.commit()

    res = await client.get('/conversations/unread-count')
    assert res.status_code == 200
    assert res.json() == {'count': 2}


@pytest.mark.asyncio
async def test_list_messages_marks_conversation_read(client, async_session):
    await async_session.execute(delete(Message))
    await async_session.execute(delete(Conversation))
    await async_session.commit()

    conv = Conversation(whatsapp_number_hash='z' * 64, status=ConversationStatus.ACTIVE, is_read=False)
    async_session.add(conv)
    await async_session.commit()

    res = await client.get(f'/chat/conversations/{conv.id}/messages')
    assert res.status_code == 200

    n_unread = await async_session.scalar(select(func.count(Conversation.id)).where(Conversation.is_read.is_(False)))
    assert int(n_unread or 0) == 0
