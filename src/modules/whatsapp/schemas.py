from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class WebhookText(BaseModel):
    body: str


class WebhookMessage(BaseModel):
    id: str
    from_: str = Field(alias='from')
    timestamp: str
    type: str
    text: WebhookText | None = None


class WebhookStatus(BaseModel):
    id: str
    status: str
    timestamp: str
    recipient_id: str


class ValueModel(BaseModel):
    messages: list[WebhookMessage] = []
    statuses: list[WebhookStatus] = []


class ChangeModel(BaseModel):
    value: ValueModel


class EntryModel(BaseModel):
    changes: list[ChangeModel]


class WebhookPayload(BaseModel):
    object: str
    entry: list[EntryModel]
    message: WebhookMessage | None = None

    @model_validator(mode='after')
    def extract(self):
        for e in self.entry:
            for c in e.changes:
                if c.value.messages:
                    self.message = c.value.messages[0]
                    return self
        return self


class WebhookAckResponse(BaseModel):
    message: str
