from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str
    vector_store: str
