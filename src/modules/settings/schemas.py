from __future__ import annotations

from pydantic import BaseModel


class SettingResponse(BaseModel):
    id: int
    key: str
    value: dict
    category: str


class SettingUpdate(BaseModel):
    value: dict
