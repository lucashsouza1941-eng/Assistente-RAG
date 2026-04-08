from __future__ import annotations

import hashlib
import hmac

import pytest

from src.core.exceptions import WebhookSignatureError
from src.modules.whatsapp.validators import validate_webhook_signature_raw


def test_signature_valida():
    payload = b'{}'
    secret = 'abc'
    sig = 'sha256=' + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    validate_webhook_signature_raw(payload, sig, secret)


def test_signature_invalida():
    with pytest.raises(WebhookSignatureError):
        validate_webhook_signature_raw(b'{}', 'sha256=bad', 'abc')
