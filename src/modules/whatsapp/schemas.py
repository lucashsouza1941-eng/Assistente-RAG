from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class WebhookValue(BaseModel):
    messages: list[WebhookMessage] = Field(default_factory=list)
    statuses: list[WebhookStatus] = Field(default_factory=list)


class WebhookChange(BaseModel):
    value: WebhookValue


class WebhookEntry(BaseModel):
    changes: list[WebhookChange] = Field(default_factory=list)


class WebhookPayload(BaseModel):
    model_config = ConfigDict(extra='allow')

    object: str
    entry: list[WebhookEntry] = Field(default_factory=list)
    message: WebhookMessage | None = None

    @model_validator(mode='after')
    def extract_message(self) -> 'WebhookPayload':
        for entry in self.entry:
            for change in entry.changes:
                if change.value.messages:
                    self.message = change.value.messages[0]
                    return self
        return self


class MessageResponseSchema(BaseModel):
    message_id: str
    status_code: int


def extract_statuses(payload: WebhookPayload) -> list[WebhookStatus]:
    statuses: list[WebhookStatus] = []
    for entry in payload.entry:
        for change in entry.changes:
            statuses.extend(change.value.statuses)
    return statuses


def to_plain_dict(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(by_alias=True)
