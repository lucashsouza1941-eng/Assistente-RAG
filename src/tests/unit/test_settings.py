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


@pytest.mark.asyncio
async def test_whatsapp_access_token_encrypted_at_rest(async_session):
    plain = 'graph-token-plain'
    s = await SettingsService(async_session).update('whatsapp.access_token', {'v': plain})
    await async_session.refresh(s)
    raw = s.value['v']
    assert isinstance(raw, str)
    assert raw.startswith('OBENC1:')
    assert raw != plain

    vals = await SettingsService(async_session).get_category_values('whatsapp')
    assert vals['access_token'] == plain

    svc = SettingsService(async_session)
    assert svc.value_for_api('whatsapp.access_token', s.value)['v'] == plain


@pytest.mark.asyncio
async def test_whatsapp_phone_number_id_not_encrypted(async_session):
    s = await SettingsService(async_session).update('whatsapp.phone_number_id', {'v': '123456789'})
    assert s.value['v'] == '123456789'


@pytest.mark.asyncio
async def test_legacy_plain_whatsapp_token_still_readable(async_session):
    async_session.add(
        Setting(key='whatsapp.verify_token', category='whatsapp', value={'v': 'legacy-verify-plain'}),
    )
    await async_session.commit()

    vals = await SettingsService(async_session).get_category_values('whatsapp')
    assert vals['verify_token'] == 'legacy-verify-plain'
