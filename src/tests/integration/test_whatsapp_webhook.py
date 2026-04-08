from __future__ import annotations

import hashlib
import hmac

import pytest

from src.dependencies import get_settings


@pytest.mark.asyncio
async def test_webhook_verify_ok(client):
    s = get_settings()
    r = await client.get(f'/whatsapp/webhook?hub.mode=subscribe&hub.verify_token={s.whatsapp_verify_token}&hub.challenge=abc')
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_invalid_signature_403(client):
    r = await client.post('/whatsapp/webhook', content='{}', headers={'X-Hub-Signature-256': 'sha256=bad'})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_valid_message_200(client):
    s = get_settings()
    payload = '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"messages":[{"id":"m1","from":"55119999","timestamp":"1","type":"text","text":{"body":"Ola"}}]}}]}]}'
    sig = 'sha256=' + hmac.new(s.whatsapp_app_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    r = await client.post('/whatsapp/webhook', content=payload, headers={'X-Hub-Signature-256': sig})
    assert r.status_code == 200
