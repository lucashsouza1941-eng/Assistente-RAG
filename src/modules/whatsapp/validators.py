from __future__ import annotations

import hashlib
import hmac

from fastapi import Depends, Header, HTTPException, Request, status

from src.config import Settings
from src.core.exceptions import WebhookSignatureError
from src.dependencies import get_settings


def validate_webhook_signature_raw(payload: bytes, signature: str, app_secret: str) -> None:
    expected_digest = hmac.new(app_secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()
    expected = f'sha256={expected_digest}'
    if not hmac.compare_digest(expected, signature):
        raise WebhookSignatureError()


async def validate_webhook_signature(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias='X-Hub-Signature-256'),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_hub_signature_256:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Missing signature')

    payload = await request.body()
    try:
        validate_webhook_signature_raw(payload, x_hub_signature_256, settings.whatsapp_app_secret)
    except WebhookSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
