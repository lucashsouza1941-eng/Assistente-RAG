from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.core.encryption import decrypt_value, encrypt_value
from src.dependencies import get_settings
from src.modules.settings.models import Setting


# Legado: chaves aglomeradas `panel_*` (painel antigo). Preferir chaves `categoria.campo` (ex.: `ai.model`, `bot.clinic_name`).
_PANEL_KEY_CATEGORY: dict[str, str] = {
    'panel_bot': 'bot',
    'panel_ai': 'ai',
    'panel_whatsapp': 'whatsapp',
    'panel_notifications': 'notifications',
}

_VALID_CATEGORY_PREFIXES = frozenset({'bot', 'ai', 'whatsapp', 'notifications'})

# Segredos WhatsApp em `settings.value` (JSONB): cifrados em repouso; IDs públicos ficam em claro.
_SETTINGS_SECRET_KEYS = frozenset({'whatsapp.access_token', 'whatsapp.verify_token'})


def _maybe_encrypt_stored(key: str, value: dict) -> dict:
    if key not in _SETTINGS_SECRET_KEYS:
        return value
    v = value.get('v')
    if isinstance(v, str) and v:
        key_mat = get_settings().settings_encryption_key
        return {**value, 'v': encrypt_value(v, key_mat)}
    return value


def _maybe_decrypt_read(key: str, value: dict) -> dict:
    if key not in _SETTINGS_SECRET_KEYS:
        return value
    v = value.get('v')
    if isinstance(v, str) and v:
        key_mat = get_settings().settings_encryption_key
        return {**value, 'v': decrypt_value(v, key_mat)}
    return value


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

    def value_for_api(self, key: str, value: object) -> object:
        """Devolve `value` como no armazenamento interno, com segredos decifrados para o painel/API."""
        if not isinstance(value, dict):
            return value
        return _maybe_decrypt_read(key, value)

    async def get_category(self, category: str) -> list[Setting]:
        return list((await self.db.execute(select(Setting).where(Setting.category == category))).scalars().all())

    async def get_category_values(self, category: str) -> dict[str, object]:
        items = await self.get_category(category)
        out: dict[str, object] = {}
        for item in items:
            key_tail = item.key.split('.', 1)[1] if item.key.startswith(f'{category}.') and '.' in item.key else item.key
            raw = item.value
            if isinstance(raw, dict):
                raw = _maybe_decrypt_read(item.key, raw)
            value = raw.get('v') if isinstance(raw, dict) and 'v' in raw else raw
            out[key_tail] = value
        return out

    async def update(self, key: str, value: dict) -> Setting:
        value = _maybe_encrypt_stored(key, value)
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

    async def seed_defaults(self, settings: Settings) -> None:
        defaults: dict[str, object] = {
            'ai.model': 'gpt-4o',
            'ai.temperature': 0.3,
            'ai.max_tokens': 500,
            'ai.escalation_threshold': 0.70,
            'bot.clinic_name': settings.clinic_name,
            'bot.welcome_message': 'Ola! Sou a assistente virtual da clinica. Como posso ajudar?',
            'bot.closing_message': 'Obrigado pelo contato! Ate logo.',
            'bot.business_hours_start': '08:00',
            'bot.business_hours_end': '18:00',
            'bot.respond_outside_hours': False,
            'bot.work_days': {
                'seg': True,
                'ter': True,
                'qua': True,
                'qui': True,
                'sex': True,
                'sab': False,
                'dom': False,
            },
        }
        for key, value in defaults.items():
            existing = await self.db.scalar(select(Setting).where(Setting.key == key))
            if existing is None:
                self.db.add(
                    Setting(
                        key=key,
                        value={'v': value},
                        category=key.split('.', 1)[0],
                    )
                )
