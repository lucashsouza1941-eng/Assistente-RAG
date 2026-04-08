from __future__ import annotations

import hashlib
import hmac

import pytest

from src.core.exceptions import WebhookSignatureError
from src.modules.whatsapp.validators import validate_webhook_signature_raw


def test_valid_signature_ok():
    payload = b'{"ok":1}'
    secret = 'abc'
    signature = 'sha256=' + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    validate_webhook_signature_raw(payload, signature, secret)


def test_invalid_signature_raises():
    with pytest.raises(WebhookSignatureError):
        validate_webhook_signature_raw(b'{"ok":1}', 'sha256=invalid', 'abc')


def test_modified_payload_fails():
    secret = 'abc'
    payload = b'original'
    signature = 'sha256=' + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    with pytest.raises(WebhookSignatureError):
        validate_webhook_signature_raw(b'modified', signature, secret)
