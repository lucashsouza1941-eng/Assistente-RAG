import hashlib
import hmac


def validate_webhook_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    digest = hmac.new(app_secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    expected = f'sha256={digest}'
    return hmac.compare_digest(expected, signature)

