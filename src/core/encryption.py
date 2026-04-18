"""Fernet-based helpers for settings secrets at rest (legacy plaintext supported)."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

_PREFIX = 'OBENC1:'


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
        return ciphertext_or_plain


def encrypt(value: str) -> str:
    from src.dependencies import get_settings

    return encrypt_value(value, get_settings().settings_encryption_key)


def decrypt(value: str) -> str:
    from src.dependencies import get_settings

    return decrypt_value(value, get_settings().settings_encryption_key)
