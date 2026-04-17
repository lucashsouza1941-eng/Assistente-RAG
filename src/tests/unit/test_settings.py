from __future__ import annotations

import pytest

from src.modules.settings.models import Setting
from src.modules.settings.service import SettingsService


@pytest.mark.asyncio
async def test_get_category(async_session):
    async_session.add(
        Setting(key='bot.clinic_name', category='bot', value={'v': 'Bot'}),
    )
    await async_session.commit()

    rows = await SettingsService(async_session).get_category('bot')
    assert len(rows) == 1
    assert rows[0].key == 'bot.clinic_name'
    assert rows[0].category == 'bot'


@pytest.mark.asyncio
async def test_update_setting(async_session):
    s = await SettingsService(async_session).update('bot.clinic_name', {'v': 'Novo'})
    assert s.value == {'v': 'Novo'}

    again = await SettingsService(async_session).update('bot.clinic_name', {'v': 'Outro'})
    assert again.value == {'v': 'Outro'}


@pytest.mark.asyncio
async def test_update_nonexistent_key(async_session):
    with pytest.raises(ValueError, match='nao_existe'):
        await SettingsService(async_session).update('nao_existe', {'x': 1})
