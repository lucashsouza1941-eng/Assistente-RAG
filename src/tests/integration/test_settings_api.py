from __future__ import annotations

import pytest

from src.modules.settings.models import Setting


@pytest.mark.asyncio
async def test_get_settings_bot(client, async_session):
    async_session.add(
        Setting(key='panel_bot', category='bot', value={'name': 'Test'}),
    )
    await async_session.commit()

    res = await client.get('/settings/bot')
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]['key'] == 'panel_bot'


@pytest.mark.asyncio
async def test_get_settings_invalid_category(client):
    res = await client.get('/settings/invalid')
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_update_setting(client, async_session):
    res = await client.put('/settings/bot.name', json={'value': {'display': 'Novo nome'}})
    assert res.status_code == 200
    data = res.json()
    assert data['key'] == 'bot.name'
    assert data['value'] == {'display': 'Novo nome'}
    assert data['category'] == 'bot'


@pytest.mark.asyncio
async def test_update_nonexistent(client):
    res = await client.put('/settings/nao_existe', json={'value': {'a': 1}})
    assert res.status_code == 404
