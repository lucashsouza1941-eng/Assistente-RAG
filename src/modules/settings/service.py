from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.settings.models import Setting


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_category(self, category: str) -> list[Setting]:
        result = await self.db.execute(select(Setting).where(Setting.category == category).order_by(Setting.key.asc()))
        return list(result.scalars().all())

    async def update(self, key: str, value: dict) -> Setting:
        setting = await self.db.scalar(select(Setting).where(Setting.key == key))
        if setting is None:
            setting = Setting(key=key, value=value, category='bot')
            self.db.add(setting)
        else:
            setting.value = value
        await self.db.commit()
        await self.db.refresh(setting)
        return setting
