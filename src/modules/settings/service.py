from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.settings.models import Setting


_PANEL_KEY_CATEGORY: dict[str, str] = {
    'panel_bot': 'bot',
    'panel_ai': 'ai',
    'panel_whatsapp': 'whatsapp',
    'panel_notifications': 'notifications',
}

_VALID_CATEGORY_PREFIXES = frozenset({'bot', 'ai', 'whatsapp', 'notifications'})


def _category_for_new_key(key: str) -> str:
    if key in _PANEL_KEY_CATEGORY:
        return _PANEL_KEY_CATEGORY[key]
    if '.' in key:
        prefix, _ = key.split('.', 1)
        if prefix in _VALID_CATEGORY_PREFIXES:
            return prefix
    raise ValueError(f'Chave de configuracao nao permitida: {key}')


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_category(self, category: str) -> list[Setting]:
        return list((await self.db.execute(select(Setting).where(Setting.category == category))).scalars().all())

    async def update(self, key: str, value: dict) -> Setting:
        setting = await self.db.scalar(select(Setting).where(Setting.key == key))
        if setting is None:
            category = _category_for_new_key(key)
            setting = Setting(key=key, category=category, value=value)
            self.db.add(setting)
        else:
            setting.value = value
        await self.db.commit()
        await self.db.refresh(setting)
        return setting
