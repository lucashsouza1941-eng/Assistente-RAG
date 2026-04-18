from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SettingResponse(BaseModel):
    id: int
    key: str
    value: dict[str, Any]
    category: str


class SettingUpdate(BaseModel):
    value: dict[str, Any]
