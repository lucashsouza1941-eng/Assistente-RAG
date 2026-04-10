from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import Settings
from src.core.logging import get_logger

log = get_logger(module='whatsapp.client')


@dataclass(slots=True)
class MessageResponse:
    message_id: str
    status_code: int


class MetaAPIClient:
    def __init__(self, settings: Settings) -> None:
        self.base = f'https://graph.facebook.com/v20.0/{settings.whatsapp_phone_number_id}'
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5, read=30, write=30, pool=30),
            headers={'Authorization': f'Bearer {settings.whatsapp_access_token}'},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def send_text_message(self, to: str, text: str) -> MessageResponse:
        start = time.perf_counter()
        r = await self._client.post(f'{self.base}/messages', json={'messaging_product': 'whatsapp', 'to': to, 'type': 'text', 'text': {'body': text}})
        r.raise_for_status()
        mid = r.json().get('messages', [{}])[0].get('id', '')
        log.info('whatsapp.send_text', duration_ms=int((time.perf_counter()-start)*1000), metadata={'to_hash': hashlib.sha256(to.encode()).hexdigest(), 'message_id_returned': mid, 'status_code': r.status_code})
        return MessageResponse(message_id=mid, status_code=r.status_code)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def send_template_message(self, to: str, template_name: str, components: list) -> MessageResponse:
        start = time.perf_counter()
        r = await self.client.post(f'{self.base}/messages', json={'messaging_product': 'whatsapp', 'to': to, 'type': 'template', 'template': {'name': template_name, 'language': {'code': 'pt_BR'}, 'components': components}})
        r.raise_for_status()
        mid = r.json().get('messages', [{}])[0].get('id', '')
        log.info('whatsapp.send_template', duration_ms=int((time.perf_counter()-start)*1000), metadata={'to_hash': hashlib.sha256(to.encode()).hexdigest(), 'message_id_returned': mid, 'status_code': r.status_code})
        return MessageResponse(message_id=mid, status_code=r.status_code)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def mark_as_read(self, message_id: str) -> None:
        start = time.perf_counter()
        r = await self._client.post(f'{self.base}/messages', json={'messaging_product': 'whatsapp', 'status': 'read', 'message_id': message_id})
        r.raise_for_status()
        log.info('whatsapp.mark_read', duration_ms=int((time.perf_counter()-start)*1000), metadata={'message_id_returned': message_id, 'status_code': r.status_code})
