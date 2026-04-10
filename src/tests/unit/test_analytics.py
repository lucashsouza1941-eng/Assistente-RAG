from __future__ import annotations

from datetime import datetime

import pytest

from src.modules.analytics.service import AnalyticsService
from src.modules.chat.models import Conversation, ConversationStatus, Message, MessageRole


@pytest.mark.asyncio
async def test_categories_classification(async_session):
    conv = Conversation(whatsapp_number_hash='a' * 64, status=ConversationStatus.ACTIVE)
    async_session.add(conv)
    await async_session.flush()
    async_session.add(
        Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content='Quero agendar uma consulta para amanha',
        ),
    )
    await async_session.commit()

    out = await AnalyticsService(async_session).categories()
    ag = next((c for c in out if c.category == 'agendamento'), None)
    assert ag is not None
    assert ag.count >= 1


@pytest.mark.asyncio
async def test_categories_outros(async_session):
    conv = Conversation(whatsapp_number_hash='b' * 64, status=ConversationStatus.ACTIVE)
    async_session.add(conv)
    await async_session.flush()
    async_session.add(
        Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content='lorem ipsum dolor sit amet',
        ),
    )
    await async_session.commit()

    out = await AnalyticsService(async_session).categories()
    outros = next((c for c in out if c.category == 'outros'), None)
    assert outros is not None
    assert outros.count >= 1


@pytest.mark.asyncio
async def test_volume_hour_granularity(async_session):
    pts = await AnalyticsService(async_session).volume('hour')
    assert len(pts) == 24
    assert [p.timestamp for p in pts] == [f'{h:02d}:00' for h in range(24)]
    assert all(isinstance(p.count, int) for p in pts)


@pytest.mark.asyncio
async def test_top_questions_limit(async_session):
    conv = Conversation(whatsapp_number_hash='c' * 64, status=ConversationStatus.ACTIVE)
    async_session.add(conv)
    await async_session.flush()
    for i in range(6):
        async_session.add(
            Message(
                conversation_id=conv.id,
                role=MessageRole.USER,
                content=f'Pergunta distinta numero {i} ' + 'x' * 10,
            ),
        )
    await async_session.commit()

    out = await AnalyticsService(async_session).top_questions(5)
    assert len(out) <= 5
    assert len(out) == 5


@pytest.mark.asyncio
async def test_volume_hour_counts_buckets(async_session):
    conv = Conversation(whatsapp_number_hash='d' * 64, status=ConversationStatus.ACTIVE)
    async_session.add(conv)
    await async_session.flush()
    async_session.add(
        Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content='msg',
        ),
    )
    await async_session.commit()

    pts = await AnalyticsService(async_session).volume('hour')
    hour = datetime.now().hour
    assert pts[hour].count >= 1
