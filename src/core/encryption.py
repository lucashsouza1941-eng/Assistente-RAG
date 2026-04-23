"""Fernet-based helpers for settings secrets at rest (legacy plaintext supported)."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from src.core.logging import get_logger

_PREFIX = 'OBENC1:'
log = get_logger(module='core.encryption')


def _fernet(key_material: str) -> Fernet:
    return Fernet(key_material.strip().encode('ascii'))


def encrypt_value(plaintext: str, key_material: str) -> str:
    if not plaintext:
        return plaintext
    f = _fernet(key_material)
    return _PREFIX + f.encrypt(plaintext.encode('utf-8')).decode('ascii')


def decrypt_value(ciphertext_or_plain: str, key_material: str) -> str:
    if not ciphertext_or_plain or not ciphertext_or_plain.startswith(_PREFIX):
        return ciphertext_or_plain
    raw = ciphertext_or_plain[len(_PREFIX) :]
    f = _fernet(key_material)
    try:
        return f.decrypt(raw.encode('ascii')).decode('utf-8')
    except InvalidToken:
        preview = f'{ciphertext_or_plain[:20]}...'
        log.error(
            'decrypt_failed_invalid_token',
            hint='Possível rotação de SETTINGS_ENCRYPTION_KEY incorreta',
            preview=preview,
            metadata={'prefix': _PREFIX, 'value_length': len(ciphertext_or_plain)},
        )
        # Trade-off consciente: mantemos o ciphertext para não quebrar migração/legado,
        # mas registramos erro estruturado para tornar falhas de rotação/chave visíveis.
        return ciphertext_or_plain


def encrypt(value: str) -> str:
    from src.dependencies import get_settings

    return encrypt_value(value, get_settings().settings_encryption_key)


def decrypt(value: str) -> str:
    from src.dependencies import get_settings

    return decrypt_value(value, get_settings().settings_encryption_key)
