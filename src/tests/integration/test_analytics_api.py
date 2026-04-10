from __future__ import annotations

import pytest

from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole


@pytest.mark.asyncio
async def test_kpis_endpoint(client):
    res = await client.get('/analytics/kpis', params={'period': 'today'})
    assert res.status_code == 200
    data = res.json()
    assert 'total_conversations' in data
    assert 'resolution_rate' in data
    assert 'avg_response_time_ms' in data
    assert 'patients_served' in data
    assert 'escalation_rate' in data


@pytest.mark.asyncio
async def test_volume_hour(client):
    res = await client.get('/analytics/volume', params={'granularity': 'hour'})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 24
    assert data[0]['timestamp'] == '00:00'
    assert 'count' in data[0]


@pytest.mark.asyncio
async def test_volume_day(client):
    res = await client.get('/analytics/volume', params={'granularity': 'day'})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    for row in data:
        assert 'timestamp' in row
        assert 'count' in row


@pytest.mark.asyncio
async def test_categories(client, async_session):
    conv = Conversation(whatsapp_number_hash='e' * 64, status=ConversationStatus.ACTIVE)
    async_session.add(conv)
    await async_session.flush()
    async_session.add(
        Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content='qual o valor da limpeza odontologica',
        ),
    )
    await async_session.commit()

    res = await client.get('/analytics/categories')
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        total_pct = sum(item['percentage'] for item in data)
        assert abs(total_pct - 100.0) < 1.0


@pytest.mark.asyncio
async def test_top_questions(client, async_session):
    conv = Conversation(whatsapp_number_hash='f' * 64, status=ConversationStatus.ACTIVE)
    async_session.add(conv)
    await async_session.flush()
    for i in range(7):
        async_session.add(
            Message(
                conversation_id=conv.id,
                role=MessageRole.USER,
                content=f'Questao API {i} ' + 'y' * 12,
            ),
        )
    await async_session.commit()

    res = await client.get('/analytics/top-questions', params={'limit': 5})
    assert res.status_code == 200
    data = res.json()
    assert len(data) <= 5
