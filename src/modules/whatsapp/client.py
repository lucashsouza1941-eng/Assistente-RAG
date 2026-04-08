from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import Settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class MessageResponse:
    message_id: str
    status_code: int


class MetaAPIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = f'https://graph.facebook.com/v20.0/{settings.whatsapp_phone_number_id}'
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=30.0),
            headers={
                'Authorization': f'Bearer {settings.whatsapp_access_token}',
                'Content-Type': 'application/json',
            },
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def send_text_message(self, to: str, text: str) -> MessageResponse:
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'text',
            'text': {'body': text},
        }
        return await self._post_message(payload, to)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def send_template_message(self, to: str, template_name: str, components: list) -> MessageResponse:
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': 'pt_BR'},
                'components': components,
            },
        }
        return await self._post_message(payload, to)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def mark_as_read(self, message_id: str) -> None:
        start = time.perf_counter()
        response = await self._client.post(
            f'{self.base_url}/messages',
            json={
                'messaging_product': 'whatsapp',
                'status': 'read',
                'message_id': message_id,
            },
        )
        response.raise_for_status()
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info('meta.mark_as_read', message_id_returned=message_id, status_code=response.status_code, duration_ms=duration_ms)

    async def _post_message(self, payload: dict, to: str) -> MessageResponse:
        start = time.perf_counter()
        response = await self._client.post(f'{self.base_url}/messages', json=payload)
        response.raise_for_status()

        body = response.json()
        message_id = body.get('messages', [{}])[0].get('id', '')
        duration_ms = int((time.perf_counter() - start) * 1000)
        to_hash = hashlib.sha256(to.encode('utf-8')).hexdigest()
        logger.info('meta.send_message', to_hash=to_hash, message_id_returned=message_id, status_code=response.status_code, duration_ms=duration_ms)
        return MessageResponse(message_id=message_id, status_code=response.status_code)
