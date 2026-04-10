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


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_category(self, category: str) -> list[Setting]:
        return list((await self.db.execute(select(Setting).where(Setting.category == category))).scalars().all())

    async def update(self, key: str, value: dict) -> Setting:
        setting = await self.db.scalar(select(Setting).where(Setting.key == key))
        if setting is None:
            category = _PANEL_KEY_CATEGORY.get(key, 'bot')
            setting = Setting(key=key, category=category, value=value)
            self.db.add(setting)
        else:
            setting.value = value
        await self.db.commit()
        await self.db.refresh(setting)
        return setting
