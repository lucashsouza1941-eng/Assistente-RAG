from __future__ import annotations

import hashlib
import hmac

import pytest

from src.dependencies import get_settings


@pytest.mark.asyncio
async def test_get_webhook_verify_token(client):
    settings = get_settings()
    resp = await client.get(f'/whatsapp/webhook?hub.mode=subscribe&hub.verify_token={settings.whatsapp_verify_token}&hub.challenge=abc')
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_webhook_wrong_token(client):
    resp = await client.get('/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=abc')
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_invalid_signature_returns_403(client):
    resp = await client.post('/whatsapp/webhook', content='{}', headers={'X-Hub-Signature-256': 'sha256=bad'})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_valid_text_message_returns_200(client):
    settings = get_settings()
    payload = '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"messages":[{"id":"m1","from":"55119999","timestamp":"1","type":"text","text":{"body":"Ola"}}]}}]}]}'
    signature = 'sha256=' + hmac.new(settings.whatsapp_app_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    resp = await client.post('/whatsapp/webhook', content=payload, headers={'X-Hub-Signature-256': signature})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_image_message_ignored(client):
    settings = get_settings()
    payload = '{"object":"whatsapp_business_account","entry":[{"changes":[{"value":{"messages":[{"id":"m2","from":"55119999","timestamp":"1","type":"image"}]}}]}]}'
    signature = 'sha256=' + hmac.new(settings.whatsapp_app_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    resp = await client.post('/whatsapp/webhook', content=payload, headers={'X-Hub-Signature-256': signature})
    assert resp.status_code == 200
